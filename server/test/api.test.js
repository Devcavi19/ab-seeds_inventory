import { test, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import { openDb } from '../src/db.js';
import { createApp } from '../src/app.js';

process.env.ADMIN_USERNAME = 'admin';
process.env.ADMIN_PASSWORD = 'admin-pass';

let db, app, adminToken;

async function login(username, password) {
  const res = await request(app).post('/api/auth/login').send({ username, password });
  return res;
}

async function createUser(username, password, role) {
  return request(app)
    .post('/api/users')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ username, password, role });
}

function itemPayload(overrides = {}) {
  return {
    id: overrides.id ?? crypto.randomUUID(),
    name: 'Tomato Seeds',
    sku: 'TOM-001',
    category: 'Vegetables',
    unit: 'packs',
    priceCents: 250,
    lowStockThreshold: 10,
    isArchived: false,
    updatedAt: Date.now(),
    ...overrides,
  };
}

beforeEach(async () => {
  db = openDb(':memory:');
  app = createApp(db);
  adminToken = (await login('admin', 'admin-pass')).body.token;
});

test('login succeeds with valid credentials and returns role', async () => {
  const res = await login('admin', 'admin-pass');
  assert.equal(res.status, 200);
  assert.ok(res.body.token);
  assert.equal(res.body.user.role, 'admin');
});

test('login fails with wrong password', async () => {
  const res = await login('admin', 'nope');
  assert.equal(res.status, 401);
});

test('disabled user cannot log in and existing token is revoked', async () => {
  await createUser('worker', 'secret123', 'user');
  const workerToken = (await login('worker', 'secret123')).body.token;

  const workerId = db.prepare("SELECT id FROM users WHERE username = 'worker'").get().id;
  const patch = await request(app)
    .patch(`/api/users/${workerId}`)
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ isActive: false });
  assert.equal(patch.status, 200);

  assert.equal((await login('worker', 'secret123')).status, 401);
  const me = await request(app).get('/api/me').set('Authorization', `Bearer ${workerToken}`);
  assert.equal(me.status, 401);
});

test('password reset bumps token_version and kills old JWT', async () => {
  await createUser('worker', 'secret123', 'user');
  const oldToken = (await login('worker', 'secret123')).body.token;
  const workerId = db.prepare("SELECT id FROM users WHERE username = 'worker'").get().id;

  await request(app)
    .patch(`/api/users/${workerId}`)
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ password: 'newpass99' });

  const me = await request(app).get('/api/me').set('Authorization', `Bearer ${oldToken}`);
  assert.equal(me.status, 401);
  assert.equal((await login('worker', 'newpass99')).status, 200);
});

test('user role gets 403 on user management', async () => {
  await createUser('worker', 'secret123', 'user');
  const workerToken = (await login('worker', 'secret123')).body.token;
  const res = await request(app).get('/api/users').set('Authorization', `Bearer ${workerToken}`);
  assert.equal(res.status, 403);
});

test('sync push item + movement, pull from 0 returns them with correct qty', async () => {
  const item = itemPayload();
  const push = await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({
      lastServerSeq: 0,
      items: [item],
      movements: [
        { id: crypto.randomUUID(), itemId: item.id, type: 'in', qtyDelta: 50, note: 'initial', createdAt: Date.now() },
        { id: crypto.randomUUID(), itemId: item.id, type: 'out', qtyDelta: -8, note: '', createdAt: Date.now() },
      ],
    });
  assert.equal(push.status, 200);
  assert.equal(push.body.rejected.items.length, 0);
  assert.equal(push.body.rejected.movements.length, 0);
  assert.equal(push.body.items.length, 1);
  assert.equal(push.body.movements.length, 2);

  const qty = db.prepare('SELECT current_qty FROM items WHERE id = ?').get(item.id).current_qty;
  assert.equal(qty, 42);
  // Movement attribution comes from the JWT, not the payload.
  assert.equal(push.body.movements[0].username, 'admin');
});

test('re-pushing the same movement UUID is idempotent', async () => {
  const item = itemPayload();
  const mv = { id: crypto.randomUUID(), itemId: item.id, type: 'in', qtyDelta: 10, createdAt: Date.now() };
  const send = () =>
    request(app)
      .post('/api/sync')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ lastServerSeq: 0, items: [item], movements: [mv] });

  await send();
  await send();
  const qty = db.prepare('SELECT current_qty FROM items WHERE id = ?').get(item.id).current_qty;
  assert.equal(qty, 10);
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM movements').get().n, 1);
});

test('LWW: newer updatedAt wins regardless of arrival order', async () => {
  const id = crypto.randomUUID();
  const newer = itemPayload({ id, name: 'Newer Name', updatedAt: 2000 });
  const older = itemPayload({ id, name: 'Older Name', updatedAt: 1000 });

  const push = (it) =>
    request(app)
      .post('/api/sync')
      .set('Authorization', `Bearer ${adminToken}`)
      .send({ lastServerSeq: 0, items: [it], movements: [] });

  await push(newer);
  const res = await push(older);
  const name = db.prepare('SELECT name FROM items WHERE id = ?').get(id).name;
  assert.equal(name, 'Newer Name');
  // The losing pusher still pulls back the winning row.
  assert.equal(res.body.items[0].name, 'Newer Name');
});

test('user role: item push rejected per-row, movement accepted', async () => {
  const item = itemPayload();
  await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ lastServerSeq: 0, items: [item], movements: [] });

  await createUser('worker', 'secret123', 'user');
  const workerToken = (await login('worker', 'secret123')).body.token;

  const res = await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${workerToken}`)
    .send({
      lastServerSeq: 0,
      items: [itemPayload({ id: item.id, name: 'Hacked' })],
      movements: [{ id: crypto.randomUUID(), itemId: item.id, type: 'out', qtyDelta: -3, createdAt: Date.now() }],
    });
  assert.equal(res.status, 200);
  assert.equal(res.body.rejected.items.length, 1);
  assert.equal(res.body.rejected.movements.length, 0);
  assert.equal(db.prepare('SELECT name FROM items WHERE id = ?').get(item.id).name, 'Tomato Seeds');
  assert.equal(db.prepare('SELECT current_qty FROM items WHERE id = ?').get(item.id).current_qty, -3);
  assert.equal(res.body.movements.at(-1).username, 'worker');
});

test('archive propagates through pull cursor', async () => {
  const item = itemPayload();
  const first = await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ lastServerSeq: 0, items: [item], movements: [] });
  const cursor = first.body.serverSeq;

  await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ lastServerSeq: cursor, items: [{ ...item, isArchived: true, updatedAt: Date.now() + 1 }], movements: [] });

  // A second client that synced up to `cursor` pulls only the archived update.
  const pull = await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({ lastServerSeq: cursor, items: [], movements: [] });
  assert.equal(pull.body.items.length, 1);
  assert.equal(pull.body.items[0].isArchived, true);
});

test('movement referencing unknown item is rejected per-row', async () => {
  const res = await request(app)
    .post('/api/sync')
    .set('Authorization', `Bearer ${adminToken}`)
    .send({
      lastServerSeq: 0,
      items: [],
      movements: [{ id: crypto.randomUUID(), itemId: 'nope', type: 'in', qtyDelta: 5, createdAt: Date.now() }],
    });
  assert.equal(res.status, 200);
  assert.equal(res.body.rejected.movements.length, 1);
  assert.equal(res.body.rejected.movements[0].reason, 'unknown item');
});

test('sync requires auth', async () => {
  const res = await request(app).post('/api/sync').send({ lastServerSeq: 0, items: [], movements: [] });
  assert.equal(res.status, 401);
});
