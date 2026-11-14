"""Build an ``effiskill infer`` task CSV from the public EffiBench-X dataset.

The benchmark is not redistributed with EffiSkill. This command downloads the
statements and canonical solutions from Hugging Face and keeps the 623 tasks per
language evaluated in the paper (listed in ``effiskill/task_ids``).
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


DATASET = "EffiBench/effibench-x"
SOLUTION_KEY = {"python": "python3", "cpp": "cpp"}
COLUMNS = ["id", "source", "title_slug", "description", "solutions"]


def task_id(row: dict) -> str:
    """EffiSkill task ids are ``<source>_<id>_<title_slug>``, e.g. ``atcoder_abc397a_thermometer``."""
    return f"{row['source']}_{row['id']}_{row['title_slug']}"


def paper_task_ids(language: str) -> list[str]:
    path = Path(__file__).with_name("task_ids") / f"effibench_x_{language}.txt"
    return path.read_text(encoding="utf-8").split()


def load_rows(revision: str | None) -> list[dict]:
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
        ref = f"@{revision}" if revision else ""
        with fs.open(f"datasets/{DATASET}{ref}/{name}", "rb") as handle:
            rows.extend(pq.read_table(handle, columns=COLUMNS).to_pylist())
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="effiskill fetch-tasks", description=__doc__.splitlines()[0])
    parser.add_argument("--language", choices=sorted(SOLUTION_KEY), required=True)
    parser.add_argument("--out", type=Path, required=True, help="CSV to write (problem_id, description, canonical_solution)")
    parser.add_argument("--revision", default=None, help="Dataset revision (commit) to download; default: latest")
    parser.add_argument("--all-tasks", action="store_true", help="Keep every task, not only the 623 evaluated in the paper")
    args = parser.parse_args(argv)

    key = SOLUTION_KEY[args.language]
    wanted = None if args.all_tasks else set(paper_task_ids(args.language))
    out_rows = []
    for row in load_rows(args.revision):
        code = ((row.get("solutions") or {}).get(key) or {}).get("code") or ""
        pid = task_id(row)
        if not code.strip() or (wanted is not None and pid not in wanted):
            continue
        out_rows.append({"problem_id": pid, "description": row["description"], "canonical_solution": code})
    out_rows.sort(key=lambda r: r["problem_id"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["problem_id", "description", "canonical_solution"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {len(out_rows)} tasks to {args.out}")
    if wanted is not None and len(out_rows) != len(wanted):
        missing = sorted(wanted - {r["problem_id"] for r in out_rows})
        print(f"warning: {len(missing)} paper tasks not found in this revision, e.g. {missing[:3]}", file=sys.stderr)


if __name__ == "__main__":
    main()
