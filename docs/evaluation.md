# Evaluation protocol

## Benchmark

EffiBench-X ([code](https://github.com/EffiBench/EffiBench-X),
[dataset](https://huggingface.co/datasets/EffiBench/effibench-x)), 623 tasks per
language, evaluated separately for Python and C++. Every method optimizes the
same input program per task. The benchmark is not redistributed here;
`effiskill fetch-tasks --language <python|cpp> --out tasks.csv` downloads the
623 tasks evaluated in the paper.

The paper's input programs differ from the current dataset for 210 Python and
161 C++ tasks (statements are identical). The released candidates were
generated from the paper's inputs, so measure every input program's runtime
with your own evaluator rather than reusing recorded baselines.

## Test split

Each task's 100 EffiBench-X tests were randomly partitioned into 20 public and
80 private tests with a fixed per-task seed. The split indices were not
preserved. To compare with EffiSkill, re-split with your own seed and evaluate
every method you report, including the released EffiSkill candidates, on that
same split and machine.

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
well. `results/effibench-x/` has all 26 paper runs in this format.

```bash
effiskill score --language python my_run results/effibench-x/python/gpt-5-mini/effiskill \
  --per-task-csv outputs/my_run_tasks.csv
```

The paper's significance tests are one-sided paired task-level bootstraps
(10,000 replicates, percentile 95% intervals, Holm adjustment across the eight
endpoints) over the per-task `top{k}_opt` columns, with the explicit seeds of
Table 5. `effiskill reproduce` writes them to `outputs/rq1/table5_significance.csv`.
