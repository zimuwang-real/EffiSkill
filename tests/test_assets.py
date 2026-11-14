"""Sanity checks for the bundled skill libraries and task lists."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from effiskill.paths import repo_root, skills_root

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
def test_paper_task_ids_follow_upstream_naming(language):
    from effiskill.fetch_tasks import paper_task_ids, task_id

    ids = paper_task_ids(language)
    assert len(ids) == 623
    assert task_id({"source": "atcoder", "id": "abc397a", "title_slug": "thermometer"}) == "atcoder_abc397a_thermometer"
    assert all(i.split("_", 1)[0] in {"aizu", "atcoder", "codechef", "codeforces", "leetcode"} for i in ids)


def test_no_benchmark_content_is_bundled():
    assert not (repo_root() / "data").exists()
