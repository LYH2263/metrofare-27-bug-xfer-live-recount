"""transfer_penalty 模块测试:途经序列、换乘计数、加价、冲突拒绝、记录快照。

纯 assert 写法,pytest 与裸 python 均可运行。
"""
import json
import sqlite3

from app import seed
from app.engines.graph_bfs import shortest_path
from app.engines.route_quote import quote_route
from app.modules.transfer_penalty.engine import apply_transfer_rules, transfer_points
from app.modules.transfer_penalty.service import (
    RuleConflictError,
    RuleNotFoundError,
    create_rule,
    deactivate_rule,
    update_rule,
)
from app.services.metro_service import MetroService

L1, L2 = "1号线", "支线"
EDGES = [("A1", "A2", L1), ("A2", "A3", L1), ("A2", "B1", L2), ("B1", "B2", L2)]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]
TP = [{"id": 1, "from_line": L1, "to_line": L2, "surcharge": 2.0, "active": True}]


def _mem_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    seed.init_db(conn)
    return conn


def test_shortest_path_returns_station_sequence():
    path, lines = shortest_path(EDGES, "A1", "B2")
    assert path == ["A1", "A2", "B1", "B2"]
    assert lines == [L1, L2, L2]


def test_same_line_run_is_not_a_transfer():
    path, lines = shortest_path(EDGES, "A1", "A3")
    assert path == ["A1", "A2", "A3"]
    assert transfer_points(path, lines) == []


def test_transfer_points_count_line_changes():
    path, lines = shortest_path(EDGES, "A1", "B2")
    pts = transfer_points(path, lines)
    assert len(pts) == 1
    assert pts[0] == {"at": "A2", "from_line": L1, "to_line": L2}


def test_apply_transfer_rules_sums_surcharge():
    pts = [{"at": "A2", "from_line": L1, "to_line": L2}]
    detailed, total = apply_transfer_rules(pts, TP)
    assert total == 2.0 and detailed[0]["surcharge"] == 2.0 and detailed[0]["rule_id"] == 1
    # 无规则组合加价 0
    _, total2 = apply_transfer_rules([{"at": "X", "from_line": L2, "to_line": "L9"}], TP)
    assert total2 == 0.0


def test_quote_route_breakdown():
    q = quote_route(EDGES, "A1", "B2", RULES, TP)
    assert q["path"] == ["A1", "A2", "B1", "B2"]
    assert q["base_fare"] == 4.0
    assert q["transfer_count"] == 1
    assert q["surcharge_total"] == 2.0
    assert q["fare"] == 6.0


def test_quote_route_without_lines_or_rules_is_backward_compatible():
    q = quote_route([("A1", "A2"), ("A2", "A3")], "A1", "A3", RULES)
    assert q["fare"] == 3.0 and q["transfer_count"] == 0 and q["surcharge_total"] == 0.0


def test_conflict_on_create_names_existing_rule():
    conn = _mem_db()
    try:
        create_rule(conn, L1, L2, 5.0, active=True)
        raise AssertionError("应拒绝同组合第二条启用规则")
    except RuleConflictError as e:
        assert "#1" in str(e) and L1 in str(e) and L2 in str(e)
    finally:
        conn.close()


def test_conflict_on_activate_names_both_ids():
    conn = _mem_db()
    try:
        dup = create_rule(conn, L1, L2, 5.0, active=False)  # 停用状态允许同组合
        try:
            update_rule(conn, dup["id"], active=True)
            raise AssertionError("应拒绝启用第二条")
        except RuleConflictError as e:
            assert "#1" in str(e) and f"#{dup['id']}" in str(e)
    finally:
        conn.close()


def test_update_and_deactivate():
    conn = _mem_db()
    try:
        r = update_rule(conn, 1, surcharge=3.5)
        assert r["surcharge"] == 3.5 and r["active"] is True
        r = deactivate_rule(conn, 1)
        assert r["active"] is False
        try:
            deactivate_rule(conn, 999)
            raise AssertionError("应 404")
        except RuleNotFoundError:
            pass
    finally:
        conn.close()


def test_readonly_quote_writes_no_record_and_snapshot_is_immutable():
    conn = _mem_db()
    try:
        with MetroService(conn) as s:
            n0 = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
            q = s.quote("A1", "B2", persist=False)
            assert q["run_id"] is None and q["surcharge_total"] == 2.0
            n1 = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
            assert n1 == n0  # 只读试算不写记录

            qp = s.quote("A1", "B2", persist=True)
            assert qp["run_id"] is not None

            s.deactivate_transfer_rule(1)
            q2 = s.quote("A1", "B2", persist=False)
            assert q2["surcharge_total"] == 0.0 and q2["fare"] == 4.0  # 停用后加价消失

            row = conn.execute(
                "SELECT result_json FROM calc_runs WHERE id=?", (qp["run_id"],)
            ).fetchone()
            snap = json.loads(row["result_json"])
            # 已写入记录仍带当时途经站与当时加价
            assert snap["path"] == ["A1", "A2", "B1", "B2"]
            assert snap["surcharge_total"] == 2.0 and snap["fare"] == 6.0

            # 记录页按编号取回的仍是写入当时那一版,不被停用/改规则改写
            viewed = json.loads(s.history_item(qp["run_id"])["result_json"])
            assert viewed["path"] == ["A1", "A2", "B1", "B2"]
            assert viewed["transfer_count"] == 1
            assert viewed["surcharge_total"] == 2.0 and viewed["fare"] == 6.0

            # 连续两次只读试算之间记录条数不增加
            n_before = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
            s.quote("A1", "B2", persist=False)
            s.quote("A1", "B2", persist=False)
            n_after = conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
            assert n_after == n_before
    finally:
        conn.close()
