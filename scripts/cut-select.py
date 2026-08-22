#!/usr/bin/env python3
"""Prepare the full-body figures for the character-select cards.

Two things are wrong with them as they come off the reference sheet.

The first is a white rim. The sheet was drawn on white, so every pixel along the
silhouette is part subject and part paper: at the soft edge the two are mixed in
the alpha channel, and on the last opaque row the paper has usually won
outright. Against the game's near-black cards that reads as a cut-out sticker.
The mix is undone rather than blurred away — for a pixel that is `a` subject over
white, the observed colour is `a*C + (1-a)*white`, so `C` comes back out by
rearranging — and the outermost opaque ring, which has no alpha left to undo, is
simply eaten.

The second is that they are lit for a white page: bright, low-contrast, and
sitting apart from a game whose whole palette is deep. So the grade pushes the
midtones down, opens the gap between light and dark, and warms the shadows the
way the street lamps in the game do.

    python3 scripts/cut-select.py [outdir]

Writes <name>-select.png beside the figures.
"""
import os
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

FIGURES = ['rocco-front', 'vinnie-front']
RIM = 1            # opaque rings to eat; the paper has fully won on these
GAMMA = 1.16       # >1 deepens the midtones
SAT = 1.20
CONTRAST = 1.14
PIVOT = 0.46
WARM = np.array([1.03, 0.995, 0.955])   # shadows toward the sodium lamps
PALE = 0.80          # a region this bright is a candidate for paper
FACE_BAND = 0.26     # top of the figure where interior whites are legitimate
WARM_KEEP = 0.045    # red-over-blue above this means drawn, not paper


def unmatte(rgb, a):
    """Recover the subject's own colour from a blend over white."""
    out = rgb.copy()
    soft = (a > 0.004) & (a < 0.996)
    if soft.any():
        av = a[soft][:, None]
        out[soft] = np.clip((rgb[soft] - (1.0 - av)) / av, 0.0, 1.0)
    return out


def depaper(rgb, a):
    """Punch out the pockets of paper the figure encloses.

    The extraction that produced these files filled interior holes, which is
    right for an eye or a tooth and wrong for the gap between two fingers: the
    paper trapped inside the silhouette came through as an opaque pale blob.
    Colour alone will not separate the two — the pockets sit around 234 grey and
    a tooth is not much darker — so two things are asked of each pale region.

    Is it neutral? Paper is; the drawing's own whites are warmed by the ink and
    the tint around them, so an eye reads red-over-blue by a good margin.

    And is it low on the figure? Every genuine interior white on these two is in
    the face, in the top quarter. The pockets the eye catches are between the
    fingers, under the arms and between the legs, all well below it.

    A region has to fail both tests to be cleared, so a warm patch anywhere and
    anything at all in the face are both left alone.
    """
    op = a > 0.78
    if not op.any():
        return a
    ys = np.nonzero(op.any(axis=1))[0]
    top, bottom = ys[0], ys[-1]
    face_line = top + (bottom - top) * FACE_BAND

    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    pale = op & (mn > PALE) & (sat < 0.11)
    lab, n = ndimage.label(pale)
    if not n:
        return a
    cleared = np.zeros_like(pale)
    for cid in range(1, n + 1):
        m = lab == cid
        if m.sum() < 6:
            continue
        cy = np.nonzero(m.any(axis=1))[0].mean()
        if cy <= face_line:
            continue                                  # in the face: leave it
        warm = float(rgb[m][:, 0].mean() - rgb[m][:, 2].mean())
        if warm > WARM_KEEP:
            continue                                  # tinted: part of the drawing
        cleared |= m
    if cleared.any():
        # feather by a pixel so the new edges are not stencil-sharp
        soft = ndimage.binary_dilation(cleared, np.ones((3, 3)))
        a = np.where(cleared, 0.0, a)
        a = np.where(soft & ~cleared, a * 0.55, a)
    return a


def grade(rgb):
    x = np.clip(rgb, 0, 1) ** GAMMA
    lum = x @ np.array([0.2126, 0.7152, 0.0722])
    x = np.clip(lum[..., None] + (x - lum[..., None]) * SAT, 0, 1)
    x = np.clip((x - PIVOT) * CONTRAST + PIVOT, 0, 1)
    # warm the dark end only, so highlights stay neutral
    shade = (1.0 - lum)[..., None] ** 2
    x = np.clip(x * (1.0 + (WARM - 1.0) * shade), 0, 1)
    return x


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else 'assets/images/rig'
    for name in FIGURES:
        im = Image.open(os.path.join(outdir, name + '.png')).convert('RGBA')
        arr = np.asarray(im).astype(np.float32) / 255.0
        rgb, a = arr[:, :, :3], arr[:, :, 3]

        rgb = unmatte(rgb, a)
        a = depaper(rgb, a)
        # eat the outermost opaque ring, which carries pure paper
        keep = ndimage.binary_erosion(a > 0.5, np.ones((3, 3)), iterations=RIM)
        a = np.where(keep, a, np.minimum(a, 0.0))
        rgb = grade(rgb)

        out = np.dstack([rgb, a])
        img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGBA')
        box = img.getbbox()
        if box:
            img = img.crop(box)
        who = name.split('-')[0]
        img.save(os.path.join(outdir, who + '-select.png'))

        al = np.asarray(img).astype(np.float32)[:, :, 3] / 255.0
        px = np.asarray(img).astype(np.float32)[:, :, :3].mean(axis=2)
        op = al > 0.8
        edge = op & ~ndimage.binary_erosion(op, np.ones((5, 5)))
        print('%-8s %dx%d  edge lum %.0f (was ~195)  body lum %.0f' %
              (who, img.width, img.height, px[edge].mean(), px[ndimage.binary_erosion(op, np.ones((9, 9)))].mean()))


if __name__ == '__main__':
    main()
