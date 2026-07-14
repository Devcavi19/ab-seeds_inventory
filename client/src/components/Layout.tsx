import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { logout, useSession } from '../auth';
import SyncStatus from './SyncStatus';
import ReloginBanner from './ReloginBanner';

export default function Layout({ children }: { children: ReactNode }) {
  const session = useSession();
  const navigate = useNavigate();
  const isAdmin = session?.user.role === 'admin';

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-brand">
          <span className="brand-mark">🌱</span>
          <span className="brand-name">AB Seeds</span>
        </div>
        <nav className="topbar-nav">
          <NavLink to="/" end>
            <span className="nav-icon">📊</span>
            <span className="nav-label">Dashboard</span>
          </NavLink>
          <NavLink to="/items">
            <span className="nav-icon">📦</span>
            <span className="nav-label">Items</span>
          </NavLink>
          {isAdmin && (
            <NavLink to="/users">
              <span className="nav-icon">👥</span>
              <span className="nav-label">Users</span>
            </NavLink>
          )}
        </nav>
        <div className="topbar-right">
          <SyncStatus />
          <div className="user-chip" title={`Signed in as ${session?.user.username} (${session?.user.role})`}>
            <span className="nav-label">{session?.user.username}</span>
            <button className="btn btn-ghost btn-sm" onClick={() => void handleLogout()}>
              Log out
            </button>
          </div>
        </div>
      </header>
      <ReloginBanner />
      <main className="content">{children}</main>
    </div>
  );
}
