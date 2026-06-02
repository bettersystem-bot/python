"""节点处理器（handlers）—— worker 真正"干活"的地方。

每种 NodeType 对应一个 async handler。handler 接收 TaskMessage，
返回该节点的 output（会成为下游节点的输入）。

这里用模拟负载演示三类典型异步场景：
- CPU 型：计算密集。真实场景应丢到进程池（asyncio.to_thread / ProcessPool）避免阻塞事件循环；
  这里用 asyncio.to_thread 把"阻塞计算"挪到线程，演示"不要在协程里跑 CPU 死循环"的正确姿势。
- IO 型：用 asyncio.sleep 模拟网络/磁盘等待，这是 asyncio 最擅长的场景。
- GPU 型：模拟较长的推理耗时。

params 约定（方便前端构造演示用例）：
- work_ms: 模拟耗时（毫秒）。
- fail_until_attempt: 若设置为 N，则前 N 次尝试故意失败，用于演示重试。
- fail: True 则总是失败，用于演示失败策略。
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from app.models import NodeType, TaskMessage


def _cpu_bound(n: int) -> int:
    """一段真正占用 CPU 的同步计算（故意写成阻塞的）。"""
    total = 0
    for i in range(n):
        total += (i * i) % 7
    return total


async def handle_cpu(task: TaskMessage) -> Any:
    work_ms = int(task.params.get("work_ms", 200))
    # 关键：CPU 密集计算放到线程里跑，避免阻塞 worker 的事件循环。
    iterations = max(1, work_ms * 5000)
    result = await asyncio.to_thread(_cpu_bound, iterations)
    return {"kind": "cpu", "checksum": result, "iterations": iterations}


async def handle_io(task: TaskMessage) -> Any:
    work_ms = int(task.params.get("work_ms", 300))
    # IO 等待用 sleep 模拟，事件循环此时可去处理其它协程。
    await asyncio.sleep(work_ms / 1000)
    return {"kind": "io", "bytes": work_ms * 1024, "upstream": list(task.upstream_outputs.keys())}


async def handle_gpu(task: TaskMessage) -> Any:
    work_ms = int(task.params.get("work_ms", 800))
    await asyncio.sleep(work_ms / 1000)
    return {"kind": "gpu", "tokens": work_ms, "model": task.params.get("model", "demo-llm")}


_HANDLERS = {
    NodeType.CPU: handle_cpu,
    NodeType.IO: handle_io,
    NodeType.GPU: handle_gpu,
}


class NodeExecutionError(RuntimeError):
    pass


async def execute(task: TaskMessage) -> tuple[Any, float]:
    """执行一个任务，返回 (output, duration_ms)。失败抛 NodeExecutionError。"""
    # 演示失败/重试：
    if task.params.get("fail") is True:
        raise NodeExecutionError(f"node {task.node_id} 被配置为总是失败")
    fail_until = int(task.params.get("fail_until_attempt", 0))
    if fail_until and task.attempt <= fail_until:
        raise NodeExecutionError(
            f"node {task.node_id} 第 {task.attempt} 次尝试故意失败（fail_until_attempt={fail_until}）")

    handler = _HANDLERS.get(task.node_type)
    if handler is None:
        raise NodeExecutionError(f"未知节点类型: {task.node_type}")

    start = time.perf_counter()
    output = await handler(task)
    duration_ms = (time.perf_counter() - start) * 1000
    return output, duration_ms
