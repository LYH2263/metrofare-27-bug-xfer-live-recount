from app.db import connect
from app.engines.route_quote import quote_route
from app.modules.transfer_penalty import repository as transfer_repo
from app.modules.transfer_penalty import service as transfer_ops
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class MetroService:
    def __init__(self, conn=None):
        self._conn = conn if conn is not None else connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [
            {"a": a, "b": b, "line": line}
            for a, b, line in edges_repo.list_triples(self._conn)
        ]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def transfer_rules(self):
        return transfer_repo.list_all(self._conn)

    def create_transfer_rule(self, from_line, to_line, surcharge, active=True):
        return transfer_ops.create_rule(
            self._conn, from_line, to_line, surcharge, active
        )

    def update_transfer_rule(self, rule_id, **fields):
        return transfer_ops.update_rule(self._conn, rule_id, **fields)

    def deactivate_transfer_rule(self, rule_id):
        return transfer_ops.deactivate_rule(self._conn, rule_id)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_triples(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        transfer_rules = transfer_repo.list_active(self._conn)
        result = quote_route(edges, start, end, rules, transfer_rules)
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def history_item(self, run_id: int):
        # 记录是写入当时的快照:途经、换乘次数、加价、应付一律按落库原样返回,
        # 不随规则停用/改价重算。
        return runs_repo.get_by_id(self._conn, run_id)

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
