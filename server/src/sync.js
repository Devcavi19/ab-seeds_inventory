import { allocateSeqRange, currentSeq } from './db.js';
import { asyncHandler } from './auth.js';

function itemToWire(row) {
  return {
    id: row.id,
    name: row.name,
    sku: row.sku,
    category: row.category,
    unit: row.unit,
    priceCents: Number(row.price_cents),
    lowStockThreshold: Number(row.low_stock_threshold),
    isArchived: !!Number(row.is_archived),
    updatedAt: Number(row.updated_at),
  };
}

function movementToWire(row) {
  return {
    id: row.id,
    itemId: row.item_id,
    type: row.type,
    qtyDelta: Number(row.qty_delta),
    note: row.note,
    userId: row.user_id,
    username: row.username,
    createdAt: Number(row.created_at),
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

async function getItem(tx, id) {
  return (await tx.execute({ sql: 'SELECT * FROM items WHERE id = ?', args: [id] })).rows[0];
}

async function runSync(db, user, lastServerSeq, items, movements) {
  const rejected = { items: [], movements: [] };
  const isAdmin = user.role === 'admin';

  const tx = await db.transaction('write');
  try {
    // Reserve enough sequence numbers for every row we might write, in one
    // round trip. Unused numbers (rejected/duplicate rows) leave gaps, which
    // the cursor-based pull tolerates.
    const maxWrites = items.length + movements.length;
    let seq = maxWrites > 0 ? await allocateSeqRange(tx, maxWrites) : 0;

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
      const args = {
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
      const existing = await getItem(tx, it.id);
      if (!existing) {
        await tx.execute({
          sql: `INSERT INTO items (id, name, sku, category, unit, price_cents, low_stock_threshold, is_archived, current_qty, updated_at, server_seq)
                VALUES (:id, :name, :sku, :category, :unit, :price_cents, :low_stock_threshold, :is_archived, 0, :updated_at, :server_seq)`,
          args: { ...args, server_seq: seq++ },
        });
      } else if (args.updated_at >= Number(existing.updated_at)) {
        await tx.execute({
          sql: `UPDATE items SET name=:name, sku=:sku, category=:category, unit=:unit, price_cents=:price_cents,
                  low_stock_threshold=:low_stock_threshold, is_archived=:is_archived, updated_at=:updated_at, server_seq=:server_seq
                WHERE id=:id`,
          args: { ...args, server_seq: seq++ },
        });
      } else {
        // Stale write loses LWW; bump seq so the pusher pulls back the winning version.
        await tx.execute({ sql: 'UPDATE items SET server_seq = ? WHERE id = ?', args: [seq++, it.id] });
      }
    }

    for (const mv of movements) {
      if (!validMovement(mv)) {
        rejected.movements.push({ id: mv?.id ?? null, reason: 'invalid movement payload' });
        continue;
      }
      if (!(await getItem(tx, mv.itemId))) {
        rejected.movements.push({ id: mv.id, reason: 'unknown item' });
        continue;
      }
      const result = await tx.execute({
        sql: `INSERT OR IGNORE INTO movements (id, item_id, type, qty_delta, note, user_id, username, created_at, server_seq)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        args: [
          mv.id,
          mv.itemId,
          mv.type,
          mv.qtyDelta,
          typeof mv.note === 'string' ? mv.note : '',
          user.id,
          user.username,
          mv.createdAt,
          seq++,
        ],
      });
      if (result.rowsAffected > 0) {
        await tx.execute({
          sql: 'UPDATE items SET current_qty = current_qty + ? WHERE id = ?',
          args: [mv.qtyDelta, mv.itemId],
        });
      }
    }

    const [serverSeq, pulledItems, pulledMovements] = [
      await currentSeq(tx),
      (await tx.execute({ sql: 'SELECT * FROM items WHERE server_seq > ? ORDER BY server_seq', args: [lastServerSeq] })).rows,
      (await tx.execute({ sql: 'SELECT * FROM movements WHERE server_seq > ? ORDER BY server_seq', args: [lastServerSeq] })).rows,
    ];

    await tx.commit();

    return {
      serverSeq,
      items: pulledItems.map(itemToWire),
      movements: pulledMovements.map(movementToWire),
      rejected,
    };
  } catch (err) {
    tx.close();
    throw err;
  }
}

export function syncHandler(db) {
  return asyncHandler(async (req, res) => {
    const body = req.body ?? {};
    const lastServerSeq = Number.isFinite(body.lastServerSeq) ? body.lastServerSeq : 0;
    const items = Array.isArray(body.items) ? body.items : [];
    const movements = Array.isArray(body.movements) ? body.movements : [];
    res.json(await runSync(db, req.user, lastServerSeq, items, movements));
  });
}
