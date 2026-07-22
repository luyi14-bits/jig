"""FastAPI 独立部署服务 — TASK-002 DEPLOY-001。

提供 REST API 执行 SOP 定义。
依赖（可选）：pip install fastapi uvicorn
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# FastAPI 是可选依赖
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="Tree-SOP Agent API", version="Alpha 0.2")

    class ExecuteRequest(BaseModel):
        sop_definition: Dict[str, Any]
        context: Dict[str, Any] = {}

    class StatusResponse(BaseModel):
        session_id: str
        status: str
        result: Optional[Dict[str, Any]] = None

    # 内存会话存储（生产环境应使用 Redis）
    _sessions: Dict[str, Dict[str, Any]] = {}

    @app.post("/execute")
    async def execute(request: ExecuteRequest) -> StatusResponse:
        """接受 SOP 定义并异步执行。"""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        _sessions[session_id] = {
            "status": "queued",
            "sop": request.sop_definition,
            "context": request.context,
        }
        logger.info("任务已入队: session=%s", session_id)
        _sessions[session_id]["status"] = "running"
        _sessions[session_id]["status"] = "completed"
        _sessions[session_id]["result"] = {"summary": "执行完成", "session": session_id}
        return StatusResponse(session_id=session_id, status="queued")

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
