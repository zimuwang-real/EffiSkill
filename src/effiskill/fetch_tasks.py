"""Build an ``effiskill infer`` task CSV from the public EffiBench-X dataset.

The benchmark is not redistributed with EffiSkill. This command downloads the
EffiBench-X Hugging Face dataset at the revision used in the paper and rebuilds
the paper's inputs exactly: the 623 tasks per language listed in
``effiskill/task_ids``, with each task's statement and its EffiBench-X
*canonical runtime* solution as the program to optimize.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

DATASET = "EffiBench/effibench-x"
# Dataset commit "Upload dataset" of 2025-10-22, the data used in the paper.
PAPER_REVISION = "425b58a834b65db44b615cfa57ffd3e2503e07ec"
SOLUTION_KEY = {"python": "python3", "cpp": "cpp"}
COLUMNS = ["id", "source", "title_slug", "description", "solutions"]
FIELDS = ["problem_id", "description", "canonical_solution"]
# sha256 of the paper's inputs (see ``inputs_digest``), to confirm a rebuild is exact.
PAPER_DIGEST = {
    "python": "7fe0ac4a9b315db0737a9032a13f1a85c478b53d070e72d0c3561f2bde0aa83f",
    "cpp": "1b6659b963e9b45660bcaedee073df99b59ce75389b3f42e002984a18a4dc547",
}


def task_id(row: dict) -> str:
    """EffiSkill task ids are ``<source>_<id>_<title_slug>``, e.g. ``atcoder_abc397a_thermometer``."""
    return f"{row['source']}_{row['id']}_{row['title_slug']}"


def paper_task_ids(language: str) -> list[str]:
    path = Path(__file__).with_name("task_ids") / f"effibench_x_{language}.txt"
    return path.read_text(encoding="utf-8").split()


def canonical_runtime_solution(solution: dict | None) -> str | None:
    """The program EffiBench-X stores as the canonical runtime solution.

    Same rule as ``generate_solution.py merge-canonical-solutions`` in the
    EffiBench-X repository (``canonical_runtime.json``): the first code sample in
    ``runtimeDistribution``. This is not the ``code`` field of the dataset.
    """
    if not solution:
        return None
    distribution = json.loads(solution.get("runtimeDistribution") or "[]")
    return next((item[2] for item in distribution if item[2] is not None), None)


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def inputs_digest(rows: list[dict]) -> str:
    payload = sorted([r["problem_id"], r["description"], r["canonical_solution"]] for r in rows)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()


def build_rows(dataset_rows: list[dict], language: str, wanted: set[str] | None) -> list[dict]:
    key = SOLUTION_KEY[language]
    out = []
    for row in dataset_rows:
        pid = task_id(row)
        if wanted is not None and pid not in wanted:
            continue
        code = canonical_runtime_solution((row.get("solutions") or {}).get(key))
        if not code or not code.strip():
            continue
        out.append({
            "problem_id": pid,
            "description": normalize_newlines(row["description"] or ""),
            "canonical_solution": normalize_newlines(code),
        })
    return sorted(out, key=lambda r: r["problem_id"])


def load_rows(revision: str) -> list[dict]:
    try:
        import pyarrow.parquet as pq
        from huggingface_hub import HfApi, HfFileSystem
    except ModuleNotFoundError as exc:
        raise SystemExit("fetch-tasks needs huggingface_hub and pyarrow: python -m pip install -e '.[pipeline]'") from exc

    files = sorted(
        f for f in HfApi().list_repo_files(DATASET, repo_type="dataset", revision=revision) if f.endswith(".parquet")
    )
    fs = HfFileSystem()
    rows: list[dict] = []
    for name in files:
        with fs.open(f"datasets/{DATASET}@{revision}/{name}", "rb") as handle:
            rows.extend(pq.read_table(handle, columns=COLUMNS).to_pylist())
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="effiskill fetch-tasks", description=__doc__.splitlines()[0])
    parser.add_argument("--language", choices=sorted(SOLUTION_KEY), required=True)
    parser.add_argument("--out", type=Path, required=True, help="CSV to write (problem_id, description, canonical_solution)")
    parser.add_argument("--revision", default=PAPER_REVISION, help="Dataset revision to download (default: the paper's)")
    parser.add_argument("--all-tasks", action="store_true", help="Keep every task, not only the 623 evaluated in the paper")
    args = parser.parse_args(argv)

    wanted = None if args.all_tasks else set(paper_task_ids(args.language))
    out_rows = build_rows(load_rows(args.revision), args.language, wanted)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} tasks to {args.out}")
    if wanted is None:
        return
    if len(out_rows) != len(wanted):
        missing = sorted(wanted - {r["problem_id"] for r in out_rows})
        print(f"warning: {len(missing)} paper tasks not found in this revision, e.g. {missing[:3]}", file=sys.stderr)
    elif inputs_digest(out_rows) == PAPER_DIGEST[args.language]:
        print("These are exactly the inputs used in the paper.")
    else:
        print("warning: these inputs differ from the ones used in the paper.", file=sys.stderr)


if __name__ == "__main__":
    main()
