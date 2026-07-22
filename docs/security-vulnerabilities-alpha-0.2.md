# Alpha 0.2 安全漏洞报告

> **审计日期**: 2026-07-16 | **框架**: Luyi14-security-academy + Luyi14-coding-ethics

---

## 🔴 CRITICAL — 必须立即修复

### C1: API Key 明文落盘

**文件**: `src/jig/core/config_manager.py:62-65, 81-91`
**违反**: 全局约束 `global_constraints.py:26-27`（"API Key / Token 禁止明文落盘"）
**漏洞**: `deepseek_api_key` 以纯文本形式写入 `~/.tree-sop/config.json`，任何能读取该文件的进程均可获取用户 API Key
**CWE**: CWE-312 (Cleartext Storage of Sensitive Information)
**修复**: 使用操作系统密钥链（Windows Credential Manager / macOS Keychain）或至少使用 AES-GCM 派生密钥加密

### C2: settings.py 环境变量不安全性

**文件**: `src/jig/settings.py:31`
**漏洞**: 虽然 API Key 来自环境变量，但 `.env` 文件本身可能被提交到版本控制
**CWE**: CWE-522 (Insufficiently Protected Credentials)
**状态**: 当前 `.env` 已在 `.gitignore` 中 ✅，但无额外保护

### C3: AppConfig 明文存储

**文件**: `src/jig/core/config_manager.py:42`
**漏洞**: `AppConfig` dataclass 中 `deepseek_api_key` 为明文 `str`，序列化时直接写盘

---

## 🟠 HIGH

### H1-H2: repo_map.py 静默吞异常

**文件**: `src/jig/adapters/repo_map.py:79-80, 130-131`
**漏洞**: 两处 `except Exception: continue` 无声无息隐藏 IO/编码错误
**违反**: 第十九荣 / 安全红线 8

### H3: memory.py SQL 注入风险

**文件**: `src/jig/orchestrator/memory.py:238-244`
**漏洞**: `Consolidator.merge()` 使用 f-string 拼接 SQL（`WHERE id IN ({placeholders})`）
**CWE**: CWE-89

---

## 🟡 MEDIUM

### M1-M2: 路径遍历风险

**文件**:
- `orchestrator/orchestrator.py:239,247` — `CheckpointManager` 未校验 `session_id`
- `core/agent_factory.py:103-115` — `write_log()` 未校验 `skill_name`
**CWE**: CWE-22

### M3: Secretary 权限过大

**文件**: `adapters/mcp_client.py:81`
**漏洞**: Secretary Agent 的白名单包含不加限制的 Bash 和 Git 命令

### M4-M5: 配置文件权限

**文件**: `config_manager.py:81-91` / `memory.py:31`
**漏洞**: `config.json` 和 `memory.db` 文件权限取决于 umask，可能被其他用户读取

### M6: settings 模块级副作用

**文件**: `settings.py:98`
**漏洞**: `settings = Settings()` 在 import 时实例化，可能将 API Key 暴露给调试器

---

## 🔵 LOW

| ID | 文件:行 | 问题 |
|:--:|---------|------|
| L1 | `server/app.py:62` | FastAPI 默认绑定 0.0.0.0，应改为 127.0.0.1 |
| L2 | `orchestrator/orchestrator.py:234` | CheckpointManager 默认目录无权限硬化 |
| L3-L4 | `dispatcher.py:27`, `agent_factory.py:103` | 硬编码相对路径 `"skills"` |
| L5 | `test_e2e_loop.py:105-108` | 测试中使用 subprocess 跑 pytest（不标准） |

---

## 代码质量

| ID | 文件:行 | 问题 | 严重度 |
|:--:|---------|------|:------:|
| Q1 | `settings.py:98` | `settings = Settings()` 模块级副作用 | HIGH |
| Q2-Q3 | `server/app.py:21,33` | FastAPI 实例 + 内存 session 在模块级 | MEDIUM |
| Q9 | `adapters/mcp_client.py:49-62` | web_search 和 fetch_page 是模拟桩 | HIGH |
| Q10 | `adapters/conversation_compressor.py:122-147` | _make_summary 是离线关键词桩 | MEDIUM |
| Q11 | `server/app.py:45-47` | /execute 端点是同步无操作存根 | MEDIUM |
| Q12 | `orchestrator/dispatcher.py:33-74` | Dispatcher.handle() 是桩，硬编码路由 | MEDIUM |

---

## 总结

| 等级 | 数量 | 代表问题 |
|:----:|:----:|---------|
| 🔴 CRITICAL | 3 | API Key 明文落盘 / 环境变量泄露 / AppConfig 明文存储 |
| 🟠 HIGH | 3 | repo_map 静默吞异常、SQL 注入风险、 |
| 🟡 MEDIUM | 6 | 路径遍历 / 权限过大 / 默认权限 / 模块副作用 |
| 🔵 LOW | 5 | 绑定 0.0.0.0 / 硬编码路径 / 测试不规范 |
| 代码质量 | 12 | settings 副作用、模拟桩、同步存根 <= 12 |

**最严重问题**: API Key 明文落盘直接违反自己的安全约束（`global_constraints.py` 第 26-27 行），且影响所有使用桌面的用户。
