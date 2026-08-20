import requests
import subprocess

OLLAMA_URL = "http://localhost:11434/api/generate"

REVIEW_PROMPT = """You are a code review assistant. Review the following code diff.

Only comment on lines that were added or removed (prefixed with + or -). Do not
comment on unchanged context lines.

Output one finding per line, in this exact format: SEVERITY|LOCATION|MESSAGE

Severity levels:
- BLOCKER = bugs, security issues, or logic errors that will cause failures
- SUGGESTION = unclear naming, missing error handling, design concerns
- NIT = style, formatting, trivial wording

Example: BLOCKER|validate_token()|Missing null check before dereferencing user

If there are no issues, output exactly: CLEAN|-|No issues found.

Be concise. Do not include any other text, explanation, or preamble.

Diff:
"""

def call_ollama(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    
    response = requests.post(OLLAMA_URL, json=payload, verify=False)
    if response.status_code == 200:
        return response.json().get("response", "")
    
    return f"Error: {response.status_code} - {response.text}"


def get_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True)
    return result.stdout


if __name__ == "__main__":
    
    diff = get_diff()
    prompt = REVIEW_PROMPT + diff
    
    result = call_ollama("gemma2:2b", prompt)
    print(result)
