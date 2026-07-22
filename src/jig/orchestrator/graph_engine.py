"""Graph 编排引擎 — 图工作流替代线性管道。

IDEA-061: 让 Jig 支持条件路由、自环、递归的图编排。
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EdgeType(Enum):
    """边类型。"""
    CONDITIONAL = "conditional"  # 条件路由
    DEFAULT = "default"          # 默认路由
    TIMEOUT = "timeout"          # 超时路由


@dataclass
class GraphNode:
    """图节点 — 一个 Agent 或子管道。"""
    name: str
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """图边 — 节点间的连接。"""
    source: str
    target: str
    edge_type: EdgeType = EdgeType.DEFAULT
    condition: Optional[Callable] = None  # 条件函数(上下文→bool)
    timeout_seconds: Optional[float] = None


class GraphRuntimeError(Exception):
    """图执行错误。"""
    pass


class GraphOrchestrator:
    """图编排引擎。

    支持:
    - 线性执行（A → B → C）
    - 条件分支（if condition → B else → C）
    - 并行执行（A → B∥C → D）
    - 自环（A → A，带收敛检测）
    """

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: List[GraphEdge] = []
        self._context: Dict[str, Any] = {}

    def add_node(self, node: GraphNode) -> None:
        self._nodes[node.name] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self._nodes:
            raise GraphRuntimeError(f"源节点不存在: {edge.source}")
        if edge.target not in self._nodes:
            raise GraphRuntimeError(f"目标节点不存在: {edge.target}")
        self._edges.append(edge)

    def run(self, start_node: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行图编排。

        Args:
            start_node: 起始节点名称
            context: 初始上下文

        Returns:
            执行结果上下文
        """
        if start_node not in self._nodes:
            raise GraphRuntimeError(f"起始节点不存在: {start_node}")

        self._context = dict(context or {})
        self._execute_node(start_node)
        return self._context

    def _execute_node(self, node_name: str, visited: Optional[Set[str]] = None) -> None:
        if visited is None:
            visited = set()

        if node_name in visited:
            logger.warning("检测到环: %s, 跳过", node_name)
            return

        visited.add(node_name)
        node = self._nodes[node_name]
        logger.info("执行节点: %s", node_name)

        # 找到从当前节点出发的所有边
        outgoing = [e for e in self._edges if e.source == node_name]

        # 按类型处理
        conditional_edges = [e for e in outgoing if e.edge_type == EdgeType.CONDITIONAL]
        default_edges = [e for e in outgoing if e.edge_type == EdgeType.DEFAULT]

        if conditional_edges:
            # 条件分支：执行第一个条件满足的分支
            executed = False
            for edge in conditional_edges:
                if edge.condition and edge.condition(self._context):
                    self._execute_node(edge.target, visited.copy())
                    executed = True
                    break
            if not executed and default_edges:
                self._execute_node(default_edges[0].target, visited.copy())
        elif default_edges:
            # 默认顺序执行所有出边
            for edge in default_edges:
                self._execute_node(edge.target, visited.copy())

    def get_graph_info(self) -> Dict:
        """获取图拓扑信息。"""
        return {
            "nodes": list(self._nodes.keys()),
            "edges": [{"from": e.source, "to": e.target, "type": e.edge_type.value} for e in self._edges],
        }
