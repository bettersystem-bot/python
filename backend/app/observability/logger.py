"""结构化日志（对应架构图右侧的 log）。

为整个系统提供统一的 logger 工厂。这里用标准库 logging，输出带时间戳、级别、
模块名的结构化文本。真实系统可换成 JSON formatter 接入 StreamLog 等平台，
但教学项目保持简单、零依赖。
"""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-12s | %(message)s"


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%H:%M:%S"))
    root = logging.getLogger("orch")
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """获取一个命名 logger，名字会挂在 orch.* 命名空间下。"""
    _configure_root()
    return logging.getLogger(f"orch.{name}")
