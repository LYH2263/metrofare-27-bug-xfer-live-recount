"""换乘加价模块:线路对规则落库 + 途经序列换乘计数。

- 站点归属线路,邻接边标明所属线路(见 seed/migration)。
- 规则按 (离开线路, 进入线路) 计价,支持列表/创建/更新/停用;
  同一组合上两条规则都启用时拒绝并点名两条标识。
- 询价先求途经站序列,再数相邻两边线路不同的次数,同线连续站不计换乘。
"""
from app.modules.transfer_penalty import engine, repository, service

__all__ = ["engine", "repository", "service"]
