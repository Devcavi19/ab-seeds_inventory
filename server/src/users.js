import { Router } from 'express';
import { randomUUID } from 'node:crypto';
import bcrypt from 'bcryptjs';
import { publicUser, requireAdmin, asyncHandler } from './auth.js';

export function usersRouter(db) {
  const router = Router();
  router.use(requireAdmin);

  const getUser = async (id) =>
    (await db.execute({ sql: 'SELECT * FROM users WHERE id = ?', args: [id] })).rows[0];

  router.get('/', asyncHandler(async (req, res) => {
    const result = await db.execute('SELECT * FROM users ORDER BY created_at');
    res.json({ users: result.rows.map(publicUser) });
  }));

  router.post('/', asyncHandler(async (req, res) => {
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
    const existing = await db.execute({
      sql: 'SELECT id FROM users WHERE username = ?',
      args: [username.trim()],
    });
    if (existing.rows.length > 0) return res.status(409).json({ error: 'username already taken' });
    const id = randomUUID();
    await db.execute({
      sql: `INSERT INTO users (id, username, password_hash, role, is_active, token_version, created_at)
            VALUES (?, ?, ?, ?, 1, 1, ?)`,
      args: [id, username.trim(), bcrypt.hashSync(password, 10), role, new Date().toISOString()],
    });
    res.status(201).json({ user: publicUser(await getUser(id)) });
  }));

  router.patch('/:id', asyncHandler(async (req, res) => {
    const user = await getUser(req.params.id);
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
      await db.execute({ sql: 'UPDATE users SET role = ? WHERE id = ?', args: [role, user.id] });
    }
    if (isActive !== undefined) {
      if (user.id === req.user.id && !isActive) {
        return res.status(400).json({ error: 'you cannot disable yourself' });
      }
      await db.execute({ sql: 'UPDATE users SET is_active = ? WHERE id = ?', args: [isActive ? 1 : 0, user.id] });
      if (!isActive) revoke = true;
    }
    if (password !== undefined) {
      if (typeof password !== 'string' || password.length < 6) {
        return res.status(400).json({ error: 'password must be at least 6 characters' });
      }
      await db.execute({
        sql: 'UPDATE users SET password_hash = ? WHERE id = ?',
        args: [bcrypt.hashSync(password, 10), user.id],
      });
      revoke = true;
    }
    if (revoke) {
      await db.execute({ sql: 'UPDATE users SET token_version = token_version + 1 WHERE id = ?', args: [user.id] });
    }
    res.json({ user: publicUser(await getUser(user.id)) });
  }));

  return router;
}
