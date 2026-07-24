"""FastAPI 独立部署服务。

提供 REST API + MCP 协议执行 SOP 管道。
依赖（可选）：pip install fastapi uvicorn
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# FastAPI 是可选依赖
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="Jig Agent Firewall API", version="v0.6.0")

    class ExecuteRequest(BaseModel):
        prompt: str = ""
        context: Dict[str, Any] = {}

    class StatusResponse(BaseModel):
        session_id: str
        status: str
        result: Optional[Dict[str, Any]] = None

    # 内存会话存储（生产环境应使用 Redis）
    _sessions: Dict[str, Dict[str, Any]] = {}

    @app.post("/execute")
    async def execute(request: ExecuteRequest) -> StatusResponse:
        """接受用户输入并执行 SOP 管道。"""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        _sessions[session_id] = {"status": "running", "prompt": request.prompt, "context": request.context}
        logger.info("任务已入队: session=%s", session_id)
        try:
            from ..orchestrator.dispatcher import Dispatcher
            from ..core.skill_registry import SkillRegistry
            from ..core.agent_factory import AgentFactory
            registry = SkillRegistry()
            skills_dir = Path("skills")
            if skills_dir.exists():
                registry.register_skill_dir(str(skills_dir))
                registry.load_all()
            factory = AgentFactory(registry)
            d = Dispatcher(registry, factory)
            result = d.handle(request.prompt)
            _sessions[session_id]["status"] = "completed"
            _sessions[session_id]["result"] = {"summary": result, "session": session_id}
        except Exception as e:
            logger.error("执行失败: %s", e)
            _sessions[session_id]["status"] = "failed"
            _sessions[session_id]["result"] = {"error": str(e)}
        return StatusResponse(session_id=session_id, status=_sessions[session_id]["status"], result=_sessions[session_id].get("result"))

    @app.get("/mcp/tools")
    async def list_mcp_tools():
        """返回 MCP 协议格式的可用工具列表。"""
        try:
            from ..adapters.mcp_protocol import MCPServer
            from ..core.skill_registry import SkillRegistry
            registry = SkillRegistry()
            skills_dir = Path("skills")
            if skills_dir.exists():
                registry.register_skill_dir(str(skills_dir))
                registry.load_all()
            server = MCPServer(registry)
            return {"tools": server.list_tools()}
        except Exception as e:
            return {"tools": [], "error": str(e)}

    @app.get("/status/{session_id}")
    async def get_status(session_id: str) -> StatusResponse:
        """查询执行状态。"""
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return StatusResponse(
            session_id=session_id,
            status=session["status"],
            result=session.get("result"),
        )

    def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
        """启动 FastAPI 服务。"""
        import uvicorn
        uvicorn.run(app, host=host, port=port)

except ImportError:
    logger.warning("FastAPI 未安装，独立部署模式不可用。安装: pip install fastapi uvicorn")

    def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
        raise ImportError("FastAPI 未安装，请运行: pip install fastapi uvicorn")
