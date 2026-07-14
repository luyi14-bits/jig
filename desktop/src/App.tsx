import React, { useState, useEffect, useCallback } from "react";

// 当 Tauri 可用时使用 invoke，否则 fallback 到 mock
let invoke: any = null;
try {
  const tauri = window.__TAURI__ || (window as any).tauri;
  if (tauri?.invoke) {
    invoke = tauri.invoke;
  }
} catch (_) {}

interface Agent {
  name: string;
  description: string;
  model: string;
  status: string;
}

const AGENT_ICONS: Record<string, string> = {
  dispatcher: "🔀", pm: "📋", spec: "📐", coding: "💻",
  "code-review": "🔍", tdd: "🧪", acceptance: "✅", security: "🔒",
  devops: "🚀", secretary: "📁", trinity: "🎓", loop: "🔄",
};

function getAgentIcon(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, icon] of Object.entries(AGENT_ICONS)) {
    if (lower.includes(key)) return icon;
  }
  return "🤖";
}

function getAgentModelBadge(model: string): string {
  return model === "pro" ? "🧠 Pro" : "⚡ Flash";
}

const FALLBACK_AGENTS: Agent[] = [
  { name: "Dispatcher", description: "群聊入口/需求路由", model: "pro", status: "就绪" },
  { name: "PM", description: "产品经理 — PRD/需求分析", model: "pro", status: "就绪" },
  { name: "Trinity", description: "技术评审/架构审查", model: "pro", status: "就绪" },
  { name: "Spec-Pipeline", description: "管线工程师 — 拆任务", model: "pro", status: "就绪" },
  { name: "Coding", description: "编码实现", model: "flash", status: "就绪" },
  { name: "Code-Review", description: "代码质量审查", model: "pro", status: "就绪" },
  { name: "TDD", description: "测试开发", model: "flash", status: "就绪" },
  { name: "Acceptance", description: "功能验收", model: "flash", status: "就绪" },
  { name: "Security", description: "安全审计", model: "pro", status: "就绪" },
  { name: "DevOps", description: "构建/发布/回滚", model: "flash", status: "就绪" },
  { name: "Secretary", description: "留痕/看板/版本", model: "flash", status: "就绪" },
  { name: "LOOP SOP", description: "总调度/门禁/降级", model: "pro", status: "监控" },
];

const App: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([
    "Dispatcher 已就绪。输入需求，Agent 团队自动协作。",
  ]);

  useEffect(() => {
    async function load() {
      try {
        if (invoke) {
          const raw = await invoke("list_skills", { skillDir: "skills" });
          const parsed = JSON.parse(raw as string);
          if (parsed.length > 0) {
            setAgents(parsed.map((a: any) => ({ ...a, description: "", status: "就绪" })));
            return;
          }
        }
      } catch (_) {}
      setAgents(FALLBACK_AGENTS);
    }
    load();
  }, []);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;
    const msg = input;
    setMessages((prev) => [...prev, `> ${msg}`]);
    setInput("");

    try {
      if (invoke) {
        const result = await invoke("run_pipeline", { prompt: msg, skillDir: "skills" });
        setMessages((prev) => [...prev, `${result}`]);
      } else {
        setMessages((prev) => [...prev, `[PM Agent] 已收到: "${msg}". (模拟模式 — 启动 --chat 获得真实响应)`]);
      }
    } catch (e: any) {
      setMessages((prev) => [...prev, `[错误] ${e}`]);
    }
  }, [input]);

  return (
    <div style={styles.container}>
      <div style={styles.titleBar}>
        <span style={styles.title}>Tree-SOP Agent</span>
        <span style={styles.subtitle}>群聊式多 Agent 协作平台</span>
        <span style={styles.agentsBadge}>{agents.length} Agent</span>
      </div>
      <div style={styles.main}>
        <div style={styles.sidebar}>
          <div style={styles.sidebarHeader}>Agent 团队</div>
          <div style={styles.agentList}>
            {agents.map((agent) => (
              <div key={agent.name} style={styles.agentCard}>
                <span style={styles.agentIcon}>{getAgentIcon(agent.name)}</span>
                <div style={styles.agentInfo}>
                  <div style={styles.agentName}>{agent.name}</div>
                  <div style={styles.agentDesc}>{agent.description}</div>
                </div>
                <span style={{ ...styles.agentModel, background: agent.model === "pro" ? "#1a3a5c" : "#2d4a2d" }}>
                  {getAgentModelBadge(agent.model)}
                </span>
              </div>
            ))}
          </div>
        </div>
        <div style={styles.center}>
          <div style={styles.chatArea}>
            {messages.map((msg, i) => (
              <div key={i} style={styles.message}>{msg}</div>
            ))}
          </div>
          <div style={styles.bottom}>
            <div style={styles.terminal}>
              <span style={{ color: "#888", fontSize: 12 }}>$ 终端就绪</span>
            </div>
            <div style={styles.inputBar}>
              <input
                style={styles.input}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="输入需求，Agent 团队自动协作..."
              />
              <button style={styles.sendBtn} onClick={handleSend}>→</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: { display: "flex", flexDirection: "column", height: "100vh", background: "#1e1e1e", color: "#ccc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
  titleBar: { display: "flex", alignItems: "center", gap: 12, padding: "8px 16px", background: "#2d2d2d", borderBottom: "1px solid #3c3c3c", userSelect: "none" },
  title: { fontSize: 14, fontWeight: 600, color: "#fff" },
  subtitle: { fontSize: 12, color: "#888" },
  agentsBadge: { marginLeft: "auto", fontSize: 11, background: "#3c3c3c", padding: "2px 8px", borderRadius: 10 },
  main: { display: "flex", flex: 1, overflow: "hidden" },
  sidebar: { width: 280, background: "#252526", borderRight: "1px solid #3c3c3c", display: "flex", flexDirection: "column" },
  sidebarHeader: { padding: "10px 14px", fontSize: 11, fontWeight: 600, textTransform: "uppercase", color: "#888", borderBottom: "1px solid #3c3c3c", letterSpacing: 1 },
  agentList: { overflow: "auto", flex: 1 },
  agentCard: { display: "flex", alignItems: "center", gap: 10, padding: "8px 14px", borderBottom: "1px solid #2a2a2a", cursor: "pointer" },
  agentIcon: { fontSize: 18, flexShrink: 0 },
  agentInfo: { flex: 1, minWidth: 0 },
  agentName: { fontSize: 13, fontWeight: 500, color: "#4fc1ff" },
  agentDesc: { fontSize: 11, color: "#888", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  agentModel: { fontSize: 10, padding: "1px 6px", borderRadius: 8, color: "#ccc", flexShrink: 0 },
  center: { flex: 1, display: "flex", flexDirection: "column" },
  chatArea: { flex: 1, padding: 16, overflow: "auto", fontSize: 13, lineHeight: 1.6 },
  message: { marginBottom: 8, whiteSpace: "pre-wrap" },
  bottom: { borderTop: "1px solid #3c3c3c" },
  terminal: { height: 120, padding: 12, background: "#1a1a1a", fontFamily: "monospace", fontSize: 12, overflow: "auto" },
  inputBar: { display: "flex", padding: 8, gap: 8, background: "#2d2d2d", borderTop: "1px solid #3c3c3c" },
  input: { flex: 1, padding: "8px 12px", background: "#3c3c3c", border: "1px solid #555", color: "#ccc", borderRadius: 4, fontSize: 13, outline: "none" },
  sendBtn: { padding: "8px 16px", background: "#0078d4", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 14, fontWeight: 600 },
};

export default App;
