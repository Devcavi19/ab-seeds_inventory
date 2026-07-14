import { Router } from 'express';
import { randomUUID } from 'node:crypto';
import bcrypt from 'bcryptjs';
import { publicUser, requireAdmin } from './auth.js';

export function usersRouter(db) {
  const router = Router();
  router.use(requireAdmin);

  router.get('/', (req, res) => {
    const rows = db.prepare('SELECT * FROM users ORDER BY created_at').all();
    res.json({ users: rows.map(publicUser) });
  });

  router.post('/', (req, res) => {
    const { username, password, role } = req.body ?? {};
    if (typeof username !== 'string' || !username.trim()) {
      return res.status(400).json({ error: 'username is required' });
    }
    if (typeof password !== 'string' || password.length < 6) {
      return res.status(400).json({ error: 'password must be at least 6 characters' });
    }
    if (role !== 'admin' && role !== 'user') {
      return res.status(400).json({ error: "role must be 'admin' or 'user'" });
    }
    const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username.trim());
    if (existing) return res.status(409).json({ error: 'username already taken' });
    const id = randomUUID();
    db.prepare(
      `INSERT INTO users (id, username, password_hash, role, is_active, token_version, created_at)
       VALUES (?, ?, ?, ?, 1, 1, ?)`
    ).run(id, username.trim(), bcrypt.hashSync(password, 10), role, new Date().toISOString());
    res.status(201).json({ user: publicUser(db.prepare('SELECT * FROM users WHERE id = ?').get(id)) });
  });

  router.patch('/:id', (req, res) => {
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.params.id);
    if (!user) return res.status(404).json({ error: 'user not found' });
    const { role, isActive, password } = req.body ?? {};
    let revoke = false;

    if (role !== undefined) {
      if (role !== 'admin' && role !== 'user') {
        return res.status(400).json({ error: "role must be 'admin' or 'user'" });
      }
      if (user.id === req.user.id && role !== 'admin') {
        return res.status(400).json({ error: 'you cannot demote yourself' });
      }
      db.prepare('UPDATE users SET role = ? WHERE id = ?').run(role, user.id);
    }
    if (isActive !== undefined) {
      if (user.id === req.user.id && !isActive) {
        return res.status(400).json({ error: 'you cannot disable yourself' });
      }
      db.prepare('UPDATE users SET is_active = ? WHERE id = ?').run(isActive ? 1 : 0, user.id);
      if (!isActive) revoke = true;
    }
    if (password !== undefined) {
      if (typeof password !== 'string' || password.length < 6) {
        return res.status(400).json({ error: 'password must be at least 6 characters' });
      }
      db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(bcrypt.hashSync(password, 10), user.id);
      revoke = true;
    }
    if (revoke) {
      db.prepare('UPDATE users SET token_version = token_version + 1 WHERE id = ?').run(user.id);
    }
    res.json({ user: publicUser(db.prepare('SELECT * FROM users WHERE id = ?').get(user.id)) });
  });

  return router;
}
