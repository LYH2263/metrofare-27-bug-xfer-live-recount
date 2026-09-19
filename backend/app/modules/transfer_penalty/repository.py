"""transfer_rules 表:按 (离开线路, 进入线路) 组合的换乘加价规则,可落库。"""
import sqlite3
from datetime import datetime, timezone

DDL = """
CREATE TABLE IF NOT EXISTS transfer_rules(
    id INTEGER PRIMARY KEY,
    from_line TEXT NOT NULL,
    to_line TEXT NOT NULL,
    surcharge REAL NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT
);
"""


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "from_line": r["from_line"],
        "to_line": r["to_line"],
        "surcharge": r["surcharge"],
        "active": bool(r["active"]),
        "created_at": r["created_at"],
    }


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM transfer_rules ORDER BY id"
    ).fetchall()
    return [_row(r) for r in rows]


def list_active(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM transfer_rules WHERE active=1 ORDER BY id"
    ).fetchall()
    return [_row(r) for r in rows]


def get(conn: sqlite3.Connection, rule_id: int) -> dict | None:
    r = conn.execute(
        "SELECT * FROM transfer_rules WHERE id=?", (rule_id,)
    ).fetchone()
    return _row(r) if r else None


def insert(
    conn: sqlite3.Connection,
    from_line: str,
    to_line: str,
    surcharge: float,
    active: bool = True,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO transfer_rules(from_line, to_line, surcharge, active, created_at)"
        " VALUES (?,?,?,?,?)",
        (from_line, to_line, float(surcharge), 1 if active else 0, now),
    )
    return int(cur.lastrowid)


def update(
    conn: sqlite3.Connection,
    rule_id: int,
    from_line: str,
    to_line: str,
    surcharge: float,
    active: bool,
) -> None:
    conn.execute(
        "UPDATE transfer_rules SET from_line=?, to_line=?, surcharge=?, active=? WHERE id=?",
        (from_line, to_line, float(surcharge), 1 if active else 0, rule_id),
    )


def set_active(conn: sqlite3.Connection, rule_id: int, active: bool) -> None:
    conn.execute(
        "UPDATE transfer_rules SET active=? WHERE id=?",
        (1 if active else 0, rule_id),
    )


def active_conflicts(
    conn: sqlite3.Connection,
    from_line: str,
    to_line: str,
    exclude_id: int | None = None,
) -> list[dict]:
    """同一离开/进入组合上已启用的其它规则(用于拒绝两条同时启用)。"""
    q = "SELECT * FROM transfer_rules WHERE from_line=? AND to_line=? AND active=1"
    args: list = [from_line, to_line]
    if exclude_id is not None:
        q += " AND id<>?"
        args.append(exclude_id)
    return [_row(r) for r in conn.execute(q, args).fetchall()]
