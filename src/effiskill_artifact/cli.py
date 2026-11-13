from __future__ import annotations

import argparse
import importlib
import sys
from types import ModuleType


COMMAND_CHOICES = [
    "pairs-to-traces",
    "extract-skills",
    "build-registry",
    "infer",
    "reproduce-rq1",
    "reproduce-rq4",
    "reproduce-paper",
]


def _dispatch(module: ModuleType, argv: list[str]) -> None:
    prev = sys.argv[:]
    try:
        sys.argv = [module.__name__] + argv
        module.main()
    finally:
        sys.argv = prev


def _import_module(name: str) -> ModuleType:
    try:
        return importlib.import_module(f".{name}", __package__)
    except ModuleNotFoundError as exc:
        missing_name = getattr(exc, "name", "") or ""
        if missing_name.startswith("effiskill_artifact"):
            raise
        raise SystemExit(
            "Missing optional dependency for this command. "
            'Install the full pipeline extras with `python -m pip install -e ".[full]"` '
            f"and retry. Missing module: {missing_name}"
        ) from exc


def _load_command_module(command: str, language: str) -> ModuleType:
    module_name = {
        ("pairs-to-traces", "python"): "pairs_to_traces",
        ("pairs-to-traces", "cpp"): "pairs_to_traces_cpp",
        ("extract-skills", "python"): "extract_skills",
        ("extract-skills", "cpp"): "extract_skills_cpp",
        ("build-registry", "python"): "build_registry",
        ("build-registry", "cpp"): "build_registry_cpp",
        ("infer", "python"): "infer_noexec",
        ("infer", "cpp"): "infer_noexec_cpp",
        ("reproduce-rq1", "python"): "paper_rq1",
        ("reproduce-rq4", "python"): "paper_rq4",
    }.get((command, language))
    if module_name is None:
        raise RuntimeError(f"Unsupported command/language combination: {command} / {language}")
    return _import_module(module_name)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="effiskill-artifact",
        description="EffiSkill optimization baseline and archived-result reconstruction. "
        "Commands: " + ", ".join(COMMAND_CHOICES),
        add_help=False,
    )
    parser.add_argument("command", nargs="?")
    parser.add_argument("--language", choices=["python", "cpp"], default="python")
    parser.add_argument("-h", "--help", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args, remainder = parser.parse_known_args(argv)
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]

    if args.command is None:
        parser.print_help()
        if args.help:
            return
        raise SystemExit("Missing command.")

    if args.command not in COMMAND_CHOICES:
        parser.error(f"argument command: invalid choice: {args.command!r} (choose from {', '.join(COMMAND_CHOICES)})")

    if args.help:
        remainder = ["--help"] + remainder

    if args.command == "pairs-to-traces":
        module = _load_command_module(args.command, args.language)
        _dispatch(module, remainder)
        return

    if args.command == "extract-skills":
        module = _load_command_module(args.command, args.language)
        _dispatch(module, remainder)
        return

    if args.command == "build-registry":
        module = _load_command_module(args.command, args.language)
        _dispatch(module, remainder)
        return

    if args.command == "infer":
        module = _load_command_module(args.command, args.language)
        _dispatch(module, remainder)
        return

    if args.command == "reproduce-rq1":
        _dispatch(_load_command_module(args.command, "python"), remainder)
        return

    if args.command == "reproduce-rq4":
        _dispatch(_load_command_module(args.command, "python"), remainder)
        return

    if args.command == "reproduce-paper":
        _load_command_module("reproduce-rq1", "python").main(remainder)
        _load_command_module("reproduce-rq4", "python").main(remainder)
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
