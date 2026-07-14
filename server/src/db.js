import Database from 'better-sqlite3';
import { readFileSync } from 'node:fs';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID, randomBytes } from 'node:crypto';
import bcrypt from 'bcryptjs';

const __dirname = dirname(fileURLToPath(import.meta.url));

export function openDb(dbPath) {
  const path = dbPath ?? process.env.DB_PATH ?? join(__dirname, '..', 'data', 'inventory.db');
  if (path !== ':memory:') mkdirSync(dirname(path), { recursive: true });
  const db = new Database(path);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  db.exec(readFileSync(join(__dirname, 'schema.sql'), 'utf8'));
  seedAdmin(db);
  return db;
}

function seedAdmin(db) {
  const count = db.prepare('SELECT COUNT(*) AS n FROM users').get().n;
  if (count > 0) return;
  const username = process.env.ADMIN_USERNAME || 'admin';
  let password = process.env.ADMIN_PASSWORD;
  let generated = false;
  if (!password) {
    password = randomBytes(9).toString('base64url');
    generated = true;
  }
  db.prepare(
    `INSERT INTO users (id, username, password_hash, role, is_active, token_version, created_at)
     VALUES (?, ?, ?, 'admin', 1, 1, ?)`
  ).run(randomUUID(), username, bcrypt.hashSync(password, 10), new Date().toISOString());
  if (generated) {
    console.log(`\nCreated initial admin account -> username: ${username}  password: ${password}`);
    console.log('Change this password after first login (or set ADMIN_USERNAME/ADMIN_PASSWORD env vars).\n');
  } else {
    console.log(`Created initial admin account "${username}" from environment variables.`);
  }
}

// Allocates n consecutive sequence numbers and returns the first one.
// Must be called inside a transaction.
export function nextSeq(db, n = 1) {
  const last = Number(db.prepare("SELECT value FROM meta WHERE key = 'last_seq'").get().value);
  db.prepare("UPDATE meta SET value = ? WHERE key = 'last_seq'").run(String(last + n));
  return last + 1;
}

export function currentSeq(db) {
  return Number(db.prepare("SELECT value FROM meta WHERE key = 'last_seq'").get().value);
}
