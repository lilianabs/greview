import subprocess
import sys

import click
import requests

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

SEVERITY_STYLE = {
    "BLOCKER": ("red", "✗"),
    "SUGGESTION": ("yellow", "!"),
    "NIT": ("cyan", "·"),
}


def call_ollama(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()
    return response.json()["response"]


def get_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def split_diff_by_file(diff_text: str) -> dict[str, str]:
    """Split a unified diff into {filename: diff_chunk} pairs."""
    chunks = {}
    current_file = None
    current_lines = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            if current_file and current_lines:
                chunks[current_file] = "\n".join(current_lines)
            # "diff --git a/path b/path" -> take the b/ path
            parts = line.split(" b/")
            current_file = parts[-1] if len(parts) > 1 else line
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_file and current_lines:
        chunks[current_file] = "\n".join(current_lines)

    return chunks


def parse_findings(txt: str) -> list[dict]:
    findings = []

    for line in txt.splitlines():
        line = line.strip()
        line = line.lstrip("+-").strip()

        if not line or "|" not in line:
            continue

        parts = line.split("|")
        if len(parts) != 3:
            continue

        severity, location, message = (p.strip() for p in parts)

        if severity not in ("BLOCKER", "SUGGESTION", "NIT"):
            continue

        findings.append({"severity": severity, "location": location, "message": message})

    return findings


def print_report(results: dict[str, list[dict]]):
    total = sum(len(findings) for findings in results.values())
    blockers = sum(
        1 for findings in results.values() for f in findings if f["severity"] == "BLOCKER"
    )

    if total == 0:
        click.echo(click.style("✓ No issues found. Clean diff.", fg="green", bold=True))
        return

    for filename, findings in results.items():
        if not findings:
            continue
        click.echo()
        click.echo(click.style(filename, bold=True, underline=True))
        for f in findings:
            color, icon = SEVERITY_STYLE[f["severity"]]
            label = click.style(f"{icon} {f['severity']}", fg=color, bold=True)
            click.echo(f"  {label}  {f['location']}: {f['message']}")

    click.echo()
    click.echo("-" * 40)
    summary_color = "red" if blockers else "yellow"
    click.echo(
        click.style(
            f"{total} finding(s) across {len([f for f in results.values() if f])} file(s)"
            + (f"  ·  {blockers} blocker(s)" if blockers else ""),
            fg=summary_color,
            bold=True,
        )
    )


@click.group()
def cli():
    """greview - offline AI code review powered by Gemma via Ollama."""
    pass


@cli.command()
@click.option("--model", default="gemma2:2b", help="Ollama model to use.")
def review(model):
    """Review the current staged git diff."""
    diff_text = get_diff()

    if not diff_text.strip():
        click.echo("No staged changes to review. Stage some with `git add`.")
        return

    file_chunks = split_diff_by_file(diff_text)

    results = {}
    with click.progressbar(file_chunks.items(), label="Reviewing files") as bar:
        for filename, chunk in bar:
            prompt = REVIEW_PROMPT + "\n" + chunk
            raw_response = call_ollama(model, prompt)
            results[filename] = parse_findings(raw_response)

    print_report(results)

    has_blockers = any(
        f["severity"] == "BLOCKER" for findings in results.values() for f in findings
    )
    if has_blockers:
        sys.exit(1)


if __name__ == "__main__":
    cli()
