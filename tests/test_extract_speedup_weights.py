import json
import sys

import numpy as np

from effiskill_artifact import extract_skills, extract_skills_cpp
from effiskill_artifact.speedup_impact import SpeedupWeightConfig


def _write_trace(path, *, speedup_ratio):
    trace = {
        "problem_id": "P1",
        "speedup_ratio": speedup_ratio,
        "ProblemBrief": {"constraints_guess": {}, "problem_type_tags": ["array"]},
        "SlowAudit": {
            "dominant_ops": ["nested loops"],
            "complexity": {"time": "O(n^2)"},
            "bottlenecks": [{"kind": "asymptotic", "detail": "nested loops"}],
        },
        "FastAudit": {"core_idea": "use prefix sums", "complexity": {"time": "O(n)"}},
        "DeltaSummary": {
            "delta_type": ["algorithmic"],
            "complexity_delta": {"from": "O(n^2)", "to": "O(n)"},
            "transformation_steps": ["replace nested loop"],
            "trigger_signals": ["large n"],
            "pitfalls": [],
        },
    }
    path.write_text(json.dumps(trace) + "\n", encoding="utf-8")


def test_python_prepare_traces_uses_speedup_ratio(tmp_path):
    traces_path = tmp_path / "traces.jsonl"
    out_path = tmp_path / "normalized.jsonl"
    _write_trace(traces_path, speedup_ratio="5x")

    traces, stats = extract_skills.prepare_traces(
        str(traces_path),
        str(out_path),
        stage_mode="stage1",
        speedup_weight_config=SpeedupWeightConfig(cap=20.0, beta=2.0),
    )

    assert traces[0]["speedup_ratio"] == 5.0
    assert traces[0]["speedup_impact_band"] == "high"
    assert traces[0]["trace_weight"] > 1.0
    assert stats["impact_speedup_max"] == 5.0


def test_cpp_prepare_traces_uses_speedup_ratio(tmp_path):
    traces_path = tmp_path / "traces.jsonl"
    out_path = tmp_path / "normalized.jsonl"
    _write_trace(traces_path, speedup_ratio="12x")

    traces, stats = extract_skills_cpp.prepare_traces(
        str(traces_path),
        str(out_path),
        stage_mode="stage1",
        speedup_weight_config=SpeedupWeightConfig(cap=20.0, beta=2.0),
    )

    assert traces[0]["speedup_ratio"] == 12.0
    assert traces[0]["speedup_impact_band"] == "very_high"
    assert traces[0]["trace_weight"] > 1.0
    assert stats["impact_speedup_max"] == 12.0


def test_prepare_traces_filters_semantic_risk_traces_by_default(tmp_path):
    traces_path = tmp_path / "traces.jsonl"
    out_path = tmp_path / "normalized.jsonl"
    unsafe_trace = {
        "problem_id": "P_BAD",
        "speedup_ratio": 50.0,
        "ProblemBrief": {"constraints_guess": {}, "problem_type_tags": ["array"]},
        "SlowAudit": {"dominant_ops": [], "complexity": {}, "bottlenecks": []},
        "FastAudit": {"core_idea": "Emit a fixed output and ignore input."},
        "DeltaSummary": {
            "delta_type": ["SEMANTIC_CHANGE_NON_EQUIVALENT"],
            "complexity_delta": {"from": "O(n)", "to": "O(1)"},
            "transformation_steps": ["delete the algorithm"],
            "trigger_signals": ["constant output"],
            "pitfalls": [],
        },
    }
    safe_trace = {
        "problem_id": "P_OK",
        "speedup_ratio": 8.0,
        "ProblemBrief": {"constraints_guess": {}, "problem_type_tags": ["array"]},
        "SlowAudit": {"dominant_ops": [], "complexity": {}, "bottlenecks": []},
        "FastAudit": {"core_idea": "Use prefix sums."},
        "DeltaSummary": {
            "delta_type": ["algorithmic"],
            "complexity_delta": {"from": "O(n^2)", "to": "O(n)"},
            "transformation_steps": ["replace nested loop with prefix sums"],
            "trigger_signals": ["nested loop"],
            "pitfalls": [],
        },
    }
    traces_path.write_text(
        json.dumps(unsafe_trace) + "\n" + json.dumps(safe_trace) + "\n",
        encoding="utf-8",
    )

    traces, stats = extract_skills.prepare_traces(
        str(traces_path),
        str(out_path),
        stage_mode="stage1",
        speedup_weight_config=SpeedupWeightConfig(cap=20.0, beta=2.0),
    )

    assert [t["problem_id"] for t in traces] == ["P_OK"]
    assert stats["semantic_risk_filtered"] == 1


