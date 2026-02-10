# timer_cui

Rich-based CLI countdown timer with large ASCII-art time display.

## Features
- Large dot-matrix time display (`mm:ss` or `hh:mm:ss`)
- Progress bar and percent complete
- Pause/Resume controls from the keyboard
- Flexible duration formats (`90`, `2m30s`, `00:10`, `1:02:03`)

## Requirements
- Python 3.10+
- `rich`

## Install
This project uses a `src/` layout. Install in editable mode:

```bash
uv sync
```

## Usage
Run the timer with a duration:

```bash
uv run timer 3m9s
uv run timer 90
uv run timer 00:10
uv run timer 1:02:03
```

Optional label and refresh tick:

```bash
uv run timer 5m --label "Focus"
uv run timer 10m --tick 0.2
```

## Controls
- `space` / `p`: pause or resume
- `s`: start (resume when paused)
- `q`: quit

## Customize ASCII Art
The digit glyphs live in `src/glyphs.py`. Edit `BIG_GLYPHS` to change the design.
