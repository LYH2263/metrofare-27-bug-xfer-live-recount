"""换乘加价:按途经站序列里相邻两边所属线路的变化计换乘。"""


def transfer_points(path: list[str], edge_lines: list[str | None]) -> list[dict]:
    """数序列里相邻两边所属线路不同的次数;同线连续站不计换乘。

    第 i 次换乘发生在 path[i+1] 站(两条线路不同的相邻边之间的站)。
    """
    points: list[dict] = []
    for i in range(len(edge_lines) - 1):
        leave, enter = edge_lines[i], edge_lines[i + 1]
        if leave is None or enter is None or leave == enter:
            continue
        points.append({"at": path[i + 1], "from_line": leave, "to_line": enter})
    return points


def apply_transfer_rules(
    transfers: list[dict], rules: list[dict]
) -> tuple[list[dict], float]:
    """按启用中的 (离开线路, 进入线路) 规则给每次换乘计价,返回 (明细, 加价合计)。"""
    total = 0.0
    detailed: list[dict] = []
    for t in transfers:
        hit = next(
            (
                r
                for r in rules
                if r["from_line"] == t["from_line"] and r["to_line"] == t["to_line"]
            ),
            None,
        )
        surcharge = round(float(hit["surcharge"]), 2) if hit else 0.0
        total = round(total + surcharge, 2)
        detailed.append({**t, "surcharge": surcharge, "rule_id": hit["id"] if hit else None})
    return detailed, total
