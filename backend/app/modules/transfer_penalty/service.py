"""换乘加价规则的写操作:创建 / 更新 / 停用,含同组合双启用冲突拒绝。"""
import sqlite3

from app.modules.transfer_penalty import repository


class RuleConflictError(Exception):
    """同一离开/进入组合上两条规则都启用时抛出;message 点名两条标识。"""

    def __init__(self, from_line: str, to_line: str, labels: list[str]):
        self.from_line = from_line
        self.to_line = to_line
        self.labels = list(labels)
        names = "、".join(self.labels)
        super().__init__(
            f"换乘规则冲突: 线路组合 {from_line}→{to_line} 上 {names} 不能同时启用"
        )


class RuleNotFoundError(Exception):
    def __init__(self, rule_id: int):
        self.rule_id = rule_id
        super().__init__(f"换乘规则 #{rule_id} 不存在")


def _check_conflict(
    conn: sqlite3.Connection,
    from_line: str,
    to_line: str,
    exclude_id: int | None,
    self_label: str,
) -> None:
    others = repository.active_conflicts(conn, from_line, to_line, exclude_id)
    if others:
        labels = [f"#{o['id']}" for o in others] + [self_label]
        raise RuleConflictError(from_line, to_line, labels)


def create_rule(
    conn: sqlite3.Connection,
    from_line: str,
    to_line: str,
    surcharge: float,
    active: bool = True,
) -> dict:
    if active:
        # 新规则尚未落库,以 “新规则(组合)” 作为标识参与点名
        _check_conflict(
            conn, from_line, to_line,
            exclude_id=None, self_label=f"新规则({from_line}→{to_line})",
        )
    rule_id = repository.insert(conn, from_line, to_line, surcharge, active)
    conn.commit()
    return repository.get(conn, rule_id)


def update_rule(
    conn: sqlite3.Connection,
    rule_id: int,
    *,
    from_line: str | None = None,
    to_line: str | None = None,
    surcharge: float | None = None,
    active: bool | None = None,
) -> dict:
    cur = repository.get(conn, rule_id)
    if cur is None:
        raise RuleNotFoundError(rule_id)
    new_from = from_line if from_line is not None else cur["from_line"]
    new_to = to_line if to_line is not None else cur["to_line"]
    new_sur = surcharge if surcharge is not None else cur["surcharge"]
    new_active = active if active is not None else cur["active"]
    if new_active:
        _check_conflict(
            conn, new_from, new_to, exclude_id=rule_id, self_label=f"#{rule_id}"
        )
    repository.update(conn, rule_id, new_from, new_to, new_sur, new_active)
    conn.commit()
    return repository.get(conn, rule_id)


def deactivate_rule(conn: sqlite3.Connection, rule_id: int) -> dict:
    cur = repository.get(conn, rule_id)
    if cur is None:
        raise RuleNotFoundError(rule_id)
    repository.set_active(conn, rule_id, False)
    conn.commit()
    return repository.get(conn, rule_id)
