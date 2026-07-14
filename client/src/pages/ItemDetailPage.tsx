import { useLiveQuery } from 'dexie-react-hooks';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { db } from '../db';
import { useSession } from '../auth';
import { updateItem } from '../data';
import { formatPrice, formatQty, isLowStock } from '../domain';
import LowStockBadge from '../components/LowStockBadge';

export default function ItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const session = useSession();
  const navigate = useNavigate();
  const isAdmin = session?.user.role === 'admin';

  const data = useLiveQuery(async () => {
    if (!id) return null;
    const [item, movements] = await Promise.all([
      db.items.get(id),
      db.movements.where('itemId').equals(id).toArray(),
    ]);
    return { item, movements };
  }, [id]);

  if (!data) return null;
  if (!data.item) {
    return (
      <div className="page">
        <p className="muted">Item not found.</p>
        <Link to="/items">Back to items</Link>
      </div>
    );
  }

  const { item, movements } = data;
  const qty = movements.reduce((sum, mv) => sum + mv.qtyDelta, 0);
  const history = [...movements].sort((a, b) => b.createdAt - a.createdAt);

  async function handleArchive() {
    if (!item) return;
    const verb = item.isArchived ? 'restore' : 'archive';
    if (!window.confirm(`Are you sure you want to ${verb} "${item.name}"?`)) return;
    await updateItem(item.id, { isArchived: item.isArchived ? 0 : 1 });
    navigate('/items');
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>
            {item.name} {item.isArchived ? <span className="badge">Archived</span> : null}{' '}
            <LowStockBadge qty={qty} threshold={item.lowStockThreshold} />
          </h1>
          <p className="muted">
            SKU {item.sku} {item.category && <>· {item.category}</>} · {formatPrice(item.priceCents)} per {item.unit}
          </p>
        </div>
        <div className="btn-row">
          {!item.isArchived && (
            <Link className="btn btn-primary" to={`/items/${item.id}/move`}>
              Stock in / out
            </Link>
          )}
          {isAdmin && (
            <>
              <Link className="btn" to={`/items/${item.id}/edit`}>
                Edit
              </Link>
              <button className="btn btn-danger" onClick={() => void handleArchive()}>
                {item.isArchived ? 'Restore' : 'Archive'}
              </button>
            </>
          )}
        </div>
      </div>

      <div className="stat-row">
        <div className={`stat-card ${isLowStock(item, qty) ? 'stat-card-warn' : ''}`}>
          <div className="stat-value">
            {formatQty(qty)} <span className="stat-unit">{item.unit}</span>
          </div>
          <div className="stat-label">Current quantity</div>
        </div>
        {item.lowStockThreshold > 0 && (
          <div className="stat-card">
            <div className="stat-value">
              {formatQty(item.lowStockThreshold)} <span className="stat-unit">{item.unit}</span>
            </div>
            <div className="stat-label">Low-stock threshold</div>
          </div>
        )}
      </div>

      <section className="card">
        <h2>Movement history</h2>
        {history.length === 0 ? (
          <p className="muted">No movements recorded for this item yet.</p>
        ) : (
          <ul className="plain-list">
            {history.map((mv) => (
              <li key={mv.id}>
                <span className={`move-tag move-${mv.type}`}>
                  {mv.type === 'in' ? 'IN' : mv.type === 'out' ? 'OUT' : 'ADJ'}
                </span>{' '}
                {mv.qtyDelta > 0 ? '+' : ''}
                {formatQty(mv.qtyDelta)} {item.unit}
                {mv.note && <span> — {mv.note}</span>}
                <span className="muted">
                  {' '}
                  · {mv.username || 'unknown'} · {new Date(mv.createdAt).toLocaleString()}
                  {mv.synced === 0 && ' · not yet synced'}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
