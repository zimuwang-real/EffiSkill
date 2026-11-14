"""End-to-end Stage II run against a fake OpenAI client (no network, no cost)."""

from __future__ import annotations

import csv
import importlib
import json
from types import SimpleNamespace

import pytest

pytest.importorskip("openai")

from effiskill import cli
from effiskill.export import export_candidates

PY_CODE = "import sys\nvals = list(map(int, sys.stdin.read().split()))\nprint(sum(v * v for v in vals))\n"
CPP_CODE = "#include <bits/stdc++.h>\nint main(){long long x,s=0;while(std::cin>>x)s+=x*x;std::cout<<s<<'\\n';}\n"


class FakeCompletions:
    def __init__(self, language: str, calls: list):
        self.language = language
        self.calls = calls

    def create(self, **kwargs):
        self.calls.append(kwargs)
        system = kwargs["messages"][0]["content"]
        if "diagnostician" in system:
            payload = {
                "constraints_guess": {"n_max": "1e5", "q_max": "1", "notes": ""},
                "problem_type_tags": ["implementation"],
                "dominant_ops": ["list comprehension"],
                "complexity": {"time": "O(n)", "space": "O(n)", "why": "materialized list"},
                "bottlenecks": [{"kind": "allocation", "detail": "temporary list"}],
                "must_change": "implementation",
                "risks": [],
                "confidence": "high",
            }
        elif "skill router" in system:
            payload = {
                "skill_sets": [
                    {"set_id": "S_a", "confidence": "high", "selection_theme": "io", "route_type": "io",
                     "expected_change": "stream input", "selected_skills": [
                         {"skill_id": "O001", "reason": "constant factors", "expected_role": "primary_high_impact"}]},
                    {"set_id": "S_b", "confidence": "medium", "selection_theme": "math", "route_type": "constant_factor",
                     "expected_change": "cheaper arithmetic", "selected_skills": [
                         {"skill_id": "O002", "reason": "alternative", "expected_role": "supporting"}]},
                ]
            }
        elif "generate plans" in system:
            payload = {
                "plans": [
                    {"plan_id": f"P{i}", "plan_style": style, "name": style, "core_idea": "stream and fold",
                     "target_complexity": "O(n)", "risks": [], "steps": ["read once", "fold"],
                     "route_type": "io", "optimization_mechanism": "streaming", "old_hot_path": "list",
                     "new_mechanism": "generator", "expected_speedup_band": "mild", "impact_skill_ids": ["O001"],
                     "must_change_alignment": "matches"}
                    for i, style in enumerate(["conservative", "balanced", "aggressive"], start=1)
                ]
            }
        elif "Generate optimized" in system:
            payload = {
                "code": PY_CODE if self.language == "python" else CPP_CODE,
                "complexity": "O(n)",
                "dominant_ops": ["sum"],
                "notes": "",
                "static_verdict": "pass",
                "interface_match": True,
                "complexity_plausible": True,
                "static_issues": [],
                "static_confidence": "high",
                "change_summary": {"removed_hot_path": "list", "new_mechanism": "generator", "expected_effect": "mild"},
            }
        else:
            payload = {"verdict": "pass", "code": PY_CODE}
        message = SimpleNamespace(content=json.dumps(payload))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _write_tasks(path, language):
    slow = "print(sum([int(x)**2 for x in input().split()]))\n" if language == "python" else CPP_CODE
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["problem_id", "description", "canonical_solution"])
        writer.writerow(["toy_sum_squares", "Read integers and print the sum of their squares.", slow])


@pytest.mark.parametrize("prompt_version", ["paper", "impact"])
@pytest.mark.parametrize("language", ["python", "cpp"])
@pytest.mark.parametrize("model", ["gpt-5-mini", "Qwen3-Coder-30B-A3B-Instruct"])
def test_infer_and_export_offline(tmp_path, monkeypatch, language, prompt_version, model):
    module_name = cli.MODULES[("infer", language, prompt_version)]
    module = importlib.import_module(f"effiskill.{module_name}")
    calls: list = []
    fake = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(language, calls)))
    monkeypatch.setattr(module, "create_client", lambda base_url, api_key: fake)

    tasks = tmp_path / "tasks.csv"
    _write_tasks(tasks, language)
    out = tmp_path / "runs.jsonl"
    cli.main([
        "infer", "--language", language, "--prompt-version", prompt_version,
        "--data", str(tasks), "--out", str(out), "--fail-dir", str(tmp_path / "fail"),
        "--base-url", "http://fake", "--api-key", "fake", "--model", model,
    ])

    record = json.loads(out.read_text().splitlines()[-1])
    assert record["status"] == "ok", record
    assert len(record["candidates"]) == 8
    assert {s["skill_id"] for ss in record["skill_sets"] for s in ss["selected_skills"]} <= {"O001", "O002"}

    sent_temperature = [("temperature" in c) for c in calls]
    if model.startswith("gpt-5"):
        assert not any(sent_temperature)
    else:
        assert all(sent_temperature)

    counts = export_candidates(out, tmp_path / "cands", language)
    assert counts["tasks"] == 1 and counts["rank_8"] == 1
    lang_key = "python3" if language == "python" else "cpp"
    rank1 = json.loads((tmp_path / "cands" / "rank_1.json").read_text())
    assert rank1["toy_sum_squares"][lang_key].strip()
    original = "original.json" if language == "python" else "canonical_cpp.json"
    assert (tmp_path / "cands" / original).exists()
