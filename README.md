# Ratatatata! — Sewer Assault

A browser-based, side-scrolling action game prototype built with the Canvas 2D and Web Audio APIs. It currently runs without a build step or external dependencies.

## Run locally

Because the game is self-contained, you can open `index.html` directly in a browser. For more consistent browser behavior, serve the repository with any static file server, for example:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## The ground is not the level

Every biome climbs in its own language, and the camera goes with you.

**The sewers** are cut on two levels. Stretches of the main channel drop a storey
into a sump: pipework steps you down the near side, a ladder brings you back up
the far one, and there is usually something worth having at the bottom. Overhead,
grated catwalks run above the tunnel with a ladder at one end and pipes stepping
back down at the other, so the high lane is a loop rather than a dead end.

**The street** leaves the pavement. A fire escape zig-zags up the side of a block
to a run of rooftops — water tanks for cover, guards already up there, bats
working the gaps between buildings — and a second flight steps down the far side
to street level, where the exit is.

**The warehouse** stacks its crates small, medium, large. The stack is a
staircase, and it exists because a P.C.U. freight container stands in the way at
nearly two hundred pixels: too tall to jump, so the only way past is up and over.
Above the container hangs a gantry with the reason to be up there at all.

Everything load-bearing in all three is indestructible. A route that could be
shot away is a route that could strand you at the bottom of a pit.

Outdoors the camera follows what you are standing on. Land on a crate and it
lifts a little, on a catwalk a lot, on a rooftop all the way — and it stays there
while you do. Height is measured against the street directly beneath you, so
ground that merely rises and falls moves nothing, and a jump on its own moves
nothing either: the shot takes a new height when you land, not while you are in
the air. A fall pulls it back down before you can drop out of frame.

### One path, and reasons to leave it

There is one way from the start of a stage to its exit, and it is not a straight
line. The ground lane is broken on purpose: a sump in the sewers you drop into
and climb out of, a P.C.U. barricade across the street two and a half storeys
tall, a freight container in the warehouse too high to jump. Getting through
means straight, then up or down, then straight again — and on the roofs,
sometimes across a plank somebody laid between two buildings before you got
there. The thing the mission wants sits on that path, off the ground lane but
never down a branch.

Everything else is optional. A catwalk with no wall under it, a gantry over the
container, the upper floors of a block you could just as easily walk past — those
are pockets, and each one holds something worth the climb: a weapon, a grenade,
a brass slug for the wallet. Walk by and you lose nothing but the loot.

### Hints

A hint arrives where the decision is — at the ladder, at the pipes, at the
barricade — as a chevron and three or four words. It flashes there for about a
second and a half, then flies up and parks beside the brother's name in the HUD,
so it stays readable without standing in front of anything. One at a time, and
gone the moment you have answered it.

## Tokens

The brothers' money is brass turnstile slugs. You start with five, a mini-boss
drops one when it goes down, and finishing a job pays two. On the game over
screen a token buys a life and puts you back **where you fell**, not at the start
of the stage — which is what a token has bought in an arcade since arcades
existed. Quitting to the menu is the other door there, and it never costs
anything.

The wallet is yours to keep: it carries over between sessions, so slugs are worth
hoarding. If you spend down to nothing, starting a fresh run tops you back up to
three — a bad night should not lock you out of the next one.

## Select a job

A scrolled column of jobs. Each row carries a small square of the place itself —
its own sky and ground colours with the thing that stage is made of drawn on top:
pipes for the sewers, a lamp over a manhole downtown, stacked crates in the
warehouse, a vent grille for the way into the tower — beside the level's name and
its one-line slogan. Three or four are on screen; drag, scroll or use the arrow
keys for the rest.

The ones you have finished can be run again; the rest carry a padlock. Pick one,
press Continue, choose your brother, and the job starts on your confirmation. The
list opens on the last job you took rather than at the top.

## What the game remembers

Progress lives in one record in the browser's `localStorage`, under
`rat.save.v1`: the jobs you have cleared, your token wallet, your best score, the
furthest stage you reached and which brother you played last. It is written the
moment each of those changes, so closing the tab mid-run loses only the run.

Storage is per-browser and per-origin — a different browser, a different machine
or a private window is a different player, with a fresh save. Where the browser
refuses storage outright, the game plays exactly as before and simply forgets
when you leave. Builds before this kept a key per value; those are folded into
the record the first time this one runs, so nothing already unlocked is lost.

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
