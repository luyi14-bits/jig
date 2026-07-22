"""服务化架构 — FastAPI 异步应用服务。

IDEA-038: 将 FastAPI server 升级为异步执行 + 队列支持。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    app = FastAPI(title="AgentHarness API", version="Alpha 0.2")

    class ExecuteRequest(BaseModel):
        prompt: str
        skill_dir: str = "skills"

    _results: Dict[str, Any] = {}

    @app.post("/execute")
    async def execute(request: ExecuteRequest) -> Dict[str, Any]:
        from forge import AgentHarness
        h = AgentHarness(skills_dir=request.skill_dir)
        result = h.run(request.prompt)
        return {"result": result}

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok", "version": "Alpha 0.2"}

except ImportError:
    app = None
