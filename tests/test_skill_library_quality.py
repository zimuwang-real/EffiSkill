import json
from pathlib import Path

from effiskill.mining import extract_skills
from effiskill.mining import extract_skills_cpp
from effiskill.mining.library_quality import (
    build_library_diversity_report,
    example_sanity_warnings,
    validate_cluster_summary_quality,
    write_example_sanity_report,
    write_library_diversity_report,
)


def test_llm_json_call_retries_invalid_json_until_limit(monkeypatch, tmp_path):
    calls = []
    responses = ["not json", "still not json", "{\"ok\": true}"]

    def fake_chat_completion(**kwargs):
        calls.append(kwargs["stage"])
        return responses.pop(0)

    monkeypatch.setattr(extract_skills, "cached_chat_completion", fake_chat_completion)

    obj = extract_skills._llm_json_call(
        messages=[{"role": "user", "content": "x"}],
        cache_dir=str(tmp_path / "cache"),
        stage="stage",
        model="m",
        temperature=0.2,
        max_tokens=100,
        out_fail_dir=str(tmp_path / "fail"),
        max_retries=3,
    )

    assert obj == {"ok": True}
    assert calls == ["stage", "stage_retry1", "stage_retry2"]


def test_llm_json_call_stops_after_retry_limit_without_fallback(monkeypatch, tmp_path):
    calls = []

    def fake_chat_completion(**kwargs):
        calls.append(kwargs["stage"])
        return "not json"

    monkeypatch.setattr(extract_skills, "cached_chat_completion", fake_chat_completion)

    obj = extract_skills._llm_json_call(
        messages=[{"role": "user", "content": "x"}],
        cache_dir=str(tmp_path / "cache"),
        stage="stage",
        model="m",
        temperature=0.2,
        max_tokens=100,
        out_fail_dir=str(tmp_path / "fail"),
        fallback_model="other-model",
        max_retries=3,
    )

    assert obj is None
    assert calls == ["stage", "stage_retry1", "stage_retry2", "stage_retry3"]
    assert "fallback" not in " ".join(calls)


def test_active_summary_finalization_bypasses_semantic_filter_but_keeps_support_reject():
    raw = [
        {
            "cluster_id": "C001",
            "proposed_name": "Hardcode Bounds Removal",
            "description": "Avoid hard-coded oversized bounds.",
            "optimization_scope": "implementation",
            "tags": ["bounds"],
            "canonical_triggers": ["hard-coded limit"],
            "canonical_steps": ["derive size from constraints"],
            "support_count": 8,
            "support_weight": 8.0,
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Weak",
            "description": "Too little support.",
            "optimization_scope": "implementation",
            "tags": ["weak"],
            "canonical_triggers": ["rare"],
            "canonical_steps": ["cleanup"],
            "support_count": 4,
            "support_weight": 40.0,
        },
    ]

    final, report = extract_skills.finalize_cluster_summaries_for_library(
        raw_summaries=raw,
        merge_similarity=0.99,
        min_skills=0,
        max_skills=None,
        min_support_count=8,
        support_reject_mode="reject",
    )

    assert [s["proposed_name"] for s in final] == ["Hardcode Bounds Removal"]
    assert report["semantic_filter_active"] is False
    assert report["support_reject"]["rejected_count"] == 1


def test_sanitize_summary_keeps_complete_description_sentences_without_generic_fallback():
    raw = {
        "cluster_id": "C001",
        "proposed_name": "UnionFindReplacementForGraphTraversal",
        "description": (
            "Replace explicit graph construction and traversal with a compact DSU when only "
            "connectivity or relative differences matter. "
            "This long second sentence intentionally contains many details about DFS, BFS, "
            "Prim, constraint propagation, weighted potentials, path compression, union by "
            "size, component aggregates, and cache locality so that a naive character limit "
            "would cut it in the middle of an unfinished clause that damages the final card."
        ),
        "primary_mechanism": (
            "Model graph connectivity and pairwise constraints with optimized Union-Find "
            "instead of explicit adjacency traversal."
        ),
        "optimization_scope": "algorithmic",
        "tags": ["dsu"],
        "canonical_triggers": ["only connectivity matters"],
        "canonical_steps": ["replace traversal with union/find operations"],
        "support_count": 12,
        "support_weight": 12.0,
    }

    for module in (extract_skills, extract_skills_cpp):
        clean = module.sanitize_summary(raw)
        assert clean["description"].endswith(".")
        assert "Reusable optimization pattern distilled" not in clean["description"]
        assert validate_cluster_summary_quality(clean) == []


