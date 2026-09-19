import heapq
from collections import defaultdict, deque
from itertools import count


def shortest_hops(edges: list[tuple[str, str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count; None if unreachable."""
    if start == end:
        return 0
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        g[a].add(b)
        g[b].add(a)
    if start not in g or end not in g:
        return None
    q = deque([(start, 0)])
    seen = {start}
    while q:
        cur, d = q.popleft()
        for nxt in g[cur]:
            if nxt in seen:
                continue
            if nxt == end:
                return d + 1
            seen.add(nxt)
            q.append((nxt, d + 1))
    return None


def shortest_path(
    edges: list[tuple[str, str, str | None]], start: str, end: str
) -> tuple[list[str] | None, list[str | None] | None]:
    """途经站序列 + 每段边所属线路。

    edges 为 (a, b, line) 三元组,无向。代价按 (站数, 换线次数) 字典序最小化:
    先求最短站数,并列时优先少换线。不可达返回 (None, None)。
    """
    if start == end:
        return [start], []
    g: dict[str, list[tuple[str, str | None]]] = defaultdict(list)
    for a, b, line in edges:
        g[a].append((b, line))
        g[b].append((a, line))
    if start not in g or end not in g:
        return None, None
    inf = (float("inf"), float("inf"))
    seq = count()
    start_state = (start, None)  # (站点, 到达该站所用边的线路)
    dist = {start_state: (0, 0)}
    prev: dict[tuple, tuple | None] = {start_state: None}
    pq: list[tuple] = [((0, 0), next(seq), start_state)]
    best_end = None
    while pq:
        cost, _, state = heapq.heappop(pq)
        if cost != dist.get(state, inf):
            continue
        station, inc_line = state
        if station == end:
            best_end = state
            break
        hops, transfers = cost
        for nxt, line2 in g[station]:
            step = 0 if inc_line is None or line2 == inc_line else 1
            ncost = (hops + 1, transfers + step)
            nstate = (nxt, line2)
            if ncost < dist.get(nstate, inf):
                dist[nstate] = ncost
                prev[nstate] = state
                heapq.heappush(pq, (ncost, next(seq), nstate))
    if best_end is None:
        return None, None
    path: list[str] = []
    lines: list[str | None] = []
    s = best_end
    while s is not None:
        path.append(s[0])
        if prev[s] is not None:
            lines.append(s[1])
        s = prev[s]
    path.reverse()
    lines.reverse()
    return path, lines
