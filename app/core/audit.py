from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logger import log_error, log_info


AUDIT_FILE = (
    settings.LOG_DIR / "nexus_audit.jsonl"
)


def _safe(value: Any) -> Any:
    """Convert common objects to JSON-safe values."""

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): _safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            _safe(item)
            for item in value
        ]

    try:
        return str(value)

    except Exception:
        return repr(value)


def audit_event(
    event: str,
    *,
    status: str = "success",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Write one structured event to the NEXUS audit trail.
    """

    record = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event": str(event),
        "status": str(status),
        "details": _safe(
            details or {}
        ),
    }

    try:

        AUDIT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with AUDIT_FILE.open(
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

        log_info(
            f"Audit event recorded: {event}"
        )

    except Exception as error:

        log_error(
            f"Unable to write audit event: {error}"
        )

    return record


def read_audit_events(
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Read the most recent audit events.
    """

    if not AUDIT_FILE.exists():
        return []

    try:

        with AUDIT_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:

            lines = file.readlines()

        events = []

        for line in lines[-limit:]:

            line = line.strip()

            if not line:
                continue

            try:

                events.append(
                    json.loads(line)
                )

            except json.JSONDecodeError:
                continue

        return events

    except Exception as error:

        log_error(
            f"Unable to read audit trail: {error}"
        )

        return []


def clear_audit_events() -> bool:
    """
    Clear the audit trail.
    """

    try:

        if AUDIT_FILE.exists():
            AUDIT_FILE.unlink()

        audit_event(
            "audit_cleared",
            details={
                "reason": "manual_clear"
            },
        )

        return True

    except Exception as error:

        log_error(
            f"Unable to clear audit trail: {error}"
        )

        return False