"""
Data Processing Example — Jig-powered data analysis pipeline.

Demonstrates using Jig to analyze and transform structured data.
"""
from jig import Jig

app = Jig(skills_dir="./skills")

def analyze_dataset(description: str) -> str:
    prompt = f"Analyze this dataset description and suggest processing steps:\n\n{description}"
    return app.run(prompt)

if __name__ == "__main__":
    result = analyze_dataset("CSV with 10k rows, columns: date, revenue, user_id, region")
    print(f"Analysis: {result}")
