use std::process::Command;
use std::path::PathBuf;

/// 列出所有已加载的 Agent
#[tauri::command]
fn list_skills(skill_dir: String) -> Result<String, String> {
    let output = Command::new("python")
        .args(["-m", "src.tree_sop_agent.cli.main", "--skill-dir", &skill_dir, "--list"])
        .output()
        .map_err(|e| format!("Python 调用失败: {}", e))?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let skills: Vec<String> = stdout.lines()
        .filter(|l| l.contains("🚀") || l.contains("⚡"))
        .map(|l| {
            let trimmed = l.trim_start();
            let model = if trimmed.starts_with("🚀") { "pro" } else { "flash" };
            let after_emoji = trimmed.splitn(2, ' ').nth(1).unwrap_or("");
            let name = after_emoji.split(':').next().unwrap_or("").trim();
            format!(r#"{{"name":"{}","model":"{}"}}"#, name, model)
        }).collect();
    Ok(format!("[{}]", skills.join(",")))
}

/// 运行 SOP 管道
#[tauri::command]
fn run_pipeline(prompt: String, skill_dir: String) -> Result<String, String> {
    let current_dir = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let src_path = current_dir.join("src");
    let output = Command::new("python")
        .arg("-c")
        .arg(&format!(
            "import sys; sys.path.insert(0,'{}'); from tree_sop_agent.orchestrator.dispatcher import Dispatcher; d=Dispatcher(skill_dir='{}'); print(d.handle('{}'))",
            src_path.to_string_lossy().replace("\\", "\\\\"),
            skill_dir.replace("\\", "\\\\"),
            prompt.replace('\'', "\\'")
        )).output().map_err(|e| format!("Pipeline 执行失败: {}", e))?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    if stdout.is_empty() && !stderr.is_empty() {
        return Err(format!("引擎错误: {}", stderr.lines().last().unwrap_or("unknown")));
    }
    Ok(stdout.trim().to_string())
}

// ── 配置统一访问（config.json） ──
fn config_path() -> PathBuf {
    let home = std::env::var("USERPROFILE").or_else(|_| std::env::var("HOME")).unwrap_or_else(|_| ".".to_string());
    PathBuf::from(home).join(".tree-sop").join("config.json")
}

fn read_config() -> serde_json::Value {
    let path = config_path();
    if !path.exists() { return serde_json::json!({}); }
    let content = std::fs::read_to_string(&path).unwrap_or_else(|_| "{}".to_string());
    serde_json::from_str(&content).unwrap_or_else(|_| serde_json::json!({}))
}

fn write_config(config: &serde_json::Value) -> Result<(), String> {
    let path = config_path();
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| format!("创建目录失败: {}", e))?;
    }
    let json = serde_json::to_string_pretty(config).map_err(|e| format!("JSON 序列化失败: {}", e))?;
    std::fs::write(&path, json)
        .map_err(|e| format!("写入配置失败: {}", e))
}

/// 读取完整配置（JSON）
#[tauri::command]
fn get_config() -> Result<String, String> {
    Ok(read_config().to_string())
}

/// 保存 DeepSeek API Key
#[tauri::command]
fn save_api_key(value: String) -> Result<String, String> {
    if value.is_empty() {
        return Err("API Key 不能为空".to_string());
    }
    let mut config = read_config();
    config["deepseek_api_key"] = serde_json::json!(value);
    write_config(&config)?;
    Ok(config.to_string())
}

/// 添加 MCP Server（存入 config.json.mcp_servers）
#[tauri::command]
fn add_mcp_server(name: String, url: String) -> Result<String, String> {
    if name.is_empty() || url.is_empty() {
        return Err("Name 和 URL 不能为空".to_string());
    }
    let mut config = read_config();
    let servers = config["mcp_servers"].as_array_mut();
    if let Some(s) = servers {
        s.push(serde_json::json!({"name": name, "url": url}));
    } else {
        config["mcp_servers"] = serde_json::json!([{"name": name, "url": url}]);
    }
    write_config(&config)?;
    Ok(config["mcp_servers"].to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            list_skills, run_pipeline,
            get_config, save_api_key, add_mcp_server
        ])
        .run(tauri::generate_context!())
        .expect("启动 Tree-SOP Agent 桌面应用失败");
}
