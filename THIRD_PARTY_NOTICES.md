# Third-party notices

The [MIT license](LICENSE) covers EffiSkill code, skill libraries, evaluation
statistics and generated candidates. No dependency source code is vendored.

## EffiBench-X

`data/effibench-x/python_tasks.csv` and `data/effibench-x/cpp_tasks.csv` contain
problem statements and canonical solutions from EffiBench-X, redistributed
under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
The input programs are the canonical solutions as used in the paper; some
differ from the current public dataset revision. No EffiBench-X test cases are included;
the `public`/`private` folders under `results/` hold only recorded statistics.

- Software and evaluator: https://github.com/EffiBench/EffiBench-X
- Dataset: https://huggingface.co/datasets/EffiBench/effibench-x
- Paper: https://arxiv.org/abs/2505.13004

## Skill mining corpora

The skill libraries are derived from slow/fast pairs drawn from PIE, Mercury,
DeepMind Code Contests and APPS. The pairs are not redistributed. Cards contain
short illustrative snippets generated during mining, not copied pairs.
