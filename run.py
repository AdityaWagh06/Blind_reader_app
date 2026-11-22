#!/usr/bin/env python3
"""Launcher: checks Python and dependencies, then starts the website (python app.py)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

REQUIRED = {"torch": "torch", "transformers": "transformers", "PIL": "pillow",
            "fastapi": "fastapi", "uvicorn": "uvicorn", "multipart": "python-multipart"}


def main():
    if sys.version_info < (3, 9):  # noqa: UP036 - friendly message instead of a syntax error
        print(f"Python 3.9 or higher is required (you have {sys.version.split()[0]}).")
        return 1
    missing = [pkg for module, pkg in REQUIRED.items() if importlib.util.find_spec(module) is None]
    if missing:
        print("Missing packages: " + ", ".join(missing))
        print("Install them with:  pip install -r requirements.txt")
        return 1
    print("Starting Blind Reader Assistant at http://127.0.0.1:8000  (Ctrl+C to stop)")
    try:
        return subprocess.call([sys.executable, "app.py"], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
