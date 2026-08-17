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
| Jump | Z, K, or Space |
| Fire / bite | X or J; automatically bites when an enemy is within melee range |
| Grenade | Hold C or L to ready; release for short, medium, or three-second maximum throw |
| Swap brother | Left Shift or Q |
| Start / restart | Enter or R |
| Pause | P or Escape |

On compatible phones, touch controls float over the full-screen landscape game: an analog stick on the left, four action buttons on the right, and pause in the upper-left corner.

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
- Pistol, machine gun, shotgun, flamethrower, bat, and grenades
- Procedural stage layouts, platforms, enterable buildings, and pickups
- Mouse, bat, weasel, and cat enemies plus a final boss
- Eleven visual stage themes, particles, lighting, camera shake, and synthesized sound effects
