from __future__ import annotations

import re
import sys
import time
from typing import Annotated, Any

import typer

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text

from glyphs import BIG_GLYPHS

if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty
    msvcrt = None


DURATION_PATTERN = re.compile(
    r"^\s*(?:(?P<hours>\d+)h)?\s*(?:(?P<minutes>\d+)m)?\s*(?:(?P<seconds>\d+)s)?\s*$",
    re.IGNORECASE,
)

def parse_duration(value: str) -> int:
    value = value.strip()
    if not value:
        raise ValueError("Empty duration")

    if ":" in value:
        parts = [p.strip() for p in value.split(":")]
        if not all(part.isdigit() for part in parts):
            raise ValueError(f"Invalid time format: {value}")
        numbers = [int(part) for part in parts]
        if len(numbers) == 2:
            minutes, seconds = numbers
            return minutes * 60 + seconds
        if len(numbers) == 3:
            hours, minutes, seconds = numbers
            return hours * 3600 + minutes * 60 + seconds
        raise ValueError(f"Invalid time format: {value}")

    if value.isdigit():
        return int(value)

    match = DURATION_PATTERN.match(value)
    if not match:
        raise ValueError(f"Invalid duration: {value}")

    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_time(total_seconds: float) -> str:
    total_seconds = max(0, int(total_seconds + 0.5))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def render_big_time(time_str: str) -> Text:
    lines = [""] * len(BIG_GLYPHS["0"])
    gap = "░"
    for idx in range(len(lines)):
        lines[idx] = gap
    for ch in time_str:
        glyph = BIG_GLYPHS.get(ch, BIG_GLYPHS[" "])
        for idx, row in enumerate(glyph):
            lines[idx] += f"{row}{gap}"
    rendered = "\n".join(lines)
    return Text(rendered, style="bold bright_cyan", justify="center")


def build_header(label: str, remaining: float, total: float, paused: bool) -> Panel:
    percent = 0 if total == 0 else min(100.0, (1 - remaining / total) * 100)
    time_text = render_big_time(format_time(remaining))
    status = "Paused" if paused else "Running"
    status_style = "bold yellow" if paused else "bold green"
    sub = Text(f"{label}  |  {percent:5.1f}%  |  {status}", style="bold white")
    sub.stylize(status_style, sub.plain.rfind(status), len(sub.plain))
    hint = Text("Controls: [space]/p pause, s start, q quit", style="dim")
    return Panel(Group(time_text, sub, hint), title="Timer", border_style="bright_blue")


class KeyReader:
    def __init__(self) -> None:
        self._use_windows = sys.platform == "win32"
        self._fd: int | None = None
        self._old_settings: list[Any] | None = None

    def __enter__(self) -> "KeyReader":
        if not self._use_windows:
            self._fd = sys.stdin.fileno()
            self._old_settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if (
            not self._use_windows
            and self._fd is not None
            and self._old_settings is not None
        ):
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)

    def read_key(self) -> str | None:
        if self._use_windows and msvcrt is not None:
            if msvcrt.kbhit():
                return msvcrt.getwch()
            return None
        if select.select([sys.stdin], [], [], 0)[0]:
            return sys.stdin.read(1)
        return None


def validate_duration(seconds: int) -> None:
    if seconds <= 0:
        raise ValueError("Duration must be greater than 0")


app = typer.Typer(help="Rich CLI timer")


def run_timer(duration: int, label: str, tick: float) -> None:
    console = Console()
    progress = Progress(
        TextColumn("[bold]Progress[/bold]"),
        BarColumn(bar_width=None),
        TextColumn("{task.percentage:>5.1f}%"),
        console=console,
        expand=True,
    )
    task_id = progress.add_task("timer", total=duration)

    start = time.monotonic()
    elapsed_before_pause = 0.0
    paused = False
    with Live(
        refresh_per_second=max(4, int(1 / max(tick, 0.05))), console=console
    ) as live:
        with KeyReader() as keys:
            while True:
                now = time.monotonic()
                key = keys.read_key()
                if key:
                    key = key.lower()
                    if key in {"q"}:
                        return
                    if key in {"p", " "}:
                        if paused:
                            start = now
                            paused = False
                        else:
                            elapsed_before_pause += now - start
                            paused = True
                    if key in {"s"} and paused:
                        start = now
                        paused = False

                if paused:
                    elapsed = elapsed_before_pause
                else:
                    elapsed = elapsed_before_pause + (now - start)

                remaining = duration - elapsed
                progress.update(task_id, completed=min(elapsed, duration))
                live.update(
                    Group(build_header(label, remaining, duration, paused), progress)
                )
                if remaining <= 0:
                    break
                time.sleep(tick)

    console.print(Panel(Text("Time's up!", style="bold green"), border_style="green"))


@app.command(epilog="Examples: timer 90, timer 2m30s, timer 00:10")
def main(
    duration: Annotated[str, typer.Argument(help="Duration (seconds, 2m30s, or mm:ss)")],
    label: Annotated[str, typer.Option("--label", "-l", help="Label text")] = "Countdown",
    tick: Annotated[float, typer.Option(help="Refresh interval seconds")] = 0.1,
) -> None:
    try:
        seconds = parse_duration(duration)
        validate_duration(seconds)
    except ValueError as exc:
        raise typer.BadParameter(str(exc))

    if tick <= 0:
        raise typer.BadParameter("--tick must be greater than 0")

    run_timer(seconds, label, tick)


if __name__ == "__main__":
    app()
