import { createDb, ensureReady } from './db.js';
import { createApp } from './app.js';

const db = createDb();
await ensureReady(db);
const app = createApp(db);
const port = Number(process.env.PORT || 3001);

app.listen(port, () => {
  console.log(`AB Seeds Inventory server listening on http://localhost:${port}`);
});
