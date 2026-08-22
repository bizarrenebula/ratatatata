#!/usr/bin/env python3
"""Lift the title logo off the transparency checkerboard it was flattened onto.

The artwork arrived as a JPEG, which has no alpha channel, so the checkerboard
that stood for transparency was baked in as real pixels: a 23-pixel grid of two
flat greys, 188 and 223 once the encoder had finished with them.

Removing them by brightness alone would punch holes in the logo — the ampersand
is silver and the fangs are white, both inside that range — so the checker is
identified by being a checker. The grid's period and phase are measured off the
picture, a synthetic one is laid over it, and a pixel counts as background only
where it is neutral, unsaturated and sitting at the level the grid says it
should be. Flat artwork cannot agree with a two-level alternating grid across a
whole square by accident, so the logo survives and the paper does not.

That also reaches the checker trapped inside the counters of the A, the C and
the second A, which a flood from the border never could: those pockets are
fenced off by the letterforms themselves.

What is left is a JPEG edge, a band a pixel or two wide where the encoder mixed
artwork into checker. That band is eaten and the new edge feathered, so the logo
does not come out wearing a grey hem.

    python3 scripts/cut-logo.py <source.jpg> <out.png>
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

NEUTRAL = 18        # max channel spread still counted as grey
TOL = 15            # how far off its grid level a pixel may sit
MIN_PATCH = 220     # a real pocket of checker is most of a square; specks are not
EAT = 2             # pixels of blended edge to remove


def grid(lum):
    """Period, phase and the two levels of the baked-in checkerboard.

    The period comes off a border scanline. The phase is searched rather than
    derived: getting a half-pixel wrong in the arithmetic silently offsets the
    whole grid by one square, and a grid that is out of phase matches nothing.
    Twenty-three by twenty-three by two candidates is nothing to try.
    """
    edge = lum[3, :]
    mid = (edge.min() + edge.max()) / 2.0
    flips = np.where(np.diff((edge > mid).astype(int)) != 0)[0]
    px = int(np.median(np.diff(flips))) if len(flips) > 2 else 23
    lo = float(np.median(edge[edge <= mid]))
    hi = float(np.median(edge[edge > mid]))

    h, w = lum.shape
    ys, xs = np.mgrid[0:h:3, 0:w:3]            # every third pixel is plenty
    sub = lum[0:h:3, 0:w:3]
    best, bo = -1, (0, 0, False)
    for ox in range(px):
        for oy in range(px):
            par = (((xs + ox) // px) + ((ys + oy) // px)) % 2
            for flip in (False, True):
                want = np.where(par == (1 if flip else 0), lo, hi)
                score = int((np.abs(sub - want) < TOL).sum())
                if score > best:
                    best, bo = score, (ox, oy, flip)
    return px, bo[0], bo[1], bo[2], lo, hi


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else 'out.png'
    im = Image.open(src).convert('RGB')
    a = np.asarray(im).astype(np.int16)
    mx, mn = a.max(axis=2), a.min(axis=2)
    lum = a.mean(axis=2)
    h, w = lum.shape

    px, ox, oy, flip, lo, hi = grid(lum)
    ys, xs = np.mgrid[0:h, 0:w]
    par = (((xs + ox) // px) + ((ys + oy) // px)) % 2
    want = np.where(par == (1 if flip else 0), lo, hi)

    background = (mx - mn < NEUTRAL) & (np.abs(lum - want) < TOL)
    background = ndimage.binary_closing(background, np.ones((7, 7)))
    lab, n = ndimage.label(background)
    if n:
        sizes = ndimage.sum(background, lab, range(1, n + 1))
        small = np.isin(lab, 1 + np.where(sizes < MIN_PATCH)[0])
        background &= ~small

    keep = ndimage.binary_erosion(~background, np.ones((3, 3)), iterations=EAT)
    keep = ndimage.binary_opening(keep, np.ones((3, 3)))

    alpha = ndimage.gaussian_filter(keep.astype(np.float32), 0.7)
    alpha = np.clip((alpha - 0.35) / 0.45, 0, 1)

    out = np.dstack([a.astype(np.float32), alpha * 255]).astype(np.uint8)
    img = Image.fromarray(out, 'RGBA')
    box = img.getbbox()
    if box:
        img = img.crop(box)
    img.save(dst)
    al = np.asarray(img)[:, :, 3]
    print('%s  %dx%d  grid %dpx phase %d,%d levels %.0f/%.0f  opaque %.1f%%' %
          (dst, img.width, img.height, px, ox, oy, lo, hi, 100.0 * (al > 200).mean()))


if __name__ == '__main__':
    main()
