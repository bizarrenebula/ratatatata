#!/usr/bin/env node
/* Rendezvous for two browsers, and a static file server for the game itself.
 *
 * Two peers cannot find each other on their own: before a direct connection
 * exists, each has to hand the other a description of how to reach it. That is
 * all this does. The host posts an offer, the guest collects it and posts an
 * answer back, and from the moment the answer lands the two browsers talk
 * directly to each other — nothing about the game passes through here.
 *
 * A room is a pair of mailboxes and nothing more: no accounts, no history, and
 * no persistence. Rooms expire ten minutes after their last use.
 *
 * Serving the game from the same origin is deliberate: the link the host sends
 * is then just this server's address plus the room code, and the page can reach
 * the signalling endpoints without any cross-origin arrangement.
 *
 *   node scripts/signal-server.js [port]
 *
 * For a friend on another network, expose the port with a tunnel
 * (`cloudflared tunnel --url http://localhost:8080`, `ngrok http 8080`, …) and
 * send them the tunnel's address; the room code travels in the link's fragment.
 */
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const PORT = Number(process.argv[2] || process.env.PORT || 8080);
const ROOM_TTL = 10 * 60 * 1000;
const POLL_MS = 25000;
const MAX_BODY = 64 * 1024;
/* Room codes are read off a screen and typed by hand, so the alphabet leaves
   out the characters people confuse: no O/0, no I/1. */
const ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

const rooms = new Map();

function newCode() {
  let code;
  do {
    const bytes = crypto.randomBytes(6);
    code = '';
    for (let i = 0; i < 6; i++) code += ALPHABET[bytes[i] % ALPHABET.length];
  } while (rooms.has(code));
  return code;
}

function makeRoom() {
  const code = newCode();
  rooms.set(code, { touched: Date.now(), box: { host: [], guest: [] }, waiting: { host: [], guest: [] } });
  return code;
}

/* A peer polls for whatever the other one has left it. If the mailbox is empty
   the request is parked rather than answered, so a message posted a moment later
   is delivered at once instead of on the next poll. */
function deliver(room, role) {
  const queue = room.box[role];
  if (!queue.length) return;
  const waiters = room.waiting[role].splice(0);
  for (const res of waiters) {
    clearTimeout(res.__timer);
    send(res, 200, { messages: queue.splice(0) });
    break;
  }
}

function send(res, status, body) {
  if (res.__done) return;
  res.__done = true;
  const text = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(text),
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Cache-Control': 'no-store'
  });
  res.end(text);
}

function readBody(req, cb) {
  let size = 0;
  const chunks = [];
  req.on('data', (c) => {
    size += c.length;
    if (size > MAX_BODY) { req.destroy(); return; }
    chunks.push(c);
  });
  req.on('end', () => {
    try { cb(JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}')); }
    catch (err) { cb(null); }
  });
}

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.ogg': 'audio/ogg',
  '.md': 'text/markdown; charset=utf-8', '.ico': 'image/x-icon'
};

function serveStatic(req, res, pathname) {
  const rel = decodeURIComponent(pathname === '/' ? '/index.html' : pathname);
  const file = path.join(ROOT, rel);
  // Never serve outside the repository, whatever the request claims to want.
  if (file !== ROOT && !file.startsWith(ROOT + path.sep)) { res.writeHead(403); res.end('forbidden'); return; }
  fs.stat(file, (err, stat) => {
    if (err || !stat.isFile()) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, {
      'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Content-Length': stat.size,
      'Cache-Control': 'no-cache'
    });
    fs.createReadStream(file).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://' + (req.headers.host || 'localhost'));
  const p = url.pathname;

  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    res.end();
    return;
  }

  if (p === '/net/new' && req.method === 'POST') {
    const code = makeRoom();
    console.log('room ' + code + ' opened');
    send(res, 200, { code: code });
    return;
  }

  if (p === '/net/send' && req.method === 'POST') {
    const code = (url.searchParams.get('code') || '').toUpperCase();
    const from = url.searchParams.get('from');
    const room = rooms.get(code);
    if (!room || (from !== 'host' && from !== 'guest')) { send(res, 404, { error: 'no such room' }); return; }
    readBody(req, (msg) => {
      if (!msg) { send(res, 400, { error: 'bad message' }); return; }
      const to = from === 'host' ? 'guest' : 'host';
      room.touched = Date.now();
      room.box[to].push(msg);
      deliver(room, to);
      send(res, 200, { ok: true });
    });
    return;
  }

  if (p === '/net/recv' && req.method === 'GET') {
    const code = (url.searchParams.get('code') || '').toUpperCase();
    const as = url.searchParams.get('as');
    const room = rooms.get(code);
    if (!room || (as !== 'host' && as !== 'guest')) { send(res, 404, { error: 'no such room' }); return; }
    room.touched = Date.now();
    if (room.box[as].length) { send(res, 200, { messages: room.box[as].splice(0) }); return; }
    room.waiting[as].push(res);
    res.__timer = setTimeout(() => {
      const held = room.waiting[as];
      const at = held.indexOf(res);
      if (at >= 0) held.splice(at, 1);
      send(res, 200, { messages: [] });
    }, POLL_MS);
    req.on('close', () => {
      const held = room.waiting[as];
      const at = held.indexOf(res);
      if (at >= 0) held.splice(at, 1);
      clearTimeout(res.__timer);
      res.__done = true;
    });
    return;
  }

  if (p.startsWith('/net/')) { send(res, 404, { error: 'unknown endpoint' }); return; }

  serveStatic(req, res, p);
});

setInterval(() => {
  const now = Date.now();
  for (const [code, room] of rooms) {
    if (now - room.touched < ROOM_TTL) continue;
    for (const role of ['host', 'guest'])
      for (const res of room.waiting[role].splice(0)) { clearTimeout(res.__timer); send(res, 410, { error: 'room expired' }); }
    rooms.delete(code);
    console.log('room ' + code + ' expired');
  }
}, 30000).unref();

server.listen(PORT, () => {
  console.log('Ratatatata! serving ' + ROOT);
  console.log('  http://localhost:' + PORT + '/');
  console.log('Signalling ready. Create a game in the browser and send the link it gives you.');
});
