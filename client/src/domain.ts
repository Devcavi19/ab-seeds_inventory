export type Role = 'admin' | 'user';

export interface SessionUser {
  id: string;
  username: string;
  role: Role;
}

export interface Item {
  id: string;
  name: string;
  sku: string;
  category: string;
  unit: string;
  priceCents: number;
  lowStockThreshold: number;
  isArchived: 0 | 1;
  updatedAt: number;
  dirty: 0 | 1;
}

export type MovementType = 'in' | 'out' | 'adjustment';

export interface Movement {
  id: string;
  itemId: string;
  type: MovementType;
  qtyDelta: number;
  note: string;
  userId: string;
  username: string;
  createdAt: number;
  synced: 0 | 1;
}

/** Sum of movement deltas per item — the single source of truth for quantities. */
export function quantitiesFromMovements(movements: Pick<Movement, 'itemId' | 'qtyDelta'>[]): Map<string, number> {
  const map = new Map<string, number>();
  for (const mv of movements) {
    map.set(mv.itemId, (map.get(mv.itemId) ?? 0) + mv.qtyDelta);
  }
  return map;
}

export function isLowStock(item: Pick<Item, 'lowStockThreshold'>, qty: number): boolean {
  return item.lowStockThreshold > 0 && qty <= item.lowStockThreshold;
}

export function formatPrice(cents: number): string {
  return (cents / 100).toFixed(2);
}

export function formatQty(qty: number): string {
  return Number.isInteger(qty) ? String(qty) : qty.toFixed(2);
}
