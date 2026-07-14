import { syncNow, useSyncState } from '../sync';

function timeAgo(ts: number | null): string {
  if (!ts) return 'never';
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 10) return 'just now';
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function SyncStatus() {
  const sync = useSyncState();

  const dotClass = !sync.online ? 'dot-offline' : sync.syncing ? 'dot-syncing' : 'dot-online';
  const label = !sync.online ? 'Offline' : sync.syncing ? 'Syncing…' : 'Online';

  return (
    <div className="sync-status">
      <span className={`dot ${dotClass}`} aria-hidden />
      <span className="sync-label">{label}</span>
      {sync.pendingCount > 0 && (
        <span className="badge badge-pending" title={`${sync.pendingCount} change(s) waiting to sync`}>
          {sync.pendingCount}
        </span>
      )}
      <button
        className="btn btn-ghost btn-sm"
        onClick={() => void syncNow()}
        disabled={!sync.online || sync.syncing}
        title={`Last synced ${timeAgo(sync.lastSyncAt)}`}
      >
        Sync now
      </button>
    </div>
  );
}
