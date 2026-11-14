# Third-party notices

The [MIT license](LICENSE) covers EffiSkill code, skill libraries, evaluation
statistics and generated candidates. No dependency source code is vendored.

## EffiBench-X

EffiSkill is evaluated on EffiBench-X (Apache-2.0), which is used by reference
only: no task statements, input programs or tests are included in this
repository or its release assets. `effiskill fetch-tasks` downloads them from
the upstream dataset. The `public`/`private` folders under `results/` hold only
recorded runtime and pass statistics.

- Software and evaluator: https://github.com/EffiBench/EffiBench-X
- Dataset: https://huggingface.co/datasets/EffiBench/effibench-x
- Paper: https://arxiv.org/abs/2505.13004

## Skill mining corpora

The skill libraries are derived from slow/fast pairs drawn from PIE, Mercury,
DeepMind Code Contests and APPS. The pairs are not redistributed. Cards contain
short illustrative snippets generated during mining, not copied pairs.
