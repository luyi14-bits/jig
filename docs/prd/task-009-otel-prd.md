# PRD: OpenTelemetry 可观测性 (IDEA-038)

## Why
当前框架无任何运行时指标。SOP 管道执行、API 调用延迟、节点失败率均不可见。

## Requirements
- R1: 每个 SOP 节点执行时长直方图
- R2: API call 延迟/成功率指标
- R3: Trace ID 贯穿 pipeline
- R4: Prometheus /std-metrics 端点
- R5: 可选导出到 Jaeger / OTLP

## Tasks
1. Metrics 采集装饰器 (2h)
2. Trace context 注入 dispatcher (1h)
3. /metrics 端点 (1h)
4. Integration tests (1h)

## Out of Scope
- Grafana dashboard (外部工具)
- 全链路采样策略
