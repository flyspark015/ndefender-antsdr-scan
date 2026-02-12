import json
from typing import Iterable, Iterator


def read_jsonl(path: str) -> Iterator[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_jsonl(path: str, records: Iterable[dict]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, separators=(",", ":"), ensure_ascii=True))
            f.write("\n")
