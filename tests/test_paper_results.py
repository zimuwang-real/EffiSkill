"""The bundled evaluation statistics reproduce Table 1 of the paper."""

from __future__ import annotations

import csv

import pytest

from effiskill.paths import results_root
from effiskill.scoring import score_run, summarize

# (language, model, method) -> (OPT@1, OPT@8), Table 1 of the paper.
TABLE1 = {
    ("python", "gpt-5-mini", "instruction"): (18.62, 31.62),
    ("python", "gpt-5-mini", "rag"): (19.90, 29.37),
    ("python", "gpt-5-mini", "cot"): (18.62, 28.73),
    ("python", "gpt-5-mini", "sbllm"): (17.34, 18.94),
    ("python", "gpt-5-mini", "fasterpy"): (21.19, 32.42),
    ("python", "gpt-5-mini", "effiskill"): (26.48, 37.40),
    ("cpp", "gpt-5-mini", "instruction"): (31.62, 48.15),
    ("cpp", "gpt-5-mini", "rag"): (34.19, 45.43),
    ("cpp", "gpt-5-mini", "cot"): (40.93, 54.74),
    ("cpp", "gpt-5-mini", "sbllm"): (38.84, 53.45),
    ("cpp", "gpt-5-mini", "fasterpy"): (38.84, 51.69),
    ("cpp", "gpt-5-mini", "effiskill"): (44.62, 66.77),
    ("python", "qwen3-coder-30b", "instruction"): (12.52, 24.40),
    ("python", "qwen3-coder-30b", "rag"): (7.22, 19.74),
    ("python", "qwen3-coder-30b", "cot"): (16.05, 26.00),
    ("python", "qwen3-coder-30b", "sbllm"): (6.90, 8.67),
    ("python", "qwen3-coder-30b", "fasterpy"): (13.96, 28.25),
    ("python", "qwen3-coder-30b", "efficoder"): (14.29, 16.69),
    ("python", "qwen3-coder-30b", "effiskill"): (21.35, 36.60),
    ("cpp", "qwen3-coder-30b", "instruction"): (26.00, 32.58),
    ("cpp", "qwen3-coder-30b", "rag"): (16.37, 25.04),
    ("cpp", "qwen3-coder-30b", "cot"): (23.11, 30.02),
    ("cpp", "qwen3-coder-30b", "sbllm"): (28.41, 43.98),
    ("cpp", "qwen3-coder-30b", "fasterpy"): (19.90, 34.19),
    ("cpp", "qwen3-coder-30b", "efficoder"): (14.77, 25.20),
    ("cpp", "qwen3-coder-30b", "effiskill"): (34.19, 56.50),
}


@pytest.mark.parametrize("key", sorted(TABLE1))
def test_table1_cell(key):
    language, model, method = key
    frame = score_run(results_root() / "effibench-x" / language / model / method, language)
    summary = summarize(frame)
    assert summary["tasks"] == 623
    assert round(summary["OPT@1"], 2) == TABLE1[key][0]
    assert round(summary["OPT@8"], 2) == TABLE1[key][1]


def test_reproduce_writes_table(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    from effiskill import cli

    cli.main(["reproduce", "--output-dir", str(tmp_path)])
    with (tmp_path / "rq1" / "table1_rq1.csv").open() as handle:
        rows = {(r["Model"], r["Method"]): r for r in csv.DictReader(handle)}
    assert rows[("GPT-5-mini", "EffiSkill")]["Python OPT@8 (%)"].startswith("37.40")
    assert (tmp_path / "rq4" / "skill_family_usage.csv").exists()

    with (tmp_path / "rq1" / "table5_significance.csv").open() as handle:
        sig = list(csv.DictReader(handle))
    # Table 5: seven of eight endpoints significant after Holm; GPT/C++ OPT@1 is not.
    assert [r["significant"] for r in sig].count("True") == 7
    gpt_cpp_opt1 = next(r for r in sig if r["Backbone"] == "GPT-5-mini" and r["Language"] == "C++" and r["Endpoint"] == "OPT@1")
    assert gpt_cpp_opt1["significant"] == "False" and round(float(gpt_cpp_opt1["p_holm"]), 6) == 0.070593
    gpt_py_opt1 = next(r for r in sig if r["Backbone"] == "GPT-5-mini" and r["Language"] == "Python" and r["Endpoint"] == "OPT@1")
    assert round(float(gpt_py_opt1["ci_low"]), 3) == 1.766 and round(float(gpt_py_opt1["p_holm"]), 6) == 0.007499

    with (tmp_path / "rq1" / "table7_terminal_outcomes.csv").open() as handle:
        outcomes = {(r["Language"], r["Model"]): r for r in csv.DictReader(handle) if r["Method"] == "EffiSkill"}
    # Table 7.
    assert [outcomes[("Python", "GPT-5-mini")][k] for k in ("Success", "No public survivor", "Public, no private-correct", "Private-correct < 1.10x")] == ["233", "8", "4", "378"]
    assert outcomes[("C++", "Qwen3-Coder-30B")]["Success"] == "352"

    with (tmp_path / "rq1" / "speedup_geomean.csv").open() as handle:
        geo = {(r["Language"], r["Model"], r["Method"]): r["Geometric mean speedup"] for r in csv.DictReader(handle)}
    assert geo[("Python", "GPT-5-mini", "EffiSkill")] == "1.188" and geo[("C++", "GPT-5-mini", "EffiSkill")] == "1.448"

    with (tmp_path / "rq4" / "table9_skill_attachments.csv").open() as handle:
        att = list(csv.DictReader(handle))
    assert (att[0]["Card"], att[0]["Uses"], att[0]["Denominator"]) == ("O001", "2366", "10360")
