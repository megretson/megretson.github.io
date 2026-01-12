#!/usr/bin/env python3
"""Update each day-N/index.md with Day/Event/Quilt Block from master _index.md.

Usage:
  python update_day_indexes.py --master _index.md --src content/projects/quilts/30-30-30

It parses lines like:
  1. Day 21: Southport killer pleads guilty..., modified interlocked squares

and updates `day-21/index.md` so the markdown body becomes:
  Day: 21
  Event: Southport killer pleads guilty ...
  Quilt Block: modified interlocked squares
"""
from __future__ import annotations

import argparse
import os
import re
from typing import Dict, Tuple


def parse_master(master_path: str) -> Dict[int, Tuple[str, str]]:
    """Return mapping day_num -> (event, block) parsed from master file.

    Strategy: find lines starting with a number and containing 'Day N:' then
    take the remainder of the line and split at the LAST comma to separate
    event (left) and quilt block (right).
    """
    text = open(master_path, 'r', encoding='utf-8').read()
    entries: Dict[int, Tuple[str, str]] = {}
    for line in text.splitlines():
        m = re.match(r'\s*\d+\.\s*Day\s*(\d+)\s*:\s*(.+)', line)
        if not m:
            continue
        day = int(m.group(1))
        rest = m.group(2).strip()
        # split at last comma
        if ',' in rest:
            idx = rest.rfind(',')
            event = rest[:idx].strip()
            block = rest[idx+1:].strip()
        else:
            event = rest
            block = ''
        entries[day] = (event, block)
    return entries


def update_index(md_path: str, day: int, event: str, block: str) -> None:
    """Replace the body of md_path (after the frontmatter +++ block) with the data."""
    if not os.path.exists(md_path):
        raise FileNotFoundError(md_path)
    text = open(md_path, 'r', encoding='utf-8').read()
    # find end of frontmatter '+++'
    fm_end = None
    # frontmatter may start at top with +++
    if text.startswith('+++'):
        # split into three parts: '', frontmatter body, rest
        parts = text.split('+++', 2)
        if len(parts) >= 3:
            # reconstruct frontmatter including the delimiters exactly once
            fm = '+++' + parts[1] + '+++'
            fm_end = fm
            rest = parts[2].lstrip('\n')
        else:
            # malformed; treat entire file as frontmatter
            fm_end = text
            rest = ''
    else:
        # no frontmatter; treat whole file as rest
        fm_end = ''
        rest = text

    # Normalize quilt block to title case for consistent presentation
    block = block.title()
    body_lines = []
    body_lines.append(f'Day: {day}')
    body_lines.append(f'Event: {event}')
    body_lines.append(f'Quilt Block: {block}')
    body = '\n\n'.join(body_lines) + '\n'

    # If there is frontmatter, place a single blank line between it and the body
    if fm_end:
        new_text = fm_end.rstrip() + '\n\n' + body
    else:
        new_text = body
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(new_text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--master', required=True, help='Path to master _index.md containing ordering')
    p.add_argument('--src', required=True, help='Folder containing day-N subfolders')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    entries = parse_master(args.master)
    if not entries:
        print('No Day entries found in master file')
        return

    for day, (event, block) in entries.items():
        folder = os.path.join(args.src, f'day-{day}')
        md = os.path.join(folder, 'index.md')
        if not os.path.exists(md):
            print(f'SKIP: {md} not found')
            continue
        if args.dry_run:
            print(f'Would update {md}: Day={day} Event="{event}" Block="{block}"')
        else:
            print(f'Updating {md}...')
            update_index(md, day, event, block)


if __name__ == '__main__':
    main()
