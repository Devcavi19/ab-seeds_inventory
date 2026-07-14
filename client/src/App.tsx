import { useEffect, useState } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { loadSession, useSession } from './auth';
import { startSyncEngine } from './sync';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ItemsPage from './pages/ItemsPage';
import ItemDetailPage from './pages/ItemDetailPage';
import ItemFormPage from './pages/ItemFormPage';
import MovementFormPage from './pages/MovementFormPage';
import UsersPage from './pages/UsersPage';

export default function App() {
  const [ready, setReady] = useState(false);
  const session = useSession();
  const location = useLocation();

  useEffect(() => {
    void loadSession().then(() => setReady(true));
  }, []);

  useEffect(() => {
    if (ready && session) startSyncEngine();
  }, [ready, session]);

  if (!ready) return null;

  if (!session) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace state={{ from: location.pathname }} />} />
      </Routes>
    );
  }

  const isAdmin = session.user.role === 'admin';

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/items" element={<ItemsPage />} />
        <Route path="/items/new" element={isAdmin ? <ItemFormPage /> : <Navigate to="/items" replace />} />
        <Route path="/items/:id" element={<ItemDetailPage />} />
        <Route path="/items/:id/edit" element={isAdmin ? <ItemFormPage /> : <Navigate to="/items" replace />} />
        <Route path="/items/:id/move" element={<MovementFormPage />} />
        <Route path="/users" element={isAdmin ? <UsersPage /> : <Navigate to="/" replace />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
