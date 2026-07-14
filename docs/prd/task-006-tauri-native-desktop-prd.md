# IDEA-018: 真·Tauri 原生桌面应用 — PRD

> **版本**: v0.1 | **作者**: PM (Luyi14-pm-mentor) | **日期**: 2026-07-15 | **状态**: 阶段 0 — 对齐

---

## 1. Executive Summary

将现有的 Tauri 桌面壳（`desktop/` 脚手架）改造为**真正的原生桌面应用**。解决三个核心差距：前端从 mock 变为真实 IPC 通信、Rust 后端 sidecar 启动 Python 引擎、`npm run tauri build` 产出独立 `.exe`。

## 2. 现状 vs 目标

| 维度 | 当前（v1.0.0 Tauri 壳） | 目标（IDEA-018） |
|------|------------------------|-----------------|
| 前端 | React App.tsx（mock 数据，无真实调用） | 真实调用 `@tauri-apps/api` invoke |
| Agent 列表 | 硬编码在 App.tsx 中 | 从 Rust `list_skills` 命令实时获取 |
| 聊天功能 | 前端 mock，无后端响应 | 输入 → invoke → Python Dispatcher → 回显 |
| Python 引擎 | 无 | sidecar 方式启动，stdout 流到前端终端 |
| 构建产出 | 无（未跑过 tauri build） | `desktop/src-tauri/target/release/TreeSOP-Agent.exe` |

## 3. 需要做的工作

### 3.1 前端改造（App.tsx）

| 功能 | 当前 | 目标 |
|------|------|------|
| Agent 列表 | 硬编码 12 个角色 | 启动时调用 `invoke("list_skills")` 获取 |
| 聊天 | 纯本地 mock | 输入 → invoke("run_pipeline") → 显示返回 |
| 终端 | 静态 HTML 文本 | 接入 xterm.js，接收 Rust stdout 事件 |
| 输入框 | 基础 input | 保留，增加 loading 状态 |

### 3.2 Rust 后端改造（main.rs）

当前已有 `list_skills` 和 `run_pipeline` 命令，但：

| 问题 | 修复 |
|------|------|
| `run_pipeline` 用 `python -c` 传参，shell 注入风险 | 改为 Tauri sidecar（嵌入脚本）或 HTTP 调用 |
| 无流式输出 | 改用 Tauri event 机制：`app_handle.emit("terminal-output", data)` |
| `list_skills` 输出原始 CLI 文本 | 改为 JSON 结构化输出 |

### 3.3 Python 侧改造

新增 `desktop_engine.py` 入口（替代 `--chat` 模式）：

```python
# 简单的 JSON 协议：stdin 读请求 → stdout 写 JSON 响应
# 或者启动轻量 HTTP 服务器（可选）
```

### 3.4 构建验证

```
cd desktop
npm run tauri build
# 产物: desktop/src-tauri/target/release/TreeSOP-Agent.exe
```

## 4. 不做的（Out of Scope）

- Monaco Editor 代码编辑器（当前已有依赖但未接入，放到后续迭代）
- 完整的文件树浏览器
- 用户登录/认证
- 跨平台（Windows 优先，macOS/Linux 后续）

## 5. 成功指标

| 指标 | 目标 |
|------|------|
| exe 产出 | `tauri build` 成功，产物 < 200MB |
| Agent 加载 | 启动时成功从 Python 加载 10+ 个 skill |
| 聊天交互 | 输入 → invoke → 回显，端到端 < 5s |
| 终端 | Rust stdout 事件实时推送到前端 |
