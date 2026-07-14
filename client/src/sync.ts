import { useSyncExternalStore } from 'react';
import { db, getMeta, setMeta } from './db';
import { getToken } from './auth';
import type { Item, Movement } from './domain';

export interface SyncState {
  online: boolean;
  syncing: boolean;
  pendingCount: number;
  lastSyncAt: number | null;
  needsLogin: boolean;
  error: string | null;
  rejected: { id: string | null; reason: string }[];
}

let state: SyncState = {
  online: navigator.onLine,
  syncing: false,
  pendingCount: 0,
  lastSyncAt: null,
  needsLogin: false,
  error: null,
  rejected: [],
};

const listeners = new Set<() => void>();

function setState(patch: Partial<SyncState>) {
  state = { ...state, ...patch };
  for (const fn of listeners) fn();
}

export function useSyncState(): SyncState {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => state
  );
}

async function refreshPendingCount() {
  const [dirtyItems, unsyncedMovements] = await Promise.all([
    db.items.where('dirty').equals(1).count(),
    db.movements.where('synced').equals(0).count(),
  ]);
  setState({ pendingCount: dirtyItems + unsyncedMovements });
}

interface WireItem {
  id: string;
  name: string;
  sku: string;
  category: string;
  unit: string;
  priceCents: number;
  lowStockThreshold: number;
  isArchived: boolean;
  updatedAt: number;
}

interface WireMovement {
  id: string;
  itemId: string;
  type: Movement['type'];
  qtyDelta: number;
  note: string;
  userId: string;
  username: string;
  createdAt: number;
}

let inFlight: Promise<void> | null = null;

/** Push dirty/unsynced rows and pull everything new. Safe to call at any time. */
export function syncNow(): Promise<void> {
  if (inFlight) return inFlight;
  inFlight = doSync().finally(() => {
    inFlight = null;
  });
  return inFlight;
}

async function doSync(): Promise<void> {
  const token = getToken();
  await refreshPendingCount();
  if (!token) {
    setState({ needsLogin: true });
    return;
  }
  if (!navigator.onLine) return;

  setState({ syncing: true, error: null });
  try {
    const dirtyItems = await db.items.where('dirty').equals(1).toArray();
    const unsyncedMovements = await db.movements.where('synced').equals(0).toArray();
    const lastServerSeq = (await getMeta<number>('lastServerSeq')) ?? 0;

    const res = await fetch('/api/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        lastServerSeq,
        items: dirtyItems.map((it) => ({
          id: it.id,
          name: it.name,
          sku: it.sku,
          category: it.category,
          unit: it.unit,
          priceCents: it.priceCents,
          lowStockThreshold: it.lowStockThreshold,
          isArchived: !!it.isArchived,
          updatedAt: it.updatedAt,
        })),
        movements: unsyncedMovements.map((mv) => ({
          id: mv.id,
          itemId: mv.itemId,
          type: mv.type,
          qtyDelta: mv.qtyDelta,
          note: mv.note,
          createdAt: mv.createdAt,
        })),
      }),
    });

    if (res.status === 401) {
      setState({ needsLogin: true });
      return;
    }
    if (!res.ok) throw new Error(`Sync failed (${res.status})`);

    const body: {
      serverSeq: number;
      items: WireItem[];
      movements: WireMovement[];
      rejected: { items: { id: string | null; reason: string }[]; movements: { id: string | null; reason: string }[] };
    } = await res.json();

    const pushedItemIds = new Set(dirtyItems.map((it) => it.id));
    const pushedItemStamps = new Map(dirtyItems.map((it) => [it.id, it.updatedAt]));
    const pushedMovementIds = new Set(unsyncedMovements.map((mv) => mv.id));

    await db.transaction('rw', db.items, db.movements, db.meta, async () => {
      for (const wire of body.items) {
        const local = await db.items.get(wire.id);
        // Skip rows re-dirtied while the request was in flight — the local
        // edit wins here and gets pushed on the next sync.
        if (local?.dirty === 1 && local.updatedAt !== pushedItemStamps.get(wire.id)) continue;
        const row: Item = {
          id: wire.id,
          name: wire.name,
          sku: wire.sku,
          category: wire.category,
          unit: wire.unit,
          priceCents: wire.priceCents,
          lowStockThreshold: wire.lowStockThreshold,
          isArchived: wire.isArchived ? 1 : 0,
          updatedAt: wire.updatedAt,
          dirty: 0,
        };
        await db.items.put(row);
      }

      // Clear dirty flags for pushed items the pull didn't echo back
      // (only possible for per-row rejects; keep data, stop retrying).
      for (const id of pushedItemIds) {
        const local = await db.items.get(id);
        if (local?.dirty === 1 && local.updatedAt === pushedItemStamps.get(id)) {
          await db.items.update(id, { dirty: 0 as const });
        }
      }

      for (const wire of body.movements) {
        await db.movements.put({
          id: wire.id,
          itemId: wire.itemId,
          type: wire.type,
          qtyDelta: wire.qtyDelta,
          note: wire.note,
          userId: wire.userId,
          username: wire.username,
          createdAt: wire.createdAt,
          synced: 1,
        });
      }

      const rejectedMovementIds = new Set(body.rejected.movements.map((r) => r.id));
      for (const id of pushedMovementIds) {
        if (rejectedMovementIds.has(id)) continue; // leave unsynced; surfaced in UI
        await db.movements.update(id, { synced: 1 as const });
      }

      await setMeta('lastServerSeq', body.serverSeq);
      await setMeta('lastSyncAt', Date.now());
    });

    setState({
      needsLogin: false,
      lastSyncAt: Date.now(),
      rejected: [...body.rejected.items, ...body.rejected.movements],
    });
  } catch (err) {
    // Network failures are normal offline operation — flags stay set, next trigger retries.
    setState({ error: err instanceof Error ? err.message : String(err) });
  } finally {
    setState({ syncing: false });
    await refreshPendingCount();
  }
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

/** Call after every local write: updates the pending badge and schedules a sync. */
export function scheduleSync(): void {
  void refreshPendingCount();
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => void syncNow(), 2000);
}

let started = false;

export function startSyncEngine(): void {
  if (started) return;
  started = true;

  window.addEventListener('online', () => {
    setState({ online: true });
    void syncNow();
  });
  window.addEventListener('offline', () => setState({ online: false }));

  setInterval(() => {
    if (navigator.onLine && !state.syncing) void syncNow();
  }, 60_000);

  void getMeta<number>('lastSyncAt').then((t) => setState({ lastSyncAt: t ?? null }));
  void syncNow();
}
