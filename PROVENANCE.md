# Source and reproducibility provenance

The authoritative release source is the latest full local
`artifact_release/effiskill_ase2026_artifact.zip`, dated May 27, 2026.
Its SHA-256 is
`a3d49297a5b932b9121aa8fd8f008e3a3f82ce17ea346a02419c11fca1100e32`.
The older main-only archive was not used. The source archive itself is not
required by, or included in, this standalone package.

`provenance.json` maps every bundled scientific asset to its source archive
member, source checksum and released checksum. Of 542 scientific files,
540 retain identical bytes; two inference logs are documented projections.
The 22 Python modules and 11 original test modules were recovered from that
archive. Scientific extraction, inference, ranking/selection, speedup weighting,
quality controls and result calculations are retained.

The release was compared with the available local `pipeline_new` and `src`
implementations. Many extracted files were macOS dataless placeholders; the
readable `CodeEffiGen.zip` supplied comparison copies. All 33 frozen skill cards
and their registry in `pipeline_new/fix-version/skills` match the selected
artifact exactly. `pipeline_new` is an alternate modular/configuration-based
pipeline, while `src/optimize.py` is a separate earlier optimizer; neither was
silently substituted for the latest standalone implementation. The selected
May artifact already includes available speedup-aware mining and inference
impact metadata updates. Its default settings are not asserted to be the
configuration behind the revised EACL paper.

## Allowlist

The package includes:

- All standalone `src/effiskill_artifact/*.py` modules.
- The 11 archived test modules, two archived C++ helper scripts, and the provider environment-name example.
- RQ1/RQ4 evaluation JSON statistics needed by the archived reconstruction scripts.
- The frozen Python registry, 29 operator cards and four legacy ASE meta cards.
- Minimal RQ4 candidate-to-skill metadata, new toy format examples, portability tests and release documentation.

`data/` from the archive is relocated under `src/effiskill_artifact/data/` so
wheels contain their own frozen assets. The revised EACL method's persistent
knowledge is the 29 Python operator skills; the four meta cards are auxiliary
legacy assets required by this archived inference implementation (S1/S2/S3 are
loaded). No frozen C++ library is represented as the paper's verified library.

Excluded: Git history, macOS resource forks/metadata, caches, generated experiment
outputs, internal reports, raw mining JSONL, benchmark canonical solutions,
intermediate trace/profile corpora, and full inference logs. No private endpoint,
API credential or evaluator test suite is distributed.

## RQ4 metadata projection

For each original JSONL row, preserve `problem_id`, every skill set's `set_id`
and selected `skill_id` values, and the original candidate array order and
candidate fields `candidate_id`, `set_id`, `plan_id`, `plan_style` when present.
For GPT-5-mini preserve `candidates`; for Qwen preserve `survivor_candidates`,
matching the unchanged archived RQ4 loader. Drop statements, code, local paths,
prompts, reasoning and fields unused by summary computation.

The original `candidate_code` column consequently becomes empty internally;
it is not used by any emitted RQ4 table/claim. No candidate rank, task assignment,
skill assignment or timing statistic is changed. All three reconstructed RQ4
CSV/LaTeX outputs are byte-identical when computed from the full original logs
and from these projections in the tested environment.

## Packaging-only behavior changes

- Add `effiskill` as an alias for the existing `effiskill-artifact` CLI and remove stale conference branding from help.
- Locate frozen inputs inside the installed Python package, supporting editable installs and wheels.
- Write default reconstruction outputs below the caller's working directory instead of the source checkout. Parsing help does not create output directories.
- Permit both registry builders to accept a bare output filename such as `registry.json`.
- Separate offline dependencies from optional hosted-pipeline and embedding dependencies; provide tested direct-dependency constraints.

All eight reconstructed CSV/LaTeX files match the source archive's stored
outputs byte-for-byte in the tested environment. Three PDF figures are generated
successfully; PDF byte identity is not promised across fonts/platforms.
This validates reconstruction of the available archived RQ1/RQ4 outputs,
not a rerun of generation, correctness/timing evaluation, or complete revised
EACL experiments. Scientific interpretation and unresolved experimental issues
remain for the authors to assess.
