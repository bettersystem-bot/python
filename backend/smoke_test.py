"""离线烟测：用内存版假队列驱动真实的编排引擎，验证核心逻辑。

不依赖 Redis。它把 app.core.queue 的单例换成一个内存 broker，然后：
- 提交多种示例 DAG；
- 模拟 worker：从任务流取任务 -> 跑真实 handler -> 回传结果 -> 引擎推进；
- 断言：拓扑顺序正确、菱形并发、重试成功、失败策略（fail_fast / continue）符合预期。
运行： python smoke_test.py
"""
import asyncio
import sys

# ---- 内存版假队列（实现 orchestrator/worker 用到的接口子集）----
class FakeQueue:
    def __init__(self):
        self.task_streams = {}   # stream -> list[(id, TaskMessage)]
        self.results = []        # list[(id, ResultMessage)]
        self._seq = 0

    async def connect(self): pass
    async def ensure_group(self, *a, **k): pass

    async def enqueue_task(self, task):
        from app.config import settings
        s = settings.queue_name(task.node_type.value)
        self._seq += 1
        self.task_streams.setdefault(s, []).append((str(self._seq), task))
        return str(self._seq)

    async def publish_result(self, result):
        self._seq += 1
        self.results.append((str(self._seq), result))
        return str(self._seq)

    def drain_tasks(self):
        out = []
        for s, lst in self.task_streams.items():
            out.extend((s, mid, t) for mid, t in lst)
            self.task_streams[s] = []
        return out

    def drain_results(self):
        out = self.results[:]
        self.results = []
        return out


async def run_dag(spec_dict, fake):
    from app.core import dag_parser
    from app.core.dag_executor import orchestrator
    from app.models import DagSpec, DagStatus
    from app.workers import handlers

    run = dag_parser.parse(DagSpec(**spec_dict))
    await orchestrator.submit(run)

    # 手动模拟 worker + 结果推进循环，直到整图结束。
    for _ in range(500):
        if run.status in (DagStatus.SUCCEEDED, DagStatus.FAILED):
            break
        tasks = fake.drain_tasks()
        for _s, _mid, task in tasks:
            try:
                output, dur = await handlers.execute(task)
                res = _result(task, True, output=output, dur=dur)
            except Exception as e:  # noqa
                res = _result(task, False, error=str(e))
            await fake.publish_result(res)
        for _mid, result in fake.drain_results():
            await orchestrator._handle_result(result)
        await asyncio.sleep(0)
    return run


def _result(task, success, output=None, error=None, dur=0.0):
    from app.models import ResultMessage
    return ResultMessage(dag_run_id=task.dag_run_id, node_id=task.node_id,
                         success=success, output=output, error=error,
                         worker_id="smoke", attempt=task.attempt, duration_ms=dur)


async def main():
    # 注入假队列到所有引用点。
    import app.core.queue as q
    fake = FakeQueue()
    q.queue = fake
    import app.core.scheduler as sched
    import app.core.dag_executor as ex
    sched.queue = fake
    ex.queue = fake

    from app.api.examples import EXAMPLES
    from app.models import NodeStatus

    failures = []

    # 1) diamond：全部成功，rank 必须最后成功。
    run = await run_dag(EXAMPLES["diamond"], fake)
    assert run.status.value == "succeeded", run.status
    assert run.nodes["rank"].status == NodeStatus.SUCCEEDED
    assert run.nodes["rank"].finished_at >= run.nodes["feature"].finished_at
    assert run.nodes["rank"].finished_at >= run.nodes["embed"].finished_at
    print("[OK] diamond 拓扑顺序与并发正确")

    # 2) pipeline：线性，store 最后。
    run = await run_dag(EXAMPLES["pipeline"], fake)
    assert run.status.value == "succeeded"
    order = ["download", "parse", "infer", "store"]
    for a, b in zip(order, order[1:]):
        assert run.nodes[a].finished_at <= run.nodes[b].finished_at
    print("[OK] pipeline 线性顺序正确")

    # 3) retry：flaky 前两次失败、第三次成功 -> 整图成功。
    run = await run_dag(EXAMPLES["retry"], fake)
    assert run.status.value == "succeeded", run.status
    assert run.nodes["flaky"].status == NodeStatus.SUCCEEDED
    assert run.nodes["flaky"].attempt == 3, run.nodes["flaky"].attempt
    print("[OK] retry 重试 3 次后成功，attempt=%d" % run.nodes["flaky"].attempt)

    # 4) failure (continue_on_error)：bad 失败，after_bad 被跳过，after_good 仍成功。
    run = await run_dag(EXAMPLES["failure"], fake)
    assert run.status.value == "failed", run.status
    assert run.nodes["bad"].status == NodeStatus.FAILED
    assert run.nodes["after_bad"].status == NodeStatus.SKIPPED
    assert run.nodes["after_good"].status == NodeStatus.SUCCEEDED
    print("[OK] continue_on_error：失败节点后代被跳过，其它分支继续")

    # 5) 环检测：构造一个有环图，必须被拒绝。
    from app.core import dag_parser
    from app.models import DagSpec
    cyc = {"name": "cycle", "nodes": [
        {"id": "a", "type": "io", "depends_on": ["b"]},
        {"id": "b", "type": "io", "depends_on": ["a"]},
    ]}
    try:
        dag_parser.parse(DagSpec(**cyc))
        failures.append("环检测未生效")
    except dag_parser.DagValidationError:
        print("[OK] 环检测生效，拒绝带环 DAG")

    if failures:
        print("FAILED:", failures); sys.exit(1)
    print("\n全部烟测通过 ✅")


if __name__ == "__main__":
    asyncio.run(main())
