# Third-party notices and data scope

The MIT license in `LICENSE` applies to EffiSkill-authored software and release
documentation. It does not relicense upstream datasets, benchmark problems,
solutions, test suites, dependency packages, or their authors' contributions.

The source artifact contains no standalone third-party license/NOTICE files
that could be verified and copied. No additional permission grant is inferred
from that absence. Dependencies are installed separately and retain their own
licenses; their source code is not vendored here.

The frozen reference statistics were produced by the archived evaluation on
EffiBench-X tasks (identifiers include Aizu and AtCoder problem families).
Statistics contain task identifiers, pass/runtime/memory records and aggregate
measurement fields. They are research records rather than benchmark problem
statements, reference solutions or executable test cases. The `private` split
name refers to the original evaluator's split; no private test cases ship here.

Skill cards and the registry are the archived EffiSkill-derived library.
They may contain illustrative optimization snippets. Their archive bytes are
preserved with provenance; this release does not assert exclusive ownership of
any underlying third-party algorithm or example. Obtain underlying benchmark
content from its upstream maintainer under its applicable terms.

Raw Python/C++ mining pairs, canonical solution CSVs, intermediate trace/profile
corpora and full inference logs are excluded because upstream redistribution
terms have not been established in this preparation. The RQ4 projections retain
only task IDs, candidate IDs/order and skill assignments required to reconstruct
the summaries; task statements, source/candidate code, prompts and local paths
are omitted. No benchmark-content license is invented or bundled as a substitute
for upstream terms.

The release review checked the distributed asset schemas, provenance hashes,
and representative skill examples. No raw benchmark statements, solutions or
tests, or concrete missing-attribution issue, were identified in that reviewed
scope. This records the scope of the review rather than a comprehensive
ownership determination. See `PROVENANCE.md` and `RELEASE_CHECKLIST.md` for the
exact distributed content.


Official upstream acquisition sources: [EffiBench-X code and evaluation
tooling](https://github.com/EffiBench/EffiBench-X) and the
[EffiBench-X dataset](https://huggingface.co/datasets/EffiBench/effibench-x).
These links are identified by the [NeurIPS 2025 benchmark paper
page](https://proceedings.neurips.cc/paper_files/paper/2025/hash/6b8198f777d1ba87a8250368db2ea16a-Abstract-Datasets_and_Benchmarks_Track.html).
Follow each upstream resource's own license/access instructions; linking to it
does not imply that its content is redistributed in this package.
