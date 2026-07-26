"""
Web Tool Example — Jig-powered code review assistant.

Demonstrates using Jig's SOP pipeline through a web interface.
"""
from jig import Jig
import json

app = Jig(skills_dir="./skills")

def review_code(code_snippet: str) -> str:
    """Send code for review through the SOP pipeline."""
    prompt = f"Review this code for security and quality issues:\n\n```python\n{code_snippet}\n```"
    return app.run(prompt)

if __name__ == "__main__":
    sample = "def login(password):\n    return eval(password)"
    print("Reviewing sample code...")
    result = review_code(sample)
    print(f"Result: {result}")
