# log-sentry
log-sentry is a lightweight, hybrid terminal utility designed to ingest Linux system logs, parse anomaly metrics in Python, and trigger high-priority system alerts or TUI dashboards.

## Getting started

Log Sentry currently reads recent systemd journal entries and reports critical
messages and services producing repeated errors. It uses Python's standard
library and requires Python 3.10 or newer.

Install it from the repository:

```bash
python -m pip install .
```

Run against the last hour of journal entries:

```bash
log-sentry
```

You can change the time range and repeated-error threshold:

```bash
log-sentry --since "30 minutes ago" --repeat-threshold 10 --lines 2000
```

To try it without system journal access, create a JSON-lines file (one journal
entry object per line) and pass it with `--input`:

```bash
log-sentry --input sample.jsonl
```

The command exits with status `1` when it finds alerts or encounters an error,
and `0` when no anomalies are found. Run the tests with:

```bash
python -m unittest discover -s tests
```
