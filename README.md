# AB Seeds Inventory

A simple, offline-first inventory web app. Works on desktop and mobile browsers, keeps working with no internet connection, and syncs automatically when connectivity returns. Installable as a PWA.

## Features

- **Offline-first**: all data lives in the browser (IndexedDB). View stock, record stock in/out, and add or edit items with no connection; changes queue locally and sync when you're back online.
- **Sync**: one `POST /api/sync` round trip pushes local changes and pulls everything new. Stock movements are an append-only log (never conflict); item edits resolve last-write-wins.
- **Roles**: **Admin** manages user accounts and items; **User** views inventory and records stock in/out.
- **Inventory**: items with SKU, category, unit, price, and low-stock threshold; stock in / stock out / adjustment movements with full history and who-did-what; low-stock indicators; search and filters; dashboard.
- **Responsive**: table layout on desktop, stacked cards on phones. Installable to the home screen.

## Stack

- **Client**: React + TypeScript + Vite, Dexie (IndexedDB), vite-plugin-pwa. No UI framework.
- **Server**: Node.js + Express + better-sqlite3, JWT auth. Single process serves the API and the built frontend.

## Development

```bash
npm install
npm run dev        # server on :3001, Vite dev server on :5173 (proxies /api)
npm test           # server API tests (node:test + supertest, in-memory DB)
```

On first run the server creates an admin account. Set `ADMIN_USERNAME` / `ADMIN_PASSWORD`, or a random password is generated and printed to the console once.

## Production

```bash
npm install
npm run build                                  # builds client/dist
JWT_SECRET=<long-random-string> npm start      # serves app + API on :3001
```

Environment variables:

| Variable | Default | Notes |
|---|---|---|
| `PORT` | `3001` | |
| `JWT_SECRET` | — | **Required in production.** |
| `DB_PATH` | `server/data/inventory.db` | SQLite file location |
| `ADMIN_USERNAME` | `admin` | Used only when the users table is empty |
| `ADMIN_PASSWORD` | random (printed once) | Used only when the users table is empty |
| `TOKEN_TTL` | `30d` | Login token lifetime |

Run it under systemd or pm2, e.g.:

```ini
# /etc/systemd/system/ab-seeds.service
[Unit]
Description=AB Seeds Inventory
After=network.target

[Service]
WorkingDirectory=/opt/ab-seeds_inventory
Environment=NODE_ENV=production
Environment=JWT_SECRET=change-me
ExecStart=/usr/bin/node server/src/index.js
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**HTTPS is required for offline support.** Service workers only activate over HTTPS (or localhost), so put Caddy or nginx with TLS in front:

```
# Caddyfile — TLS is automatic
inventory.example.com {
    reverse_proxy localhost:3001
}
```

**Backups**: the entire database is one file. `sqlite3 inventory.db ".backup backup.db"` (safe while running), or stop the service and copy the file.

## How offline & sync work

- The UI always renders from local IndexedDB, so offline is not a special case.
- Every local write marks rows as pending (`dirty` items / unsynced movements) and schedules a debounced sync; sync also runs on app start, on reconnect, every 60s, and via the **Sync now** button.
- Quantities are derived from the append-only movement log, so all devices converge to the same numbers. Negative stock is possible if devices race offline — the UI warns instead of blocking.
- Login tokens last 30 days and the session is cached locally, so reopening the app offline keeps you signed in. If the token expires, the app keeps working locally and shows a sign-in banner; pending changes sync right after you sign back in.
- Logging out keeps local data (so unsynced work is never destroyed); signing in as a *different* user on the same device clears it.

## Manual offline test

1. `npm run build && JWT_SECRET=x ADMIN_PASSWORD=secret npm start`, open `http://localhost:3001`, log in.
2. DevTools → Network → **Offline**: browse items, record a stock-out, add an item — everything works and the pending counter in the header rises.
3. Reload the page while offline — still signed in, data present.
4. Go back online — the pending counter drains to zero within a couple of seconds. Verify from a second browser profile.
5. Edit the same item in two profiles (one offline), reconnect — the newer edit wins on both.
6. Log in as a `user`-role account — no edit/archive/user-management UI, and the server rejects item edits from that account regardless.
