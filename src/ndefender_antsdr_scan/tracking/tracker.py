from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Callable

from .models import Observation, ContactState, FeatureHints


@dataclass(frozen=True)
class TrackerConfig:
    bucket_hz: int
    ttl_s: float
    min_hits_to_confirm: int
    update_interval_s: float


class Tracker:
    def __init__(self, config: TrackerConfig, time_ms_provider: Callable[[], int] | None = None) -> None:
        self._config = config
        self._contacts: dict[int, ContactState] = {}
        self._time_ms_provider = time_ms_provider

    def ingest(self, observations: Iterable[Observation], now_ms: int | None = None) -> list[dict]:
        obs_list = list(observations)
        if now_ms is None:
            if obs_list:
                now_ms = max(obs.timestamp_ms for obs in obs_list)
            else:
                now_ms = self._now_ms()

        events: list[dict] = []
        for obs in obs_list:
            events.extend(self._handle_observation(obs))

        events.extend(self._expire(now_ms))
        return events

    def _handle_observation(self, obs: Observation) -> list[dict]:
        bucket_value_hz = self._bucketize(obs.freq_hz)
        contact = self._contacts.get(bucket_value_hz)
        if contact is None:
            contact = ContactState(
                id=f"rf:{bucket_value_hz}",
                bucket_value_hz=bucket_value_hz,
                band=obs.band,
                bandwidth_class=obs.bandwidth_class,
                hit_count=0,
                confirmed=False,
                first_seen_ms=obs.timestamp_ms,
                last_seen_ms=obs.timestamp_ms,
                last_update_emitted_ms=None,
                last_emitted_snr_db=obs.snr_db,
                last_snr_db=obs.snr_db,
                freq_hz=obs.freq_hz,
                peak_db=obs.peak_db,
                noise_floor_db=obs.noise_floor_db,
                confidence=self._confidence_from_snr(obs.snr_db),
                features=obs.features,
            )
            self._contacts[bucket_value_hz] = contact

        contact.hit_count += 1
        contact.last_seen_ms = obs.timestamp_ms
        contact.last_snr_db = obs.snr_db
        contact.freq_hz = obs.freq_hz
        contact.peak_db = obs.peak_db
        contact.noise_floor_db = obs.noise_floor_db
        contact.band = obs.band
        contact.bandwidth_class = obs.bandwidth_class
        contact.features = obs.features
        contact.confidence = self._confidence_from_snr(obs.snr_db)

        if not contact.confirmed:
            if contact.hit_count >= self._config.min_hits_to_confirm:
                contact.confirmed = True
                contact.last_update_emitted_ms = obs.timestamp_ms
                contact.last_emitted_snr_db = obs.snr_db
                return [self._make_event("RF_CONTACT_NEW", obs.timestamp_ms, contact)]
            return []

        if self._should_update(contact, obs):
            contact.last_update_emitted_ms = obs.timestamp_ms
            contact.last_emitted_snr_db = obs.snr_db
            return [self._make_event("RF_CONTACT_UPDATE", obs.timestamp_ms, contact)]

        return []

    def _expire(self, now_ms: int) -> list[dict]:
        ttl_ms = int(self._config.ttl_s * 1000)
        expired: list[int] = []
        events: list[dict] = []
        for bucket_value_hz, contact in self._contacts.items():
            if now_ms - contact.last_seen_ms >= ttl_ms:
                expired.append(bucket_value_hz)
                if contact.confirmed:
                    events.append(self._make_event("RF_CONTACT_LOST", now_ms, contact))
        for bucket_value_hz in expired:
            self._contacts.pop(bucket_value_hz, None)
        return events

    def _should_update(self, contact: ContactState, obs: Observation) -> bool:
        if contact.last_update_emitted_ms is None:
            return True
        interval_ms = int(self._config.update_interval_s * 1000)
        interval_elapsed = obs.timestamp_ms - contact.last_update_emitted_ms >= interval_ms
        snr_change = abs(obs.snr_db - contact.last_emitted_snr_db) > 2.0
        return interval_elapsed or snr_change

    def _bucketize(self, freq_hz: float) -> int:
        size = self._config.bucket_hz
        if size <= 0:
            raise ValueError("bucket_hz must be positive")
        return int(freq_hz // size) * size

    def _now_ms(self) -> int:
        if self._time_ms_provider is None:
            raise ValueError("now_ms required when no time provider is configured")
        return int(self._time_ms_provider())

    @staticmethod
    def _confidence_from_snr(snr_db: float) -> float:
        if snr_db <= 0:
            return 0.0
        if snr_db >= 50:
            return 1.0
        return snr_db / 50.0

    @staticmethod
    def _make_event(event_type: str, timestamp_ms: int, contact: ContactState) -> dict:
        class_path = contact.features.class_path
        return {
            "type": event_type,
            "timestamp": int(timestamp_ms),
            "source": "antsdr",
            "data": {
                "id": contact.id,
                "freq_hz": contact.freq_hz,
                "bucket_hz": contact.bucket_value_hz,
                "band": contact.band,
                "snr_db": contact.last_snr_db,
                "peak_db": contact.peak_db,
                "noise_floor_db": contact.noise_floor_db,
                "bandwidth_class": contact.bandwidth_class,
                "confidence": contact.confidence,
                "features": {
                    "prominence_db": contact.features.prominence_db,
                    "cluster_size": contact.features.cluster_size,
                    "pattern_hint": contact.features.pattern_hint,
                    "hop_hint": contact.features.hop_hint,
                    "class_path": class_path if class_path else [],
                    "classification_confidence": contact.features.classification_confidence or 0.0,
                },
            },
        }


def make_observation(
    freq_hz: float,
    band: str,
    snr_db: float,
    peak_db: float,
    noise_floor_db: float,
    bandwidth_class: str,
    features: FeatureHints,
    timestamp_ms: int,
) -> Observation:
    return Observation(
        freq_hz=freq_hz,
        band=band,
        snr_db=snr_db,
        peak_db=peak_db,
        noise_floor_db=noise_floor_db,
        bandwidth_class=bandwidth_class,
        features=features,
        timestamp_ms=timestamp_ms,
    )
