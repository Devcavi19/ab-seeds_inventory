import { useSyncExternalStore } from 'react';
import { db, getMeta, setMeta, clearDataTables, type Session } from './db';

let session: Session | null | undefined; // undefined = not loaded yet
const listeners = new Set<() => void>();

function emit() {
  for (const fn of listeners) fn();
}

export async function loadSession(): Promise<Session | null> {
  if (session !== undefined) return session;
  session = (await getMeta<Session>('session')) ?? null;
  emit();
  return session;
}

export function getSession(): Session | null {
  return session ?? null;
}

export function getToken(): string | null {
  return session?.token ?? null;
}

export async function login(username: string, password: string): Promise<Session> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `Login failed (${res.status})`);

  const next: Session = { token: body.token, user: body.user };
  // A different user on this device must not inherit the previous user's local data.
  const prevUserId = await getMeta<string>('deviceUserId');
  if (prevUserId && prevUserId !== next.user.id) {
    await clearDataTables();
  }
  await setMeta('deviceUserId', next.user.id);
  await setMeta('session', next);
  session = next;
  emit();
  return next;
}

/** Plain logout keeps local data so unsynced work is never destroyed. */
export async function logout(clearDevice = false): Promise<void> {
  await db.meta.delete('session');
  if (clearDevice) {
    await clearDataTables();
    await db.meta.delete('deviceUserId');
  }
  session = null;
  emit();
}

export function useSession(): Session | null {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => session ?? null
  );
}