def test_prepare_traces_deduplicates_source_hashes(tmp_path):
    traces_path = tmp_path / "traces.jsonl"
    out_path = tmp_path / "normalized.jsonl"
    trace = {
        "source_hash": "same",
        "problem_id": "P_OK",
        "speedup_ratio": 8.0,
        "ProblemBrief": {"constraints_guess": {}, "problem_type_tags": ["array"]},
        "SlowAudit": {"dominant_ops": [], "complexity": {}, "bottlenecks": []},
        "FastAudit": {"core_idea": "Use prefix sums."},
        "DeltaSummary": {
            "delta_type": ["algorithmic"],
            "complexity_delta": {"from": "O(n^2)", "to": "O(n)"},
            "transformation_steps": ["replace nested loop with prefix sums"],
            "trigger_signals": ["nested loop"],
            "pitfalls": [],
        },
    }
    traces_path.write_text(
        json.dumps(trace) + "\n" + json.dumps(trace) + "\n",
        encoding="utf-8",
    )

    traces, stats = extract_skills.prepare_traces(
        str(traces_path),
        str(out_path),
        stage_mode="stage1",
        speedup_weight_config=SpeedupWeightConfig(cap=20.0, beta=2.0),
    )

    assert len(traces) == 1
    assert stats["duplicate_source_hash_filtered"] == 1


def test_semantic_risk_filter_allows_legitimate_arithmetic_semantic_change_phrase():
    trace = {
        "FastAudit": {
            "core_idea": "The only significant semantic change is heavier modular arithmetic."
        },
        "DeltaSummary": {
            "delta_type": ["SLOWER"],
            "transformation_steps": ["add redundant modulo operations"],
            "trigger_signals": ["modulo operations dominate"],
        },
    }

    assert not extract_skills.is_semantic_risk_trace(trace)


def test_cpp_graph_fallback_example_for_dsu_is_relevant():
    summary = {
        "proposed_name": "DSU based Connectivity with Flat Arrays",
        "tags": ["graph", "connected_components", "union_find"],
        "canonical_triggers": ["only need connectivity"],
        "canonical_steps": ["replace DFS adjacency traversal with DSU"],
    }

    before, after = extract_skills_cpp._example_template_for_family(summary, "graph")

    assert "topo_dp" not in before + after
    assert "find_root" in after
    assert "unite" in after
    assert "vector<vector<int>>" in before


def test_cluster_profiles_include_speedup_impact_stats(tmp_path):
    traces = [
        {
            "trace_id": "T1",
            "problem_id": "P1",
            "speedup_ratio": 2.0,
            "speedup_impact_band": "moderate",
            "speedup_trace_weight": 1.4,
            "trace_weight": 1.4,
            "ProblemBrief": {"problem_type_tags": ["array"]},
            "SlowAudit": {"bottlenecks": [{"kind": "asymptotic"}]},
            "DeltaSummary": {
                "delta_type": ["algorithmic"],
                "complexity_delta": {"from": "O(n^2)", "to": "O(n)"},
                "trigger_signals": ["large n"],
                "transformation_steps": ["replace nested loop"],
            },
        },
        {
            "trace_id": "T2",
            "problem_id": "P2",
            "speedup_ratio": 12.0,
            "speedup_impact_band": "very_high",
            "speedup_trace_weight": 2.7,
            "trace_weight": 2.7,
            "ProblemBrief": {"problem_type_tags": ["array"]},
            "SlowAudit": {"bottlenecks": [{"kind": "asymptotic"}]},
            "DeltaSummary": {
                "delta_type": ["algorithmic"],
                "complexity_delta": {"from": "O(n^2)", "to": "O(n)"},
                "trigger_signals": ["large n"],
                "transformation_steps": ["replace nested loop"],
            },
        },
    ]

    profiles = extract_skills.build_cluster_profiles(
        traces=traces,
        labels=[0, 0],
        out_path=str(tmp_path / "profiles.jsonl"),
        sample_per_cluster=2,
    )

    profile = profiles["C001"]
    assert profile["impact_speedup_max"] == 12.0
    assert profile["impact_expected_band"] in {"high", "very_high"}
    assert profile["sample_traces"][0]["speedup_ratio"] == 12.0
    assert profile["sample_traces"][0]["speedup_impact_band"] == "very_high"


