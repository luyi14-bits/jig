# 桌面应用 Bug 反馈汇总

> **日期**: 2026-07-16 | **版本**: Alpha 0.2 | **状态**: 已修复

---

## 问题概述

Tree-SOP Agent 桌面应用的 Settings 面板中，「API Key 保存」「MCP Server 添加」「Skills 加载」三个功能全部失效。exe 打开后显示"无法访问页面"。

---

## 根因分析

### Bug 1：Tauri v2 命令名自动转换导致 invoke 静默失败

**文件**: `desktop/src/App.tsx`
**严重度**: 🔴 CRITICAL

Tauri v2 在 Rust 后端和 JS 前端之间使用 IPC 通信。Rust 端注册的命令名 `save_api_key` 会被 Tauri 自动转为 camelCase（`saveApiKey`），但前端 `invoke()` 调用时仍使用 snake_case 原始名称。

| 前端调用（旧） | Tauri v2 实际匹配 | 结果 |
|:---:|:---:|:----:|
| `invoke("get_config")` | `getConfig` | ❌ 静默失败 |
| `invoke("save_api_key", ...)` | `saveApiKey` | ❌ 静默失败 |
| `invoke("add_mcp_server", ...)` | `addMcpServer` | ❌ 静默失败 |
| `invoke("list_skills", ...)` | `listSkills` | ❌ 静默失败 |
| `invoke("run_pipeline", ...)` | `runPipeline` | ❌ 静默失败 |

**影响范围**: 所有 invoke 调用全部失效，三个 Settings 功能均因此不工作。

### Bug 2：Rust 端 emoji 字节索引导致崩溃

**文件**: `desktop/src-tauri/src/lib.rs:17`
**严重度**: 🟠 HIGH

```rust
// 旧代码（有 bug）
let name = trimmed[2..].split(':').next().unwrap_or("").trim();
```

Python CLI 输出 `"  🚀 Luyi14-acceptance-testing: ..."`，其中 emoji 占 3-4 字节。`trimmed[2..]` 对 🚀（4 字节）做字节切片，索引 2 落在字符中间，Rust 运行时直接 panic 崩溃。

### Bug 3：Webview 资源路径错误

**文件**: `desktop/vite.config.ts`
**严重度**: 🟡 MEDIUM

`vite.config.ts` 未设置 `base` 选项，构建产物使用绝对路径 `/assets/xxx.js`。Tauri 生产模式下通过自定义 protocol（`tauri://`）加载页面，绝对路径无法解析，WebView 显示空白页面。

---

## 修复清单

| # | 文件 | 修改内容 | 改动量 |
|:-:|------|---------|:------:|
| 1 | `desktop/src/App.tsx` | 6 处 `invoke` 命令名 snake_case → camelCase | 6 行 |
| 2 | `desktop/src-tauri/src/lib.rs` | emoji 字节索引改为 `splitn` 安全解析 | 3 行 |
| 3 | `desktop/vite.config.ts` | 增加 `base: ""` 使资源路径为相对路径 | 1 行 |

---

## 验证方法

1. 双击 exe 启动桌面应用
2. 确认原生窗口正常显示（不再 localhost 错误）
3. 点击 ⚙ 齿轮图标进入 Settings
4. API Key Tab：输入 key → Save → 关闭重开 → 确认 key 保留
5. MCP Server Tab：添加 name+url → 确认列表更新
6. Skills Tab：确认 12 个 skill 正常加载
