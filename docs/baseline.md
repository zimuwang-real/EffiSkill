# Running EffiSkill as a baseline

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

Models used in the paper:

- **GPT-5-mini**: `gpt-5-mini-2025-08-07` (OpenAI API).
- **Qwen3-Coder**: `Qwen3-Coder-30B-A3B-Instruct` served locally with vLLM, e.g.

  ```bash
  vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct --port 8000 --served-model-name Qwen3-Coder-30B-A3B-Instruct
  export EFFISKILL_BASE_URL=http://localhost:8000/v1 EFFISKILL_API_KEY=EMPTY EFFISKILL_MODEL=Qwen3-Coder-30B-A3B-Instruct
  ```

**Sampling.** Stages use fixed temperatures (0.8 for diagnosis, retrieval and
planning; per-plan-style temperatures for generation). GPT-5-family and
o-series models only accept the default temperature, and the gateway used for
the paper ignored the field, so EffiSkill omits `temperature` for those models.
This matches what the paper's GPT-5-mini runs effectively used. Set
`EFFISKILL_SEND_TEMPERATURE=1` to send it anyway.

## Input

A CSV with one task per row. Defaults match the bundled EffiBench-X files:

| Column | Flag to rename | Meaning |
|---|---|---|
| `problem_id` | (fixed) | unique task id |
| `description` | `--statement-column` | problem statement / specification |
| `canonical_solution` | `--slow-column` | the correct program to optimize |

`data/effibench-x/python_tasks.csv` and `cpp_tasks.csv` are the exact inputs
used for every method in the paper.

## Running

```bash
effiskill infer --language cpp \
  --data data/effibench-x/cpp_tasks.csv \
  --out runs/cpp_qwen.jsonl --fail-dir runs/cpp_qwen_failures --workers 16
```

Useful options (see `effiskill infer --language python --help`):

- `--skills-root DIR`: a different skill library (default: `skills/<language>`).
- `--k 8`, `--skill-sets 3`, `--skills-per-set 6`: the paper's budget.
- `--limit N`, `--start N`, `--problem-id ID`: run a subset.
- Runs resume by default: tasks already in `--out` with status `ok` or
  `no_survivor` are skipped. Use `--no-resume` to start over.
- `--prompt-version impact`: a later revision of the prompts, not used for the
  paper's numbers.

For C++, a local `g++`/`clang++` is used (when available) to record compiler
diagnostics for each candidate. Nothing is executed.

## Output

One JSON record per task:

- `optimization_brief`: S1 diagnosis (constraints, bottlenecks, complexity).
- `skill_sets`: retrieved Operator Skills, grouped into up to three sets.
- `plans`: conservative / balanced / aggressive plans per set.
- `candidates`: up to 8 generated programs with static diagnostics.
- `survivor_candidates`: for Python, candidates whose model-judged static
  verdict is `pass` and whose interface matches the input program (plus valid
  syntax with `--require-syntax`); for C++, the same list as `candidates`.

Convert to EffiBench-X candidate files with:

```bash
effiskill export --language cpp --runs runs/cpp_qwen.jsonl --out-dir runs/cpp_qwen
```

The paper evaluated `candidates` in all settings except Qwen3-Coder/Python,
which evaluated `survivor_candidates` (`--field survivor_candidates`).

## Notes on the paper runs

- The full inference logs of the four EffiSkill runs are in the
  `effiskill-inference-logs` release asset.
- The GPT-5-mini/C++ run used a minor variant of the retrieval prompt that also
  asked for a per-set `selection_role` label. That variant's source was not
  preserved; the other three runs match the released code.
- LLM sampling is not deterministic, so a rerun will not regenerate the same
  candidates. Use the released candidates when you need the paper's exact outputs.
