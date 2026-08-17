# Ratatatata! — Sewer Assault

A browser-based, side-scrolling action game prototype built with the Canvas 2D and Web Audio APIs. It currently runs without a build step or external dependencies.

## Run locally

Because the game is self-contained, you can open `index.html` directly in a browser. For more consistent browser behavior, serve the repository with any static file server, for example:

```sh
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Controls

| Action | Keyboard |
| --- | --- |
| Move / aim | Arrow keys or WASD |
| Roll | Move left/right + press Down; press Down once while airborne to somersault |
| Drop through | Hold Down and press Jump while standing on a platform or interior floor |
| Jump | Z, K, or Space |
| Fire / bite | X or J; automatically bites when an enemy is within melee range |
| Grenade | Hold C or L to ready; release for short, medium, or three-second maximum throw |
| Swap brother | Left Shift or Q |
| Start / restart | Enter or R |
| Pause | P or Escape |

On compatible phones, touch controls float over the full-screen landscape game: an analog movement/aim stick on the left, four action buttons on the right, a vertical weapon swiper at the far-right edge, and pause in the upper-left corner. Tap Jump for a short hop or hold it for a higher jump. Aim assistance can be switched on or off on the character-select screen.

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
