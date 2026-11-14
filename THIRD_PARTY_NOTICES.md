# Third-party notices

The [MIT license](LICENSE) covers EffiSkill code and skill libraries. No dependency source code is vendored.

## EffiBench-X

EffiSkill is evaluated on EffiBench-X (Apache-2.0), which is used by reference
only: no task statements, input programs or tests are included in this
repository. `effiskill fetch-tasks` downloads them from the upstream dataset;
the repository lists only the ids of the 623 tasks per language used in the
paper (`src/effiskill/task_ids`).

- Software and evaluator: https://github.com/EffiBench/EffiBench-X
- Dataset: https://huggingface.co/datasets/EffiBench/effibench-x
- Paper: https://arxiv.org/abs/2505.13004

## Skill mining corpora

The skill libraries are derived from slow/fast pairs drawn from PIE, Mercury,
DeepMind Code Contests and APPS. The pairs are not redistributed. Cards contain
short illustrative snippets generated during mining, not copied pairs.
