"""Repo Map — AST 代码图谱 + PageRank 符号排名。

第 2 层压缩：将代码库提取为关键符号定义，替代原始源码。
参考 Aider Repo Map 的 tree-sitter + PageRank 方案。
"""

from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# 简单 Python 源码解析（纯 re，不依赖 tree-sitter）
# 生产环境可换成 tree-sitter-python 以获得更高精度


class PySymbolExtractor:
    """Python 源码符号提取器。"""

    # 正则: 函数定义 / 类定义 / 方法定义 / 顶层导入
    RE_FUNC = re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE)
    RE_CLASS = re.compile(r"^class\s+(\w+)", re.MULTILINE)
    RE_METHOD = re.compile(r"^\s+async?\s+def\s+(\w+)\s*\(", re.MULTILINE)
    RE_IMPORT = re.compile(r"^(?:from\s+(\S+)\s+)?import\s+(\S+)", re.MULTILINE)

    @classmethod
    def extract(cls, source: str, filepath: str = "") -> List[str]:
        """提取源码中的符号定义列表。"""
        symbols = []
        for match in cls.RE_CLASS.finditer(source):
            symbols.append(f"class {match.group(1)}")
        for match in cls.RE_FUNC.finditer(source):
            symbols.append(f"def {match.group(1)}")
        for match in cls.RE_IMPORT.finditer(source):
            from_ = match.group(1)
            what = match.group(2)
            symbols.append(f"import {from_}.{what}" if from_ else f"import {what}")
        return symbols


class RepoMapBuilder:
    """Repo Map 构建器 — 提取仓库关键符号，PageRank 排序后输出最高优先级片段。

    Usage:
        builder = RepoMapBuilder()
        top_symbols = builder.build(Path("src"), token_budget=1024)
    """

    def __init__(self) -> None:
        self._rank: Dict[str, float] = defaultdict(float)
        self._graph: Dict[str, Set[str]] = defaultdict(set)

    def build(self, root_dir: Path, token_budget: int = 1024) -> str:
        """构建 Repo Map。

        1. 递归扫描 .py 文件
        2. 提取符号 + 构建 import 依赖图
        3. PageRank 迭代
        4. 按 token 预算输出 Top-K
        """
        if not root_dir.exists():
            return "[Repo Map] 目录不存在"

        # 扫描文件
        all_symbols: Dict[str, List[str]] = {}
        for py_file in sorted(root_dir.rglob("*.py")):
            if "site-packages" in str(py_file) or py_file.name == "__init__.py":
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="replace")
                syms = PySymbolExtractor.extract(source, str(py_file))
                if syms:
                    rel_path = py_file.relative_to(root_dir.parent)
                    all_symbols[str(rel_path)] = syms
            except Exception:
                continue

        if not all_symbols:
            return "[Repo Map] 未找到符号"

        # 构建 import 依赖图 → PageRank
        self._build_graph(all_symbols)
        self._page_rank(iterations=10)

        # 按排名排序
        ranked_files = sorted(self._rank.items(), key=lambda x: -x[1])
        ranked_files = [f for f in ranked_files if f[0] in all_symbols]

        # 按 token 预算输出
        output_parts = []
        budget = 0
        for filepath, score in ranked_files:
            symbols = all_symbols.get(filepath, [])
            for sym in symbols:
                estimated_tokens = len(sym) / 4 + 5  # 粗略估算
                if budget + estimated_tokens > token_budget:
                    break
                output_parts.append(f"{filepath}:{sym}")
                budget += estimated_tokens

        result = "\n".join(output_parts)
        logger.info(
            "Repo Map 构建完成: %d 个符号, %d 文件, %.0f tokens",
            len(output_parts),
            len(ranked_files),
            budget,
        )
        return result

    def build_for_skills(self, skill_dir: Path) -> str:
        """为 skill 目录构建符号索引（提取 SKILL.md 中的关键声明）。"""
        if not skill_dir.exists():
            return "[Repo Map] Skill 目录不存在"
        parts = []
        for md_file in sorted(skill_dir.rglob("SKILL.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                # 提取 frontmatter 中的 name/description
                name_match = re.search(r"^name:\s*\"(.+?)\"", content, re.MULTILINE)
                desc_match = re.search(r"^description:\s*\"(.+?)\"", content, re.MULTILINE)
                agent_match = re.search(r"^agent_name:\s*\"(.+?)\"", content, re.MULTILINE)
                if name_match:
                    a_name = agent_match.group(1) if agent_match else name_match.group(1)
                    desc = desc_match.group(1) if desc_match else ""
                    parts.append(f"[skill] {a_name} ({name_match.group(1)}): {desc[:60]}")
            except Exception:
                continue
        return "\n".join(parts) if parts else "[Repo Map] 未找到 SKILL.md"

    def _build_graph(self, all_symbols: Dict[str, List[str]]) -> None:
        """从 import 关系构建有向图。"""
        for filepath, symbols in all_symbols.items():
            for sym in symbols:
                if sym.startswith("import "):
                    # import x.y → 指向被导入的模块
                    target = sym.replace("import ", "").split(".")[0]
                    for other in all_symbols:
                        if target in other:
                            self._graph[filepath].add(other)

    def _page_rank(self, iterations: int = 10, damping: float = 0.85) -> None:
        """简化 PageRank 计算。"""
        files = list(self._graph.keys()) if self._graph else []
        if not files:
            return
        n = len(files)
        # 没有图时给均匀分
        for f in files:
            self._rank[f] = 1.0 / n
        if not self._graph:
            return

        for _ in range(iterations):
            new_rank = defaultdict(float)
            for f in files:
                incoming = [src for src, targets in self._graph.items() if f in targets]
                rank_sum = sum(self._rank[src] / max(len(self._graph[src]), 1) for src in incoming)
                new_rank[f] = (1 - damping) / n + damping * rank_sum
            self._rank = new_rank
