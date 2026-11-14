# Data and assets

## In the repository

| Path | Contents | Format |
|---|---|---|
| `skills/<language>/` | Frozen skill libraries: S1-S4 controller cards and Operator Skills (`O###`), one `SKILL.md` per card, plus `registry.json` | Markdown with YAML front matter; JSON |
| `results/effibench-x/<language>/<model>/<method>/` | Evaluator statistics for the 26 runs in Table 1 | see [evaluation.md](evaluation.md) |
| `results/skill-attribution/python_<model>.jsonl` | Which Operator Skills produced each Python EffiSkill candidate (used for the skill-family analysis) | JSONL |
| `examples/` | Tiny toy inputs for smoke tests | CSV, JSONL |

Methods: `instruction`, `rag`, `cot`, `sbllm`, `fasterpy`, `efficoder`
(Qwen3-Coder only) and `effiskill`. Models: `gpt-5-mini`, `qwen3-coder-30b`.

## Release assets

Attached to the [v1.0.0 release](https://github.com/zimuwang-real/EffiSkill/releases/tag/v1.0.0),
with checksums in `SHA256SUMS`.

**`effiskill-candidates-v1.0.0.tar.gz`**: the candidates behind 24 of the 26
Table 1 runs, as `effiskill-candidates/<language>/<model>/<method>/rank_<i>.json`
(EffiBench-X candidate format, `{problem_id: {"python3" | "cpp": code}}`). Slot *i* is the candidate
scored as `stats_rank_<i>.json`. `MANIFEST.json` lists every run and its gaps.

- The two Python Instruction runs are not included: their candidate files
  could not be matched to the evaluated slots reliably.
- Qwen3-Coder/C++ EffiSkill has 9 evaluated slots whose code was not preserved,
  and GPT-5-mini/Python CoT has 3 slots with empty code.

**`effiskill-inference-logs-v1.0.0.tar.gz`**: Stage II logs (diagnosis,
retrieved skills, plans, candidates) for the four EffiSkill runs, one JSONL per
language and model, written by `--prompt-version paper-runs`.
`evaluated_candidate_field` in each record says whether `candidates` or
`survivor_candidates` was evaluated. Task statements and input programs were
removed; join on `problem_id` with the output of `effiskill fetch-tasks`.

## EffiBench-X

EffiBench-X tasks and tests are not redistributed. `effiskill fetch-tasks`
downloads the statements and canonical solutions of the 623 tasks per language
from the [upstream dataset](https://huggingface.co/datasets/EffiBench/effibench-x)
(task ids are `<source>_<id>_<title_slug>`). The tests come from the same dataset.

## Licenses

EffiSkill code, skill libraries, results and generated candidates are MIT
licensed. EffiBench-X is Apache-2.0; see
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
