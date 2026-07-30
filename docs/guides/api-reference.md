# API Reference

## Jig
```python
from jig import Jig
app = Jig(skills_dir="./skills")
app.run(prompt: str) -> HandoverPackage
app.skill_count -> int
```

## SOPRunner
```python
runner = SOPRunner(config=None)
runner.run(sop: SOPNode, context: dict) -> HandoverPackage
runner.arun(sop: SOPNode, context: dict) -> HandoverPackage  # async
runner.approve(session_id: str) -> str
runner.reject(session_id: str) -> str
```

## Dispatcher
```python
dispatcher = Dispatcher()
dispatcher.handle(task: str) -> dict
dispatcher.register_agent(name, agent)
```

## MetricsCollector
```python
from jig.adapters.metrics import get_collector
collector = get_collector()
collector.record(name, duration_ms, error=False)
collector.metrics_text()  # Prometheus format
```
