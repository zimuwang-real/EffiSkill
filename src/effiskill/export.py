"""Convert ``effiskill infer`` output into EffiBench-X candidate files.

Writes one JSON file per candidate slot, ``rank_<k>.json`` with
``{problem_id: {lang_key: code}}``, plus the input programs
(``original.json`` for Python, ``canonical_cpp.json`` for C++). This is the
layout the paper's runs were evaluated from; feed it to the EffiBench-X
evaluator and score the resulting statistics with ``effiskill score``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

LANG_KEY = {"python": "python3", "cpp": "cpp"}
ORIGINAL_NAME = {"python": "original.json", "cpp": "canonical_cpp.json"}


def iter_records(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def export_candidates(runs: Path, out_dir: Path, language: str, field: str = "candidates", k: int = 8) -> dict[str, int]:
    lang_key = LANG_KEY[language]
    slots: list[dict[str, dict[str, str]]] = [{} for _ in range(k)]
    originals: dict[str, dict[str, str]] = {}
    seen: dict[str, dict] = {}
    for record in iter_records(runs):
        problem_id = record.get("problem_id")
        if not problem_id:
            continue
        # With --resume, a retried task may appear more than once; keep the last record.
        seen[problem_id] = record

    for problem_id, record in seen.items():
        if record.get("slow_code"):
            originals[problem_id] = {lang_key: record["slow_code"]}
        candidates = record.get(field) or []
        for index, candidate in enumerate(candidates[:k]):
            code = candidate.get("code") if isinstance(candidate, dict) else None
            if isinstance(code, str) and code.strip():
                slots[index][problem_id] = {lang_key: code}

    out_dir.mkdir(parents=True, exist_ok=True)
    for index, slot in enumerate(slots, start=1):
        (out_dir / f"rank_{index}.json").write_text(json.dumps(slot, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / ORIGINAL_NAME[language]).write_text(json.dumps(originals, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"tasks": len(seen), **{f"rank_{i}": len(s) for i, s in enumerate(slots, start=1)}}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="effiskill export", description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=Path, required=True, help="JSONL written by `effiskill infer`.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--language", choices=["python", "cpp"], required=True)
    parser.add_argument(
        "--field",
        choices=["candidates", "survivor_candidates"],
        default="candidates",
        help="Which candidate list fills the slots (paper: candidates, except the Qwen/Python run).",
    )
    parser.add_argument("--k", type=int, default=8)
    args = parser.parse_args(argv)
    counts = export_candidates(args.runs, args.out_dir, args.language, args.field, args.k)
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
