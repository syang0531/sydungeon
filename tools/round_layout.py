# -*- coding: utf-8 -*-
"""Where every one of the round tower's cells goes, and what may stand in it.

Kept apart from generate_round.py because this is the argument, not the bricks.

THE IDEA
A maze that grows from door to door can never promise that a cell gets built: a cell exists
only because some neighbour pointed at it, and corners go unclaimed. So the tower does not
grow one. `core` carries a jigsaw for **every** cell and places all seventy-two itself. What
is random is which piece lands in each, not whether one does.

That would leave connection to chance, so each floor has a route: a path of cells from the
one you arrive in to the one the next stair stands in. A cell on the route is drawn from a
pool that is guaranteed to have a door the way the route goes, so the climb cannot break. A
cell off the route is drawn from `leaf`, which is where the sealed room - no doors at all,
a chest inside, found only by noticing the floor is a cell short and digging - comes from.

Vanilla turns a piece to face the jigsaw that placed it, so a piece needs no rotations of its
own: one `corner` is every corner. That also means the side `core` places a cell from decides
which way the piece faces, which is how the route is steered.

THE STAIR
It opens west at the bottom and west at the top, so you come out one floor above the cell you
went in from. That makes the chain: the route on a floor ends at the cell beside the stair,
and the next floor starts in that same cell.
"""

DIRS = ('north', 'east', 'south', 'west')
STEP = {'north': (0, -1), 'east': (1, 0), 'south': (0, 1), 'west': (-1, 0)}
OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
GRID = 3
FLOORS = 8


def step(cell, side):
    dx, dz = STEP[side]
    return (cell[0] + dx, cell[1] + dz)


def inside(cell):
    return 0 <= cell[0] < GRID and 0 <= cell[1] < GRID


def side_between(here, there):
    for side in DIRS:
        if step(here, side) == there:
            return side
    return None


def relative(anchor, side):
    """Where `side` lies for a piece whose way in faces `anchor`: back, through, left, right.

    The pieces are all written with their way in on the west face, so `west` is back, `east`
    through, `north` left and `south` right - and a piece placed from another side is the
    same piece turned."""
    turn = (DIRS.index(side) - DIRS.index(anchor)) % 4
    return ('back', 'left', 'through', 'right')[turn]


# what each pool promises, beyond the way in
POOLS = {
    'link_through': {'through'},
    'link_left': {'left'},
    'link_right': {'right'},
    'link_cross': {'through', 'left', 'right'},
    'leaf': set(),
}


def pool_for(anchor, needed):
    """The cheapest pool that has a door every way this cell must open."""
    want = {relative(anchor, side) for side in needed} - {'back'}
    for name in ('leaf', 'link_through', 'link_left', 'link_right', 'link_cross'):
        if want <= POOLS[name]:
            return name
    return 'link_cross'


# How much of a floor the guaranteed route should cover. The rest are side cells, and they
# are the point: a corridor cannot be a room, so every reward room and every sealed room hangs
# off the route rather than lying on it. Route every cell and the tower is all corridor.
ROUTE_SHARE = 0.6


def pick_path(free, start, goal, target):
    """A walk from start to goal as near `target` cells long as there is, and one that leaves
    no side cell stranded: anything off it must touch it, or nothing could open into it."""
    best = None
    seen_paths = []

    def walk(at, seen):
        if at == goal:
            seen_paths.append(list(seen))
        for side in DIRS:
            nxt = step(at, side)
            if nxt in free and nxt not in seen:
                seen.append(nxt)
                walk(nxt, seen)
                seen.pop()

    walk(start, [start])
    reachable = []
    for path in seen_paths:
        on = set(path)
        if any(not any(step(c, s) in on for s in DIRS) for c in free - on):
            continue                           # a side cell with nothing to open off
        reachable.append(path)
    if not reachable:                          # no short route leaves the floor whole
        reachable = [p for p in seen_paths if set(p) == free]
    for path in reachable:
        if best is None or abs(len(path) - target) < abs(len(best) - target):
            best = path
    return best


