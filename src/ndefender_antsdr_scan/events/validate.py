import json
from dataclasses import dataclass
from importlib import resources
from typing import Iterable

import jsonschema


@dataclass(frozen=True)
class ValidationError:
    line: int
    message: str


def _load_schema() -> dict:
    schema_path = resources.files("ndefender_antsdr_scan.events").joinpath("schema.json")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


_SCHEMA = _load_schema()
_VALIDATOR = jsonschema.Draft202012Validator(_SCHEMA)


def validate_event(event: dict) -> None:
    _VALIDATOR.validate(event)


def iter_validation_errors(lines: Iterable[str]) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for idx, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(ValidationError(idx, f"invalid JSON: {exc.msg}"))
            continue
        try:
            validate_event(payload)
        except jsonschema.ValidationError as exc:
            errors.append(ValidationError(idx, exc.message))
    return errors


def validate_jsonl(path: str) -> list[ValidationError]:
    with open(path, "r", encoding="utf-8") as f:
        return iter_validation_errors(f)
