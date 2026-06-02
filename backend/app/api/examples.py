"""示例 DAG，供前端一键提交、快速看到编排效果。

每个示例都演示一类编排模式：
- diamond:   菱形依赖（A -> B,C -> D），演示 fan-out / fan-in 与并发。
- pipeline:  线性流水线，演示数据在节点间流动。
- retry:     含一个前两次失败、第三次成功的节点，演示重试。
- failure:   含一个必然失败的节点，演示失败策略（fail_fast / continue）。
- wide:      宽并发（一个根，扇出 N 个并行 GPU 节点），演示并发上限/背压。
"""
from __future__ import annotations

from typing import Any

EXAMPLES: dict[str, dict[str, Any]] = {
    "diamond": {
        "name": "菱形依赖（fan-out/fan-in）",
        "failure_policy": "fail_fast",
        "nodes": [
            {"id": "ingest", "name": "数据接入", "type": "io", "depends_on": [], "params": {"work_ms": 300}},
            {"id": "feature", "name": "特征计算", "type": "cpu", "depends_on": ["ingest"], "params": {"work_ms": 400}},
            {"id": "embed", "name": "向量化", "type": "gpu", "depends_on": ["ingest"], "params": {"work_ms": 600}},
            {"id": "rank", "name": "排序合并", "type": "cpu", "depends_on": ["feature", "embed"], "params": {"work_ms": 300}},
        ],
    },
    "pipeline": {
        "name": "线性流水线",
        "failure_policy": "fail_fast",
        "nodes": [
            {"id": "download", "name": "下载", "type": "io", "depends_on": [], "params": {"work_ms": 300}},
            {"id": "parse", "name": "解析", "type": "cpu", "depends_on": ["download"], "params": {"work_ms": 300}},
            {"id": "infer", "name": "推理", "type": "gpu", "depends_on": ["parse"], "params": {"work_ms": 700}},
            {"id": "store", "name": "落库", "type": "io", "depends_on": ["infer"], "params": {"work_ms": 200}},
        ],
    },
    "retry": {
        "name": "重试演示（节点前2次失败）",
        "failure_policy": "fail_fast",
        "nodes": [
            {"id": "prepare", "name": "准备", "type": "io", "depends_on": [], "params": {"work_ms": 200}},
            {"id": "flaky", "name": "不稳定任务", "type": "cpu", "depends_on": ["prepare"],
             "params": {"work_ms": 200, "fail_until_attempt": 2}},
            {"id": "finish", "name": "完成", "type": "io", "depends_on": ["flaky"], "params": {"work_ms": 200}},
        ],
    },
    "failure": {
        "name": "失败策略演示（含必败节点）",
        "failure_policy": "continue_on_error",
        "nodes": [
            {"id": "root", "name": "根", "type": "io", "depends_on": [], "params": {"work_ms": 200}},
            {"id": "good", "name": "正常分支", "type": "cpu", "depends_on": ["root"], "params": {"work_ms": 300}},
            {"id": "bad", "name": "必败分支", "type": "cpu", "depends_on": ["root"], "params": {"fail": True}},
            {"id": "after_bad", "name": "依赖必败者（将被跳过）", "type": "io", "depends_on": ["bad"], "params": {"work_ms": 200}},
            {"id": "after_good", "name": "依赖正常者（继续执行）", "type": "io", "depends_on": ["good"], "params": {"work_ms": 200}},
        ],
    },
    "wide": {
        "name": "宽并发（背压演示）",
        "failure_policy": "fail_fast",
        "nodes": (
            [{"id": "seed", "name": "种子", "type": "io", "depends_on": [], "params": {"work_ms": 200}}]
            + [{"id": f"infer_{i}", "name": f"并行推理{i}", "type": "gpu", "depends_on": ["seed"],
                "params": {"work_ms": 500}} for i in range(12)]
            + [{"id": "merge", "name": "汇总", "type": "cpu",
                "depends_on": [f"infer_{i}" for i in range(12)], "params": {"work_ms": 300}}]
        ),
    },
}
