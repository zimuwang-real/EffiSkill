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
    assert (tmp_path / "rq4" / "table3_skill_family_summary.csv").exists()
