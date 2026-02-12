import argparse
import sys

from ndefender_antsdr_scan.version import __version__
from ndefender_antsdr_scan.cli.helpers import (
    build_engine,
    iter_live_frames,
    load_app_config,
    null_live_frames,
    run_replay,
    run_stats,
)
from ndefender_antsdr_scan.events.validate import validate_jsonl


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_app_config(args.config)
    if not config.sweep.bands:
        print("no sweep bands configured; add sweep.bands or sweep.plans to config")
        return 2
    engine, _emitter = build_engine(config)
    try:
        frame_iter = null_live_frames(config) if args.null_radio else iter_live_frames(config)
        processed = 0
        for frame in frame_iter:
            engine.process_frame(frame)
            processed += 1
            if args.max_frames > 0 and processed >= args.max_frames:
                break
    except KeyboardInterrupt:
        print("shutdown requested")
    finally:
        engine.flush()
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    config = load_app_config(args.config)
    engine, emitter = build_engine(config, jsonl_path=args.output)
    stats = run_replay(args.log, engine, emitter)
    print(f"replayed {stats['frames']} frames")
    print(f"emitted {stats['events_emitted']} events")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_jsonl(args.log)
    if errors:
        for err in errors:
            print(f"line {err.line}: {err.message}")
        print(f"validation failed: {len(errors)} error(s)")
        return 1
    print("validation ok")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    stats = run_stats(args.log)
    print(f"total events: {stats['total']}")
    print("counts:")
    for event_type, count in stats["counts"].items():
        print(f"  {event_type}: {count}")
    if stats["last_timestamp"] is not None:
        print(f"last timestamp: {stats['last_timestamp']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ndefender-antsdr-scan")
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run live AntSDR scan")
    run.add_argument("--config", required=True, help="Path to config YAML")
    run.add_argument(
        "--null-radio",
        action="store_true",
        help="Use a null radio for dry runs (no hardware required)",
    )
    run.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after N frames (0 = run continuously)",
    )
    run.set_defaults(func=_cmd_run)

    replay = subparsers.add_parser("replay", help="Replay a JSONL log")
    replay.add_argument("--log", required=True, help="Path to JSONL log")
    replay.add_argument(
        "--config",
        default="config/default.yaml",
        help="Path to config YAML (for detector/tracker settings)",
    )
    replay.add_argument(
        "--output",
        default=None,
        help="Optional JSONL output path (defaults to system log)",
    )
    replay.set_defaults(func=_cmd_replay)

    validate = subparsers.add_parser("validate", help="Validate a JSONL log")
    validate.add_argument("--log", required=True, help="Path to JSONL log")
    validate.set_defaults(func=_cmd_validate)

    stats = subparsers.add_parser("stats", help="Summarize a JSONL log")
    stats.add_argument("--log", required=True, help="Path to JSONL log")
    stats.set_defaults(func=_cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
