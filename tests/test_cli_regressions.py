"""Commands exactly as the README and docs show them."""

from __future__ import annotations

import importlib
import json
from types import SimpleNamespace

import pytest

from effiskill import cli


def test_build_registry_defaults_to_skills_dir(tmp_path):
    skills = tmp_path / "skills"
    card = skills / "operators" / "O001_demo"
    card.mkdir(parents=True)
    (card / "SKILL.md").write_text("---\nskill_id: O001\nname: Demo\ndescription: demo card\n---\n\nBody.\n")
    cli.main(["build-registry", "--skills-dir", str(skills)])
    registry = json.loads((skills / "registry.json").read_text())
    assert [c["skill_id"] for c in registry] == ["O001"]


def _write_stats(run, scale):
    for split in ("public", "private"):
        (run / split).mkdir(parents=True)
        for i in range(1, 9):
            stats = {"t1": {"python3": {"passed": True, "runtime_sum": 1.0 * scale}}}
            (run / split / f"stats_rank_{i}.json").write_text(json.dumps(stats))
    (run / "private" / "stats_original.json").write_text(json.dumps({"t1": {"python3": {"passed": True, "runtime_sum": 2.0}}}))


def test_score_writes_per_task_csv_for_several_runs(tmp_path):
    import pandas as pd

    _write_stats(tmp_path / "a", 1.0)
    _write_stats(tmp_path / "b", 3.0)
    out = tmp_path / "per_task.csv"
    cli.main(["score", "--language", "python", str(tmp_path / "a"), str(tmp_path / "b"), "--per-task-csv", str(out)])
    frame = pd.read_csv(out)
    assert sorted(frame["run"].map(lambda r: r[-1])) == ["a", "b"]
    assert frame.set_index(frame["run"].str[-1])["top1_opt"].to_dict() == {"a": 1, "b": 0}


def test_pairs_to_traces_accepts_bare_output_filename(tmp_path, monkeypatch):
    pytest.importorskip("openai")
    from effiskill.mining import llm_utils
    from test_mining_offline import _fake_llm

    monkeypatch.setattr(llm_utils, "chat_completion", _fake_llm)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pairs.jsonl").write_text(json.dumps({
        "problem_id": "my_task_0", "statement": "Sum.", "slow_code": "print(sum(range(9)))", "fast_code": "print(36)",
    }) + "\n")
    cli.main(["pairs-to-traces", "--language", "python", "--input", "pairs.jsonl", "--output", "traces.jsonl",
              "--cache-dir", "cache", "--fail-dir", "fail", "--model", "fake", "--workers", "1"])
    assert len((tmp_path / "traces.jsonl").read_text().splitlines()) == 1


@pytest.mark.parametrize("language", ["python", "cpp"])
def test_no_resume_overwrites_output(tmp_path, monkeypatch, language):
    pytest.importorskip("openai")
    from test_inference_offline import FakeCompletions, _write_tasks

    module = importlib.import_module(f"effiskill.{cli.MODULES[('infer', language)]}")
    fake = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(language, [])))
    monkeypatch.setattr(module, "create_client", lambda base_url, api_key: fake)
    tasks = tmp_path / "tasks.csv"
    _write_tasks(tasks, language)
    out = tmp_path / "runs.jsonl"
    argv = ["infer", "--language", language, "--data", str(tasks), "--out", str(out),
            "--fail-dir", str(tmp_path / "fail"), "--base-url", "http://fake", "--api-key", "fake", "--model", "fake-model"]
    cli.main(argv)
    cli.main(argv + ["--no-resume"])
    assert len(out.read_text().splitlines()) == 1
