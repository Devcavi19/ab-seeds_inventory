import { useCallback, useEffect, useState } from 'react';
import { getToken, useSession } from '../auth';
import { useSyncState } from '../sync';
import type { Role } from '../domain';

interface ApiUser {
  id: string;
  username: string;
  role: Role;
  isActive: boolean;
}

async function api(path: string, options: RequestInit = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`,
      ...options.headers,
    },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error ?? `Request failed (${res.status})`);
  return body;
}

export default function UsersPage() {
  const session = useSession();
  const sync = useSyncState();
  const [users, setUsers] = useState<ApiUser[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState<Role>('user');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const body = await api('/api/users');
      setUsers(body.users);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    if (sync.online) void load();
  }, [sync.online, load]);

  if (!sync.online) {
    return (
      <div className="page">
        <h1>Users</h1>
        <p className="muted card">
          User management needs an internet connection. Inventory keeps working offline — this page will load once
          you're back online.
        </p>
      </div>
    );
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api('/api/users', {
        method: 'POST',
        body: JSON.stringify({ username: newUsername.trim(), password: newPassword, role: newRole }),
      });
      setNewUsername('');
      setNewPassword('');
      setNewRole('user');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function patchUser(id: string, patch: Record<string, unknown>) {
    setError(null);
    try {
      await api(`/api/users/${id}`, { method: 'PATCH', body: JSON.stringify(patch) });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleResetPassword(user: ApiUser) {
    const password = window.prompt(`New password for ${user.username} (min 6 characters):`);
    if (!password) return;
    await patchUser(user.id, { password });
  }

  return (
    <div className="page">
      <h1>Users</h1>
      {error && <p className="form-error">{error}</p>}

      <section className="card">
        <h2>Add user</h2>
        <form className="form form-inline" onSubmit={(e) => void handleCreate(e)}>
          <label>
            Username
            <input value={newUsername} onChange={(e) => setNewUsername(e.target.value)} required />
          </label>
          <label>
            Password
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              minLength={6}
              required
            />
          </label>
          <label>
            Role
            <select value={newRole} onChange={(e) => setNewRole(e.target.value as Role)}>
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <button className="btn btn-primary" disabled={busy}>
            {busy ? 'Adding…' : 'Add user'}
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Accounts</h2>
        {!users ? (
          <p className="muted">Loading…</p>
        ) : (
          <div className="item-table-wrap">
            <table className="item-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const isSelf = u.id === session?.user.id;
                  return (
                    <tr key={u.id}>
                      <td data-label="Username">
                        {u.username} {isSelf && <span className="badge">You</span>}
                      </td>
                      <td data-label="Role">
                        <select
                          value={u.role}
                          disabled={isSelf}
                          onChange={(e) => void patchUser(u.id, { role: e.target.value })}
                        >
                          <option value="user">User</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                      <td data-label="Status">{u.isActive ? 'Active' : 'Disabled'}</td>
                      <td className="row-actions">
                        <button className="btn btn-sm" onClick={() => void handleResetPassword(u)}>
                          Reset password
                        </button>
                        {!isSelf && (
                          <button
                            className={`btn btn-sm ${u.isActive ? 'btn-danger' : ''}`}
                            onClick={() => void patchUser(u.id, { isActive: !u.isActive })}
                          >
                            {u.isActive ? 'Disable' : 'Enable'}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
