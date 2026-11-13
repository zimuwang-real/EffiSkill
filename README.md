# EffiSkill

[Source repository](https://github.com/zimuwang-real/EffiSkill)

EffiSkill mines reusable optimization skill cards from code pairs and uses them
to guide model-generated Python and C++ optimizations. This standalone release
contains the available archived implementation, a frozen Python skill library,
and offline scripts that reconstruct archived RQ1/RQ4 tables and figures.

**Scope:** this is a cleaned release of the May 27, 2026 full ASE artifact with
its available local implementation updates. It does not establish complete
reproduction of the revised EACL evaluation. Mining options in this code include
later speedup-aware weighting and quality controls; do not assume their defaults
are the configuration that produced every archived paper result.

## Install

Use a fresh Python virtual environment (Python 3.12 tested; metadata permits
Python 3.10+):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
effiskill --help
```

This installs the offline reconstruction and registry dependencies. Installing
packages needs access to a package index; the commands below need no credentials,
model requests, or benchmark downloads after installation. The compatibility
command `effiskill-artifact` accepts the same arguments.

For development and the full existing test suite:

```bash
python -m pip install -e '.[pipeline,dev]' -c constraints-tested.txt
python -m pytest -q
```

The constraints record tested direct dependencies on Python 3.12/macOS ARM64;
they are not a universal lockfile. Optional embedding models, HDBSCAN and hosted
execution were not exercised in release validation. Use `.[embeddings]` in
addition to `.[pipeline]` if needed; `.[full]` requests both.

## Offline quick start

Build a registry from the hand-written toy card, without a model:

```bash
effiskill build-registry --language python -- \
  --skills_dir examples/toy_skills --out outputs/toy_registry.json
```

The toy card and CSV/JSONL examples demonstrate formats only; their names and
speedup field do not assert a measured improvement. The bundled research library
is separate: 29 Python operator cards plus four legacy ASE meta cards. The archived
inference implementation reads S1/S2/S3 meta cards; these auxiliary assets are
not presented as persistent-knowledge components of the revised EACL method.
Locate the library from an
installed package, including a wheel:

```bash
SKILLS_ROOT="$(python -c 'from effiskill_artifact.paths import data_root; print(data_root() / "rq4/fix-version/skills")')"
effiskill build-registry --language python -- \
  --skills_dir "$SKILLS_ROOT" --out outputs/frozen_registry.json
```

Rebuilding a registry writes a new file; keep the archived registry unchanged for
result reconstruction. The available frozen library is Python. The C++ pipeline
accepts a library you mine or supply; this release does not label a later,
experimental C++ library as the paper's frozen library.

## Reconstruct archived results offline

From any writable working directory after installation:

```bash
effiskill reproduce-paper
```

This writes `outputs/rq1/` and `outputs/rq4/` beneath your current working
directory. It computes tables/figures from recorded evaluation statistics and
skill assignments; it does not rerun model generation, execute submissions,
reconstruct benchmark timing, or recover private test cases.

You can run each part separately and choose explicit output directories:

```bash
effiskill reproduce-rq1 -- --output-dir outputs/rq1
effiskill reproduce-rq4 -- --output-dir outputs/rq4
```

Outputs include `table1_rq1.csv`, its LaTeX version, mean-speedup summaries and
three RQ1 PDF figures, plus `table3_skill_family_summary.csv`, its LaTeX version
and `rq4_claims.csv`. `public` and `private` in the data directories denote the
archived evaluator splits; both contain recorded statistics, not downloadable
private tests. RQ4 logs are metadata-only projections, with candidate order,
identifiers and skill assignments preserved. No candidate code is required for
the emitted RQ4 summary outputs. See [PROVENANCE.md](PROVENANCE.md).

For a headless machine, set `MPLBACKEND=Agg`; set `MPLCONFIGDIR` to a writable
directory if the default Matplotlib cache directory is unavailable. PDF metadata
and fonts may differ across platforms.

## Use as an optimization baseline (optional model calls)

The following workflow sends code and task text to your configured provider and
may incur charges. No provider or credentials are bundled. Choose your provider
and supply its configuration yourself:

**Archived request profile:** the hosted callers retain the original Chat
Completions parameters, including explicit nondefault `temperature` values and
`max_completion_tokens`. Your endpoint must accept that request profile. In
particular, this profile is incompatible with the standard OpenAI GPT-5 mini
endpoint, which does not support those temperature settings; see the
[official parameter-compatibility guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2).
The model names in the historical mining example below therefore require a
compatible gateway, not just access to that named model. A provider-adapter
update and live validation are separate from this archived release.

```bash
python -m pip install -e '.[pipeline]'
export EFFISKILL_BASE_URL='https://your-provider.example/v1'
export EFFISKILL_API_KEY='your-key'
export EFFISKILL_MODEL='your-model'
export EFFISKILL_LLM_TIMEOUT_SEC=180
```

`configs/providers.example.yaml` documents environment names; it is not an
automatically loaded configuration file. Prefer environment variables over
putting secrets in command history. From the repository root, with `SKILLS_ROOT`
set by the offline command above:

```bash
effiskill infer --language python -- \
  --dataset custom --data examples/tasks.csv --slow-column slow_code \
  --skills-root "$SKILLS_ROOT" --out outputs/toy_runs.jsonl
```

Inference generates candidates and static/interface diagnostics. It does not
execute code or establish correctness/speedup; evaluate candidates with your own
correctness tests and timing protocol. For C++, use `--language cpp`, your C++
task CSV and a C++ skills directory.

To mine your own library, use a representative corpus you have rights to use.
`examples/pairs.jsonl` illustrates the schema only; a single toy pair is not a
validated mining workload. Set `MY_PAIRS_JSONL` to your own multi-task corpus.

**Archived extractor restriction:** both language extractors require
`--fallback-model` to start with `gpt-5`. Its default is `EFFISKILL_MODEL`, so a
Qwen-only configuration fails before mining starts. Use a provider/endpoint
that actually supports the GPT-5-family model selected below; changing the name
does not add provider support. This restriction does not apply to the separate
inference command. Hosted execution/provider compatibility has not been tested
in this release preparation.

The following optional workflow makes model requests. Its explicit primary and
fallback model names assume your configured gateway accepts the archived
`gpt-5-mini` request profile described above:

```bash
export MY_PAIRS_JSONL='/absolute/path/to/your_pairs.jsonl'
effiskill pairs-to-traces --language python -- \
  --input "$MY_PAIRS_JSONL" --output outputs/my_traces.jsonl \
  --cache-dir outputs/trace_cache --fail-dir outputs/trace_failures \
  --model gpt-5-mini
effiskill extract-skills --language python -- \
  --traces outputs/my_traces.jsonl --gen-dir outputs/my_library \
  --cluster-mode stage1 --cluster-algorithm kmeans \
  --model gpt-5-mini --fallback-model gpt-5-mini \
  --disable-sentence-embeddings
```

Use `--language cpp` for analogous C++ commands. Pass explicit input, skills
and output paths for real workflows; historical pipeline defaults reference
stage directories that are not shipped. Extractor help lists available options,
including `--no-speedup-aware-mining`; new mining runs do not reproduce the
frozen library by construction. Historical C++ helper scripts are retained
under `scripts/` with their original options and must be run from the repository
root with your own input files. They use `EFFISKILL_MODEL` for both primary and
fallback, so the same GPT-5-family restriction applies; they can overwrite a
chosen output directory when explicitly configured to do so.

Raw mining corpora, benchmark statements/solutions and test cases are excluded.
Obtain benchmark data and evaluation tooling from the official
[EffiBench-X repository](https://github.com/EffiBench/EffiBench-X) and
[dataset](https://huggingface.co/datasets/EffiBench/effibench-x), under their
upstream terms. Both are linked by the
[NeurIPS 2025 benchmark paper](https://proceedings.neurips.cc/paper_files/paper/2025/hash/6b8198f777d1ba87a8250368db2ea16a-Abstract-Datasets_and_Benchmarks_Track.html).
Adapt your permitted inputs to the documented pair/task formats. The release
contains no evaluator or complete benchmark-acquisition pipeline.

## Build and licensing

```bash
python -m pip wheel --no-deps . --wheel-dir /tmp/effiskill-wheels
```

Wheels include the frozen reference assets. Both editable installation and wheel
installation support offline reconstruction from outside the checkout. Do not
copy generated `build/`, caches or environment folders into a source release.

EffiSkill code is licensed under [MIT](LICENSE). Benchmark statistics, derived
skill assets and external dependencies have the provenance and limitations in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md); the code license does not grant
rights to third-party benchmark inputs. Citation metadata is in
[CITATION.cff](CITATION.cff). See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) before
publishing a version or describing reproduced scientific claims.


## Research citation

The accepted Findings of EACL 2027 paper is titled **Automated Code Efficiency
Optimization via Agent Skill Mining**. The current arXiv preprint retains the
earlier title below; no final proceedings DOI is asserted here.

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
