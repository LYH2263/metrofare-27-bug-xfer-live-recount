from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path
from app.modules.transfer_penalty.engine import apply_transfer_rules, transfer_points


def _normalize(edges: list[tuple]) -> list[tuple[str, str, str | None]]:
    """兼容 (a, b) 二元组(无线路信息)与 (a, b, line) 三元组。"""
    out = []
    for e in edges:
        a, b = e[0], e[1]
        line = e[2] if len(e) > 2 else None
        out.append((a, b, line))
    return out


def quote_route(
    edges: list[tuple],
    start: str,
    end: str,
    rules: list[dict],
    transfer_rules: list[dict] | None = None,
) -> dict:
    """先求途经站序列,再数序列里相邻两边线路不同的次数计换乘加价。

    返回:基础票价 base_fare、换乘次数 transfer_count、加价合计
    surcharge_total、应付票价 fare、途经站 path 及每次换线明细 transfers。
    """
    path, edge_lines = shortest_path(_normalize(edges), start, end)
    if path is None:
        return {
            "start": start,
            "end": end,
            "hops": None,
            "fare": None,
            "reachable": False,
            "path": None,
            "edge_lines": None,
            "base_fare": None,
            "transfer_count": 0,
            "transfers": [],
            "surcharge_total": 0.0,
        }
    hops = len(path) - 1
    base_fare = fare_for_hops(hops, rules)
    transfers = transfer_points(path, edge_lines)
    transfers, surcharge_total = apply_transfer_rules(transfers, transfer_rules or [])
    fare = round(base_fare + surcharge_total, 2)
    return {
        "start": start,
        "end": end,
        "hops": hops,
        "fare": fare,
        "reachable": True,
        "path": path,
        "edge_lines": edge_lines,
        "base_fare": base_fare,
        "transfer_count": len(transfers),
        "transfers": transfers,
        "surcharge_total": surcharge_total,
    }
