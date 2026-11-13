# Publication checklist

This checklist records the reviewed scope of the source release.

- [x] EffiSkill-authored software uses the author-selected MIT license.
- [x] Source is curated from the full May 27 archive with scientific logic preserved.
- [x] Raw benchmark inputs, mining corpora, full inference logs and private endpoints are excluded.
- [x] Installation, existing regression tests, registry construction and archived-output reconstruction are checked offline after dependency installation.
- [x] Frozen data checksums and source mappings are recorded in `provenance.json`.
- [x] Review the distributed data scope: numeric evaluation statistics, metadata-only skill assignments, and generic derived skill illustrations; raw upstream benchmark inputs and tests are excluded. Third-party scope is documented separately from the MIT code license.
- [x] Set the repository URL in citation metadata: `https://github.com/zimuwang-real/EffiSkill`.
- [ ] Add final publication bibliography/DOI only when authoritative metadata is available.
- [ ] Independently assess scientific claims and verify any desired revised EACL experiments. This cleanup does not resolve statistical, experimental or claimed-improvement issues.
- [x] Review the exact files to publish, excluding caches, environment/build directories and internal preparation reports.

The available archived RQ1/RQ4 reconstruction is distinct from generating new
optimizations and from rerunning evaluator tests/timings. No complete revised
EACL reproduction should be claimed based solely on these offline commands.
