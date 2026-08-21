#!/usr/bin/env python3
"""Split each side view into a torso and a pair of legs.

Three drawn positions is all a walk needs at this size — legs forward, legs
under him, legs back — and two of the three can be made from the one that was
drawn. So the legs are cut off as a single block that the game mirrors and
squeezes about the hip, rather than as separate limbs that would have to be
rotated and would need clean sockets to do it.

The cut is a horizontal line at the hip, with everything to the left of the tail
line kept out of it: the tail hangs below the hip too, and a tail that flips to
the other side of the body every time the legs swing is worse than no legs at
all.

    python3 scripts/cut-legs.py [outdir]

Writes <name>-torso.png and <name>-legs.png beside the figures, and records the
hip in rig-manifest.json so the game knows where to pivot.
"""
import json
import os
import sys
import numpy as np
from PIL import Image

# hip: where the legs start, down the picture. tail: the line the tail runs
# along, given as two points — everything left of it stays with the torso, and
# it slopes because the tail does. A straight vertical line cannot separate
# Vinnie's tail from his trailing foot: the tail leaves his hip at four tenths
# across and is down at nothing by the time it ends, and his back shoe sits
# between the two. pivot: the middle of the hips, which the legs swing about.
CUTS = {
    'rocco-side':  {'hip': 0.605, 'pivot': 0.425, 'tail': (0.30, 0.58, 0.02, 0.90)},
    'vinnie-side': {'hip': 0.560, 'pivot': 0.605, 'tail': (0.47, 0.74, 0.02, 0.82)},
}


def tail_edge(c, W, H):
    """For each row, the x left of which belongs to the tail and so to the torso."""
    x0, y0, x1, y1 = c['tail']
    ys = np.arange(H) / H
    t = np.clip((ys - y0) / (y1 - y0), 0, 1)
    return ((x0 + (x1 - x0) * t) * W).astype(int)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else 'assets/images/rig'
    path = os.path.join(outdir, 'rig-manifest.json')
    manifest = json.load(open(path)) if os.path.exists(path) else {}

    for name, c in CUTS.items():
        im = Image.open(os.path.join(outdir, name + '.png')).convert('RGBA')
        W, H = im.size
        a = np.asarray(im).copy()
        hip, edge = int(round(H * c['hip'])), tail_edge(c, W, H)
        cols = np.arange(W)[None, :]
        keep = cols >= edge[:, None]                 # right of the tail line
        below = np.zeros((H, W), bool)
        below[hip:, :] = True
        legmask = keep & below

        legs = a.copy()
        legs[~legmask, 3] = 0
        torso = a.copy()
        torso[legmask, 3] = 0

        for part, arr in (('torso', torso), ('legs', legs)):
            img = Image.fromarray(arr)
            box = img.getbbox()
            if box is None:
                print('EMPTY %s-%s' % (name, part))
                continue
            img.crop(box).save(os.path.join(outdir, name + '-' + part + '.png'))
            manifest[name + '-' + part] = {
                'w': box[2] - box[0], 'h': box[3] - box[1], 'kind': part,
                # Where this piece sits inside the whole figure, and where the hip
                # is within it — both as fractions of the original picture, so the
                # game can reassemble them without knowing any pixel counts.
                'ox': box[0] / W, 'oy': box[1] / H,
                'pivotX': c['pivot'], 'pivotY': c['hip']
            }
            print('%-24s %4dx%-4d at %.3f,%.3f' % (
                name + '-' + part, box[2] - box[0], box[3] - box[1], box[0] / W, box[1] / H))

    json.dump(manifest, open(path, 'w'), indent=1, sort_keys=True)


if __name__ == '__main__':
    main()
