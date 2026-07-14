import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { Link, useNavigate } from 'react-router-dom';
import { db } from '../db';
import { useSession } from '../auth';
import { quantitiesFromMovements, isLowStock, formatQty, formatPrice } from '../domain';
import LowStockBadge from '../components/LowStockBadge';

export default function ItemsPage() {
  const session = useSession();
  const navigate = useNavigate();
  const isAdmin = session?.user.role === 'admin';

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [lowOnly, setLowOnly] = useState(false);
  const [showArchived, setShowArchived] = useState(false);

  const data = useLiveQuery(async () => {
    const [items, movements] = await Promise.all([db.items.toArray(), db.movements.toArray()]);
    return { items, movements };
  });

  if (!data) return null;

  const quantities = quantitiesFromMovements(data.movements);
  const categories = [...new Set(data.items.filter((it) => !it.isArchived).map((it) => it.category).filter(Boolean))].sort();

  const q = search.trim().toLowerCase();
  const items = data.items
    .filter((it) => (showArchived ? true : !it.isArchived))
    .filter((it) => !q || it.name.toLowerCase().includes(q) || it.sku.toLowerCase().includes(q))
    .filter((it) => !category || it.category === category)
    .filter((it) => !lowOnly || isLowStock(it, quantities.get(it.id) ?? 0))
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="page">
      <div className="page-head">
        <h1>Items</h1>
        {isAdmin && (
          <Link className="btn btn-primary" to="/items/new">
            + New item
          </Link>
        )}
      </div>

      <div className="filter-bar">
        <input
          className="filter-search"
          placeholder="Search name or SKU…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <label className="check">
          <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />
          Low stock only
        </label>
        {isAdmin && (
          <label className="check">
            <input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} />
            Show archived
          </label>
        )}
      </div>

      {items.length === 0 ? (
        <p className="muted card">No items match. {isAdmin && 'Use “New item” to add your first product.'}</p>
      ) : (
        <div className="item-table-wrap">
          <table className="item-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>SKU</th>
                <th>Category</th>
                <th className="num">Qty</th>
                <th className="num">Price</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => {
                const qty = quantities.get(it.id) ?? 0;
                return (
                  <tr
                    key={it.id}
                    className={it.isArchived ? 'row-archived' : ''}
                    onClick={() => navigate(`/items/${it.id}`)}
                  >
                    <td data-label="Name">
                      {it.name} {it.isArchived ? <span className="badge">Archived</span> : null}
                    </td>
                    <td data-label="SKU">{it.sku}</td>
                    <td data-label="Category">{it.category || '—'}</td>
                    <td data-label="Qty" className="num">
                      {formatQty(qty)} {it.unit} <LowStockBadge qty={qty} threshold={it.lowStockThreshold} />
                    </td>
                    <td data-label="Price" className="num">
                      {formatPrice(it.priceCents)}
                    </td>
                    <td className="row-actions" onClick={(e) => e.stopPropagation()}>
                      {!it.isArchived && (
                        <Link className="btn btn-sm" to={`/items/${it.id}/move`}>
                          Stock ±
                        </Link>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
