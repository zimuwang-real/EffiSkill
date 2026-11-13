# Data provenance

The baseline derives from the full EffiSkill artifact archive dated May 27,
2026 (SHA-256 `a3d49297a5b932b9121aa8fd8f008e3a3f82ce17ea346a02419c11fca1100e32`).
The scientific extraction, inference, ranking, and result-calculation code is
preserved. Changes concern packaging, CLI help, and portable input/output paths.

## Included assets

- Evaluation statistics used by archived RQ1/RQ4 reconstruction.
- The frozen Python library: 29 operator cards, four auxiliary meta cards, and
  their original registry. The archived inference code reads S1/S2/S3.
- RQ4 metadata containing task/candidate identifiers, order, and skill assignments.

[provenance.json](provenance.json) records archive-member names and source/release
SHA-256 checksums for 496 scientific assets and 22 Python modules. Of those data
assets, 494 retain their archive bytes; two inference logs were projected to the
metadata needed for reconstruction, removing code, prompts, and local paths.
The 46 unused statistics files removed during cleanup do not participate in
reconstruction. All eight reconstructed CSV/LaTeX outputs remain identical.

Raw mining corpora, benchmark programs/test cases, full inference logs, generated
experiments, and prior Git history are excluded. Benchmark inputs and execution
tooling can be obtained from [EffiBench-X](https://github.com/EffiBench/EffiBench-X)
and its [dataset](https://huggingface.co/datasets/EffiBench/effibench-x).

This release reconstructs recorded results rather than rerunning the benchmark.
It does not claim complete reproduction of the revised EACL evaluation.
See [reproduction](reproduction.md) and [third-party notices](../THIRD_PARTY_NOTICES.md).
