import { useLiveQuery } from 'dexie-react-hooks';
import { Link } from 'react-router-dom';
import { db } from '../db';
import { quantitiesFromMovements, isLowStock, formatQty } from '../domain';

export default function DashboardPage() {
  const data = useLiveQuery(async () => {
    const [items, movements, recent] = await Promise.all([
      db.items.where('isArchived').equals(0).toArray(),
      db.movements.toArray(),
      db.movements.orderBy('createdAt').reverse().limit(10).toArray(),
    ]);
    return { items, movements, recent };
  });

  if (!data) return null;

  const { items, movements, recent } = data;
  const quantities = quantitiesFromMovements(movements);
  const itemById = new Map(items.map((it) => [it.id, it]));
  const lowStock = items.filter((it) => isLowStock(it, quantities.get(it.id) ?? 0));

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-value">{items.length}</div>
          <div className="stat-label">Active items</div>
        </div>
        <div className={`stat-card ${lowStock.length > 0 ? 'stat-card-warn' : ''}`}>
          <div className="stat-value">{lowStock.length}</div>
          <div className="stat-label">Low stock</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{movements.length}</div>
          <div className="stat-label">Movements recorded</div>
        </div>
      </div>

      {lowStock.length > 0 && (
        <section className="card">
          <h2>Low stock</h2>
          <ul className="plain-list">
            {lowStock.map((it) => (
              <li key={it.id}>
                <Link to={`/items/${it.id}`}>{it.name}</Link>
                <span className="muted">
                  {' '}
                  — {formatQty(quantities.get(it.id) ?? 0)} {it.unit} left (threshold {formatQty(it.lowStockThreshold)})
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card">
        <h2>Recent movements</h2>
        {recent.length === 0 ? (
          <p className="muted">No movements yet. Add items and record stock in/out to see activity here.</p>
        ) : (
          <ul className="plain-list">
            {recent.map((mv) => {
              const item = itemById.get(mv.itemId);
              return (
                <li key={mv.id}>
                  <span className={`move-tag move-${mv.type}`}>
                    {mv.type === 'in' ? 'IN' : mv.type === 'out' ? 'OUT' : 'ADJ'}
                  </span>{' '}
                  {mv.qtyDelta > 0 ? '+' : ''}
                  {formatQty(mv.qtyDelta)}{' '}
                  <Link to={`/items/${mv.itemId}`}>{item?.name ?? 'Unknown item'}</Link>
                  <span className="muted">
                    {' '}
                    · {mv.username || 'unknown'} · {new Date(mv.createdAt).toLocaleString()}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
