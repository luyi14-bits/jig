use std::process::Command;
use std::path::PathBuf;

/// 列出所有已加载的 Agent（调用 Python CLI → JSON）
#[tauri::command]
fn list_skills(skill_dir: String) -> Result<String, String> {
    let output = Command::new("python")
        .args(["-m", "src.tree_sop_agent.cli.main", "--skill-dir", &skill_dir, "--list"])
        .output()
        .map_err(|e| format!("Python 调用失败: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();

    // 从 CLI 输出中提取 skill 行
    let skills: Vec<String> = stdout
        .lines()
        .filter(|l| l.starts_with("  🚀") || l.starts_with("  ⚡"))
        .map(|l| {
            let trimmed = l.trim_start();
            let model = if trimmed.starts_with("🚀") { "pro" } else { "flash" };
            let name = trimmed[2..].split(':').next().unwrap_or("").trim();
            format!(r#"{{"name":"{}","model":"{}"}}"#, name, model)
        })
        .collect();

    let json = format!("[{}]", skills.join(","));
    Ok(json)
}

/// 运行 SOP 管道（通过 Python 脚本文件）
#[tauri::command]
fn run_pipeline(prompt: String, skill_dir: String) -> Result<String, String> {
    // 使用 python -m 直接调用，而非 -c
    let current_dir = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    let src_path = current_dir.join("src");

    let output = Command::new("python")
        .arg("-c")
        .arg(&format!(
            "import sys; sys.path.insert(0,'{}'); from tree_sop_agent.orchestrator.dispatcher import Dispatcher; d=Dispatcher(skill_dir='{}'); print(d.handle('{}'))",
            src_path.to_string_lossy().replace("\\", "\\\\"),
            skill_dir.replace("\\", "\\\\"),
            prompt.replace('\'', "\\'")
        ))
        .output()
        .map_err(|e| format!("Pipeline 执行失败: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if stdout.is_empty() && !stderr.is_empty() {
        return Err(format!("引擎错误: {}", stderr.lines().last().unwrap_or("unknown")));
    }

    Ok(stdout.trim().to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![list_skills, run_pipeline])
        .run(tauri::generate_context!())
        .expect("启动 Tree-SOP Agent 桌面应用失败");
}
