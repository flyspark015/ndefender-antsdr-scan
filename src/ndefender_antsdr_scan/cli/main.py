import argparse
import sys

from ndefender_antsdr_scan.version import __version__


def _cmd_run(args: argparse.Namespace) -> int:
    print(f"run not implemented yet: config={args.config}")
    return 0


def _cmd_replay(args: argparse.Namespace) -> int:
    print(f"replay not implemented yet: log={args.log}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    from ndefender_antsdr_scan.events.validate import validate_jsonl

    errors = validate_jsonl(args.log)
    if errors:
        for err in errors:
            print(f"line {err.line}: {err.message}")
        print(f"validation failed: {len(errors)} error(s)")
        return 1
    print("validation ok")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    print(f"stats not implemented yet: log={args.log}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ndefender-antsdr-scan")
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run live AntSDR scan")
    run.add_argument("--config", required=True, help="Path to config YAML")
    run.set_defaults(func=_cmd_run)

    replay = subparsers.add_parser("replay", help="Replay a JSONL log")
    replay.add_argument("--log", required=True, help="Path to JSONL log")
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
