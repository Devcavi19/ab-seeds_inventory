import { nextSeq, currentSeq } from './db.js';

function itemToWire(row) {
  return {
    id: row.id,
    name: row.name,
    sku: row.sku,
    category: row.category,
    unit: row.unit,
    priceCents: row.price_cents,
    lowStockThreshold: row.low_stock_threshold,
    isArchived: !!row.is_archived,
    updatedAt: row.updated_at,
  };
}

function movementToWire(row) {
  return {
    id: row.id,
    itemId: row.item_id,
    type: row.type,
    qtyDelta: row.qty_delta,
    note: row.note,
    userId: row.user_id,
    username: row.username,
    createdAt: row.created_at,
  };
}

const MOVEMENT_TYPES = new Set(['in', 'out', 'adjustment']);

function validItem(it) {
  return (
    it && typeof it.id === 'string' && it.id &&
    typeof it.name === 'string' && it.name.trim() &&
    typeof it.sku === 'string' &&
    typeof it.updatedAt === 'number' &&
    Number.isFinite(it.priceCents ?? 0) &&
    Number.isFinite(it.lowStockThreshold ?? 0)
  );
}

function validMovement(mv) {
  return (
    mv && typeof mv.id === 'string' && mv.id &&
    typeof mv.itemId === 'string' && mv.itemId &&
    MOVEMENT_TYPES.has(mv.type) &&
    typeof mv.qtyDelta === 'number' && Number.isFinite(mv.qtyDelta) &&
    typeof mv.createdAt === 'number'
  );
}

export function syncHandler(db) {
  const getItem = db.prepare('SELECT * FROM items WHERE id = ?');
  const insertItem = db.prepare(
    `INSERT INTO items (id, name, sku, category, unit, price_cents, low_stock_threshold, is_archived, current_qty, updated_at, server_seq)
     VALUES (@id, @name, @sku, @category, @unit, @price_cents, @low_stock_threshold, @is_archived, 0, @updated_at, @server_seq)`
  );
  const updateItem = db.prepare(
    `UPDATE items SET name=@name, sku=@sku, category=@category, unit=@unit, price_cents=@price_cents,
       low_stock_threshold=@low_stock_threshold, is_archived=@is_archived, updated_at=@updated_at, server_seq=@server_seq
     WHERE id=@id`
  );
  const touchItemSeq = db.prepare('UPDATE items SET server_seq = ? WHERE id = ?');
  const insertMovement = db.prepare(
    `INSERT OR IGNORE INTO movements (id, item_id, type, qty_delta, note, user_id, username, created_at, server_seq)
     VALUES (@id, @item_id, @type, @qty_delta, @note, @user_id, @username, @created_at, @server_seq)`
  );
  const bumpQty = db.prepare('UPDATE items SET current_qty = current_qty + ? WHERE id = ?');
  const pullItems = db.prepare('SELECT * FROM items WHERE server_seq > ? ORDER BY server_seq');
  const pullMovements = db.prepare('SELECT * FROM movements WHERE server_seq > ? ORDER BY server_seq');

  const runSync = db.transaction((user, lastServerSeq, items, movements) => {
    const rejected = { items: [], movements: [] };
    const isAdmin = user.role === 'admin';

    // Items first so movements can reference items pushed in the same request.
    for (const it of items) {
      if (!validItem(it)) {
        rejected.items.push({ id: it?.id ?? null, reason: 'invalid item payload' });
        continue;
      }
      if (!isAdmin) {
        rejected.items.push({ id: it.id, reason: 'only admins can create or edit items' });
        continue;
      }
      const row = {
        id: it.id,
        name: it.name.trim(),
        sku: it.sku.trim(),
        category: (it.category ?? '').trim(),
        unit: (it.unit ?? 'pcs').trim() || 'pcs',
        price_cents: Math.round(it.priceCents ?? 0),
        low_stock_threshold: it.lowStockThreshold ?? 0,
        is_archived: it.isArchived ? 1 : 0,
        updated_at: it.updatedAt,
      };
      const existing = getItem.get(it.id);
      if (!existing) {
        insertItem.run({ ...row, server_seq: nextSeq(db) });
      } else if (row.updated_at >= existing.updated_at) {
        updateItem.run({ ...row, server_seq: nextSeq(db) });
      } else {
        // Stale write loses LWW; bump seq so the pusher pulls back the winning version.
        touchItemSeq.run(nextSeq(db), it.id);
      }
    }

    for (const mv of movements) {
      if (!validMovement(mv)) {
        rejected.movements.push({ id: mv?.id ?? null, reason: 'invalid movement payload' });
        continue;
      }
      if (!getItem.get(mv.itemId)) {
        rejected.movements.push({ id: mv.id, reason: 'unknown item' });
        continue;
      }
      const result = insertMovement.run({
        id: mv.id,
        item_id: mv.itemId,
        type: mv.type,
        qty_delta: mv.qtyDelta,
        note: typeof mv.note === 'string' ? mv.note : '',
        user_id: user.id,
        username: user.username,
        created_at: mv.createdAt,
        server_seq: nextSeq(db),
      });
      if (result.changes > 0) bumpQty.run(mv.qtyDelta, mv.itemId);
    }

    return {
      serverSeq: currentSeq(db),
      items: pullItems.all(lastServerSeq).map(itemToWire),
      movements: pullMovements.all(lastServerSeq).map(movementToWire),
      rejected,
    };
  });

  return (req, res) => {
    const body = req.body ?? {};
    const lastServerSeq = Number.isFinite(body.lastServerSeq) ? body.lastServerSeq : 0;
    const items = Array.isArray(body.items) ? body.items : [];
    const movements = Array.isArray(body.movements) ? body.movements : [];
    res.json(runSync(req.user, lastServerSeq, items, movements));
  };
}
