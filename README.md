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
| [`skills/python`](skills/python), [`skills/cpp`](skills/cpp) | The frozen skill libraries used in the paper: 29 Python Operator Skills (Appendix A) and 28 C++ Operator Skills, plus the S1-S4 controller cards. One `SKILL.md` per card. |
| `results/effibench-x/` | Per-task evaluation statistics for all 26 runs in Table 1 (public and private test splits). |
| `src/effiskill/` | Stage I mining, Stage II inference, export, OPT@k scoring and paper reproduction. |
| [Release assets](https://github.com/zimuwang-real/EffiSkill/releases/tag/v1.0.0) | The generated candidates for 24 of the 26 runs, and the EffiSkill inference logs. |

EffiBench-X tasks and tests are not redistributed. `effiskill fetch-tasks`
downloads the tasks from the [upstream dataset](https://huggingface.co/datasets/EffiBench/effibench-x).

## Install

Python 3.10+ (tested on 3.12).

```bash
git clone https://github.com/zimuwang-real/EffiSkill.git
cd EffiSkill
python -m pip install -e '.[pipeline]'
```

The core install (`pip install -e .`) is enough to reproduce the tables and
score results. The `pipeline` extra adds what `infer`, `fetch-tasks` and mining need.

## 1. Reproduce the paper's numbers (no API calls)

```bash
effiskill reproduce
```

This regenerates the paper's numbers from the recorded evaluation statistics:
Table 1 and Figures 4-5 plus Appendix Tables 5-8 and the speedup geometric means
(`outputs/rq1/`), and the skill-attachment counts behind Figure 6 / Table 9
(`outputs/rq4/`). The tests check every value against the paper. To score a
single run:

```bash
effiskill score --language cpp results/effibench-x/cpp/gpt-5-mini/effiskill
```

## 2. Compare against EffiSkill without running it

Runtimes depend on hardware, so compare methods on your own machine. Download
the candidates every method generated, evaluate them with your EffiBench-X
harness alongside your method, and score everything the same way:

```bash
curl -LO https://github.com/zimuwang-real/EffiSkill/releases/download/v1.0.0/effiskill-candidates-v1.0.0.tar.gz
tar -xzf effiskill-candidates-v1.0.0.tar.gz
# effiskill-candidates/<language>/<model>/<method>/rank_<i>.json
```

See [Evaluation protocol](docs/evaluation.md) for the metric, the stats format
`effiskill score` reads, and the test split.

## 3. Run EffiSkill on EffiBench-X or your own programs

Any OpenAI-compatible endpoint works. The paper used `gpt-5-mini-2025-08-07`
and `Qwen3-Coder-30B-A3B-Instruct`.

```bash
export EFFISKILL_BASE_URL=https://api.openai.com/v1
export EFFISKILL_API_KEY=...
export EFFISKILL_MODEL=gpt-5-mini-2025-08-07

effiskill fetch-tasks --language python --out tasks/python.csv

effiskill infer --language python \
  --data tasks/python.csv \
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
`--slow-column`). Details, model settings and caveats: [Running
EffiSkill](docs/baseline.md).

## 4. Mine a skill library from your own pairs

```bash
effiskill pairs-to-traces --language python --input my_pairs.jsonl --output traces.jsonl \
  --cache-dir outputs/trace_cache --fail-dir outputs/trace_failures
effiskill extract-skills --language python --traces traces.jsonl --gen-dir outputs/my_library
effiskill infer --language python --skills-root outputs/my_library/skills --data tasks.csv
```

See [Skill mining](docs/mining.md) for input formats and the paper's settings.

## Code versions

The default `infer` and mining code is the pipeline described in the paper
(Section 3, Appendices B and C). The EffiSkill runs in Table 1 were generated
with an earlier revision of the Stage II code, kept as
`effiskill infer --prompt-version paper-runs`; its logs are in the release
assets. Both use the same frozen skill libraries.

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

Code, skill libraries, results and generated candidates: [MIT](LICENSE).
EffiBench-X is Apache-2.0 and is used by reference only; see
[third-party notices](THIRD_PARTY_NOTICES.md).
