# EffiSkill

Code for **Automated Code Efficiency Optimization via Agent Skill Mining**
(Findings of EACL 2027).

EffiSkill mines reusable *Operator Skills* (cards that record a slow-to-fast
transformation's intent, applicability, procedure, effect and risks) from
slow/fast program pairs (Stage I), then uses a frozen skill library to diagnose a
program, retrieve skills, compose plans and generate up to eight candidates
without execution feedback (Stage II).

[Paper](https://arxiv.org/abs/2603.27850)

## What is in this repository

| Path | Contents |
|---|---|
| [`skills/python`](skills/python), [`skills/cpp`](skills/cpp) | The frozen skill libraries used in the paper: 29 Python Operator Skills (Appendix A) and 28 C++ Operator Skills, plus the S1-S4 controller cards. One `SKILL.md` per card. |
| `src/effiskill/` | Stage I mining, Stage II inference, candidate export and OPT@k scoring. |
| [`examples/`](examples) | Toy inputs showing the task and pair formats. |

EffiBench-X tasks and tests are not redistributed. `effiskill fetch-tasks`
downloads the tasks from the [upstream dataset](https://huggingface.co/datasets/EffiBench/effibench-x).

## Install

Python 3.10+ (tested on 3.12).

```bash
git clone https://github.com/zimuwang-real/EffiSkill.git
cd EffiSkill
python -m pip install -e '.[pipeline]'
```

Add the `embeddings` extra (`'.[pipeline,embeddings]'`) to mine with sentence
embeddings, as in the paper.

## 1. Optimize programs with the released skills

Any OpenAI-compatible endpoint works. The paper used `gpt-5-mini-2025-08-07`
and `Qwen3-Coder-30B-A3B-Instruct`.

```bash
export EFFISKILL_BASE_URL=https://api.openai.com/v1
export EFFISKILL_API_KEY=...
export EFFISKILL_MODEL=gpt-5-mini-2025-08-07

effiskill infer --language python \
  --data examples/tasks.csv \
  --out runs/my_run.jsonl --workers 8
```

The input is a CSV with `problem_id`, `description` (the problem statement)
and `canonical_solution` (the correct program to optimize); rename the last two
with `--statement-column` and `--slow-column`. `infer` uses the bundled library
for the chosen language and the paper's settings (8 candidates, up to 3 skill
sets of up to 6 skills), and resumes interrupted runs. Each output record holds
the diagnosis, retrieved skills, plans and candidates. Details: [Running
EffiSkill](docs/inference.md).

## 2. Evaluate on your benchmark

```bash
effiskill export --language python --runs runs/my_run.jsonl --out-dir runs/my_run
```

`export` writes `rank_1.json` … `rank_8.json` (`{problem_id: {"python3" | "cpp": code}}`)
in the EffiBench-X candidate format. Run them through your evaluator, then
compute OPT@1..8 with `effiskill score` (see [Evaluation](docs/evaluation.md)
for the metric and the statistics format it reads).

For EffiBench-X:

```bash
effiskill fetch-tasks --language python --out tasks/python.csv   # the 623 tasks used in the paper
```

## 3. Mine a skill library from your own pairs

```bash
effiskill pairs-to-traces --language python --input my_pairs.jsonl --output traces.jsonl \
  --cache-dir outputs/trace_cache --fail-dir outputs/trace_failures
effiskill extract-skills --language python --traces traces.jsonl --gen-dir outputs/my_library
effiskill infer --language python --skills-root outputs/my_library/skills --data tasks.csv
```

Pairs are CSV/JSONL rows with `problem_id`, `statement`, `slow_code` and
`fast_code` (format: [`examples/pairs.jsonl`](examples/pairs.jsonl); the paper
mined 900 pairs per language). The defaults are the paper's mining settings. See [Skill
mining](docs/mining.md) for input formats and options.

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

Code and skill libraries: [MIT](LICENSE). EffiBench-X is Apache-2.0 and is used
by reference only; see [third-party notices](THIRD_PARTY_NOTICES.md).
