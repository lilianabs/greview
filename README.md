# greview

Offline AI code review powered by local Ollama models. Review your staged git changes instantly without sending code to external services.

## Quick Start

### Prerequisites
- Python 3.13+
- [Ollama](https://ollama.ai) running locally (default: `http://localhost:11434`)

### Installation
```bash
# Install dependencies with uv
uv sync
```

### Usage
```bash
# Review your staged changes
python greview.py review

# Use a specific model
python greview.py review --model gemma2:7b
```

Stage your changes with `git add`, then run `greview` to get a categorized report of:
- **BLOCKER** — bugs, security issues, logic errors
- **SUGGESTION** — design concerns, unclear naming
- **NIT** — style and formatting

The tool exits with code 1 if blockers are found, making it suitable for pre-commit hooks.

## How It Works

1. Fetches your staged diff
2. Splits it by file
3. Sends each file to Ollama for review
4. Parses structured findings and displays them with color-coding

See [CLAUDE.md](CLAUDE.md) for architecture details and design decisions.