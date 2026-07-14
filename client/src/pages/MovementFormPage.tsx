import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { db } from '../db';
import { recordMovement } from '../data';
import { formatQty, type MovementType } from '../domain';

export default function MovementFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [type, setType] = useState<MovementType>('in');
  const [qty, setQty] = useState('');
  const [counted, setCounted] = useState('');
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);

  const data = useLiveQuery(async () => {
    if (!id) return null;
    const [item, movements] = await Promise.all([
      db.items.get(id),
      db.movements.where('itemId').equals(id).toArray(),
    ]);
    return { item, currentQty: movements.reduce((s, m) => s + m.qtyDelta, 0) };
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
  const { item, currentQty } = data;

  function computeDelta(): number | null {
    if (type === 'adjustment') {
      const target = parseFloat(counted);
      if (Number.isNaN(target)) return null;
      return target - currentQty;
    }
    const n = parseFloat(qty);
    if (Number.isNaN(n) || n <= 0) return null;
    return type === 'in' ? n : -n;
  }

  const delta = computeDelta();
  const resulting = delta === null ? null : currentQty + delta;
  const wouldGoNegative = resulting !== null && resulting < 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!item || delta === null) {
      setError(type === 'adjustment' ? 'Enter the counted quantity.' : 'Enter a quantity greater than zero.');
      return;
    }
    if (type === 'adjustment' && delta === 0) {
      setError('Counted quantity matches the current quantity — nothing to adjust.');
      return;
    }
    await recordMovement(item.id, type, delta, note.trim());
    navigate(`/items/${item.id}`);
  }

  return (
    <div className="page page-narrow">
      <h1>Record movement</h1>
      <p className="muted">
        {item.name} — current quantity {formatQty(currentQty)} {item.unit}
      </p>
      <form className="card form" onSubmit={(e) => void handleSubmit(e)}>
        <div className="seg-row" role="radiogroup" aria-label="Movement type">
          {(['in', 'out', 'adjustment'] as const).map((t) => (
            <button
              type="button"
              key={t}
              className={`seg ${type === t ? 'seg-active' : ''}`}
              onClick={() => setType(t)}
            >
              {t === 'in' ? 'Stock in' : t === 'out' ? 'Stock out' : 'Adjust'}
            </button>
          ))}
        </div>

        {type === 'adjustment' ? (
          <label>
            Counted quantity ({item.unit})
            <input
              type="number"
              step="any"
              min="0"
              value={counted}
              onChange={(e) => setCounted(e.target.value)}
              placeholder={`What you actually counted, e.g. ${formatQty(Math.max(currentQty, 0))}`}
              autoFocus
            />
            {delta !== null && (
              <span className="muted">
                This records an adjustment of {delta > 0 ? '+' : ''}
                {formatQty(delta)} {item.unit}.
              </span>
            )}
          </label>
        ) : (
          <label>
            Quantity ({item.unit})
            <input
              type="number"
              step="any"
              min="0"
              value={qty}
              onChange={(e) => setQty(e.target.value)}
              autoFocus
            />
          </label>
        )}

        <label>
          Note (optional)
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. delivery, sale, damaged" />
        </label>

        {wouldGoNegative && (
          <p className="form-warn">
            This would take the stock to {formatQty(resulting!)} {item.unit} (below zero). You can still save it —
            check the count if that looks wrong.
          </p>
        )}
        {error && <p className="form-error">{error}</p>}

        <div className="btn-row">
          <button className="btn btn-primary" disabled={delta === null}>
            Save movement
          </button>
          <Link className="btn btn-ghost" to={`/items/${item.id}`}>
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
}
