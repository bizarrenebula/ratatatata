# Ratatatata! — Sewer Assault

A browser-based, side-scrolling action game prototype built with the Canvas 2D and Web Audio APIs. It currently runs without a build step or external dependencies.

## Run locally

Because the game is self-contained, you can open `index.html` directly in a browser. For more consistent browser behavior, serve the repository with any static file server, for example:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Two players

The title screen asks whether you are playing alone or with someone. **Create
game** mints a room and gives you a link; send it to a friend and their browser
joins yours directly. Once connected, the character select doubles as the lobby:
your pick wears a **P1** badge in Rocco's red, your friend's wears **P2** in
Vinnie's blue, and each of you sees the other move.

Peers cannot find each other unaided, so a small rendezvous hands them each
other's connection details. Nothing about the game passes through it — once the
two browsers have been introduced they talk directly.

Run it locally, which serves the game as well, so the link is same-origin:

```sh
node scripts/signal-server.js 8080
```

Then open <http://localhost:8080>. For a friend on another network, expose that
port with a tunnel (`cloudflared tunnel --url http://localhost:8080`, `ngrok http
8080`) and send them the address it gives you.

To run the rendezvous on Cloudflare instead — one Durable Object per room, which
is what gives both peers a single consistent place to meet:

```sh
cd scripts/cloudflare && npx wrangler deploy
```

Then serve the game from anywhere and point it at the Worker with
`?signal=https://ratatatata-signal.<your-subdomain>.workers.dev`.

**Co-op play itself is not wired up yet** — the lobby connects, but deploying
starts your own game. Both players running in one level is the next piece.

## Controls

| Action | Keyboard |
| --- | --- |
| Move / aim | Arrow keys or WASD |
| Roll | Move left/right + press Down; press Down once while airborne to somersault |
| Drop through | Hold Down and press Jump while standing on a platform or interior floor |
| Jump | Z, K, or Space |
| Fire / bite | X or J; automatically bites when an enemy is within melee range |
| Grenade | Hold C or L; range grows smoothly with the hold, from a short lob on a tap to maximum at 1.5 seconds |
| Swap brother | Left Shift or Q |
| Start / restart | Enter or R |
| Pause | P or Escape |

On compatible phones, twin sticks float over the full-screen landscape game:

| Control | Position | Does |
| --- | --- | --- |
| Move stick | bottom left | Left/right walks; a straight push up jumps, or climbs where stairs or a door are in reach; down crouches |
| Aim stick | bottom right | Aims through a full 360°, and **fires by itself** once pushed past the inner ring — a lighter push turns and aims without spending ammo |
| Bomb | above the move stick | Tap to lob a grenade at your feet; hold up to 1.5 seconds for range |
| Jump, Swap | above the aim stick | Jump button covers crouch-drops (down + jump), which one stick cannot express |
| Weapon change | on the character | Swipe left/right across the brother; the gallery appears over his head |
| Pause | upper-left corner | |

Neither thumb has to leave its stick to move, aim or shoot. While the aim stick
is pushed it also decides which way the brother faces, so you can retreat left
while still shooting right. Each stick owns the area around its own well, so
walking still works when the camera parks the brother on top of the move stick.
Aim assistance can be switched on or off on the character-select screen.

## Project structure

```text
.
├── index.html              # Complete runnable game prototype
├── assets/
│   └── images/
│       └── concept-art/    # Character and enemy reference artwork
├── README.md
└── .gitignore
```

The current implementation intentionally remains in one HTML file so this initial reorganization does not alter runtime behavior. As the game grows, the inline CSS and JavaScript can be split into focused modules (rendering, input, audio, entities, levels, and state management) with a small development toolchain.

## Current game systems

- Responsive Canvas 2D rendering and mobile arcade controls
- Two switchable characters with different movement and combat stats
- Starting claw/bite combat plus collectible knives, pistols, machine guns, shotguns, flamethrowers, bazookas, and grenades
- Procedural stage layouts, enterable buildings, and pickups
- Themed destructible props instead of bare floating platforms: pipework in the
  sewers, crates, bins, phone boxes and parked cars downtown, and crates, cargo
  trucks and cranes in the warehouses — all jumpable, and all but the crane mast
  can be shot or blown apart
- Mouse, bat, weasel, cat, and machine-gun lizard enemies plus a final boss
- Headshots: 15% of direct hits (bullets and melee, never splash) kill a
  rank-and-file enemy outright and deal double damage to mini-bosses and
  P.C.U.-9, marked by a skull-and-knife sting over the target
- Mini-bosses hold a fixed zone around their spawn: they commit the moment they
  see you inside it, and break off if you leave, so a fight can always be quit
- A live size control (top right) scales the cast; `BUILD_SCALE` and `ITEM_SCALE`
  in `index.html` scale structures and pickups to match
- Eleven visual stage themes, particles, lighting, camera shake, and synthesized sound effects