def test_generic_or_incomplete_summary_fields_fail_quality_validation():
    bad = {
        "cluster_id": "C001",
        "proposed_name": "Replace Dijkstra With BFS",
        "description": "Reusable optimization pattern distilled from weighted traces.",
        "primary_mechanism": "Replace generic graph algorithm with specialized algorithm that",
        "optimization_scope": "algorithmic",
        "tags": ["graph"],
        "canonical_triggers": ["unweighted graph"],
        "canonical_steps": ["use BFS"],
        "support_count": 8,
        "support_weight": 8.0,
    }

    warnings = validate_cluster_summary_quality(bad)
    assert "generic_description" in warnings
    assert "incomplete_primary_mechanism" in warnings


def test_exact_normalized_name_summaries_merge_even_when_long_text_similarity_is_low():
    raw = [
        {
            "cluster_id": "C001",
            "proposed_name": "FlatForwardStarAdjacency",
            "description": "Use flat adjacency arrays for static tree DFS workloads.",
            "primary_mechanism": "Replace vector adjacency with flat forward-star arrays.",
            "optimization_scope": "data_structure",
            "tags": ["graphs", "dfs", "tree"],
            "canonical_triggers": ["tree DFS with vector allocation overhead"],
            "canonical_steps": ["build head to next arrays"],
            "support_count": 12,
            "support_weight": 20.0,
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Flat Forward Star Adjacency",
            "description": "Store graph edges in a contiguous edge pool for sparse traversal.",
            "primary_mechanism": "Use head/to/nxt arrays instead of per-node dynamic containers.",
            "optimization_scope": "data_structure",
            "tags": ["static_arrays", "memory_layout", "sparse_graph"],
            "canonical_triggers": ["contiguous edge storage is needed for cache locality"],
            "canonical_steps": ["preallocate edge arrays and link by integer indices"],
            "support_count": 13,
            "support_weight": 30.0,
        },
    ]

    final, _ = extract_skills.finalize_cluster_summaries_for_library(
        raw_summaries=raw,
        merge_similarity=0.99,
        min_skills=0,
        max_skills=None,
        min_support_count=8,
        support_reject_mode="reject",
    )

    assert len(final) == 1
    assert final[0]["support_count"] == 25
    assert sorted(final[0]["cluster_ids"]) == ["C001", "C002"]


def test_distinct_names_do_not_merge_on_broad_mechanism_family_alone():
    raw = [
        {
            "cluster_id": "C001",
            "proposed_name": "Flatten Abstractions To Primitive Loops",
            "description": "Replace high-level wrappers, maps, sets, and vectors with primitive array arithmetic in hot loops.",
            "primary_mechanism": "Replace STL containers and modint wrappers with primitive arrays.",
            "optimization_scope": "implementation",
            "tags": ["arrays", "map", "constant-factor"],
            "canonical_triggers": ["array overhead in hot loops"],
            "canonical_steps": ["rewrite hot loop with primitive arrays"],
            "support_count": 20,
            "support_weight": 20.0,
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Single Pass Decision Without Aux Arrays",
            "description": "Collapse multi-pass array logic and auxiliary arrays into one streaming pass.",
            "primary_mechanism": "Collapse multi-pass O(n) logic plus auxiliary O(n) arrays into a single streaming pass.",
            "optimization_scope": "implementation",
            "tags": ["arrays", "map", "constant-factor"],
            "canonical_triggers": ["array overhead in hot loops"],
            "canonical_steps": ["replace auxiliary arrays with scalar state"],
            "support_count": 12,
            "support_weight": 12.0,
        },
        {
            "cluster_id": "C003",
            "proposed_name": "Replace Associative Containers With Flat Arrays",
            "description": "Use direct indexing or sorted vectors instead of maps for bounded keys.",
            "primary_mechanism": "Replace map/set counting with flat arrays or sorted vectors.",
            "optimization_scope": "data_structure",
            "tags": ["map", "array"],
            "canonical_triggers": ["bounded integer keys"],
            "canonical_steps": ["map keys to indices"],
            "support_count": 14,
            "support_weight": 14.0,
        },
    ]

    final, _ = extract_skills.finalize_cluster_summaries_for_library(
        raw_summaries=raw,
        merge_similarity=0.99,
        min_skills=0,
        max_skills=None,
        min_support_count=8,
        support_reject_mode="reject",
    )

    assert [s["proposed_name"] for s in final] == [
        "Flatten Abstractions To Primitive Loops",
        "Replace Associative Containers With Flat Arrays",
        "Single Pass Decision Without Aux Arrays",
    ]


