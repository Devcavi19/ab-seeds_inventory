// Vercel serverless entry point: the whole Express API runs as one function.
// Static frontend files are served by Vercel from client/dist (see vercel.json).
import { createDb } from '../server/src/db.js';
import { createApp } from '../server/src/app.js';

export default createApp(createDb());
