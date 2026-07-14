import { db } from './db';
import { getSession } from './auth';
import { scheduleSync } from './sync';
import type { Item, Movement, MovementType } from './domain';

export interface ItemInput {
  name: string;
  sku: string;
  category: string;
  unit: string;
  priceCents: number;
  lowStockThreshold: number;
}

export async function createItem(input: ItemInput): Promise<string> {
  const id = crypto.randomUUID();
  const item: Item = {
    id,
    ...input,
    isArchived: 0,
    updatedAt: Date.now(),
    dirty: 1,
  };
  await db.items.add(item);
  scheduleSync();
  return id;
}

export async function updateItem(id: string, input: Partial<ItemInput> & { isArchived?: 0 | 1 }): Promise<void> {
  await db.items.update(id, { ...input, updatedAt: Date.now(), dirty: 1 as const });
  scheduleSync();
}

export async function recordMovement(
  itemId: string,
  type: MovementType,
  qtyDelta: number,
  note: string
): Promise<void> {
  const user = getSession()?.user;
  const movement: Movement = {
    id: crypto.randomUUID(),
    itemId,
    type,
    qtyDelta,
    note,
    userId: user?.id ?? '',
    username: user?.username ?? '',
    createdAt: Date.now(),
    synced: 0,
  };
  await db.movements.add(movement);
  scheduleSync();
}
