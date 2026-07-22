"""Tree-SOP Agent 启动入口 — 纯终端 CLI 模式。

双击或命令行执行 → 进入群聊模式，不上网页。
"""

import sys
import os
from pathlib import Path

# 确保项目根在 sys.path
BASE = Path(__file__).parent.resolve()
os.chdir(BASE)
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "src"))

# ── 默认 skill 目录 ──
SKILL_DIR = BASE / "skills"
if not SKILL_DIR.exists():
    SKILL_DIR = Path(r"D:\Desktop\skill\skills")

print("=" * 50)
print("  Tree-SOP Agent — 纯终端群聊模式")
print(f"  Skills: {SKILL_DIR}")
print("=" * 50)

# ── 启动 Dispatcher ──
from jig.orchestrator.dispatcher import Dispatcher

dispatcher = Dispatcher(skill_dir=str(SKILL_DIR))
print(f"  已加载 {dispatcher.registry.count()} 个 Agent\n")

# ── 群聊循环 ──
while True:
    try:
        user_input = input("> ")
        if user_input.lower() in ("exit", "quit", "q"):
            print("Bye!")
            break
        result = dispatcher.handle(user_input)
        print(f"  {result}")
    except KeyboardInterrupt:
        print("\nBye!")
        break
