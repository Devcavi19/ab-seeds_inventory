export default function LowStockBadge({ qty, threshold }: { qty: number; threshold: number }) {
  if (threshold <= 0 || qty > threshold) return null;
  return <span className="badge badge-low">{qty <= 0 ? 'Out of stock' : 'Low stock'}</span>;
}
