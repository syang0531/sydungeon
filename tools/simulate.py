# -*- coding: utf-8 -*-
"""Roll dungeons on paper: how big do they get, how many levels, how often do stairs appear.

    python tools/simulate.py [runs]

An abstraction of vanilla jigsaw placement on the 7-block cell grid, with our pools and
weights: breadth-first from the hub, each open door picks a piece by weight, a piece is
placed if every cell it needs is free, otherwise the door is capped. Depth is counted per
path as vanilla does. The stair takes two cells (its own and the one above) and is entered
through either of its two doors at random, so half the time it leads down.

This is not the game - there is no rotation subtlety, no terrain, no max distance - but it
answers "is one-level-only chance or structure?" without generating a hundred worlds.
Change the WEIGHTS below to try a rebalance before touching the JSON.
"""
import random
import sys
from collections import Counter

# door directions as (dx, dz)
W, E, N, S = (-1, 0), (1, 0), (0, -1), (0, 1)

# piece -> (weight, door directions in the authored orientation, cells occupied relative to the
# entry door's cell as (dx, dy, dz)). Cells-only doors are marked with pool 'cells'.
PASSAGES = {
    #  name            weight  doors (dir, pool)                         extra cells
    'passage':        (10, [(W, 'p'), (E, 'p')], []),
    'passage_cell':   (10, [(W, 'p'), (E, 'p'), (S, 'c')], []),
    'passage_cells':  (10, [(W, 'p'), (E, 'p'), (N, 'c'), (S, 'c')], []),
    'cross':          (10, [(W, 'p'), (E, 'p'), (N, 'p'), (S, 'p')], []),
    'stair':          (5, [(W, 'p', 0), (W, 'p', 1)], [(0, 1, 0)]),   # door at level 0 and 1
    'cross_guard':    (4, [(W, 'p'), (E, 'p'), (N, 'p'), (S, 'p')], []),
    'dead_end':       (5, [(W, 'p')], []),
}
HUB_DOORS = [W, E, S]

ROT = {W: 0, N: 1, E: 2, S: 3}
DIRS = [W, N, E, S]


def rotate(d, r):
    return DIRS[(ROT[d] + r) % 4]


def simulate(size, rng, weights=None):
    weights = weights or {k: v[0] for k, v in PASSAGES.items()}
    names = list(PASSAGES)
    occupied = {(0, 0, 0): 'hub'}
    queue = [((0, 0, 0), d, 1) for d in HUB_DOORS]   # (cell, direction out, depth of child)
    stairs = 0
    capped = 0
    while queue:
        cell, out, depth = queue.pop(0)
        target = (cell[0] + out[0], cell[1], cell[2] + out[1])
        if depth > size or target in occupied:
            capped += 1
            continue
        # try pieces in weighted random order, like getShuffledTemplates
        order = []
        pool = list(names)
        while pool:
            pick = rng.choices(pool, [weights[n] for n in pool])[0]
            order.append(pick)
            pool.remove(pick)
        placed = False
        for name in order:
            _, doors, extra = PASSAGES[name]
            # which of the piece's passage doors is the entry? must face opposite `out`.
            entries = [d for d in doors if d[1] == 'p']
            rng.shuffle(entries)
            for entry in entries:
                edir = entry[0]
                level = entry[2] if len(entry) > 2 else 0
                # rotation so that edir points back toward the parent (-out)
                back = (-out[0], -out[1])
                r = (ROT[back] - ROT[edir]) % 4
                base = (target[0], target[1] - level, target[2])   # piece origin level
                cells = [base] + [(base[0] + ex, base[1] + ey, base[2] + ez) for ex, ey, ez in extra]
                if any(c in occupied for c in cells):
                    continue
                for c in cells:
                    occupied[c] = name
                if name == 'stair':
                    stairs += 1
                for d in doors:
                    if d is entry:
                        continue
                    ddir = rotate(d[0], r)
                    dlevel = d[2] if len(d) > 2 else 0
                    dcell = (base[0], base[1] + dlevel, base[2])
                    if d[1] == 'p':
                        queue.append((dcell, ddir, depth + 1))
                    else:
                        # a cell room: one cell, dead end
                        ct = (dcell[0] + ddir[0], dcell[1], dcell[2] + ddir[1])
                        if ct not in occupied and depth + 1 <= size:
                            occupied[ct] = 'cell'
                placed = True
                break
            if placed:
                break
        if not placed:
            capped += 1
    levels = Counter(c[1] for c, n in occupied.items() if n not in ('cell',))
    pieces = sum(1 for n in occupied.values() if n != 'cell')
    return pieces, stairs, levels, capped


def main():
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    rng = random.Random(1)
    for label, weights in (('current (stair 5)', None),
                           ('stair 3', {**{k: v[0] for k, v in PASSAGES.items()}, 'stair': 3}),
                           ('stair 10', {**{k: v[0] for k, v in PASSAGES.items()}, 'stair': 10})):
        level_counts = Counter()
        pieces_total = 0
        stairs_total = 0
        for _ in range(runs):
            size = rng.randint(16, 24) - 3          # what is left for the maze after the shaft
            pieces, stairs, levels, _ = simulate(size, rng, weights)
            # a level counts if it has more than a landing on it
            real_levels = sum(1 for lv, n in levels.items() if n >= 3)
            level_counts[real_levels] += 1
            pieces_total += pieces
            stairs_total += stairs
        print('%-18s pieces avg %5.1f  stairs avg %4.2f  levels: %s' % (
            label, pieces_total / runs, stairs_total / runs,
            ', '.join('%d:%3.0f%%' % (k, 100.0 * v / runs) for k, v in sorted(level_counts.items()))))


if __name__ == '__main__':
    main()
