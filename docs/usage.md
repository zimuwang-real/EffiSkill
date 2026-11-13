# Using EffiSkill as a baseline

Run the examples from the repository root after [installation](../README.md#install).

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

Set the frozen Python library path after installation:

```bash
SKILLS_ROOT="$(python -c 'from effiskill_artifact.paths import data_root; print(data_root() / "rq4/fix-version/skills")')"
```

Then run:

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
frozen library by construction. Use the same CLI commands for C++ with `--language cpp` and your own C++ inputs and skill library.

Raw mining corpora, benchmark statements/solutions and test cases are excluded.
Obtain benchmark data and evaluation tooling from the official
[EffiBench-X repository](https://github.com/EffiBench/EffiBench-X) and
[dataset](https://huggingface.co/datasets/EffiBench/effibench-x), under their
upstream terms. Both are linked by the
[NeurIPS 2025 benchmark paper](https://proceedings.neurips.cc/paper_files/paper/2025/hash/6b8198f777d1ba87a8250368db2ea16a-Abstract-Datasets_and_Benchmarks_Track.html).
Adapt your permitted inputs to the documented pair/task formats. The release
contains no evaluator or complete benchmark-acquisition pipeline.