def test_summarize_cluster_preserves_profile_impact_stats(monkeypatch, tmp_path):
    def fake_llm_json_call(**kwargs):
        return {
            "proposed_name": "Counting Rewrite",
            "description": "Replace repeated enumeration with counting.",
            "tags": ["counting"],
            "optimization_scope": "algorithmic",
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["count grouped cases"],
            "complexity_time": "O(n^2) to O(n)",
            "complexity_space": "O(n)",
        }

    monkeypatch.setattr(extract_skills, "_llm_json_call", fake_llm_json_call)
    profile = {
        "cluster_id": "C001",
        "size": 7,
        "support_weight": 11.5,
        "impact_support_count": 7,
        "impact_support_weight": 11.5,
        "impact_speedup_median": 4.0,
        "impact_speedup_p75": 9.0,
        "impact_speedup_max": 20.0,
        "impact_expected_band": "very_high",
        "top_steps": [],
        "top_triggers": [],
        "top_problem_tags": [],
    }

    summary = extract_skills.summarize_cluster(
        profile=profile,
        cache_dir=str(tmp_path / "cache"),
        fail_dir=str(tmp_path / "fail"),
        model="model",
        fallback_model="model",
        temperature=0.2,
        max_tokens=100,
        reasoning_effort="low",
    )

    assert summary is not None
    assert summary["impact_support_count"] == 7
    assert summary["impact_support_weight"] == 11.5
    assert summary["impact_speedup_median"] == 4.0
    assert summary["impact_speedup_p75"] == 9.0
    assert summary["impact_speedup_max"] == 20.0
    assert summary["impact_expected_band"] == "very_high"
    assert summary["expected_speedup_band"] == "very_high"


def test_dedup_merge_summaries_preserves_impact_fields():
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "Counting Rewrite",
            "description": "Replace repeated enumeration with counting.",
            "tags": ["counting"],
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["count grouped cases"],
            "support_count": 2,
            "support_weight": 3.0,
            "impact_support_count": 2,
            "impact_support_weight": 3.0,
            "impact_speedup_median": 2.0,
            "impact_speedup_p75": 3.0,
            "impact_speedup_max": 4.0,
            "impact_expected_band": "moderate",
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Counting Rewrite",
            "description": "Replace repeated enumeration with counting.",
            "tags": ["counting"],
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["count grouped cases"],
            "support_count": 3,
            "support_weight": 6.0,
            "impact_support_count": 3,
            "impact_support_weight": 6.0,
            "impact_speedup_median": 5.0,
            "impact_speedup_p75": 8.0,
            "impact_speedup_max": 12.0,
            "impact_expected_band": "high",
        },
    ]

    merged = extract_skills.dedup_merge_summaries(
        summaries=summaries,
        merge_similarity=0.1,
        min_skills=1,
    )

    assert len(merged) == 1
    assert merged[0]["impact_support_count"] == 5
    assert merged[0]["impact_support_weight"] == 9.0
    assert merged[0]["impact_speedup_max"] == 12.0
    assert merged[0]["impact_expected_band"] == "high"


def test_semantically_unsafe_summaries_are_filtered_before_skill_writing():
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "Replace Algorithm With Constant Output Stub",
            "description": "Emit a fixed output and ignore input; this is not functionally equivalent.",
            "tags": ["stub", "unsafe"],
            "canonical_triggers": ["output does not depend on input"],
            "canonical_steps": ["delete the algorithm"],
            "support_count": 10,
            "support_weight": 30.0,
            "impact_expected_band": "very_high",
            "impact_speedup_p75": 30.0,
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Counting Rewrite",
            "description": "Replace repeated enumeration with grouped counting.",
            "tags": ["counting"],
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["derive grouped count"],
            "support_count": 3,
            "support_weight": 5.0,
            "impact_expected_band": "high",
            "impact_speedup_p75": 8.0,
        },
    ]

    filtered = extract_skills.filter_semantically_unsafe_summaries(summaries)

    assert [s["proposed_name"] for s in filtered] == ["Counting Rewrite"]


