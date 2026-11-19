# Evaluation protocol

## Benchmark

EffiBench-X ([code](https://github.com/EffiBench/EffiBench-X),
[dataset](https://huggingface.co/datasets/EffiBench/effibench-x)), 623 tasks per
language, evaluated separately for Python and C++. Every method optimizes the
same input program per task. The benchmark is not redistributed here;
`effiskill fetch-tasks --language <python|cpp> --out tasks.csv` rebuilds the
paper's inputs exactly from the Hugging Face dataset at revision
[`425b58a`](https://huggingface.co/datasets/EffiBench/effibench-x/tree/425b58a834b65db44b615cfa57ffd3e2503e07ec)
(2025-10-22) and checks them against a checksum of those inputs.

The input program of each task is EffiBench-X's *canonical runtime* solution:
the first code sample in the task's `runtimeDistribution`, which is what
EffiBench-X's `generate_solution.py merge-canonical-solutions` writes to
`canonical_runtime.json`. It is not the dataset's `code` field, which differs
for 210 Python and 161 C++ of the 623 tasks. Windows line endings in the
statements are normalized to `\n`.

## Test split

Each task's 100 EffiBench-X tests were randomly partitioned into 20 public and
80 private tests with a fixed per-task seed. Use your own seed, and evaluate every
method you compare on the same split and machine.

## Metric

Public tests filter and rank candidates; private tests decide success. For
task *q* with input program *S* and candidates *c₁…c₈*:

1. Keep candidates that pass all public tests; sort them by public `runtime_sum`.
2. The task is optimized at *k* if one of the first *k* kept candidates passes
   all private tests and `runtime_sum(S) / runtime_sum(c) ≥ 1.10` on the private tests.
3. OPT@k is the percentage of the 623 tasks optimized at *k*. Tasks with no
   candidates count as failures.

`runtime_sum` is the EffiBench-X evaluator's total runtime over the tests in
the split.

## Stats format read by `effiskill score`

One directory per run:

```
<run>/public/stats_rank_1.json … stats_rank_8.json
<run>/private/stats_rank_1.json … stats_rank_8.json
<run>/private/stats_original.json        # Python input program
<run>/private/stats_canonical_cpp.json   # C++ input program
```

Each file maps `problem_id` to `{"python3" | "cpp": {"passed": bool, "runtime_sum": float, ...}}`.
Slot numbers may start at 0 or 1, and `stats_direct_<i>.json` is accepted as
well.

```bash
effiskill score --language python runs/effiskill runs/my_method      # OPT@1..8 per run
effiskill score --language python runs/effiskill runs/my_method --per-task-csv outputs/per_task.csv
```

The paper's significance tests are one-sided paired task-level bootstraps
(10,000 replicates, percentile 95% intervals, Holm adjustment across the eight
endpoints) over the per-task `top{k}_opt` columns that `--per-task-csv` writes (one row per run and task).
