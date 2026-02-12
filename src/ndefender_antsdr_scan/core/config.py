from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ndefender_antsdr_scan.core.radio import RadioConfig
from ndefender_antsdr_scan.api.ws_client import WsClientConfig
from ndefender_antsdr_scan.core.sweep import BandPlan
from ndefender_antsdr_scan.detectors.peak import PeakDetectorConfig
from ndefender_antsdr_scan.tracking.tracker import TrackerConfig


@dataclass(frozen=True)
class SweepConfig:
    bands: list[BandPlan]
    dwell_ms: int = 0


@dataclass(frozen=True)
class AppConfig:
    radio: RadioConfig
    tracker: TrackerConfig
    detector: PeakDetectorConfig
    sweep: SweepConfig
    ws: WsClientConfig


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = _load_yaml(config_path)

    radio = raw.get("radio", {})
    tracker = raw.get("tracker", {})
    detector = raw.get("detector", {})
    sweep = raw.get("sweep", {})
    ws = raw.get("ws", {})

    bands = _load_bands(config_path, sweep)

    return AppConfig(
        radio=RadioConfig(
            uri=str(radio.get("uri", "")),
            sample_rate=int(radio.get("sample_rate", 0)),
            rx_buffer_size=int(radio.get("rx_buffer_size", 4096)),
        ),
        tracker=TrackerConfig(
            bucket_hz=int(tracker.get("bucket_hz", 0)),
            ttl_s=float(tracker.get("ttl_s", 0)),
            min_hits_to_confirm=int(tracker.get("min_hits_to_confirm", 0)),
            update_interval_s=float(tracker.get("update_interval_s", 0)),
        ),
        detector=PeakDetectorConfig(
            min_snr_db=float(detector.get("min_snr_db", 0.0)),
            lo_guard_hz=float(detector.get("lo_guard_hz", 0.0)),
        ),
        sweep=SweepConfig(
            bands=bands,
            dwell_ms=int(sweep.get("dwell_ms", 0)),
        ),
        ws=WsClientConfig(
            url=str(ws.get("url", "")),
            enabled=bool(ws.get("enabled", False)),
            connect_timeout_s=float(ws.get("connect_timeout_s", 5.0)),
            send_timeout_s=float(ws.get("send_timeout_s", 2.0)),
            max_retries=int(ws.get("max_retries", 3)),
            retry_backoff_s=float(ws.get("retry_backoff_s", 1.0)),
        ),
    )


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("config root must be a mapping")
    return data


def _load_bands(config_path: Path, sweep: dict[str, Any]) -> list[BandPlan]:
    bands: list[BandPlan] = []

    for entry in sweep.get("bands", []) or []:
        bands.append(_band_from_dict(entry))

    for plan_path in sweep.get("plans", []) or []:
        plan_file = (config_path.parent / plan_path).resolve()
        plan_data = _load_yaml(plan_file)
        if isinstance(plan_data, dict) and "bands" in plan_data:
            plan_bands = plan_data.get("bands", []) or []
        else:
            plan_bands = plan_data if isinstance(plan_data, list) else []
        for entry in plan_bands:
            bands.append(_band_from_dict(entry))

    return bands


def _band_from_dict(entry: dict[str, Any]) -> BandPlan:
    return BandPlan(
        name=str(entry.get("name", "")),
        start_hz=float(entry.get("start_hz", 0.0)),
        stop_hz=float(entry.get("stop_hz", 0.0)),
        step_hz=float(entry.get("step_hz", 0.0)),
    )
