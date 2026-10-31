"""Command-line entry point for Log Sentry."""

import argparse
import sys
from pathlib import Path

from log_sentry.analyzer import Alert, analyze
from log_sentry.journal import read_input, read_journal


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect Linux journal entries for critical and repeated errors."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="read journalctl-style JSON-lines from a file instead of the system journal",
    )
    parser.add_argument(
        "--since",
        default="1 hour ago",
        help='journal time range, for example "30 minutes ago" (default: 1 hour ago)',
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=1000,
        help="maximum number of recent journal entries to read (default: 1000)",
    )
    parser.add_argument(
        "--repeat-threshold",
        type=int,
        default=5,
        help="error-level entries per service needed to trigger a repeated-error alert",
    )
    return parser


def _print_alert(alert: Alert) -> None:
    print(f"[{alert.severity}] {alert.title}: {alert.details}")


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.lines < 1:
        parser.error("--lines must be greater than zero")
    if args.repeat_threshold < 1:
        parser.error("--repeat-threshold must be greater than zero")

    try:
        entries = read_input(args.input) if args.input else read_journal(args.since, args.lines)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"log-sentry: {error}", file=sys.stderr)
        return 1

    alerts = analyze(entries, args.repeat_threshold)
    print(f"Analyzed {len(entries)} entries; found {len(alerts)} alert(s).")
    if alerts:
        for alert in alerts:
            _print_alert(alert)
        return 1
    print("No anomalies detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
