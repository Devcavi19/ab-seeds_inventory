import { useEffect, useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { db } from '../db';
import { createItem, updateItem } from '../data';

export default function ItemFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const editing = !!id;

  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [category, setCategory] = useState('');
  const [unit, setUnit] = useState('packs');
  const [price, setPrice] = useState('0');
  const [threshold, setThreshold] = useState('0');
  const [loaded, setLoaded] = useState(!editing);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!editing || !id) return;
    void db.items.get(id).then((item) => {
      if (item) {
        setName(item.name);
        setSku(item.sku);
        setCategory(item.category);
        setUnit(item.unit);
        setPrice((item.priceCents / 100).toString());
        setThreshold(item.lowStockThreshold.toString());
      }
      setLoaded(true);
    });
  }, [editing, id]);

  // Warn (not block) on duplicate SKUs — two offline devices can legitimately
  // create the same SKU, so uniqueness can't be enforced anywhere.
  const skuTaken = useLiveQuery(async () => {
    const trimmed = sku.trim();
    if (!trimmed) return false;
    const matches = await db.items.where('sku').equals(trimmed).toArray();
    return matches.some((it) => it.id !== id);
  }, [sku, id]);

  if (!loaded) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const priceCents = Math.round(parseFloat(price || '0') * 100);
    const lowStockThreshold = parseFloat(threshold || '0');
    if (!name.trim()) return setError('Name is required.');
    if (Number.isNaN(priceCents) || priceCents < 0) return setError('Price must be a non-negative number.');
    if (Number.isNaN(lowStockThreshold) || lowStockThreshold < 0)
      return setError('Low-stock threshold must be a non-negative number.');

    const input = {
      name: name.trim(),
      sku: sku.trim(),
      category: category.trim(),
      unit: unit.trim() || 'pcs',
      priceCents,
      lowStockThreshold,
    };
    if (editing && id) {
      await updateItem(id, input);
      navigate(`/items/${id}`);
    } else {
      const newId = await createItem(input);
      navigate(`/items/${newId}`);
    }
  }

  return (
    <div className="page page-narrow">
      <h1>{editing ? 'Edit item' : 'New item'}</h1>
      <form className="card form" onSubmit={(e) => void handleSubmit(e)}>
        <label>
          Name *
          <input value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
        </label>
        <label>
          SKU
          <input value={sku} onChange={(e) => setSku(e.target.value)} />
          {skuTaken && <span className="form-warn">Another item already uses this SKU.</span>}
        </label>
        <label>
          Category
          <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Vegetables" />
        </label>
        <div className="form-grid">
          <label>
            Unit
            <input value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="packs, kg, pcs…" />
          </label>
          <label>
            Price per unit
            <input type="number" step="0.01" min="0" value={price} onChange={(e) => setPrice(e.target.value)} />
          </label>
          <label>
            Low-stock threshold
            <input
              type="number"
              step="any"
              min="0"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          </label>
        </div>
        {error && <p className="form-error">{error}</p>}
        <div className="btn-row">
          <button className="btn btn-primary">{editing ? 'Save changes' : 'Create item'}</button>
          <Link className="btn btn-ghost" to={editing && id ? `/items/${id}` : '/items'}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
