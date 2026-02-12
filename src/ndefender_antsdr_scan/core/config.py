from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

import yaml

from ndefender_antsdr_scan.core.radio import RadioConfig
from ndefender_antsdr_scan.api.ws_client import WsClientConfig
from ndefender_antsdr_scan.classification.profiles import ProfileSet, load_profiles
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
    classification_profiles: ProfileSet | None
    hop_window_ms: int
    min_hop_hz: float
    api: "ApiConfig"


@dataclass(frozen=True)
class ApiConfig:
    enabled: bool = False
    bind: str = "127.0.0.1"
    port: int = 8890
    api_key: str | None = None
    max_clients: int = 25
    event_buffer: int = 500


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    raw = _load_yaml(config_path)

    radio = raw.get("radio", {})
    tracker = raw.get("tracker", {})
    correlation = raw.get("correlation", {})
    detector = raw.get("detector", {})
    sweep = raw.get("sweep", {})
    ws = raw.get("ws", {})
    classification = raw.get("classification", {})
    api = raw.get("api", {})

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
            correlation_enabled=bool(correlation.get("enabled", False)),
            correlation_window_ms=int(correlation.get("window_ms", 100)),
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
        classification_profiles=_load_classification_profiles(config_path, classification),
        hop_window_ms=int(classification.get("hop_window_ms", 1000)),
        min_hop_hz=float(classification.get("min_hop_hz", 200000.0)),
        api=ApiConfig(
            enabled=_env_bool("API_ENABLED", bool(api.get("enabled", False))),
            bind=_env_str("API_BIND", str(api.get("bind", "127.0.0.1"))),
            port=_env_int("API_PORT", int(api.get("port", 8890))),
            api_key=_env_str("API_KEY", api.get("api_key")) or None,
            max_clients=_env_int("API_MAX_CLIENTS", int(api.get("max_clients", 25))),
            event_buffer=_env_int("API_EVENT_BUFFER", int(api.get("event_buffer", 500))),
        ),
    )


def _load_classification_profiles(config_path: Path, classification: dict[str, Any]) -> ProfileSet | None:
    profiles_path = classification.get("profiles")
    if not profiles_path:
        return None
    path = (config_path.parent / profiles_path).resolve()
    return load_profiles(path)


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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _env_str(name: str, default: str | None) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw


def _band_from_dict(entry: dict[str, Any]) -> BandPlan:
    return BandPlan(
        name=str(entry.get("name", "")),
        start_hz=float(entry.get("start_hz", 0.0)),
        stop_hz=float(entry.get("stop_hz", 0.0)),
        step_hz=float(entry.get("step_hz", 0.0)),
    )
