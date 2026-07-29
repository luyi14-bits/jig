"""EvalRunner — Jig 评测系统。

运行评测集，输出准确率/SOP符合率/有害率指标。
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path


@dataclass
class EvalExample:
    input: str
    expected: str
    criteria: List[str] = field(default_factory=list)


@dataclass
class EvalResult:
    example_idx: int
    input: str
    output: str
    expected: str
    passed: bool
    criteria_scores: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class EvalReport:
    name: str
    results: List[EvalResult] = field(default_factory=list)
    timestamp: str = ""

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def pass_rate(self) -> float:
        return round(self.passed_count / max(self.total, 1), 4)

    @property
    def summary_text(self) -> str:
        return (
            f"## Eval: {self.name}\n"
            f"- Total: {self.total}\n"
            f"- Passed: {self.passed_count}\n"
            f"- Pass rate: {self.pass_rate:.1%}\n"
            f"- Time: {self.timestamp}\n"
        )

    def to_markdown(self) -> str:
        lines = [self.summary_text]
        for i, r in enumerate(self.results):
            status = "✅" if r.passed else "❌"
            lines.append(f"\n### {i+1}. {status} Input: `{r.input[:60]}`")
            lines.append(f"- Expected: `{r.expected[:80]}`")
            lines.append(f"- Got: `{r.output[:80]}`")
            if r.error:
                lines.append(f"- Error: {r.error}")
            if r.criteria_scores:
                for k, v in r.criteria_scores.items():
                    lines.append(f"- {k}: {v}")
        return "\n".join(lines)


class EvalRunner:
    """评测运行器。"""

    def __init__(self, judge_fn: Optional[Callable] = None):
        self._judge = judge_fn or self._default_judge

    @staticmethod
    def _default_judge(output: str, expected: str) -> bool:
        return expected.strip() in output.strip() or output.strip() == expected.strip()

    def run(self, name: str, examples: List[EvalExample],
            execute_fn: Callable[[str], str]) -> EvalReport:
        """执行评测集。"""
        report = EvalReport(name=name, timestamp=datetime.utcnow().isoformat())
        for idx, ex in enumerate(examples):
            try:
                output = execute_fn(ex.input)
                passed = self._judge(output, ex.expected)
                scores = {}
                for c in ex.criteria:
                    if "contain" in c.lower():
                        keyword = c.split("contain")[-1].strip().strip("'\"")
                        scores[c] = 1.0 if keyword.lower() in output.lower() else 0.0
                    else:
                        scores[c] = 1.0 if passed else 0.0
                report.results.append(EvalResult(
                    example_idx=idx, input=ex.input, output=output,
                    expected=ex.expected, passed=passed, criteria_scores=scores,
                ))
            except Exception as e:
                report.results.append(EvalResult(
                    example_idx=idx, input=ex.input, output="",
                    expected=ex.expected, passed=False, error=str(e),
                ))
        return report

    @staticmethod
    def load_dataset(path: str) -> List[EvalExample]:
        """从 JSON 文件加载评测集。"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return [EvalExample(**item) for item in data if isinstance(item, dict)]

    @staticmethod
    def save_report(report: EvalReport, path: str) -> None:
        """保存评测报告为 Markdown。"""
        Path(path).write_text(report.to_markdown(), encoding="utf-8")