def test_dedup_merge_summaries_reserves_high_impact_when_truncated():
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "Mild Container Cleanup",
            "description": "Reduce small container overhead.",
            "tags": ["container"],
            "canonical_triggers": ["minor overhead"],
            "canonical_steps": ["reserve vector capacity"],
            "support_count": 100,
            "support_weight": 100.0,
            "impact_expected_band": "mild",
            "impact_speedup_p75": 1.2,
            "impact_speedup_max": 1.4,
        },
        {
            "cluster_id": "C002",
            "proposed_name": "High Impact Counting Rewrite",
            "description": "Replace nested enumeration with counting.",
            "tags": ["counting"],
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["derive grouped count"],
            "support_count": 3,
            "support_weight": 3.0,
            "impact_expected_band": "high",
            "impact_speedup_p75": 8.0,
            "impact_speedup_max": 20.0,
        },
    ]

    merged = extract_skills.dedup_merge_summaries(
        summaries=summaries,
        merge_similarity=0.99,
        min_skills=1,
        max_skills=1,
    )

    assert len(merged) == 1
    assert merged[0]["proposed_name"] == "High Impact Counting Rewrite"


def test_dedup_merge_summaries_uses_scope_and_trigger_guards():
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "Shared Optimization Pattern",
            "description": "Replace repeated work with a cached compact representation.",
            "optimization_scope": "io",
            "tags": ["shared", "cache"],
            "canonical_triggers": ["many formatted output operations"],
            "canonical_steps": ["cache reusable formatted strings"],
            "support_count": 10,
            "support_weight": 10.0,
            "impact_expected_band": "high",
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Shared Optimization Pattern",
            "description": "Replace repeated work with a cached compact representation.",
            "optimization_scope": "algorithmic",
            "tags": ["shared", "cache"],
            "canonical_triggers": ["repeated graph state exploration"],
            "canonical_steps": ["cache reusable formatted strings"],
            "support_count": 10,
            "support_weight": 10.0,
            "impact_expected_band": "high",
        },
    ]

    merged = extract_skills.dedup_merge_summaries(
        summaries=summaries,
        merge_similarity=0.76,
        min_skills=1,
    )

    assert len(merged) == 2


def test_support_reject_happens_after_merge_and_bypasses_min_skill_fallback():
    summaries = [
        {
            "cluster_id": "C001",
            "proposed_name": "Counting Rewrite",
            "description": "Replace repeated enumeration with grouped counting.",
            "optimization_scope": "algorithmic",
            "tags": ["counting"],
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["derive grouped count"],
            "support_count": 4,
            "support_weight": 4.0,
            "impact_expected_band": "high",
        },
        {
            "cluster_id": "C002",
            "proposed_name": "Counting Rewrite",
            "description": "Replace repeated enumeration with grouped counting.",
            "optimization_scope": "algorithmic",
            "tags": ["counting"],
            "canonical_triggers": ["nested enumeration"],
            "canonical_steps": ["derive grouped count"],
            "support_count": 4,
            "support_weight": 4.0,
            "impact_expected_band": "high",
        },
        {
            "cluster_id": "C003",
            "proposed_name": "Tiny Cleanup",
            "description": "Reduce a small constant factor.",
            "optimization_scope": "implementation",
            "tags": ["constant_factor"],
            "canonical_triggers": ["minor overhead"],
            "canonical_steps": ["reserve a vector"],
            "support_count": 3,
            "support_weight": 30.0,
            "impact_expected_band": "high",
        },
    ]

    merged = extract_skills.dedup_merge_summaries(
        summaries=summaries,
        merge_similarity=0.76,
        min_skills=3,
        min_support_count=8,
        support_reject_mode="reject",
    )

    assert len(merged) == 1
    assert merged[0]["proposed_name"] == "Counting Rewrite"
    assert merged[0]["support_count"] == 8


def test_python_and_cpp_extractors_expose_threshold_cli(monkeypatch):
    argv = [
        "extract-skills",
        "--cluster-algorithm",
        "threshold",
        "--cluster-similarity-threshold",
        "0.80",
        "--support-reject-mode",
        "reject",
        "--support-reject-alpha",
        "0.01",
        "--support-reject-floor",
        "6",
        "--min-skills",
        "off",
        "--merge-similarity",
        "0.76",
    ]

    monkeypatch.setattr(sys, "argv", argv)
    py_args = extract_skills.parse_args()
    monkeypatch.setattr(sys, "argv", argv)
    cpp_args = extract_skills_cpp.parse_args()

    for args in (py_args, cpp_args):
        assert args.cluster_algorithm == "threshold"
        assert args.cluster_similarity_threshold == 0.80
        assert args.support_reject_mode == "reject"
        assert args.support_reject_alpha == 0.01
        assert args.support_reject_floor == 6
        assert args.min_skills == "off"
        assert args.merge_similarity == 0.76


