"""Entry point: python -m backspace_tracker [run|history|apps] [--db PATH]."""

from __future__ import annotations

import argparse

from .reporter import render_apps, render_history
from .storage import Storage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backspace-tracker")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["run", "history", "apps"],
        default="run",
        help="run the tracker (default), list saved sessions, or show per-app breakdown",
    )
    parser.add_argument("--db", default=None, help="override the database path")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        from .app import run  # imports pynput; keep history/apps usable without a hook

        run()
        return
    records = Storage(args.db).load_sessions()
    print(render_history(records) if args.command == "history" else render_apps(records))


if __name__ == "__main__":
    main()
