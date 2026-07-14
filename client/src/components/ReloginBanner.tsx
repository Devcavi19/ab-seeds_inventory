import { useState } from 'react';
import { login } from '../auth';
import { syncNow, useSyncState } from '../sync';

/**
 * Shown when the cached token has expired or been revoked. The app keeps
 * working locally; signing back in resumes syncing with pending work intact.
 */
export default function ReloginBanner() {
  const sync = useSyncState();
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!sync.needsLogin || !sync.online) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      setOpen(false);
      void syncNow();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="banner banner-warning">
      {!open ? (
        <>
          <span>Your session expired. Your work is saved on this device and will sync after you sign in again.</span>
          <button className="btn btn-sm" onClick={() => setOpen(true)}>
            Sign in
          </button>
        </>
      ) : (
        <form className="banner-form" onSubmit={(e) => void handleSubmit(e)}>
          <input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
          <button className="btn btn-sm" disabled={busy}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
          {error && <span className="form-error">{error}</span>}
        </form>
      )}
    </div>
  );
}