def longest_path(free, start, goal):
    """The longest walk over `free` from `start` to `goal`, visiting no cell twice.

    Nine cells, so this can be exhaustive and simply take the best."""
    best = []

    def walk(at, seen):
        nonlocal best
        if at == goal and len(seen) > len(best):
            best = list(seen)
        for side in DIRS:
            nxt = step(at, side)
            if nxt in free and nxt not in seen:
                seen.append(nxt)
                walk(nxt, seen)
                seen.pop()

    walk(start, [start])
    return best


def plan_floors(big):
    """Choose, for every floor, where the stair stands and which cell you arrive in.

    `big` maps a floor to the north-west cell of the two-by-two room on it. What carries from
    one floor to the next is only (the cell you arrive in, the stair below), so the whole
    thing is a short dynamic program over those states - eight floors by nine by nine - and
    the plan that puts the most cells on a route wins outright rather than by luck of search
    order. A cell left off a route is not a hole; it is where `leaf` and its sealed room go.
    """
    def room_cells(floor):
        if floor not in big:
            return set()
        bx, bz = big[floor]
        return {(bx + dx, bz + dz) for dx in (0, 1) for dz in (0, 1)}

    def taken(floor, stair_below, stair_here):
        out = room_cells(floor)
        for cell in (stair_below, stair_here):
            if cell:
                out.add(cell)
        return out

    def clashes(floor, stair_below, stair_here):
        """A stair and a two-by-two room cannot share a cell: both are solid pieces."""
        room = room_cells(floor)
        return bool(room & {c for c in (stair_below, stair_here) if c})

    memo = {}

    def best(floor, arrive, stair_below):
        if floor > FLOORS:
            return 0, {}
        key = (floor, arrive, stair_below)
        if key in memo:
            return memo[key]
        memo[key] = (float('-inf'), None)      # nothing reaches the top this way, until it does
        found = (float('-inf'), None)
        stairs = [None] if floor == FLOORS else [c for c in cells()
                                                 if c != arrive and c != stair_below]
        for stair in stairs:
            if clashes(floor, stair_below, stair):
                continue
            block = taken(floor, stair_below, stair)
            if arrive in block:
                continue
            free = {c for c in cells() if c not in block}
            goals = list(free) if stair is None else [step(stair, side) for side in DIRS
                                                     if step(stair, side) in free]
            for goal in goals:
                if stair is not None and (goal in taken(floor + 1, stair, None)
                                          or clashes(floor + 1, stair, None)):
                    continue
                target = max(2, int(round(len(free) * ROUTE_SHARE)))
                path = pick_path(free, arrive, goal, target)
                if not path:
                    continue
                deeper, rest = (0, {}) if stair is None else best(floor + 1, goal, stair)
                if rest is None:
                    continue
                value = -abs(len(path) - target) + deeper
                if value > found[0]:
                    plan = dict(rest)
                    plan[floor] = {'arrive': arrive, 'stair': stair,
                                   'route': path, 'free': free}
                    found = (value, plan)
        memo[key] = found
        return found

    value, plan = best(1, (0, 1), None)
    return plan


def best_plan(big_floors):
    """Try every place the big rooms could sit and keep the plan that routes the most cells."""
    from itertools import product
    corners = [(0, 0), (1, 0), (0, 1), (1, 1)]
    winner, score, where = None, -1, None
    for spots in product(corners, repeat=len(big_floors)):
        big = dict(zip(big_floors, spots))
        plan = plan_floors(big)
        if not plan:
            continue
        routed = sum(len(p['route']) for p in plan.values())
        if routed > score:
            winner, score, where = plan, routed, big
    return winner, where, score


def cells():
    return [(x, z) for z in range(GRID) for x in range(GRID)]


def describe(plan):
    lines = []
    for floor in sorted(plan):
        info = plan[floor]
        off = sorted(set(info['free']) - set(info['route']))
        lines.append('%d층  도착 %s  계단 %s  경로 %d칸  나머지 %s'
                     % (floor, info['arrive'], info['stair'], len(info['route']),
                        off if off else '없음'))
    return '\n'.join(lines)
