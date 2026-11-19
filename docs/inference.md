# Running EffiSkill

This page covers Stage II: optimizing programs with a frozen skill library.
Install with `python -m pip install -e '.[pipeline]'`.

## Endpoint and model

`effiskill infer` talks to any OpenAI-compatible Chat Completions endpoint.
Configure it with flags or environment variables:

| Flag | Environment variable |
|---|---|
| `--base-url` | `EFFISKILL_BASE_URL` |
| `--api-key` | `EFFISKILL_API_KEY` |
| `--model` | `EFFISKILL_MODEL` |

Models used in the paper: `gpt-5-mini-2025-08-07` and
`Qwen3-Coder-30B-A3B-Instruct`. To serve Qwen3-Coder yourself, any
OpenAI-compatible server works, e.g. vLLM:

```bash
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000 --served-model-name Qwen3-Coder-30B-A3B-Instruct --max-model-len 65536
export EFFISKILL_BASE_URL=http://localhost:8000/v1 EFFISKILL_API_KEY=EMPTY EFFISKILL_MODEL=Qwen3-Coder-30B-A3B-Instruct
```

Generation stages request up to 35,000 completion tokens, so serve the model
with a context length of at least 64K; shorter limits make the server reject
those requests.

**Sampling.** Each stage has a fixed temperature, with generation temperature
rising from conservative to aggressive plans (see `DecodingProfile` in
`src/effiskill/inference/common.py`; model names containing `qwen` use a
slightly lower profile). GPT-5-family and o-series models only accept the
default temperature, so EffiSkill omits `temperature` for those models. Set
`EFFISKILL_SEND_TEMPERATURE=1` to send it anyway.

## Input

A CSV with one task per row:

| Column | Flag to rename | Meaning |
|---|---|---|
| `problem_id` | (fixed) | unique task id |
| `description` | `--statement-column` | problem statement / specification |
| `canonical_solution` | `--slow-column` | the correct program to optimize |

For EffiBench-X, `effiskill fetch-tasks --language <python|cpp> --out tasks.csv`
downloads the 623 tasks per language used in the paper and rebuilds exactly
the paper's inputs (see [evaluation.md](evaluation.md)).

## Running

```bash
effiskill infer --language cpp \
  --data tasks/cpp.csv \
  --out runs/cpp_qwen.jsonl --fail-dir runs/cpp_qwen_failures --workers 16
```

Useful options (see `effiskill infer --language python --help`):

- `--skills-root DIR`: a different skill library (default: `skills/<language>`).
- `--k 8`, `--skill-sets 3`, `--skills-per-set 6`: the paper's budget.
- `--limit N`, `--start N`, `--problem-id ID`: run a subset.
- Runs resume by default: tasks already in `--out` with status `ok` or
  `no_survivor` are skipped. Use `--no-resume` to overwrite `--out` and start over.

For C++, a local `g++`/`clang++` is used (when available) to record compiler
diagnostics for each candidate. Nothing is executed.

## Output

One JSON record per task:

- `optimization_brief`: S1 diagnosis (constraints, bottlenecks, complexity, required change).
- `skill_sets`: retrieved Operator Skills, grouped into up to three sets.
- `plans`: task-specific plans for each skill set.
- `candidates`: up to 8 generated programs with static diagnostics.
- `survivor_candidates`: the same list (static diagnostics are recorded, not used to filter).

Convert to EffiBench-X candidate files with:

```bash
effiskill export --language cpp --runs runs/cpp_qwen.jsonl --out-dir runs/cpp_qwen
```

## Reproducibility

This is the Stage II pipeline described in Section 3 and Appendix C of the
paper. LLM sampling is not deterministic and runtimes depend on hardware, so
compare EffiSkill with other methods by running all of them with the same model,
inputs, test split and machine rather than against the numbers in the paper.
