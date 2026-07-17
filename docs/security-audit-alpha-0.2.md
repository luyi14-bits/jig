# Alpha 0.2 安全审计报告

> **审计日期**: 2026-07-16
> **审计框架**: Luyi14-security-academy 5 阶段审计流程
> **审计人**: Daniel Miessler (API/加密) + James Kettle (Web) + Tavis Ormandy (打包)

---

## 阶段 1: 基础设施安全

### 1.1 认证与授权

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| API Key 存储方式 | ❌ | 明文存 JSON（~/.tree-sop/config.json） |
| API Key 注入方式 | ✅ | 环境变量 DEEPSEEK_API_KEY |
| `.env` 文件保护 | ✅ | `.gitignore` 已排除 |
| 配置脱敏 | ❌ | config.json 无脱敏，Key 明文可见 |

### 1.2 输入校验

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| YAML 输入校验 | ✅ | SkillParser 严格校验 frontmatter |
| SQL 参数化 | ⚠️ | 大部分使用 `?` 参数化，但 merge() 用 f-string |
| 路径遍历防护 | ❌ | CheckpointManager + write_log 未校验输入 |

### 1.3 CSP 与 CORS

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| Tauri CSP | ⚠️ | `tauri.conf.json` 中 `"csp": null`（禁用 CSP） |
| CORS 配置 | ✅ | 桌面应用不涉及跨域 |
| Webview 安全 | ⚠️ | CSP 禁用可能允许 XSS |

---

## 阶段 2: 纵深防御

### 2.1 频率限制

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| API 调用限频 | ❌ | 无频率限制逻辑 |
| CircuitBreaker | ✅ | 已实现，但未接入实际调用 |

### 2.2 数据加密

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| API Key 加密 | ❌ | 明文存储，应用层无加密 |
| 传输加密 | ✅ | 走 HTTPS (DeepSeek API) |
| 存储加密 | ❌ | SQLite memory.db 无加密 |

---

## 阶段 3: 生成代码安全

### 3.1 异常处理

| 文件 | 行 | 问题 | 风险 |
|------|:--:|------|:----:|
| repo_map.py | 79-80 | bare `except: continue` | 静默丢失错误 |
| repo_map.py | 130-131 | bare `except: continue` | 静默丢失错误 |
| config_manager.py | 73-74 | `except Exception: pass` → 已修复 | ✅ |

### 3.2 密钥落盘

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| API Key 明文落盘 | ❌ | `~/.tree-sop/config.json` 中无加密 |
| 日志泄露 Key | ⚠️ | dispatcher.py 日志截断到 60 字有防护，但无明确脱敏 |

---

## 阶段 4: 可观测性

### 4.1 日志覆盖

| 模块 | Logger | 覆盖度 | 问题 |
|------|:------:|:------:|------|
| core/ | ✅ | 中等 | 部分 except 无日志 |
| adapters/ | ✅ | 高 | CacheEngine/ModelRouter 日志完善 |
| orchestrator/ | ✅ | 中等 | Orchestrator 无失败日志 |
| cli/ | ❌ | 低 | main.py 无 logger |

### 4.2 错误信息精度

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| 错误信息不泄露密钥 | ✅ | 无密钥在错误信息中 |
| 错误信息包含文件路径 | ⚠️ | config_manager 日志含完整路径 |

---

## 阶段 5: 去匿名化

### 5.1 打包产物审计

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| .pdb 残留 | ✅ | Rust 编译产物无 .pdb |
| .env/.db 包含 | ✅ | `.gitignore` 已排除 |
| 敏感目录包含 | ⚠️ | `.reasonix/` 已在 `.gitignore` 中 |

### 5.2 Git 作者信息

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| Git author 邮箱 | ✅ | 配置为 `user@tree-sop.dev`（非个人邮箱） |
| 提交信息不含敏感信息 | ✅ | 提交信息均为功能描述 |

### 5.3 IDE/编辑器残留

| 检查项 | 状态 | 说明 |
|--------|:----:|------|
| `.vscode/` / `.idea/` | ✅ | 均在 `.gitignore` 中 |
| 日志文件 | ✅ | `*.log` / `logs/` 均在 `.gitignore` 中 |

---

## 审计结论

| 阶段 | 评分 | 主要问题 |
|:----:|:----:|---------|
| 1 基础设施 | ⚠️ 中风险 | API Key 明文存储 |
| 2 纵深防御 | ❌ 高风险 | 无频率限制、无加密 |
| 3 生成代码 | ⚠️ 中风险 | repo_map 静默吞异常 |
| 4 可观测性 | ✅ 低风险 | 覆盖率可接受 |
| 5 去匿名化 | ✅ 低风险 | 配置合理 |

### 主要风险

1. **API Key 明文落盘** — 优先级 P0，违反自己的安全约束
2. **repo_map 静默吞异常** — 优先级 P0，两处 bare `except`
3. **SQL 注入风险** — 优先级 P1，memory.py merge()
4. **路径遍历风险** — 优先级 P1，两处未校验输入

### 合规状态

- ❌ AGPL v3 要求：已满足（LICENSE 文件完整）
- ❌ 全局约束 `global_constraints.py`：**第 26-27 行未被遵守**（明文 Key 存储违反约束）
