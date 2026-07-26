"""
Code Review Example — Jig-powered automated code audit.

Demonstrates using Jig's Luyi14-code-review skill for code review.
"""
from jig import Jig

app = Jig(skills_dir="./skills")

def audit_code(file_path: str, code: str) -> str:
    prompt = f"Review {file_path} for bugs, style issues, and security concerns:\n\n```\n{code[:2000]}\n```"
    return app.run(prompt)

if __name__ == "__main__":
    sample = "x = 1\nwhile True:\n    print(x)\n    x += 1"
    result = audit_code("example.py", sample)
    print(f"Review: {result}")
