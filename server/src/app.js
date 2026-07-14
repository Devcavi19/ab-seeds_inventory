import express from 'express';
import { existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { loginHandler, requireAuth, publicUser } from './auth.js';
import { syncHandler } from './sync.js';
import { usersRouter } from './users.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

export function createApp(db) {
  const app = express();
  app.use(express.json({ limit: '5mb' }));

  app.post('/api/auth/login', loginHandler(db));

  const auth = requireAuth(db);
  app.get('/api/me', auth, (req, res) => res.json({ user: publicUser(req.user) }));
  app.post('/api/sync', auth, syncHandler(db));
  app.use('/api/users', auth, usersRouter(db));

  app.use('/api', (req, res) => res.status(404).json({ error: 'Not found' }));

  // Serve the built frontend with SPA fallback.
  const dist = join(__dirname, '..', '..', 'client', 'dist');
  if (existsSync(dist)) {
    app.use(express.static(dist));
    app.get('*', (req, res) => res.sendFile(join(dist, 'index.html')));
  }

  return app;
}
