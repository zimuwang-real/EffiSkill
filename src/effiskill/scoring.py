"""OPT@k scoring for EffiBench-X evaluation outputs.

This is the exact metric used in the paper (Eq. 1-2). A *run directory* holds
the evaluator statistics for one method in one model/language setting::

    <run_dir>/public/stats_rank_<i>.json     # one file per candidate slot i
    <run_dir>/private/stats_rank_<i>.json
    <run_dir>/private/stats_original.json     # input program (Python)
    <run_dir>/private/stats_canonical_cpp.json  # input program (C++)

Each stats file maps ``problem_id -> {lang_key: {"passed": bool, "runtime_sum": float, ...}}``
where ``lang_key`` is ``python3`` or ``cpp`` (the EffiBench-X evaluator format).

For every task, candidates that pass the *public* tests are ranked by public
``runtime_sum``. A task counts as optimized at k when one of the first k ranked
candidates passes the *private* tests with
``private_runtime(original) / private_runtime(candidate) >= 1.10``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

TOPK_VALUES = tuple(range(1, 9))
SPEEDUP_THRESHOLD = 1.10
LANG_KEYS = {"python": "python3", "python3": "python3", "cpp": "cpp", "c++": "cpp"}
ORIGINAL_FILENAMES = ("stats_original.json", "stats_canonical_cpp.json", "stats_canonical.json")


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def lang_entry(entry: dict | None, lang_key: str) -> dict:
    if not isinstance(entry, dict):
        return {}
    return entry.get(lang_key) or {}


def runtime(entry: dict | None, lang_key: str) -> float | None:
    value = lang_entry(entry, lang_key).get("runtime_sum")
    return float(value) if value is not None else None


def passed(entry: dict | None, lang_key: str) -> bool:
    return bool(lang_entry(entry, lang_key).get("passed"))


def original_filename(lang_key: str) -> str:
    return "stats_canonical_cpp.json" if lang_key == "cpp" else "stats_original.json"


def find_original(private_dir: Path, lang_key: str) -> Path:
    preferred = private_dir / original_filename(lang_key)
    if preferred.exists():
        return preferred
    for name in ORIGINAL_FILENAMES:
        if (private_dir / name).exists():
            return private_dir / name
    raise FileNotFoundError(f"no input-program stats ({', '.join(ORIGINAL_FILENAMES)}) in {private_dir}")


def collect_candidate_paths(split_dir: Path, lang_key: str) -> dict[int, Path]:
    orig_names = set(ORIGINAL_FILENAMES)
    candidate_paths: list[tuple[int, Path]] = []
    for path in split_dir.glob("*.json"):
        if path.name in orig_names:
            continue
        for prefix in ("stats_rank_", "stats_direct_"):
            if path.name.startswith(prefix):
                candidate_paths.append((int(path.name[len(prefix) : -5]), path))
                break
    return dict(sorted(candidate_paths))


def improvement_ratio(original_runtime: float | None, candidate_runtime: float | None, is_correct: bool = True) -> float:
    if original_runtime is None or candidate_runtime is None or not is_correct:
        return 1.0
    return max(original_runtime / candidate_runtime, 1.0)


def problem_family(problem_id: str) -> str:
    return problem_id.split("_", 1)[0]


def score_run(run_dir: Path, lang_key: str) -> pd.DataFrame:
    """Per-task frame with candidate outcomes and ``top{k}_ratio`` / ``top{k}_opt``."""
    run_dir = Path(run_dir)
    lang_key = LANG_KEYS.get(lang_key, lang_key)
    private_dir = run_dir / "private"
    public_dir = run_dir / "public"
    original_private = load_json(find_original(private_dir, lang_key))
    rank_private = {i: load_json(p) for i, p in collect_candidate_paths(private_dir, lang_key).items()}
    rank_public = {i: load_json(p) for i, p in collect_candidate_paths(public_dir, lang_key).items()}

    rows: list[dict] = []
    for problem_id in sorted(original_private):
        original_runtime = runtime(original_private.get(problem_id), lang_key)
        row = {"problem_id": problem_id, "family": problem_family(problem_id), "original_runtime": original_runtime}

        public_valid: list[tuple[int, float]] = []
        for rank_index in sorted(rank_public):
            public_entry = rank_public[rank_index].get(problem_id)
            private_entry = rank_private.get(rank_index, {}).get(problem_id)
            public_pass = passed(public_entry, lang_key)
            private_pass = passed(private_entry, lang_key)
            public_runtime = runtime(public_entry, lang_key)
            private_runtime = runtime(private_entry, lang_key)

            row[f"rank_{rank_index}_public_pass"] = public_pass
            row[f"rank_{rank_index}_private_pass"] = private_pass
            row[f"rank_{rank_index}_public_runtime"] = public_runtime
            row[f"rank_{rank_index}_private_runtime"] = private_runtime
            row[f"rank_{rank_index}_private_ratio"] = improvement_ratio(original_runtime, private_runtime, private_pass)

            if public_pass and public_runtime is not None:
                public_valid.append((rank_index, public_runtime))

        public_valid.sort(key=lambda item: item[1])
        ranked_candidates = [rank_index for rank_index, _ in public_valid]
        row["public_rank_order"] = "|".join(f"rank_{rank_index}" for rank_index in ranked_candidates)

        for k in TOPK_VALUES:
            ratios = [row[f"rank_{rank_index}_private_ratio"] for rank_index in ranked_candidates[:k]]
            row[f"top{k}_ratio"] = max(ratios, default=1.0)
            row[f"top{k}_opt"] = float(row[f"top{k}_ratio"] >= SPEEDUP_THRESHOLD)

        rows.append(row)

    return pd.DataFrame(rows)


def summarize(frame: pd.DataFrame) -> dict[str, float]:
    out: dict[str, float] = {"tasks": float(len(frame))}
    for k in TOPK_VALUES:
        out[f"OPT@{k}"] = float(frame[f"top{k}_opt"].mean() * 100.0) if len(frame) else 0.0
    return out


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="effiskill score",
        description="Compute OPT@1..8 from EffiBench-X public/private evaluation statistics.",
    )
    parser.add_argument("run_dirs", nargs="+", type=Path, help="Run directories containing public/ and private/.")
    parser.add_argument("--language", choices=["python", "cpp"], required=True)
    parser.add_argument("--per-task-csv", type=Path, default=None, help="Optional per-task output (one row per run and task).")
    args = parser.parse_args(argv)

    lang_key = LANG_KEYS[args.language]
    rows = []
    frames = []
    for run_dir in args.run_dirs:
        frame = score_run(run_dir, lang_key)
        rows.append({"run": str(run_dir), **summarize(frame)})
        frames.append(frame.assign(run=str(run_dir)) if len(args.run_dirs) > 1 else frame)
    if args.per_task_csv is not None:
        args.per_task_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.concat(frames, ignore_index=True).to_csv(args.per_task_csv, index=False)
    table = pd.DataFrame(rows)
    table["tasks"] = table["tasks"].astype(int)
    with pd.option_context("display.float_format", "{:.2f}".format, "display.width", 200):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
