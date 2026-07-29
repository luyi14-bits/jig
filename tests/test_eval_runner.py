"""Tests for EvalRunner."""

from src.jig.core.eval_runner import EvalRunner, EvalExample


class TestEvalRunner:
    def test_run_pass(self):
        r = EvalRunner()
        examples = [EvalExample(input="hello", expected="world")]
        report = r.run("test", examples, lambda x: "hello world")
        assert report.total == 1
        assert report.passed_count == 1
        assert report.pass_rate == 1.0

    def test_run_fail(self):
        r = EvalRunner()
        examples = [EvalExample(input="hi", expected="bye")]
        report = r.run("test", examples, lambda x: "nope")
        assert report.passed_count == 0

    def test_run_multiple(self):
        r = EvalRunner()
        examples = [
            EvalExample(input="a", expected="1"),
            EvalExample(input="b", expected="2"),
            EvalExample(input="c", expected="3"),
        ]
        report = r.run("multi", examples, lambda x: {"a": "1", "b": "wrong", "c": "3"}.get(x, ""))
        assert report.total == 3
        assert report.passed_count == 2

    def test_run_error(self):
        r = EvalRunner()
        examples = [EvalExample(input="crash", expected="ok")]

        def crash(x):
            raise RuntimeError("boom")

        report = r.run("err", examples, crash)
        assert report.total == 1
        assert report.passed_count == 0
        assert report.results[0].error is not None

    def test_criteria_scores(self):
        r = EvalRunner()
        examples = [EvalExample(input="say hi", expected="hello", criteria=["contain 'hello'"])]
        report = r.run("criteria", examples, lambda x: "hello world")
        assert report.results[0].criteria_scores.get("contain 'hello'") == 1.0

    def test_summary_text(self):
        r = EvalRunner()
        examples = [EvalExample(input="a", expected="b")]
        report = r.run("sum", examples, lambda x: "b")
        assert "Eval: sum" in report.summary_text
        assert "Pass rate: 100.0%" in report.summary_text

    def test_empty_run(self):
        r = EvalRunner()
        report = r.run("empty", [], lambda x: "")
        assert report.total == 0
        assert report.pass_rate == 0.0
