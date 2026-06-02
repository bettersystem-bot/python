"""DAG 解析器（对应架构图的 dag parser）。

职责：把用户提交的 DagSpec 校验成一个合法、可执行的 DAG，并构建运行态 DagRun。

校验内容（异步编排前必须做的"静态检查"）：
1. 节点 id 唯一。
2. depends_on 引用的节点必须存在。
3. 不允许自依赖。
4. 整张图必须无环（DAG = 有向无环图）—— 用 Kahn 拓扑排序检测环。

为什么环检测如此重要？
若存在环（A 依赖 B、B 依赖 A），编排引擎会永远等不到依赖满足，导致死锁。
所以"提交即拒绝有环图"是编排系统的第一道防线。
"""
from __future__ import annotations

from collections import deque

from app.models import DagRun, DagSpec, NodeRun, NodeStatus


class DagValidationError(ValueError):
    """DAG 非法时抛出，API 层会转成 400。"""


def _check_references(spec: DagSpec) -> dict[str, set[str]]:
    """校验 id 唯一性与依赖引用合法性，返回 邻接表（node -> 它的上游集合）。"""
    ids: set[str] = set()
    for n in spec.nodes:
        if n.id in ids:
            raise DagValidationError(f"重复的节点 id: {n.id}")
        ids.add(n.id)

    deps: dict[str, set[str]] = {}
    for n in spec.nodes:
        dep_set = set(n.depends_on)
        if n.id in dep_set:
            raise DagValidationError(f"节点 {n.id} 不能依赖自己")
        for d in dep_set:
            if d not in ids:
                raise DagValidationError(f"节点 {n.id} 依赖了不存在的节点: {d}")
        deps[n.id] = dep_set
    return deps


def _detect_cycle(deps: dict[str, set[str]]) -> None:
    """Kahn 算法做拓扑排序；若排不出全部节点，说明存在环。

    in_degree[x] = x 依赖的上游数量。
    每次取出入度为 0 的节点（无未完成上游），并把"以它为上游"的节点入度 -1。
    若最终处理的节点数 < 总数，剩下的就在环里。
    """
    # children[u] = 依赖 u 的下游节点们（反向边）。
    children: dict[str, list[str]] = {x: [] for x in deps}
    in_degree: dict[str, int] = {x: len(parents) for x, parents in deps.items()}
    for node, parents in deps.items():
        for p in parents:
            children[p].append(node)

    queue: deque[str] = deque([x for x, d in in_degree.items() if d == 0])
    processed = 0
    while queue:
        u = queue.popleft()
        processed += 1
        for c in children[u]:
            in_degree[c] -= 1
            if in_degree[c] == 0:
                queue.append(c)

    if processed != len(deps):
        in_cycle = [x for x, d in in_degree.items() if d > 0]
        raise DagValidationError(f"DAG 中存在环，涉及节点: {sorted(in_cycle)}")


def parse(spec: DagSpec) -> DagRun:
    """校验并构建运行态 DagRun。校验失败抛 DagValidationError。"""
    deps = _check_references(spec)
    _detect_cycle(deps)

    nodes: dict[str, NodeRun] = {}
    for n in spec.nodes:
        nodes[n.id] = NodeRun(
            id=n.id,
            name=n.name or n.id,
            type=n.type,
            depends_on=list(n.depends_on),
            params=dict(n.params),
            status=NodeStatus.PENDING,
        )
    return DagRun(name=spec.name, failure_policy=spec.failure_policy, nodes=nodes)
