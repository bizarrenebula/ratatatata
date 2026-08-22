#!/usr/bin/env python3
"""Cut each brother's head out of his front view for the HUD avatar.

The head is found rather than typed in: scanning down from the top of the
drawing, every row of the head is about as wide as the one above it, and then
the shoulders arrive and the row width roughly doubles in the space of a few
rows. That step is the neck. Everything above it is the head, and the crop is
squared off around it so the game can draw it in a circle without measuring
anything.

    python3 scripts/cut-avatars.py [outdir]

Writes <name>-avatar.png beside the figures.
"""
import os
import sys
import numpy as np
from PIL import Image

FIGURES = ['rocco-front', 'vinnie-front']
PAD = 0.10          # breathing room around the head, as a fraction of its size


def head_box(alpha):
    """Top, bottom, left, right of the head, in pixels."""
    rows = (alpha > 40).sum(axis=1)
    filled = np.nonzero(rows)[0]
    top = filled[0]
    # The width to beat: how wide the drawing is just below the crown, where it
    # is unambiguously still head. Taken as a median so one stray ear tuft or a
    # cap brim does not set the bar.
    probe = rows[top:top + max(8, len(filled) // 12)]
    base = np.median(probe[probe > 0])
    neck = None
    for y in range(top + int(len(filled) * 0.06), top + int(len(filled) * 0.55)):
        if rows[y] > base * 2.0:
            neck = y
            break
    if neck is None:
        neck = top + int(len(filled) * 0.30)
    band = alpha[top:neck] > 40
    cols = np.nonzero(band.any(axis=0))[0]
    return top, neck, cols[0], cols[-1]


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else 'assets/images/rig'
    for name in FIGURES:
        im = Image.open(os.path.join(outdir, name + '.png')).convert('RGBA')
        a = np.asarray(im)[:, :, 3]
        top, neck, x0, x1 = head_box(a)
        h, w = neck - top, x1 - x0
        side = int(max(h, w) * (1 + PAD * 2))
        cx, cy = (x0 + x1) // 2, top + h // 2
        box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
        out = Image.new('RGBA', (side, side), (0, 0, 0, 0))
        out.paste(im.crop(box), (0, 0))
        out = out.resize((256, 256), Image.LANCZOS)
        who = name.split('-')[0]
        out.save(os.path.join(outdir, who + '-avatar.png'))
        print('%-14s head rows %d..%d, cols %d..%d -> %dpx square' %
              (who, top, neck, x0, x1, side))


if __name__ == '__main__':
    main()
