# Alpha 0.2 代码审计报告

> **审计日期**: 2026-07-15 | **审计框架**: Luyi14-coding-ethics + Luyi14-security-academy + Luyi14-test-driven-development
> **覆盖**: 20 个 Python 模块 + 6 个测试文件

---

## 摘要

| 指标 | 数值 |
|------|:----:|
| 扫描模块数 | 20 |
| 测试总数 | 56 pytest + 7 auto_test = 63 |
| 未覆盖模块数 | 11 |
| 红线问题 | 2 |
| 警告问题 | 8 |
| 建议改进 | 6 |

---

## 🔴 红线

### R1: config_manager.py 静默吞异常

**文件**: `src/jig/core/config_manager.py` 第 73-74 行
**违反**: 第十九荣（禁止 `except: pass`）/ 安全红线 8
**代码**:
```python
except Exception:
    pass  # ← 无声无息吞掉所有错误
```
**风险**: 配置文件损坏或缺失时静默返回空配置，用户以为配置已保存但实际上未生效
**修复**: 加 `logger.warning(f"读取配置失败: {e}")`

### R2: repo_map.py 静默吞异常

**文件**: `src/jig/adapters/repo_map.py` 第 79-80 行, 第 130-131 行
**违反**: 第十九荣 / 安全红线 8
**代码**:
```python
except Exception:
    continue  # ← 文件读取/解析失败时不记录任何信息
```
**风险**: 代码库文件损坏时静默跳过，用户不知情
**修复**: 加 `logger.warning(f"跳过 {py_file}: {e}")`

---

## 🟠 警告

### W1: LocalStore 全部 SQLite 操作无错误处理

**文件**: `src/jig/orchestrator/memory.py`
**影响**: `set_profile` / `save_session` / `log_memory` / `forget` / `merge` 等 15+ 处
**风险**: 数据库连接失败/磁盘满时直接崩溃，无降级路径
**修复**: 对每个 execute() + commit() 加 try/except，失败时 logger.exception + 返回 False/空

### W2: CheckpointManager 文件写入无错误处理

**文件**: `src/jig/orchestrator/orchestrator.py` 第 240-241 行
**风险**: JSON 序列化失败或磁盘写入失败时抛未处理异常
**修复**: 加 try/except，失败时 logger.error + 返回 "" 而非 path

### W3: 用户消息写入日志可能泄露敏感信息

**文件**: `src/jig/orchestrator/dispatcher.py` 第 45 行, 第 69 行
**文件**: `src/jig/adapters/mcp_client.py` 第 45 行
**风险**: API Key、密码等敏感输入可能出现在日志中
**修复**: dispatcher 日志截断到 60 字已有一定防护，建议加 `re.sub(r'sk-[a-zA-Z0-9]+', 'sk-***', msg)` 过滤

### W4: ToolType 枚举未导出

**文件**: `src/jig/core/__init__.py`
**问题**: `ToolType` 在 `skill_def.py` 中定义为 public enum，但未在 `__init__.py` 的 `__all__` 中导出
**修复**: 在 `core/__init__.py` 和顶层 `__init__.py` 中导出 `ToolType`

### W5: Hardcoded skills/ 路径

**文件**: `src/jig/core/agent_factory.py` 第 103 行
**文件**: `src/jig/orchestrator/dispatcher.py` 第 23 行
**风险**: 从非项目根目录运行时找不到 skills 目录
**修复**: 改为可配置路径，从 settings 或 ConfigManager 读取

### W6: SQLite 连接无异常处理

**文件**: `src/jig/orchestrator/memory.py` 第 32 行
**风险**: `sqlite3.connect()` 失败时直接抛出
**修复**: 加 try/except，失败时 logger.critical + raise 包装

---

## 🟡 建议

### S1: 11 个模块无测试覆盖

| 模块 | 建议测试 |
|------|---------|
| `config_manager.py` | JSON 读写 / 配置合并 / 字段校验 |
| `mcp_client.py` | 工具查找 / 调用路由 / 不存在工具 |
| `model_router.py` | 路由分配 / session 创建 / 重置 |
| `context.py` | 三层分区 / 冻结 / 偏移检测 |
| `deepseek_adapter.py` | reasoning_content 规则 / FC 降级 |
| `circuit_breaker.py` | 三态转换 / 恢复超时 / 调用包装 |
| `intent_router.py` | 分类 / HyDE / Decomp |
| `global_constraints.py` | 常量完整 / 格式 |

### S2: 缺少 conftest.py

无共享 fixtures、无 mock 基础设施。建议创建 `tests/conftest.py` 提供 `cache_engine` / `local_store` / `memory_router` 等 fixture。

### S3: auto_test.py 未集成到 pytest

`auto_test.py` 有 7 个策略测试 CacheEngine、DeepSeekAdapter、ContextPartitioner 等关键模块，但不属于 pytest 套件。建议迁移到 `tests/test_auto_integration.py`。

### S4: 缺少 parametrize 边界测试

仅 2 处使用 parametrize（6+4=10 变体）。建议为 skill_parser、agent_factory、cache_engine 增加 parametrize 边界值测试。

### S5: 配置文件路径信息泄露

`config_manager.py` 在错误日志中可能暴露 `~/.tree-sop/config.json`。建议日志中路径使用 `Path(...).name` 而非完整路径。

### S6: 测试中的 tempfile 样板代码

`test_memory.py` 中 4 个测试手动创建/删除临时文件。建议使用 pytest 内置 `tmp_path` fixture。

---

## 修复优先级

| 优先级 | 问题 | 工作量 |
|:------:|------|:------:|
| **P0** | R1 + R2 静默吞异常 | 10 分钟 |
| **P0** | W1 LocalStore 错误处理 | 20 分钟 |
| **P1** | W2 CheckpointManager 错误处理 | 10 分钟 |
| **P1** | S1 关键模块补测试（circuit_breaker + intent_router + config_manager） | 30 分钟 |
| **P2** | W4 ToolType 导出 / W5 硬编码路径 / W3 日志脱敏 | 15 分钟 |

---

*审计框架: Luyi14-coding-ethics + Luyi14-security-academy + Luyi14-test-driven-development*
