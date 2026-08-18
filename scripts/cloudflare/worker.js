/* The same rendezvous as scripts/signal-server.js, as a Cloudflare Worker.
 *
 * A room needs one consistent place to hold two mailboxes, which is exactly what
 * a Durable Object is: requests naming the same room code are routed to the same
 * instance wherever they come from, so an answer posted from one continent is
 * seen by a poll parked on another. Plain Workers cannot do this — they have no
 * shared memory between invocations — and KV is the wrong shape, being eventually
 * consistent when the whole point is read-after-write.
 *
 * Deploy:
 *   cd scripts/cloudflare && npx wrangler deploy
 *
 * Then point the game at it by opening the page with ?signal=https://<worker-url>
 * or by setting SIGNAL_BASE in index.html. The game itself can be served from
 * anywhere — Cloudflare Pages, a static host, or a local file server; every
 * response here carries CORS headers so the two need not share an origin.
 */

const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';   // no O/0, no I/1: codes get typed by hand
const POLL_MS = 25000;
const ROOM_TTL_MS = 10 * 60 * 1000;

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Cache-Control': 'no-store'
};

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: { 'Content-Type': 'application/json', ...CORS }
  });
}

function newCode() {
  const bytes = crypto.getRandomValues(new Uint8Array(6));
  let code = '';
  for (let i = 0; i < 6; i++) code += ALPHABET[bytes[i] % ALPHABET.length];
  return code;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });

    if (path === '/net/new' && request.method === 'POST') return json({ code: newCode() });

    if (path === '/net/send' || path === '/net/recv') {
      const code = (url.searchParams.get('code') || '').toUpperCase();
      if (!/^[A-Z0-9]{6}$/.test(code)) return json({ error: 'bad room code' }, 400);
      const room = env.ROOM.get(env.ROOM.idFromName(code));
      return room.fetch(request);
    }

    if (path === '/' || path === '/health') return json({ ok: true, service: 'ratatatata-signal' });
    return json({ error: 'unknown endpoint' }, 404);
  }
};

export class Room {
  constructor(state) {
    this.state = state;
    this.box = { host: [], guest: [] };
    this.waiting = { host: [], guest: [] };
    this.touched = Date.now();
  }

  /* Hand a parked poll whatever is waiting for it. */
  flush(role) {
    if (!this.box[role].length) return;
    const held = this.waiting[role].shift();
    if (held) held(json({ messages: this.box[role].splice(0) }));
  }

  async fetch(request) {
    const url = new URL(request.url);
    this.touched = Date.now();
    if (this.expiry) clearTimeout(this.expiry);
    this.expiry = setTimeout(() => { this.box = { host: [], guest: [] }; }, ROOM_TTL_MS);

    if (url.pathname === '/net/send') {
      const from = url.searchParams.get('from');
      if (from !== 'host' && from !== 'guest') return json({ error: 'bad role' }, 400);
      let msg;
      try { msg = await request.json(); } catch (err) { return json({ error: 'bad message' }, 400); }
      const to = from === 'host' ? 'guest' : 'host';
      this.box[to].push(msg);
      this.flush(to);
      return json({ ok: true });
    }

    const as = url.searchParams.get('as');
    if (as !== 'host' && as !== 'guest') return json({ error: 'bad role' }, 400);
    if (this.box[as].length) return json({ messages: this.box[as].splice(0) });

    // Nothing yet: park the request so a message posted in a moment lands at once.
    return new Promise((resolve) => {
      const done = (response) => {
        const at = this.waiting[as].indexOf(done);
        if (at >= 0) this.waiting[as].splice(at, 1);
        resolve(response);
      };
      this.waiting[as].push(done);
      setTimeout(() => done(json({ messages: [] })), POLL_MS);
    });
  }
}