def test_example_sanity_warns_without_blocking_render(tmp_path):
    warnings = example_sanity_warnings(
        language="cpp",
        before_code="int main(){ slow_op(); }",
        after_code="int main(){ std: :cout << 1; }",
    )

    assert "placeholder_token" in warnings
    assert "cpp_formatting_artifact" in warnings

    report_path = tmp_path / "example_sanity_report.json"
    report = write_example_sanity_report(
        report_path,
        [
            {
                "skill_id": "O001",
                "language": "cpp",
                "before_code": "int main(){ slow_op(); }",
                "after_code": "int main(){ std: :cout << 1; }",
            }
        ],
        mode="warn",
    )

    assert report["mode"] == "warn"
    assert report["warning_count"] >= 2
    assert json.loads(report_path.read_text())["items"][0]["skill_id"] == "O001"


def test_python_example_sanity_uses_ast_for_complete_modules():
    assert example_sanity_warnings("python", "x = 1\nprint(x)", "x = 2\nprint(x)") == []
    assert "python_ast_parse_error" in example_sanity_warnings("python", "def f(:\n pass", "x = 2")


def test_library_diversity_report_flags_near_duplicates(tmp_path):
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "Replace Segment Tree With Fenwick Tree",
            "primary_mechanism": "replace segment tree with fenwick tree",
            "secondary_mechanisms": ["flat arrays"],
            "optimization_scope": "data_structure",
            "tags": ["segment-tree", "fenwick"],
            "canonical_triggers": ["point update prefix query"],
            "canonical_steps": ["replace segment tree with fenwick tree"],
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Use Fenwick Instead Of Segment Tree",
            "primary_mechanism": "replace segment tree with fenwick tree",
            "secondary_mechanisms": ["lower memory"],
            "optimization_scope": "data_structure",
            "tags": ["segment-tree", "fenwick"],
            "canonical_triggers": ["point update prefix query"],
            "canonical_steps": ["replace segment tree with fenwick tree"],
        },
        {
            "cluster_id": "C003",
            "proposed_name": "Fast Input",
            "primary_mechanism": "replace slow input with buffered scanning",
            "secondary_mechanisms": [],
            "optimization_scope": "io",
            "tags": ["io"],
            "canonical_triggers": ["large input"],
            "canonical_steps": ["use buffered scanner"],
        },
    ]

    report = build_library_diversity_report(summaries)
    assert report["operator_count"] == 3
    assert report["near_duplicate_pairs"]
    assert report["primary_mechanism_duplicate_counts"]["replace segment tree with fenwick tree"] == 2

    out = tmp_path / "library_diversity_report.json"
    write_library_diversity_report(out, summaries)
    assert json.loads(out.read_text())["operator_count"] == 3


def test_library_diversity_report_flags_exact_name_duplicates_even_with_low_text_overlap():
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "FastBufferedIntegerIO",
            "primary_mechanism": "replace slow input with fread integer scanning",
            "secondary_mechanisms": [],
            "optimization_scope": "io",
            "tags": ["fast-io", "fread"],
            "canonical_triggers": ["integer-heavy input"],
            "canonical_steps": ["implement buffered reader"],
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Fast Buffered Integer IO",
            "primary_mechanism": "disable stream overhead and parse tokens manually",
            "secondary_mechanisms": [],
            "optimization_scope": "io",
            "tags": ["cin-cout", "buffering"],
            "canonical_triggers": ["endl flushing dominates"],
            "canonical_steps": ["untie cin and use newline"],
        },
    ]

    report = build_library_diversity_report(summaries)
    assert report["near_duplicate_pairs"]
    assert report["near_duplicate_pairs"][0]["reason"] == "same_normalized_name"
