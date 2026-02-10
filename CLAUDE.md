# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CLI countdown timer with large block-character digit display, built with Python and Rich. Uses `jj` for version control (colocated with git).

## Commands

```bash
# Install dependencies and project (editable)
uv sync

# Run timer
uv run timer 90        # seconds
uv run timer 2m30s     # human-readable
uv run timer 01:30     # mm:ss

# Type check
uv run mypy src/
```

## Architecture

Two source files in `src/` (flat module layout, no package directory):

- **`timer.py`** — Entry point (`main()`). Handles argument parsing, duration formatting, keyboard input (platform-aware), and the Rich Live display loop. The `render_big_time()` function assembles large block-character digits from glyphs.
- **`glyphs.py`** — `BIG_GLYPHS` dict mapping digit/colon characters to 7-row block-art strings using `█` and `░`.

The timer renders into a Rich `Panel` with a `Progress` bar below it. Keyboard controls (space/p=pause, s=start, q=quit) are read via non-blocking `select`/`termios` on Unix or `msvcrt` on Windows.

## Key Details

- Python >=3.10, sole runtime dependency is `rich>=13.0`
- Package manager: `uv` (lockfile: `uv.lock`)
- Entry point registered as `timer` console script via `pyproject.toml`
- `setuptools` build backend with `package-dir = {"" = "src"}`
