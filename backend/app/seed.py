import json

from app.db import connect
from app.engines.route_quote import quote_route
from app.modules.transfer_penalty import repository as transfer_repo

LINE_MAIN = "1号线"
LINE_BRANCH = "支线"

STATIONS = [
    ("A1", "城站", LINE_MAIN),
    ("A2", "市心", LINE_MAIN),
    ("A3", "东湾", LINE_MAIN),
    ("B1", "北苑", LINE_BRANCH),
    ("B2", "机场(种子绕远)", LINE_BRANCH),
]
EDGES = [
    ("A1", "A2", LINE_MAIN),
    ("A2", "A3", LINE_MAIN),
    ("A2", "B1", LINE_BRANCH),
    ("B1", "B2", LINE_BRANCH),
]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]
TRANSFER_RULES = [(LINE_MAIN, LINE_BRANCH, 2.0), (LINE_BRANCH, LINE_MAIN, 2.0)]


def _migrate(conn):
    """老库补 line 列:站点归属线路,邻接边标明所属线路。"""
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(stations)")]
    if "line" not in cols:
        conn.execute("ALTER TABLE stations ADD COLUMN line TEXT")
        conn.execute("UPDATE stations SET line=? WHERE code LIKE 'A%'", (LINE_MAIN,))
        conn.execute("UPDATE stations SET line=? WHERE line IS NULL", (LINE_BRANCH,))
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(edges)")]
    if "line" not in cols:
        conn.execute("ALTER TABLE edges ADD COLUMN line TEXT")
        conn.execute(
            "UPDATE edges SET line=? WHERE a LIKE 'A%' AND b LIKE 'A%'", (LINE_MAIN,)
        )
        conn.execute("UPDATE edges SET line=? WHERE line IS NULL", (LINE_BRANCH,))


def init_db(conn=None):
    own = conn is None
    if own:
        conn = connect()
    conn.executescript(
        """
    CREATE TABLE IF NOT EXISTS stations(id INTEGER PRIMARY KEY, code TEXT, name TEXT, line TEXT);
    CREATE TABLE IF NOT EXISTS edges(a TEXT, b TEXT, line TEXT);
    CREATE TABLE IF NOT EXISTS fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE IF NOT EXISTS calc_runs(
        id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
    """
    )
    transfer_repo.ensure_table(conn)
    _migrate(conn)
    if conn.execute("SELECT COUNT(*) c FROM transfer_rules").fetchone()["c"] == 0:
        for from_line, to_line, surcharge in TRANSFER_RULES:
            transfer_repo.insert(conn, from_line, to_line, surcharge, active=True)
    if conn.execute("SELECT COUNT(*) c FROM stations").fetchone()["c"] == 0:
        for code, name, line in STATIONS:
            conn.execute(
                "INSERT INTO stations(code, name, line) VALUES (?,?,?)", (code, name, line)
            )
        for a, b, line in EDGES:
            conn.execute("INSERT INTO edges(a,b,line) VALUES (?,?,?)", (a, b, line))
        conn.executemany(
            "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
            [(2, 3.0), (4, 4.0), (None, 6.0)],
        )
        conn.execute("INSERT INTO settings(key,value) VALUES ('currency','CNY')")
        q1 = quote_route(EDGES, "A1", "A3", RULES, transfer_repo.list_active(conn))
        conn.execute(
            "INSERT INTO calc_runs(kind,input_json,result_json,created_at) VALUES (?,?,?,datetime('now'))",
            ("quote", json.dumps({"start": "A1", "end": "A3"}), json.dumps(q1, ensure_ascii=False)),
        )
    conn.commit()
    if own:
        conn.close()
