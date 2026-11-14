"""Sanity checks for the bundled skill libraries, task files and results."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

from effiskill.paths import repo_root, results_root, skills_root

EXPECTED_OPERATORS = {"python": 29, "cpp": 28}


def _skill_ids(root: Path) -> set[str]:
    ids = set()
    for path in root.rglob("SKILL.md"):
        match = re.search(r"^skill_id:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
        assert match, path
        ids.add(match.group(1))
    return ids


@pytest.mark.parametrize("language", ["python", "cpp"])
def test_skill_library_is_complete(language):
    root = skills_root(language)
    registry = json.loads((root / "registry.json").read_text(encoding="utf-8"))
    registry_ids = {card["skill_id"] for card in registry}
    operators = {i for i in registry_ids if i.startswith("O")}
    assert len(operators) == EXPECTED_OPERATORS[language]
    assert {"S1", "S2", "S3"} <= registry_ids
    assert registry_ids == _skill_ids(root)
    assert all(card.get("language") in (None, language) for card in registry if card["skill_id"].startswith("O"))


@pytest.mark.parametrize("language", ["python", "cpp"])
def test_task_csv_matches_evaluated_tasks(language):
    with (repo_root() / "data" / "effibench-x" / f"{language}_tasks.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 623
    assert all(r["description"].strip() and r["canonical_solution"].strip() for r in rows)
    original = "stats_original.json" if language == "python" else "stats_canonical_cpp.json"
    stats = json.loads((results_root() / "effibench-x" / language / "gpt-5-mini" / "effiskill" / "private" / original).read_text())
    assert {r["problem_id"] for r in rows} == set(stats)