def test_python_and_cpp_threshold_cli_default_uses_one_percent_support(monkeypatch):
    argv = ["extract-skills", "--cluster-algorithm", "threshold"]

    for module in (extract_skills, extract_skills_cpp):
        monkeypatch.setattr(sys, "argv", argv)
        args = module.parse_args()
        assert args.cluster_similarity_threshold == "auto"
        assert args.support_reject_alpha == 0.01


def test_python_and_cpp_extractors_default_to_eight_summary_workers(monkeypatch):
    argv = ["extract-skills"]

    for module in (extract_skills, extract_skills_cpp):
        monkeypatch.setattr(sys, "argv", argv)
        args = module.parse_args()
        assert args.summary_workers == 8


def test_parallel_cluster_summary_preserves_cluster_order(monkeypatch, tmp_path):
    profiles = {
        "C002": {"cluster_id": "C002"},
        "C001": {"cluster_id": "C001"},
        "C003": {"cluster_id": "C003"},
    }
    calls = []

    def fake_summarize_cluster(**kwargs):
        cluster_id = kwargs["profile"]["cluster_id"]
        calls.append(cluster_id)
        return {
            "cluster_id": cluster_id,
            "proposed_name": f"Skill {cluster_id}",
            "description": "desc",
            "tags": [],
            "canonical_triggers": [],
            "canonical_steps": [],
            "common_pitfalls": [],
            "complexity_time": "",
            "complexity_space": "",
            "when_not_to_use": [],
            "support_count": 1,
            "support_weight": 1.0,
        }

    monkeypatch.setattr(extract_skills, "summarize_cluster", fake_summarize_cluster)

    summaries = extract_skills.summarize_cluster_profiles(
        cluster_profiles=profiles,
        cache_dir=str(tmp_path / "cache"),
        fail_dir=str(tmp_path / "fail"),
        model="m",
        fallback_model="m",
        temperature=0.2,
        max_tokens=1024,
        reasoning_effort="low",
        summary_workers=3,
    )

    assert [s["cluster_id"] for s in summaries] == ["C001", "C002", "C003"]
    assert sorted(calls) == ["C001", "C002", "C003"]


def test_threshold_cluster_algorithm_rejects_fixed_k(monkeypatch):
    argv = [
        "extract-skills",
        "--cluster-algorithm",
        "threshold",
        "--cluster-similarity-threshold",
        "0.80",
        "--k",
        "40",
    ]

    for module in (extract_skills, extract_skills_cpp):
        monkeypatch.setattr(sys, "argv", argv)
        try:
            module.parse_args()
        except SystemExit as exc:
            assert exc.code != 0
        else:
            raise AssertionError("threshold clustering with fixed --k should fail")


def test_auto_threshold_cluster_traces_writes_pre_llm_report(monkeypatch, tmp_path):
    angles = np.deg2rad([0, 20, 40, 120, 140, 160])
    features = np.column_stack([np.cos(angles), np.sin(angles)])
    traces = [{"trace_id": f"T{i}", "problem_id": f"P{i}"} for i in range(6)]
    signatures = [f"trace {i}" for i in range(6)]

    def fake_features(**kwargs):
        return features, features, features, "test-features"

    for module in (extract_skills, extract_skills_cpp):
        monkeypatch.setattr(module, "compute_hybrid_features", fake_features)
        report_path = tmp_path / f"{module.SKILL_LANGUAGE if hasattr(module, 'SKILL_LANGUAGE') else 'py'}_report.json"
        result = module.cluster_traces(
            traces=traces,
            signatures=signatures,
            clusters_path=str(tmp_path / f"{module.__name__}_clusters.jsonl"),
            tfidf_max_features=128,
            embedding_model="unused",
            disable_sentence_embeddings=True,
            k=None,
            cluster_algorithm="threshold",
            cluster_similarity_threshold="auto",
            min_support_count=3,
            min_cluster_coverage=1.0,
            threshold_report_path=str(report_path),
        )

        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert result.k == 2
        assert result.cluster_similarity_threshold == report["selected_threshold"]
        assert report["selected_threshold"] is not None
        assert report["selected_k"] == 2
        assert report["min_support"] == 3
