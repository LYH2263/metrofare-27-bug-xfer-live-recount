import sqlite3


def list_pairs(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    return [(r["a"], r["b"]) for r in conn.execute("SELECT a,b FROM edges").fetchall()]


def list_triples(conn: sqlite3.Connection) -> list[tuple[str, str, str | None]]:
    """(a, b, line):邻接边及其所属线路。"""
    rows = conn.execute("SELECT a,b,line FROM edges").fetchall()
    return [(r["a"], r["b"], r["line"]) for r in rows]
