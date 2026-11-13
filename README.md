# EffiSkill

Code for **Automated Code Efficiency Optimization via Agent Skill Mining**,
accepted to Findings of EACL 2027.

EffiSkill learns reusable optimization skills from slow/fast program pairs and
uses them to guide Python and C++ rewrites. This repository includes the archived
baseline implementation, a frozen Python skill library, and result-reconstruction
scripts.

[Paper](https://arxiv.org/abs/2603.27850) ·
[Releases](https://github.com/zimuwang-real/EffiSkill/releases)

## Install

Python 3.12 is recommended.

```bash
git clone https://github.com/zimuwang-real/EffiSkill.git
cd EffiSkill
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Reproduce archived results

```bash
effiskill reproduce-paper
```

Tables and figures are written to `outputs/rq1/` and `outputs/rq4/` using the
included evaluation statistics. This reconstructs recorded results; it does not
rerun model generation or benchmark execution.

## Use as an optimization baseline

```bash
python -m pip install -e '.[pipeline]'
effiskill infer --help
```

Follow the [usage guide](docs/usage.md) to configure a provider, optimize your
programs, or mine a new library. The frozen library is Python; the C++ pipeline
accepts a library you supply. Hosted calls retain the archived request format,
so check the guide's provider-compatibility requirements before running them.

## Documentation

- [Baseline usage and skill mining](docs/usage.md)
- [Reproduction commands, outputs, and development](docs/reproduction.md)
- [Data provenance and checksums](docs/provenance.md)

## Citation

The preprint currently uses the earlier title below. Final proceedings metadata
will be added when available.

```bibtex
@misc{wang2026effiskill,
  title={EffiSkill: Agent Skill Based Automated Code Efficiency Optimization},
  author={Zimu Wang and Yuling Shi and Mengfan Li and Zijun Liu and Jie M. Zhang and Chengcheng Wan and Xiaodong Gu},
  year={2026},
  eprint={2603.27850},
  archivePrefix={arXiv},
  url={https://arxiv.org/abs/2603.27850}
}
```

## License

EffiSkill code is [MIT licensed](LICENSE). See
[third-party notices](THIRD_PARTY_NOTICES.md) for data and dependency scope.
