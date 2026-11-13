# Reproducing archived results

These commands reconstruct the available archived RQ1/RQ4 outputs. They do not
rerun model generation or benchmark correctness/timing evaluation. The revised
EACL experiments remain separate from this archived reconstruction.

## Quick start

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

## Tables and figures

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
the emitted RQ4 summary outputs. See [provenance](provenance.md).

For a headless machine, set `MPLBACKEND=Agg`; set `MPLCONFIGDIR` to a writable
directory if the default Matplotlib cache directory is unavailable. PDF metadata
and fonts may differ across platforms.

## Development and build

Python 3.12 was tested. From the repository root:

```bash
python -m pip install -e '.[pipeline,dev]' -c constraints-tested.txt
python -m pytest -q
python -m pip wheel --no-deps . --wheel-dir /tmp/effiskill-wheels
```

`constraints-tested.txt` records tested direct dependencies on macOS ARM64,
rather than a universal lockfile. Optional embedding dependencies are available
through `.[embeddings]`; `.[full]` includes both pipeline and embedding extras.
Wheels include the frozen inputs needed for offline reconstruction.
