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
        """返回 MCP 协议格式的可用工具列表（含视觉/图像工具）。"""
        try:
            from ..adapters.mcp_protocol import MCPServer
            from ..core.skill_registry import SkillRegistry
            registry = SkillRegistry()
            skills_dir = Path("skills")
            if skills_dir.exists():
                registry.register_skill_dir(str(skills_dir))
                registry.load_all()
            server = MCPServer(registry)
            tools = server.list_tools()
            # 附加内置工具（接线 VisionTool / ImageReader）
            tools.extend([
                {"name": "vision.describe_image", "description": "描述图片内容（本地视觉引擎）"},
                {"name": "image.read", "description": "读取图片并返回描述（OpenAI视觉）"},
            ])
            return {"tools": tools}
        except Exception as e:
            return {"tools": [], "error": str(e)}

    class MCPCallRequest(BaseModel):
        name: str
        arguments: Dict[str, Any] = {}

    @app.post("/mcp/call")
    async def mcp_call_tool(req: MCPCallRequest):
        """调用指定 Agent 工具。"""
        try:
            from ..adapters.mcp_protocol import MCPServer
            from ..core.skill_registry import SkillRegistry
            registry = SkillRegistry()
            skills_dir = Path("skills")
            if skills_dir.exists():
                registry.register_skill_dir(str(skills_dir))
                registry.load_all()
            server = MCPServer(registry)
            result = server.call_tool(req.name, req.arguments)
            # 内置视觉/图像工具（接线 VisionTool + ImageReader）
            if req.name == "vision.describe_image":
                from ..contrib.vision_tool import VisionTool
                vt = VisionTool()
                result = vt.run(req.arguments.get("path", ""))
            elif req.name == "image.read":
                from ..contrib.image_reader import ImageReader
                ir = ImageReader()
                result = ir.read(req.arguments.get("path", ""), req.arguments.get("prompt", "请详细描述这张图片的内容"))
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    from fastapi.responses import StreamingResponse

    @app.post("/stream")
    async def stream_endpoint(prompt: str = ""):
        """SSE 流式端点 — 逐节点返回执行事件。"""
        from ..orchestrator.dispatcher import Dispatcher
        from ..core.skill_registry import SkillRegistry
        from ..core.agent_factory import AgentFactory
        from ..adapters.streaming import StreamManager, StreamEvent
        registry = SkillRegistry()
        sd = Path("skills")
        if sd.exists():
            registry.register_skill_dir(str(sd))
            registry.load_all()
        factory = AgentFactory(registry)
        d = Dispatcher(registry, factory)
        stream = StreamManager()
        queue = []

        async def event_generator():
            def subscribe():
                q: list = []
                stream._subscribers.append(q)
                return q
            q = subscribe()
            import asyncio
            for event in d.handle_stream(prompt):
                stream.publish(event.get("event", "node"), event)
                while q:
                    yield str(q.pop(0))
                await asyncio.sleep(0.01)
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

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

    # ---- FastAPI 增强端点 (IDEA-035) ----

    @app.get("/health")
    async def health():
        """健康检查 + 版本信息。"""
        return {
            "status": "ok",
            "version": "v0.6.3",
            "sessions_active": len(_sessions),
        }

    @app.post("/approve")
    async def approve(session_id: str):
        """HITL 批准节点继续执行。"""
        from ..orchestrator.sop_runner import SOPRunner
        runner = SOPRunner()
        node = runner.approve(session_id)
        if node:
            return {"status": "approved", "node": node}
        raise HTTPException(status_code=404, detail="No pending HITL session")

    @app.post("/reject")
    async def reject(session_id: str):
        """HITL 拒绝节点，跳过执行。"""
        from ..orchestrator.sop_runner import SOPRunner
        runner = SOPRunner()
        node = runner.reject(session_id)
        if node:
            return {"status": "rejected", "node": node}
        raise HTTPException(status_code=404, detail="No pending HITL session")

    @app.get("/sessions")
    async def list_sessions():
        """查看所有活跃 session。"""
        return {"sessions": [{"id": k, "status": v.get("status")} for k, v in _sessions.items()]}

    # ---- End FastAPI 增强 ----

    def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
        """启动 FastAPI 服务。"""
        import uvicorn
        uvicorn.run(app, host=host, port=port)

except ImportError:
    logger.warning("FastAPI 未安装，独立部署模式不可用。安装: pip install fastapi uvicorn")

    def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
        raise ImportError("FastAPI 未安装，请运行: pip install fastapi uvicorn")
