import React, { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";

interface Agent { name: string; description: string; model: string; status: string; }
interface MCP { name: string; url: string; }

const AGENT_ICONS: Record<string, string> = {
  dispatcher: "\uD83D\uDD00", pm: "\uD83D\uDCCB", spec: "\uD83D\uDCD0", coding: "\uD83D\uDCBB",
  "code-review": "\uD83D\uDD0D", tdd: "\uD83E\uDDEA", acceptance: "\u2705", security: "\uD83D\uDD12",
  devops: "\uD83D\uDE80", secretary: "\uD83D\uDCC1", trinity: "\uD83C\uDF93", loop: "\uD83D\uDD04",
};

const FALLBACK_AGENTS: Agent[] = [
  { name: "Dispatcher", description: "群聊入口", model: "pro", status: "就绪" },
  { name: "PM", description: "产品经理", model: "pro", status: "就绪" },
  { name: "Spec-Pipeline", description: "管线工程师", model: "pro", status: "就绪" },
  { name: "Coding", description: "编码实现", model: "flash", status: "就绪" },
  { name: "Code-Review", description: "代码审查", model: "pro", status: "就绪" },
  { name: "TDD", description: "测试", model: "flash", status: "就绪" },
  { name: "Acceptance", description: "验收", model: "flash", status: "就绪" },
  { name: "Security", description: "安全审计", model: "pro", status: "就绪" },
  { name: "DevOps", description: "构建发布", model: "flash", status: "就绪" },
  { name: "Secretary", description: "留痕看板", model: "flash", status: "就绪" },
  { name: "LOOP SOP", description: "总调度", model: "pro", status: "监控" },
];

function getAgentIcon(name: string): string {
  const lower = name.toLowerCase();
  for (const [key, icon] of Object.entries(AGENT_ICONS)) if (lower.includes(key)) return icon;
  return "\uD83E\uDD16";
}

const SettingsPanel: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [tab, setTab] = useState<"api" | "mcp" | "skills">("api");
  const [apiKey, setApiKey] = useState("");
  const [mcpName, setMcpName] = useState("");
  const [mcpUrl, setMcpUrl] = useState("");
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [savedMsg, setSavedMsg] = useState("");

  useEffect(() => {
    (async () => {
      const raw = await invoke("getConfig");
      try {
        const c = JSON.parse(raw as string);
        if (c.deepseek_api_key) setApiKey(c.deepseek_api_key);
        if (c.mcp_servers) setMcps(c.mcp_servers);
      } catch {}
      const skillsRaw = await invoke("listSkills", { skillDir: "skills" });
      try { const s = JSON.parse(skillsRaw as string); setAgents(s); } catch {}
    })();
  }, []);

  function saveApiKey(val) {
    const k = typeof val === 'string' ? val : apiKey;
    if (!k) { setSavedMsg("Key cannot be empty"); return; }
    invoke("saveApiKey", { value: k }).then(function() {
      setApiKey(k);
      setSavedMsg("Saved");
      setTimeout(function() { setSavedMsg(""); }, 2000);
    }).catch(function(e) {
      setSavedMsg("Save failed: " + e);
    });
  };

  const addMcp = async () => {
    if (!mcpName || !mcpUrl) { setSavedMsg("Name and URL required"); return; }
    try {
      const raw = await invoke("addMcpServer", { name: mcpName, url: mcpUrl });
      try { setMcps(JSON.parse(raw as string)); } catch {}
      setMcpName(""); setMcpUrl("");
      setSavedMsg("MCP Server added");
      setTimeout(function() { setSavedMsg(""); }, 2000);
    } catch(e) {
      setSavedMsg("MCP Error: " + e);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: "100%", padding: "10px 14px", margin: "6px 0",
    background: "#3c3c3c", border: "1px solid #555", color: "#ccc",
    borderRadius: 6, fontSize: 13, outline: "none", boxSizing: "border-box",
  };
  const btnStyle: React.CSSProperties = {
    padding: "8px 20px", background: "#0078d4", color: "#fff",
    border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13, fontWeight: 600, marginRight: 8,
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid #3c3c3c" }}>
        {(["api", "mcp", "skills"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{ flex: 1, padding: "12px 0", background: tab === t ? "#2d2d2d" : "#1e1e1e",
              color: tab === t ? "#fff" : "#888", border: "none", cursor: "pointer", fontSize: 13, fontWeight: tab === t ? 600 : 400 }}>
            {t === "api" ? "API Key" : t === "mcp" ? "MCP Server" : "Skills"}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, padding: 20, overflow: "auto" }}>
        {tab === "api" && (
          <div>
            <div style={{ marginBottom: 6, fontSize: 12, color: "#888" }}>DeepSeek API Key</div>
            <input style={inputStyle} type="password" placeholder="sk-..." value={apiKey}
              onChange={(e) => setApiKey(e.target.value)} />
            <button style={btnStyle} onClick={() => saveApiKey()}>{savedMsg || "Save"}</button>
            {apiKey && <button style={{ ...btnStyle, background: "#555" }} onClick={() => { setApiKey(""); saveApiKey(""); }}>Clear</button>}
            {savedMsg && <span style={{ marginLeft: 10, fontSize: 12, color: savedMsg.includes("Error") || savedMsg.includes("failed") ? "#ff6b6b" : "#4caf50" }}>{savedMsg}</span>}
          </div>
        )}
        {tab === "mcp" && (
          <div>
            <div style={{ marginBottom: 6, fontSize: 12, color: "#888" }}>{mcps.length} MCP Server(s)</div>
            {mcps.map((m, i) => (
              <div key={i} style={{ padding: "8px 12px", background: "#2a2a2a", borderRadius: 6, marginBottom: 6, fontSize: 13 }}>
                <span style={{ color: "#4fc1ff" }}>{m.name}</span>
                <span style={{ color: "#888", marginLeft: 12 }}>{m.url}</span>
              </div>
            ))}
            <div style={{ fontSize: 12, color: "#888", marginTop: 16 }}>Add MCP Server</div>
            <input style={inputStyle} placeholder="Name (e.g. web-search)" value={mcpName} onChange={(e) => setMcpName(e.target.value)} />
            <input style={inputStyle} placeholder="URL or command" value={mcpUrl} onChange={(e) => setMcpUrl(e.target.value)} />
            <button style={btnStyle} onClick={addMcp}>Add</button>
          </div>
        )}
        {tab === "skills" && (
          <div>
            <div style={{ marginBottom: 6, fontSize: 12, color: "#888" }}>{agents.length} Skills Loaded</div>
            {agents.map((a, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", background: "#2a2a2a", borderRadius: 6, marginBottom: 6 }}>
                <span style={{ fontSize: 16 }}>{getAgentIcon(a.name)}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: "#4fc1ff" }}>{a.name}</div>
                  <div style={{ fontSize: 11, color: "#888" }}>{a.description || a.model}</div>
                </div>
                <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: a.model === "pro" ? "#1a3a5c" : "#2d4a2d", color: "#ccc" }}>
                  {a.model === "pro" ? "Pro" : "Flash"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>(["Dispatcher ready."]);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const raw = await invoke("listSkills", { skillDir: "skills" });
        const parsed = JSON.parse(raw as string);
        if (parsed.length > 0) { setAgents(parsed.map((a: any) => ({ ...a, description: "", status: "ready" }))); return; }
      } catch {}
      setAgents(FALLBACK_AGENTS);
    })();
  }, []);

  const handleSend = useCallback(async () => {
    if (!input.trim()) return;
    const msg = input; setInput("");
    setMessages((p) => [...p, `> ${msg}`]);
    try {
        const result = await invoke("runPipeline", { prompt: msg, skillDir: "skills" });
        setMessages((p) => [...p, `${result}`]);
    } catch (e: any) { setMessages((p) => [...p, `[Error] ${e}`]); }
  }, [input]);

  if (showSettings) {
    return (
      <div style={styles.container}>
        <div style={styles.titleBar}>
          <span style={styles.title}>Settings</span>
          <span style={styles.agentsBadge}><button onClick={() => setShowSettings(false)} style={{ background: "none", border: "none", color: "#ccc", cursor: "pointer", fontSize: 12 }}>Back</button></span>
        </div>
        <SettingsPanel onClose={() => setShowSettings(false)} />
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.titleBar}>
        <span style={styles.title}>AgentHarness</span>
        <span style={styles.subtitle}>Multi-Agent Chat</span>
        <span style={styles.agentsBadge}>{agents.length} Agents</span>
        <button onClick={() => setShowSettings(true)} style={{ background: "none", border: "none", color: "#888", cursor: "pointer", fontSize: 18, padding: "0 4px" }}>⚙</button>
      </div>
      <div style={styles.main}>
        <div style={styles.sidebar}>
          <div style={styles.sidebarHeader}>Agent Team</div>
          <div style={styles.agentList}>
            {agents.map((a) => (
              <div key={a.name} style={styles.agentCard}>
                <span style={styles.agentIcon}>{getAgentIcon(a.name)}</span>
                <div style={styles.agentInfo}>
                  <div style={styles.agentName}>{a.name}</div>
                  <div style={styles.agentDesc}>{a.description}</div>
                </div>
                <span style={{ ...styles.agentModel, background: a.model === "pro" ? "#1a3a5c" : "#2d4a2d" }}>{a.model === "pro" ? "Pro" : "Flash"}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={styles.center}>
          <div style={styles.chatArea}>
            {messages.map((msg, i) => (<div key={i} style={styles.message}>{msg}</div>))}
          </div>
          <div style={styles.bottom}>
            <div style={styles.terminal}><span style={{ color: "#888", fontSize: 12 }}>$ terminal ready</span></div>
            <div style={styles.inputBar}>
              <input style={styles.input} value={input} onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()} placeholder="Type a request..." />
              <button style={styles.sendBtn} onClick={handleSend}>Send</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: { display: "flex", flexDirection: "column", height: "100vh", background: "#1e1e1e", color: "#ccc", fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", fontSize: 13 },
  titleBar: { display: "flex", alignItems: "center", gap: 10, padding: "8px 14px", background: "#2d2d2d", borderBottom: "1px solid #3c3c3c", userSelect: "none" },
  title: { fontSize: 14, fontWeight: 600, color: "#fff" },
  subtitle: { fontSize: 11, color: "#666" },
  agentsBadge: { marginLeft: "auto", fontSize: 11, background: "#3c3c3c", padding: "2px 8px", borderRadius: 10, display: "flex", alignItems: "center", gap: 6 },
  main: { display: "flex", flex: 1, overflow: "hidden" },
  sidebar: { width: 240, background: "#252526", borderRight: "1px solid #3c3c3c", display: "flex", flexDirection: "column", flexShrink: 0 },
  sidebarHeader: { padding: "10px 14px", fontSize: 10, fontWeight: 600, textTransform: "uppercase", color: "#888", borderBottom: "1px solid #3c3c3c", letterSpacing: 1 },
  agentList: { overflow: "auto", flex: 1 },
  agentCard: { display: "flex", alignItems: "center", gap: 8, padding: "7px 12px", borderBottom: "1px solid #2a2a2a" },
  agentIcon: { fontSize: 16, flexShrink: 0 },
  agentInfo: { flex: 1, minWidth: 0 },
  agentName: { fontSize: 12, fontWeight: 500, color: "#4fc1ff" },
  agentDesc: { fontSize: 10, color: "#666", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" },
  agentModel: { fontSize: 9, padding: "1px 6px", borderRadius: 8, color: "#ccc", flexShrink: 0 },
  center: { flex: 1, display: "flex", flexDirection: "column", minWidth: 0 },
  chatArea: { flex: 1, padding: 14, overflow: "auto", fontSize: 13, lineHeight: 1.5 },
  message: { marginBottom: 6, whiteSpace: "pre-wrap" },
  bottom: { borderTop: "1px solid #3c3c3c", flexShrink: 0 },
  terminal: { height: 100, padding: 10, background: "#1a1a1a", fontFamily: "monospace", fontSize: 11, overflow: "auto" },
  inputBar: { display: "flex", padding: 8, gap: 8, background: "#2d2d2d", borderTop: "1px solid #3c3c3c" },
  input: { flex: 1, padding: "8px 12px", background: "#3c3c3c", border: "1px solid #555", color: "#ccc", borderRadius: 4, fontSize: 13, outline: "none" },
  sendBtn: { padding: "8px 18px", background: "#0078d4", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 13, fontWeight: 600 },
};

export default App;
