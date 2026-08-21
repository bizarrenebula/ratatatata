#!/usr/bin/env python3
"""Cut the character reference sheet into transparent sprites.

The sheet is one flat illustration on paper: six full figures (side, back and
front, for each brother), five head profiles and two weapon hands. This finds
each of them on its own rather than being told where they are, so a redrawn
sheet can be run through again without hand-editing coordinates.

How it finds them: everything that is not paper is one mask; connected blobs of
that mask are the drawings; blobs too small to be a drawing are the labels and
the arrows. Each blob's holes are then filled, which is what keeps the whites
that belong to the character — Vinnie's shoe soles, Rocco's shirt — instead of
punching them out along with the background.

    python3 scripts/cut-rig.py <sheet.png> [outdir]
    python3 scripts/cut-rig.py <drawing.png> [outdir] --single <name>

The second form takes the biggest drawing on the page and saves it under the
name given, for when one figure is redrawn on its own rather than the whole
sheet again. Requires pillow, numpy, scipy.
"""
import json
import sys
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# Where each drawing sits on the sheet, in fractions of the sheet's size, so the
# mapping survives a rescale. Matched to the nearest blob centre.
LAYOUT = [
    ('rocco-side',       0.16, 0.28, 'figure'),
    ('vinnie-side',      0.38, 0.30, 'figure'),
    ('rocco-back',       0.63, 0.28, 'figure'),
    ('vinnie-back',      0.86, 0.30, 'figure'),
    ('rocco-front',      0.16, 0.75, 'figure'),
    ('vinnie-front',     0.48, 0.77, 'figure'),
    ('rocco-head-level', 0.60, 0.64, 'head'),
    ('rocco-head-up',    0.71, 0.64, 'head'),
    ('vinnie-head-up',   0.79, 0.66, 'head'),
    ('rocco-head-down',  0.88, 0.64, 'head'),
    ('vinnie-head-down', 0.95, 0.65, 'head'),
    ('hand-pistol',      0.63, 0.88, 'hand'),
    ('hand-rifle',       0.86, 0.87, 'hand'),
]
MIN_AREA = {'figure': 60000, 'head': 12000, 'hand': 20000}


def paper_bounds(rgb):
    """The sheet inside whatever letterboxing the screenshot brought with it."""
    lum = rgb.mean(axis=2)
    cols = (lum > 232).mean(axis=0)
    rows = (lum > 232).mean(axis=1)
    xs = np.where(cols > 0.30)[0]
    ys = np.where(rows > 0.30)[0]
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def rules(ink):
    """The bars a screenshot brings with it, and nothing that was drawn.

    A rule is long and it is thin. Thin is the half that matters: measuring it
    against the width of the page only works when the page is a full sheet with
    many small drawings on it, and reads a single figure's outstretched arms as
    a bar. Ink more than twenty pixels tall is a drawing whatever its width, so
    that is taken out first and the test is applied to what is left.
    """
    thick = ndimage.binary_opening(ink, structure=np.ones((21, 1)))
    thin = ink & ~thick
    return ndimage.binary_opening(thin, structure=np.ones((1, 120)))


def blobs(rgb):
    lum = rgb.mean(axis=2)
    sat = rgb.max(axis=2).astype(np.int16) - rgb.min(axis=2).astype(np.int16)
    ink = (lum < 225) | (sat > 26)
    # Close the outline's gaps so a figure is one blob and not a scatter of them.
    ink = ndimage.binary_closing(ink, structure=np.ones((5, 5)))
    # Take out the bars a screenshot brings with it before labelling: a figure
    # whose shoe touches one is welded to it, and to whatever else it crosses.
    ink &= ~ndimage.binary_dilation(rules(ink), structure=np.ones((7, 7)))
    lab, n = ndimage.label(ink)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        if sl is None:
            continue
        mask = lab[sl] == i + 1
        area = int(mask.sum())
        ys, xs = sl
        out.append({'id': i + 1, 'area': area, 'slice': sl,
                    'cx': (xs.start + xs.stop) / 2, 'cy': (ys.start + ys.stop) / 2,
                    'w': xs.stop - xs.start, 'h': ys.stop - ys.start})
    return lab, out


def cut(rgb, lab, blob, pad=6):
    """One drawing on transparent, with its interior whites kept and a soft edge."""
    ys, xs = blob['slice']
    y0, y1 = max(0, ys.start - pad), min(rgb.shape[0], ys.stop + pad)
    x0, x1 = max(0, xs.start - pad), min(rgb.shape[1], xs.stop + pad)
    mask = (lab[y0:y1, x0:x1] == blob['id'])
    # Everything enclosed by the outline belongs to the character, white or not.
    mask = ndimage.binary_fill_holes(mask)
    mask = ndimage.binary_dilation(mask, structure=np.ones((3, 3)))
    alpha = Image.fromarray((mask * 255).astype(np.uint8))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.7))
    out = Image.fromarray(rgb[y0:y1, x0:x1].astype(np.uint8)).convert('RGBA')
    out.putalpha(alpha)
    return out.crop(out.getbbox())


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith('--')]
    single = sys.argv[sys.argv.index('--single') + 1] if '--single' in sys.argv else None
    src = argv[0] if argv else 'sheet.png'
    outdir = argv[1] if len(argv) > 1 else 'assets/images/rig'
    os.makedirs(outdir, exist_ok=True)
    im = Image.open(src).convert('RGB')
    x0, y0, x1, y1 = paper_bounds(np.asarray(im).astype(np.int16))
    im = im.crop((x0, y0, x1, y1))
    rgb = np.asarray(im).astype(np.int16)
    H, W, _ = rgb.shape
    lab, found = blobs(rgb)

    if single:
        best = max(found, key=lambda b: b['area'])
        sprite = cut(rgb, lab, best)
        sprite.save(os.path.join(outdir, single + '.png'))
        path = os.path.join(outdir, 'rig-manifest.json')
        manifest = json.load(open(path)) if os.path.exists(path) else {}
        manifest[single] = {'w': sprite.width, 'h': sprite.height,
                            'kind': manifest.get(single, {}).get('kind', 'figure')}
        json.dump(manifest, open(path, 'w'), indent=1, sort_keys=True)
        print('%-18s %4dx%-4d  area %7d' % (single, sprite.width, sprite.height, best['area']))
        return

    manifest, taken = {}, set()
    for name, fx, fy, kind in LAYOUT:
        want_x, want_y = fx * W, fy * H
        best, bestd = None, 1e18
        for b in found:
            if b['id'] in taken or b['area'] < MIN_AREA[kind]:
                continue
            d = (b['cx'] - want_x) ** 2 + (b['cy'] - want_y) ** 2
            if d < bestd:
                bestd, best = d, b
        if best is None:
            print('MISSING %-18s (no blob near %.2f,%.2f)' % (name, fx, fy))
            continue
        taken.add(best['id'])
        sprite = cut(rgb, lab, best)
        sprite.save(os.path.join(outdir, name + '.png'))
        manifest[name] = {'w': sprite.width, 'h': sprite.height, 'kind': kind}
        print('%-18s %4dx%-4d  area %7d' % (name, sprite.width, sprite.height, best['area']))

    with open(os.path.join(outdir, 'rig-manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    print('%d sprites -> %s' % (len(manifest), outdir))


if __name__ == '__main__':
    main()
