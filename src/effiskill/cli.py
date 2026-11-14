"""``effiskill`` command-line entry point."""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from types import ModuleType

USAGE = """\
usage: effiskill <command> [--language python|cpp] [options]

Stage II - skill-guided optimization (needs an LLM endpoint):
  infer             generate up to 8 candidates per task with the frozen skill library
  export            turn `infer` output into EffiBench-X candidate files (rank_1..8.json)

Data:
  fetch-tasks       download the EffiBench-X tasks into a task CSV

Evaluation:
  score             OPT@1..8 from EffiBench-X public/private evaluation statistics

Stage I - skill mining (needs an LLM endpoint):
  pairs-to-traces   extract structured traces from slow/fast program pairs
  extract-skills    cluster traces and induce Operator Skill cards
  build-registry    rebuild registry.json from a directory of SKILL.md cards

Run `effiskill <command> --help` for the options of a command.
"""

MODULES = {
    ("infer", "python"): "inference.python",
    ("infer", "cpp"): "inference.cpp",
    ("pairs-to-traces", "python"): "mining.pairs_to_traces",
    ("pairs-to-traces", "cpp"): "mining.pairs_to_traces_cpp",
    ("extract-skills", "python"): "mining.extract_skills",
    ("extract-skills", "cpp"): "mining.extract_skills_cpp",
}


def _import(name: str) -> ModuleType:
    try:
        return importlib.import_module(f"effiskill.{name}")
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "") or ""
        if missing.startswith("effiskill"):
            raise
        raise SystemExit(
            f"Missing optional dependency '{missing}'. Install the pipeline extras: "
            "python -m pip install -e '.[pipeline]'"
        ) from exc


def _run_script_module(module: ModuleType, prog: str, argv: list[str]) -> None:
    """Run a module whose ``main()`` parses ``sys.argv``."""
    saved = sys.argv[:]
    try:
        sys.argv = [prog] + argv
        module.main()
    finally:
        sys.argv = saved


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(USAGE)
        return
    command, rest = argv[0], argv[1:]

    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--language", choices=["python", "cpp"], default="python")
    known, rest_without = pre.parse_known_args(rest)
    if rest_without and rest_without[0] == "--":
        rest_without = rest_without[1:]

    prog = f"effiskill {command}"
    if command in {"infer", "pairs-to-traces", "extract-skills"}:
        module = _import(MODULES[(command, known.language)])
        _run_script_module(module, f"{prog} --language {known.language}", rest_without)
    elif command == "build-registry":
        _run_script_module(_import("mining.build_registry"), prog, rest_without)
    elif command == "export":
        _import("export").main(rest)
    elif command == "fetch-tasks":
        _import("fetch_tasks").main(rest)
    elif command == "score":
        _import("scoring").main(rest)
    else:
        print(USAGE, file=sys.stderr)
        raise SystemExit(f"effiskill: unknown command {command!r}")


if __name__ == "__main__":
    main()
