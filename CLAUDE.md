# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**greview** is an offline AI code review tool that uses local Ollama models (e.g., Gemma) to review staged git diffs. It provides categorized findings with severity levels (BLOCKER, SUGGESTION, NIT) and integrates directly with git to minimize context switching.

## Setup & Dependencies

- **Python**: 3.13 (specified in `.python-version`)
- **Package Manager**: `uv` for dependency management (defined in `pyproject.toml`)
- **Core Dependencies**:
  - `click>=8.4.2` — CLI framework for command interface and colored output
  - `requests>=2.34.2` — HTTP client for communicating with Ollama REST API

**Runtime Requirement**: Ollama must be running locally on `http://localhost:11434/api/generate`. The tool is model-agnostic; default is `gemma2:2b`.

## Common Commands

### Running the Code Review
```bash
python greview.py review                    # Review staged changes with default model
python greview.py review --model gemma2:7b  # Use a larger Gemma model
```

The tool:
1. Fetches staged changes via `git diff --staged`
2. Splits the unified diff into per-file chunks
3. Sends each chunk to Ollama with a structured review prompt
4. Parses findings and displays a color-coded report
5. Exits with code 1 if blockers are found (useful for git hooks)

### Testing Individual Functions
```bash
python -c "from greview import parse_findings; print(parse_findings('BLOCKER|func()|Missing check\nSUGGESTION|var|Unclear name'))"
```

## Architecture & Key Patterns

### Main Module Structure (`greview.py`)

The module is organized by responsibility:

1. **HTTP Communication** (`call_ollama`)
   - Posts to Ollama's generate endpoint with `stream: False` for complete responses
   - Extracts the `response` field from JSON

2. **Git Integration** (`get_diff`, `split_diff_by_file`)
   - `get_diff()` captures `git diff --staged` as the authoritative diff source
   - `split_diff_by_file()` parses unified diff format to isolate per-file changes
   - Handles "diff --git a/path b/path" markers to extract target filenames

3. **Finding Parsing** (`parse_findings`)
   - Expects structured output: `SEVERITY|LOCATION|MESSAGE` (one per line)
   - Strips leading `+-` characters (diff context markers) before parsing
   - Only recognizes BLOCKER, SUGGESTION, NIT as valid severities
   - Ignores unparseable lines silently to handle model variance

4. **Presentation** (`print_report`)
   - Groups findings by filename (only shows files with findings)
   - Color-codes by severity: red (BLOCKER), yellow (SUGGESTION), cyan (NIT)
   - Includes summary with blocker count if any exist

5. **CLI** (`cli` group, `review` command)
   - Uses Click's command group pattern for extensibility
   - `--model` option allows switching between Ollama models at runtime
   - Progress bar provides feedback during multi-file reviews

### Design Decisions

- **Per-file review**: Splits diffs to avoid overwhelming single-prompt token limits and to provide file-level granularity in output
- **Exit code 1 on blockers**: Allows use as a git hook to prevent commits with critical issues
- **Prompt format**: Specifies that the model should only comment on added/removed lines, reducing false positives on context
- **Lenient parsing**: The parser ignores malformed output lines rather than failing, since LLM output can vary

## Development Notes

- No test suite exists; new features should be validated manually with `git diff --staged` and inspected for parsing correctness
- The `sample.py`, `sample_2.py`, `sample_3.py` files are scratch/test files not part of the main codebase
- Ollama model choice affects review quality and speed; `gemma2:2b` is quick but less nuanced, `gemma2:7b` is more thorough
- The tool is stateless: each run is independent and pulls the latest staged diff