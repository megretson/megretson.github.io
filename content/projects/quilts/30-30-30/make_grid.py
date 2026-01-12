#!/usr/bin/env python3
"""Make a 5x6 grid from images in day-X folders.

Usage examples:
python content/projects/quilts/30-30-30/make_grid.py \
  --src content/projects/quilts/30-30-30 \
  --out 30x30_grid.jpg \
  --cols 5 --rows 6 --sash 20 --cell 400 \
  --match 'MargaretAnderson\d+\.jpg'

The script looks for subdirectories named `day-N` (N numeric), picks the first
image found in each, and arranges them in numeric order into a grid. Images
are resized to fit the cell while preserving aspect ratio and centered on a
white background cell. The output has white sashing between and around cells.
"""
from __future__ import annotations

import argparse
import os
import re
from PIL import Image
from typing import List, Tuple


def parse_order_from_file(path: str) -> List[int]:
    """Parse a markdown file and return the list of day numbers in order.

    Looks for occurrences like 'Day 21' in the file and returns the numbers
    in the order they appear.
    """
    text = ''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception:
        raise SystemExit(f'Unable to read order file: {path}')
    nums = [int(m.group(1)) for m in re.finditer(r'Day\s*(\d+)', text)]
    return nums

IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.tif', '.tiff')


def find_day_dirs(src: str) -> List[Tuple[int, str]]:
    dirs = []
    for name in os.listdir(src):
        path = os.path.join(src, name)
        if os.path.isdir(path):
            m = re.match(r'^day-(\d+)$', name)
            if m:
                dirs.append((int(m.group(1)), path))
    dirs.sort(key=lambda x: x[0])
    return dirs


def find_image_in_dir(d: str) -> str | None:
    for entry in sorted(os.listdir(d)):
        low = entry.lower()
        if any(low.endswith(ext) for ext in IMAGE_EXTS):
            return os.path.join(d, entry)
    return None


def find_image_by_pattern(d: str, pattern: str) -> str | None:
    """Return the first image filename in d matching regex pattern, else None."""
    try:
        prog = re.compile(pattern)
    except re.error:
        prog = re.compile(re.escape(pattern))
    for entry in sorted(os.listdir(d)):
        if prog.search(entry):
            low = entry.lower()
            if any(low.endswith(ext) for ext in IMAGE_EXTS):
                return os.path.join(d, entry)
    return None


def load_images(paths: List[str]) -> List[Image.Image]:
    imgs = []
    for p in paths:
        if p is None:
            imgs.append(None)
            continue
        try:
            im = Image.open(p)
            # convert to RGB for consistent output (handles PNG with alpha)
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGB')
            imgs.append(im)
        except Exception as e:
            raise RuntimeError(f"Failed to open image {p}: {e}")
    return imgs


def make_grid(images: List[Image.Image], out_path: str, cols: int, rows: int,
              sash: int, cell_w: int | None, cell_h: int | None, bg: Tuple[int,int,int]):
    # Determine cell size
    widths = [im.width for im in images if im is not None]
    heights = [im.height for im in images if im is not None]
    if not widths or not heights:
        raise RuntimeError('No images to place in grid')
    if cell_w is None:
        cell_w = max(widths)
    if cell_h is None:
        cell_h = max(heights)

    out_w = cols * cell_w + (cols + 1) * sash
    out_h = rows * cell_h + (rows + 1) * sash
    out = Image.new('RGB', (out_w, out_h), color=bg)

    idx = 0
    for r in range(rows):
        for c in range(cols):
            x0 = sash + c * (cell_w + sash)
            y0 = sash + r * (cell_h + sash)
            if idx >= len(images):
                break
            im = images[idx]
            if im is not None:
                # make a white cell and paste the resized image centered
                cell = Image.new('RGB', (cell_w, cell_h), color=bg)
                # preserve aspect ratio
                im_copy = im.copy()
                im_copy.thumbnail((cell_w, cell_h), Image.LANCZOS)
                iw, ih = im_copy.size
                paste_x = (cell_w - iw) // 2
                paste_y = (cell_h - ih) // 2
                # handle alpha
                if im_copy.mode in ('RGBA', 'LA'):
                    alpha = im_copy.split()[-1]
                    cell.paste(im_copy.convert('RGB'), (paste_x, paste_y), mask=alpha)
                else:
                    cell.paste(im_copy, (paste_x, paste_y))
                out.paste(cell, (x0, y0))
            idx += 1

    # ensure parent dir exists
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    out.save(out_path)
    print(f'Wrote {out_path} ({out_w}x{out_h})')


def main():
    p = argparse.ArgumentParser(description='Create a grid from day-X folders')
    p.add_argument('--src', required=True, help='Source folder containing day-N subfolders')
    p.add_argument('--out', required=True, help='Output image path')
    p.add_argument('--cols', type=int, default=5)
    p.add_argument('--rows', type=int, default=6)
    p.add_argument('--sash', type=int, default=20, help='Sash width in pixels')
    p.add_argument('--cell', type=int, default=None, help='Uniform cell width and height (px)')
    p.add_argument('--cell-width', type=int, default=None)
    p.add_argument('--cell-height', type=int, default=None)
    p.add_argument('--bg', default='white', help='Background color (name or #RRGGBB)')
    p.add_argument('--match', default=None, help='Regex to match image filename in each day folder')
    p.add_argument('--order-from', default=None, help='Path to markdown listing the desired Day order (e.g. _index.md)')
    args = p.parse_args()

    # collect day dirs
    days = find_day_dirs(args.src)
    if not days:
        raise SystemExit('No day-* directories found in ' + args.src)

    days = [d for _, d in days]
    needed = args.cols * args.rows
    if len(days) < needed:
        raise SystemExit(f'Found {len(days)} day folders, but grid requires {needed}')

    # determine the ordered list of day directories to use
    ordered_dirs: List[str]
    if args.order_from:
        nums = parse_order_from_file(args.order_from)
        if not nums:
            raise SystemExit('No Day entries found in order file')
        # build ordered dirs based on parsed numbers
        ordered_dirs = []
        for n in nums:
            path = os.path.join(args.src, f'day-{n}')
            if not os.path.isdir(path):
                raise SystemExit(f'Expected folder for day {n} at {path} not found')
            ordered_dirs.append(path)
        if len(ordered_dirs) < needed:
            raise SystemExit(f'Order file provides {len(ordered_dirs)} items, but grid requires {needed}')
    else:
        ordered_dirs = days

    # pick image in each ordered day folder; optionally match a filename pattern
    image_paths = []
    pattern = getattr(args, 'match', None)
    for d in ordered_dirs[:needed]:
        img = None
        if pattern:
            img = find_image_by_pattern(d, pattern)
        if not img:
            img = find_image_in_dir(d)
        image_paths.append(img)

    images = load_images(image_paths)

    # parse bg color
    if args.bg.startswith('#') and len(args.bg) == 7:
        bg = tuple(int(args.bg[i:i+2], 16) for i in (1,3,5))
    else:
        # PIL accepts color names
        from PIL import ImageColor
        try:
            bg = ImageColor.getrgb(args.bg)
        except Exception:
            bg = (255,255,255)

    cw = args.cell or args.cell_width
    ch = args.cell or args.cell_height

    make_grid(images, args.out, args.cols, args.rows, args.sash, cw, ch, bg)


if __name__ == '__main__':
    main()
