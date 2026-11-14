"""Mine a library from your own pairs, then optimize with it (fake LLM, no network)."""

from __future__ import annotations

import importlib
import json
import re
from types import SimpleNamespace

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("openai")

from effiskill import cli
from effiskill.mining import llm_utils

from test_inference_offline import FakeCompletions, _write_tasks

FAMILIES = [
    ("prefix_sum", "O(n^2)", "O(n)", "repeated range sums", "precompute prefix sums"),
    ("rolling_dp", "O(n^2) memory", "O(n) memory", "full DP table", "keep two rows"),
    ("fast_io", "O(n)", "O(n)", "input() in a loop", "read stdin once"),
]


def _fake_llm(messages, model, temperature, max_tokens, reasoning_effort="low"):
    prompt = messages[-1]["content"]
    if "ProblemBrief" in prompt:
        pid = re.search(r"problem_id:\s*(\S+)", prompt).group(1)
        name, before, after, bottleneck, step = FAMILIES[int(pid.rsplit("_", 1)[1]) % len(FAMILIES)]
        return json.dumps({
            "problem_id": pid,
            "ProblemBrief": {"constraints_guess": {"n_max": "2e5", "q_max": "1", "notes": ""}, "problem_type_tags": [name]},
            "SlowAudit": {"dominant_ops": [bottleneck], "complexity": {"time": before, "space": "O(n)", "why": bottleneck},
                          "bottlenecks": [{"kind": name, "detail": bottleneck}]},
            "FastAudit": {"core_idea": step, "complexity": {"time": after, "space": "O(n)", "why": step}},
            "DeltaSummary": {"delta_type": [name], "complexity_delta": {"from": before, "to": after, "note": ""},
                             "transformation_steps": [step, f"{name} step two"], "trigger_signals": [bottleneck],
                             "pitfalls": ["off-by-one"]},
        })
    if "optimization cluster" in prompt:
        profile = json.loads(prompt.split("cluster_profile:\n", 1)[1])
        blob = json.dumps(profile)
        name = next((f[0] for f in FAMILIES if f[0] in blob), "generic")
        return json.dumps({
            "cluster_id": profile.get("cluster_id"), "proposed_name": f"{name.replace('_', ' ').title()} Rewrite",
            "description": f"Apply {name} when the slow program shows the matching bottleneck.",
            "tags": [name], "optimization_scope": "algorithmic", "expected_speedup_band": "moderate",
            "primary_mechanism": name, "secondary_mechanisms": [], "canonical_triggers": [f"{name} trigger"],
            "canonical_steps": [f"{name} step"], "common_pitfalls": ["off-by-one"],
            "complexity_time": "O(n)", "complexity_space": "O(n)", "when_not_to_use": ["tiny inputs"],
        })
    if "before_code" in prompt:
        return json.dumps({"before_code": "s = 0\nfor i in range(n):\n    s += sum(a[:i])",
                           "after_code": "p = 0\ns = 0\nfor x in a[:n]:\n    s += p\n    p += x"})
    if "Learn meta skill" in prompt:
        return json.dumps({"name": "Meta", "description": "Reusable controller step.", "inputs": ["statement", "code"],
                           "procedure": ["inspect", "decide"], "decision_rules": ["prefer simple"],
                           "failure_modes": ["overfitting"], "output_contract": ["JSON"]})
    raise AssertionError(f"unexpected prompt: {prompt[:200]}")


@pytest.mark.parametrize("language", ["python", "cpp"])
def test_mine_then_infer_on_own_data(tmp_path, monkeypatch, language):
    monkeypatch.setattr(llm_utils, "chat_completion", _fake_llm)
    pairs = tmp_path / "pairs.jsonl"
    with pairs.open("w", encoding="utf-8") as handle:
        for i in range(30):
            handle.write(json.dumps({
                "problem_id": f"my_task_{i}", "statement": f"Task {i}: sum queries.",
                "slow_code": f"n = int(input())\nprint(sum(range(n)) + {i})",
                "fast_code": f"n = int(input())\nprint(n * (n - 1) // 2 + {i})",
            }) + "\n")

    traces = tmp_path / "traces.jsonl"
    cli.main(["pairs-to-traces", "--language", language, "--input", str(pairs), "--output", str(traces),
              "--cache-dir", str(tmp_path / "cache"), "--fail-dir", str(tmp_path / "fail"), "--model", "fake",
              "--workers", "1"])
    assert len(traces.read_text().splitlines()) == 30

    gen = tmp_path / "library"
    cli.main(["extract-skills", "--language", language, "--traces", str(traces), "--gen-dir", str(gen),
              "--model", "fake", "--disable-sentence-embeddings", "--k", "3"])
    skills = gen / "skills"
    registry = json.loads((skills / "registry.json").read_text())
    ids = {card["skill_id"] for card in registry}
    assert {"S1", "S2", "S3"} <= ids and any(i.startswith("O") for i in ids)

    module = importlib.import_module(f"effiskill.{cli.MODULES[('infer', language)]}")
    fake = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(language, [])))
    monkeypatch.setattr(module, "create_client", lambda base_url, api_key: fake)
    tasks = tmp_path / "tasks.csv"
    _write_tasks(tasks, language)
    out = tmp_path / "runs.jsonl"
    cli.main(["infer", "--language", language, "--skills-root", str(skills), "--data", str(tasks),
              "--out", str(out), "--fail-dir", str(tmp_path / "infer_fail"),
              "--base-url", "http://fake", "--api-key", "fake", "--model", "fake-model"])
    record = json.loads(out.read_text().splitlines()[-1])
    assert record["status"] == "ok", record
    assert record["candidates"]
