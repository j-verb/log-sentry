"""Simple, explainable anomaly rules for journal entries."""

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Alert:
    severity: str
    title: str
    details: str


def _priority(entry: dict[str, Any]) -> int | None:
    value = entry.get("PRIORITY")
    try:
        priority = int(value)
    except (TypeError, ValueError):
        return None
    return priority if 0 <= priority <= 7 else None


def _service(entry: dict[str, Any]) -> str:
    return str(entry.get("_SYSTEMD_UNIT") or entry.get("SYSLOG_IDENTIFIER") or "unknown")


def analyze(entries: list[dict[str, Any]], repeat_threshold: int = 5) -> list[Alert]:
    """Create alerts for critical entries and repeated error-level entries."""
    alerts: list[Alert] = []
    errors_by_service: Counter[str] = Counter()

    for entry in entries:
        priority = _priority(entry)
        if priority is None:
            continue

        service = _service(entry)
        message = str(entry.get("MESSAGE", "(no message)"))
        if priority <= 2:
            alerts.append(
                Alert("CRITICAL", f"Critical log from {service}", message)
            )
        if priority <= 3:
            errors_by_service[service] += 1

    for service, count in sorted(errors_by_service.items()):
        if count >= repeat_threshold:
            alerts.append(
                Alert(
                    "HIGH",
                    f"Repeated errors from {service}",
                    f"{count} error-level entries found (threshold: {repeat_threshold})",
                )
            )

    return alerts
