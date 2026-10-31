"""Read JSON-formatted entries from systemd journal or a fixture file."""

import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


def parse_entries(lines: Iterable[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON on line {line_number}: {error.msg}") from error
        if not isinstance(entry, dict):
            raise ValueError(f"Expected a JSON object on line {line_number}")
        entries.append(entry)
    return entries


def read_input(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as input_file:
        return parse_entries(input_file)


def read_journal(since: str, lines: int) -> list[dict[str, Any]]:
    command = [
        "journalctl",
        "--no-pager",
        "--output=json",
        f"--since={since}",
        f"--lines={lines}",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as error:
        raise RuntimeError("journalctl was not found; use --input with a JSON-lines file") from error
    if result.returncode != 0:
        message = result.stderr.strip() or f"journalctl exited with status {result.returncode}"
        raise RuntimeError(message)
    return parse_entries(result.stdout.splitlines())
