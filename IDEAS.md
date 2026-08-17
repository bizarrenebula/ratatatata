# Ideas

Features worth building on top of the game. Nothing here is committed to a
schedule — this is the backlog of things that would make Ratatatata! better.

---

## House music: the brothers' actual taste

**The pitch.** Rocco and Vinnie are sewer rats with a stereo. They do not listen
to chiptune — they listen to *house*. Replace the synthesized 8-bit soundtrack
with a set of AI-generated EDM tracks: deep house under the tunnels, something
harder and more electro as the stages climb the tower, and a proper peak-time
banger for P.C.U.-9. The whole game should feel like a night out that happens to
involve extermination.

This is a bigger change than swapping files, because the music would stop being
a background loop and start being the thing the game moves to.

### Why it fits

The pieces are already there:

- `Music` in [index.html](index.html) already crossfades between an ambient bed
  and a combat track, driven by nearby-enemy count and mini-boss engagement. That
  is exactly the "build / drop" structure house music is made of.
- Stage themes already run 11 deep, each with its own palette and mood — a
  natural mapping onto 11 tracks or 11 variations on one club night.
- The camera shake, muzzle flashes, lamps and particle bursts are all per-frame
  and already tied to gameplay events. Hanging them off a beat clock is cheap.

### What it would take

**1. Generate the tracks.** Produce them offline with a music model (Suno, Udio,
MusicGen, Stable Audio — whichever licenses cleanly for the intended use) and
commit rendered audio, not a runtime dependency. Prompts should carry the stage
brief: *"deep house, 122 BPM, dubby sub bass, dripping reverb, sewer tunnel"* →
*"peak-time techno, 138 BPM, distorted stabs, sirens"* for the tower.

Track list, mapping onto what `Music` already switches between:

| Slot | Feel | BPM |
| --- | --- | --- |
| Menu | filtered intro loop, no drums until you hit start | 120 |
| Stages 1-4 (sewers, street) | deep / tech house, rolling bassline | 120-124 |
| Stages 5-7 (warehouse, avenue) | warehouse techno, harder kick | 126-130 |
| Stages 8-10 (P.C.U. tower) | electro, acid, rising tension | 130-136 |
| Mini-boss | the drop — same key as the stage bed so it can cut in on a bar | stage BPM |
| P.C.U.-9 | peak-time banger with a breakdown for phase 2 | 138 |

**2. Fix the format.** The current WAVs are 22kHz mono and already 6.6MB for
chiptune; real music at that quality would be unlistenable and enormous. Move to
Ogg/Opus or AAC (`.m4a`) — roughly 1MB per minute at good quality — and keep the
loader's existing `decodeAudioData` path, which does not care about the codec.
Ship a fallback source per track since Safari and Chrome disagree about Ogg.

**3. Loop honestly.** House lives or dies on seamless loops. Each track needs to
be rendered to an exact bar count and looped on a sample boundary, the way
`playAmbient` already does with `loopStart`/`loopEnd`. Store the loop points and
BPM in `assets/audio/music-meta.json` next to the existing segment table.

**4. Switch on the bar, not on the frame.** Today `Music.update` swaps to the
combat track the instant a mini-boss engages, which will sound wrong the moment
the music has a groove. Queue the switch and let it land on the next bar — with
BPM known, the bar length is arithmetic, and `AudioBufferSourceNode.start(when)`
already takes a scheduled time. A one-bar filter sweep covers the transition.

**5. Layer instead of crossfade.** Rather than two whole tracks, render each
stage as stems — drums, bass, lead, pads — start them together in sync, and ride
their gains on the existing threat count. Walking an empty tunnel is drums and
sub; three enemies on screen brings in the lead; a mini-boss opens everything.
The music then *is* the tension meter, and there is never a transition to hide.

### The part that makes it a feature, not a re-skin

Once the beat clock exists, spend it:

- **Lamps and neon pulse on the beat.** `paintLamps` and the stage rim lighting
  already flicker on `tick`; drive them from beat phase instead.
- **Muzzle flashes and explosions bloom harder on the downbeat.** A free
  cinematic feel for a couple of lines in `explode` and `paintLighting`.
- **The vignette breathes with the bassline** — scale `paintVignette` by a
  low-frequency envelope sampled from an `AnalyserNode`.
- **Perfect-on-beat kills score bonus.** Land a headshot within ~80ms of a beat
  and pay out extra, with the existing skull-and-knife marker flashing gold. This
  turns the soundtrack into a mechanic and rewards playing to the rhythm — very
  much in the spirit of a rat who came to dance.
- **Mini-boss phase changes land on the drop.** Phases already step at 2/3 and
  1/3 health; hold the transition to the next bar and let the music do the work.

### Watch out for

- **Licensing.** Confirm the generator's terms permit distribution in a game
  before committing anything. Keep the prompts and the tool/version in
  `assets/audio/CREDITS.md` so provenance is traceable.
- **Repo weight.** Eleven tracks at 2-3 minutes each is 20-30MB even compressed.
  That is fine for a static site, less fine for a git repo that currently holds
  every asset inline. Consider Git LFS, or shorter loops rather than full tracks.
- **The no-build-step promise.** The game runs by opening a file. Audio decoding
  needs a real HTTP origin, which is already true of the current WAVs, but the
  README should stay honest about it.
- **Taste.** Generated EDM drifts toward generic. Budget time to reject most of
  what comes out; one good loop beats eleven mediocre ones, and reusing a strong
  track across a few stages is better than shipping filler.

### Loose ends this would tidy up

- `assets/audio/gameplay-themes.wav` is committed but referenced nowhere and is
  no longer produced by [scripts/generate_music.js](scripts/generate_music.js).
  Delete it, or fold it into the new set.
- The ambient bed has 10 segments for 11 stages, so the Extermination Core
  currently reuses an earlier stage's music. Give the final stage its own track.
