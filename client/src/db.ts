import Dexie, { type Table } from 'dexie';
import type { Item, Movement, SessionUser } from './domain';

export interface Session {
  token: string;
  user: SessionUser;
}

interface MetaRow {
  key: string;
  value: unknown;
}

class InventoryDb extends Dexie {
  items!: Table<Item, string>;
  movements!: Table<Movement, string>;
  meta!: Table<MetaRow, string>;

  constructor() {
    super('ab-seeds-inventory');
    this.version(1).stores({
      items: 'id, sku, name, category, isArchived, dirty',
      movements: 'id, itemId, createdAt, synced',
      meta: 'key',
    });
  }
}

export const db = new InventoryDb();

export async function getMeta<T>(key: string): Promise<T | undefined> {
  const row = await db.meta.get(key);
  return row?.value as T | undefined;
}

export async function setMeta(key: string, value: unknown): Promise<void> {
  await db.meta.put({ key, value });
}

export async function clearDataTables(): Promise<void> {
  await db.transaction('rw', db.items, db.movements, db.meta, async () => {
    await db.items.clear();
    await db.movements.clear();
    await db.meta.delete('lastServerSeq');
    await db.meta.delete('lastSyncAt');
  });
}
