import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

const TOKEN_TTL = process.env.TOKEN_TTL || '30d';

export function getJwtSecret() {
  if (process.env.JWT_SECRET) return process.env.JWT_SECRET;
  if (process.env.NODE_ENV === 'production' || process.env.VERCEL) {
    throw new Error('JWT_SECRET must be set in production');
  }
  return 'dev-secret-do-not-use-in-prod';
}

/** Wraps an async Express handler so rejections hit the error handler. */
export function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

export function publicUser(row) {
  return { id: row.id, username: row.username, role: row.role, isActive: !!Number(row.is_active) };
}

async function getUserBy(db, column, value) {
  const result = await db.execute({ sql: `SELECT * FROM users WHERE ${column} = ?`, args: [value] });
  return result.rows[0];
}

export function loginHandler(db) {
  return asyncHandler(async (req, res) => {
    const { username, password } = req.body ?? {};
    if (typeof username !== 'string' || typeof password !== 'string') {
      return res.status(400).json({ error: 'username and password are required' });
    }
    const user = await getUserBy(db, 'username', username.trim());
    if (!user || !Number(user.is_active) || !bcrypt.compareSync(password, user.password_hash)) {
      return res.status(401).json({ error: 'Invalid username or password' });
    }
    const token = jwt.sign(
      { sub: user.id, username: user.username, role: user.role, tv: Number(user.token_version) },
      getJwtSecret(),
      { expiresIn: TOKEN_TTL }
    );
    res.json({ token, user: publicUser(user) });
  });
}

export function requireAuth(db) {
  return asyncHandler(async (req, res, next) => {
    const header = req.headers.authorization ?? '';
    const token = header.startsWith('Bearer ') ? header.slice(7) : null;
    if (!token) return res.status(401).json({ error: 'Missing token' });
    let payload;
    try {
      payload = jwt.verify(token, getJwtSecret());
    } catch {
      return res.status(401).json({ error: 'Invalid or expired token' });
    }
    const user = await getUserBy(db, 'id', payload.sub);
    if (!user || !Number(user.is_active) || Number(user.token_version) !== payload.tv) {
      return res.status(401).json({ error: 'Session revoked' });
    }
    req.user = user;
    next();
  });
}

export function requireAdmin(req, res, next) {
  if (req.user?.role !== 'admin') {
    return res.status(403).json({ error: 'Admin access required' });
  }
  next();
}
