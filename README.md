# EffiSkill

Code for **Automated Code Efficiency Optimization via Agent Skill Mining**
(Findings of EACL 2027).

EffiSkill mines reusable *Operator Skills* (cards that record a slow-to-fast
transformation's intent, applicability, procedure, effect and risks) from
slow/fast program pairs (Stage I), then uses a frozen skill library to diagnose a
program, retrieve skills, compose plans and generate up to eight candidates
without execution feedback (Stage II).

[Paper](https://arxiv.org/abs/2603.27850) ·
[Release assets](https://github.com/zimuwang-real/EffiSkill/releases/tag/v1.0.0)

## What is in this repository

| Path | Contents |
|---|---|
| `skills/python`, `skills/cpp` | The frozen skill libraries used in the paper (29 Python and 28 C++ Operator Skills, plus the S1-S4 controller cards). |
| `data/effibench-x/` | The exact 623 input programs and statements per language that every method optimized. |
| `results/effibench-x/` | Per-task evaluation statistics for all 26 runs in Table 1 (public and private test splits). |
| `src/effiskill/` | Stage I mining, Stage II inference, export, OPT@k scoring and paper reproduction. |
| [Release assets](https://github.com/zimuwang-real/EffiSkill/releases/tag/v1.0.0) | The generated candidates for 24 of the 26 runs, and the full EffiSkill inference logs. |

## Install

Python 3.10+ (tested on 3.12).

```bash
git clone https://github.com/zimuwang-real/EffiSkill.git
cd EffiSkill
python -m pip install -e '.[pipeline]'
```

The core install (`pip install -e .`) is enough to reproduce the tables and
score results. The `pipeline` extra adds what `infer` and mining need.

## 1. Reproduce the paper's numbers (no API calls)

```bash
effiskill reproduce
```

This writes Table 1 (`outputs/rq1/table1_rq1.csv`), Figures 4-6, speedup
summaries and the skill-family analysis (`outputs/rq4/`) from the recorded
evaluation statistics. To score a single run:

```bash
effiskill score --language cpp results/effibench-x/cpp/gpt-5-mini/effiskill
```

## 2. Compare against EffiSkill without running it

Runtimes depend on hardware, so compare methods on your own machine. Download
the candidates every method generated, evaluate them with your harness
alongside your method, and score everything the same way:

```bash
curl -LO https://github.com/zimuwang-real/EffiSkill/releases/download/v1.0.0/effiskill-candidates-v1.0.0.tar.gz
tar -xzf effiskill-candidates-v1.0.0.tar.gz
# effiskill-candidates/<language>/<model>/<method>/rank_<i>.json
```

See [Evaluation protocol](docs/evaluation.md) for the metric, the stats format
`effiskill score` reads, and how the paper's test split was made.

## 3. Run EffiSkill as a baseline

Any OpenAI-compatible endpoint works. The paper used `gpt-5-mini-2025-08-07`
and `Qwen3-Coder-30B-A3B-Instruct` served with vLLM.

```bash
export EFFISKILL_BASE_URL=https://api.openai.com/v1   # or http://localhost:8000/v1 for vLLM
export EFFISKILL_API_KEY=...
export EFFISKILL_MODEL=gpt-5-mini-2025-08-07

effiskill infer --language python \
  --data data/effibench-x/python_tasks.csv \
  --out runs/python_gpt-5-mini.jsonl --workers 8

effiskill export --language python \
  --runs runs/python_gpt-5-mini.jsonl --out-dir runs/python_gpt-5-mini
```

`infer` uses the bundled frozen library for the chosen language and the paper's
settings (8 candidates, up to 3 skill sets of up to 6 skills). It resumes
interrupted runs. `export` writes `rank_1.json` … `rank_8.json` for the
EffiBench-X evaluator; score the evaluator's output with `effiskill score`.

To optimize your own programs, pass any CSV with `problem_id`, `description`
and `canonical_solution` columns (rename them with `--statement-column` and
`--slow-column`). Details, model settings and caveats: [Running EffiSkill as a
baseline](docs/baseline.md).

## 4. Mine a new skill library

```bash
effiskill pairs-to-traces --language python --input my_pairs.jsonl --output traces.jsonl \
  --cache-dir outputs/trace_cache --fail-dir outputs/trace_failures
effiskill extract-skills --language python --traces traces.jsonl --gen-dir outputs/my_library
effiskill infer --language python --skills-root outputs/my_library/skills --data tasks.csv
```

See [Skill mining](docs/mining.md) for input formats and the paper's settings.

## Code versions

`effiskill infer` runs the code that produced the paper's results.
`--prompt-version impact` selects a later revision of the Stage II prompts
(route types, expected skill roles and impact-scored slot allocation). It is
included for completeness and was not used for the reported numbers.

## Citation

```bibtex
@inproceedings{wang2027effiskill,
  title     = {Automated Code Efficiency Optimization via Agent Skill Mining},
  author    = {Wang, Zimu and Shi, Yuling and Li, Mengfan and Liu, Zijun and Zhang, Jie M. and Wan, Chengcheng and Gu, Xiaodong},
  booktitle = {Findings of the Association for Computational Linguistics: EACL 2027},
  year      = {2027},
  eprint    = {2603.27850},
  archivePrefix = {arXiv}
}
```

## License

Code and skill libraries: [MIT](LICENSE). Benchmark statements and input
programs come from EffiBench-X (Apache-2.0); see
[third-party notices](THIRD_PARTY_NOTICES.md).
