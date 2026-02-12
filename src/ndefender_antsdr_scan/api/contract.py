from __future__ import annotations

from dataclasses import dataclass

SOURCE = "antsdr"

EVENT_TYPES = {
    "RF_CONTACT_NEW",
    "RF_CONTACT_UPDATE",
    "RF_CONTACT_LOST",
}


@dataclass(frozen=True)
class Envelope:
    type: str
    timestamp: int
    source: str
    data: dict


def make_envelope(event_type: str, timestamp_ms: int, data: dict) -> dict:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported event type: {event_type}")
    return {
        "type": event_type,
        "timestamp": int(timestamp_ms),
        "source": SOURCE,
        "data": data,
    }
