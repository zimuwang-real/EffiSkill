# Data and assets

## In the repository

| Path | Contents | Format |
|---|---|---|
| `skills/<language>/` | Frozen skill libraries: S1-S4 controller cards and Operator Skills (`O###`), one `SKILL.md` per card, plus `registry.json` | Markdown with YAML front matter; JSON |
| `data/effibench-x/<language>_tasks.csv` | The 623 input programs and statements per language optimized by every method | CSV: `problem_id`, `description`, `canonical_solution` |
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
(EffiBench-X candidate format, `{problem_id: code}`). Slot *i* is the candidate
scored as `stats_rank_<i>.json`. `MANIFEST.json` lists every run and its gaps.

- The two Python Instruction runs are not included: their candidate files
  could not be matched to the evaluated slots reliably.
- Qwen3-Coder/C++ EffiSkill has 9 evaluated slots whose code was not preserved,
  and GPT-5-mini/Python CoT has 3 slots with empty code.

**`effiskill-inference-logs-v1.0.0.tar.gz`**: full Stage II logs (diagnosis,
retrieved skills, plans, candidates) for the four EffiSkill runs, one JSONL per
language and model. `evaluated_candidate_field` in each record says whether
`candidates` or `survivor_candidates` was evaluated.

## Licenses

EffiSkill code, skill libraries, results and generated candidates are MIT
licensed. The statements and input programs in `data/effibench-x/` come from
EffiBench-X and are redistributed under Apache-2.0; see
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). The EffiBench-X tests are
not included; get them from the upstream dataset.
