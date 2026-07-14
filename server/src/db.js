import { createClient } from '@libsql/client';
import { readFileSync, mkdirSync } from 'node:fs';
import { dirname, join, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID, randomBytes } from 'node:crypto';
import bcrypt from 'bcryptjs';

const __dirname = dirname(fileURLToPath(import.meta.url));

function resolveUrl(url) {
  const resolved = url ?? process.env.TURSO_DATABASE_URL ?? withFilePrefix(process.env.DB_PATH ?? defaultDbPath());
  // A bare ":memory:" opens a fresh, unshared DB per connection — the
  // separate connection libsql uses for transaction() would see no tables.
  // The shared-cache URI keeps every connection pointed at the same DB.
  return resolved === ':memory:' ? 'file::memory:?cache=shared' : resolved;
}

function defaultDbPath() {
  return join(__dirname, '..', 'data', 'inventory.db');
}

function withFilePrefix(path) {
  return path.includes(':') ? path : `file:${path}`;
}

export function createDb(url) {
  const resolved = resolveUrl(url);
  if (resolved.startsWith('file:')) {
    const path = resolved.slice(5);
    if (isAbsolute(path) || !path.startsWith(':')) mkdirSync(dirname(path), { recursive: true });
  }
  return createClient({
    url: resolved,
    authToken: process.env.TURSO_AUTH_TOKEN,
  });
}

const readyByDb = new WeakMap();

/**
 * Idempotent schema + admin seeding. The promise is cached per client so a
 * serverless cold start pays this once and warm invocations skip it.
 */
export function ensureReady(db) {
  let ready = readyByDb.get(db);
  if (!ready) {
    ready = init(db);
    readyByDb.set(db, ready);
  }
  return ready;
}

async function init(db) {
  await db.executeMultiple(readFileSync(join(__dirname, 'schema.sql'), 'utf8'));
  await seedAdmin(db);
}

async function seedAdmin(db) {
  const count = (await db.execute('SELECT COUNT(*) AS n FROM users')).rows[0].n;
  if (Number(count) > 0) return;
  const username = process.env.ADMIN_USERNAME || 'admin';
  let password = process.env.ADMIN_PASSWORD;
  let generated = false;
  if (!password) {
    password = randomBytes(9).toString('base64url');
    generated = true;
  }
  await db.execute({
    sql: `INSERT INTO users (id, username, password_hash, role, is_active, token_version, created_at)
          VALUES (?, ?, ?, 'admin', 1, 1, ?)`,
    args: [randomUUID(), username, bcrypt.hashSync(password, 10), new Date().toISOString()],
  });
  if (generated) {
    console.log(`\nCreated initial admin account -> username: ${username}  password: ${password}`);
    console.log('Change this password after first login (or set ADMIN_USERNAME/ADMIN_PASSWORD env vars).\n');
  } else {
    console.log(`Created initial admin account "${username}" from environment variables.`);
  }
}

/**
 * Reserves n consecutive sequence numbers and returns the first one.
 * Call once per sync request (inside the transaction) rather than per row —
 * against Turso every statement is an HTTP round trip. Gaps from rejected
 * rows are harmless; the pull cursor only needs monotonicity.
 */
export async function allocateSeqRange(tx, n) {
  const last = Number((await tx.execute("SELECT value FROM meta WHERE key = 'last_seq'")).rows[0].value);
  await tx.execute({ sql: "UPDATE meta SET value = ? WHERE key = 'last_seq'", args: [String(last + n)] });
  return last + 1;
}

export async function currentSeq(tx) {
  return Number((await tx.execute("SELECT value FROM meta WHERE key = 'last_seq'")).rows[0].value);
}
