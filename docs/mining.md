# Skill mining (Stage I)

Stage I turns slow/fast program pairs into a library of Operator Skill cards.
Install with `python -m pip install -e '.[pipeline,embeddings]'`. Without the
`embeddings` extra (or with `--disable-sentence-embeddings`), a truncated SVD of
the TF-IDF features (at most 128 dimensions, seed 42) replaces the sentence
embeddings, as in Appendix B.4.

```bash
effiskill pairs-to-traces --language python --input pairs.jsonl --output traces.jsonl \
  --cache-dir outputs/trace_cache --fail-dir outputs/trace_failures
effiskill extract-skills --language python --traces traces.jsonl --gen-dir outputs/my_library
effiskill build-registry --skills-dir outputs/my_library/skills   # rebuild registry.json after editing cards
```

The library is written to `<gen-dir>/skills`; pass it to
`effiskill infer --skills-root`. The LLM endpoint is configured as in
[inference.md](inference.md).

## Input pairs

CSV or JSONL, one pair per row. Accepted shapes:

1. **Slow/fast columns** (default): `problem_id`, `statement`, `slow_code`,
   `fast_code`, optional `speedup_ratio`. Rename with `--problem-id-column`,
   `--statement-column`, `--slow-column`, `--fast-column`,
   `--speedup-ratio-column`. See `examples/pairs.jsonl`.
2. **A/B comparison rows**: `input` holds two fenced blocks labelled
   `Code A` and `Code B`, and `output` starts with `FASTER` or `SLOWER`
   (whether B is faster than A). The adapter restores slow/fast order.
3. **Input/output rows**: `input` is the slow program and `output` the fast
   one. Set `direction` to `reverse` (or `fast_to_slow`, `output_to_input`) for
   rows stored the other way round.

Shapes 2 and 3 take the statement from `statement`, `instruction` or `prompt`.
Duplicate pairs are dropped before trace extraction.

## Paper settings

The defaults follow Appendix B.

| Setting | Value |
|---|---|
| Pairs | 900 unique slow/fast pairs per language (1,800 directional rows before normalization). C++ from PIE; Python from PIE, Mercury, DeepMind Code Contests and APPS. None overlap with EffiBench-X. |
| LLM | GPT-5.1 for trace extraction and cluster summarization |
| Features | row-normalized word TF-IDF (unigrams and bigrams, 4,096 features) concatenated with normalized `all-MiniLM-L6-v2` embeddings |
| Clustering | KMeans, seed 42; cluster count chosen by cosine silhouette over even values around √n (`--k` fixes it) |
| Consolidation | merge summaries with compatible scope whose names match, or whose TF-IDF cosine similarity is at least 0.76 (`--merge-similarity`) with enough trigger or tag overlap |

Options that go beyond the paper are off by default:
`--speedup-aware-mining` (weight traces by `speedup_ratio`),
`--filter-semantic-risk-traces`, `--cluster-algorithm threshold`, and
`--cluster-mode stage3` (refinement from evaluation feedback, which needs
`--feedback-paths` and `--prior-skills-root`).

## Reproducibility

The released libraries in `skills/python` and `skills/cpp` are the exact ones
used for all reported results. They received a cleanup pass after
mining, and LLM outputs vary between calls, so re-mining the same pairs gives a
similar but not identical library. Use the released libraries to run EffiSkill
as described in the paper, and the mining pipeline to build libraries for new
languages, corpora or models.
