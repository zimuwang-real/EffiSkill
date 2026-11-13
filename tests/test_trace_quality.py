from effiskill_artifact.trace_quality import (
    TraceCleaningConfig,
    classify_trace,
    clean_trace_record,
)


def _trace(*, delta_type="FASTER 2.0", speedup_ratio=8.0, slow_time="O(n^2)", fast_time="O(n)"):
    return {
        "language": "cpp",
        "problem_id": "P1",
        "ProblemBrief": {
            "constraints_guess": {"notes": "large input"},
            "problem_type_tags": ["dynamic_programming"],
        },
        "SlowAudit": {
            "dominant_ops": ["nested loops"],
            "complexity": {"time": slow_time, "space": "O(n)"},
            "bottlenecks": [{"kind": "algorithmic", "detail": "quadratic loop"}],
        },
        "FastAudit": {
            "core_idea": "linear scan",
            "complexity": {"time": fast_time, "space": "O(n)"},
        },
        "DeltaSummary": {
            "delta_type": delta_type,
            "complexity_delta": {"from": slow_time, "to": fast_time, "note": "real improvement"},
            "transformation_steps": ["replace nested loops"],
            "trigger_signals": ["large nested loop"],
            "pitfalls": [],
        },
        "source_hash": "hash",
        "speedup_ratio": speedup_ratio,
    }


def test_slower_trace_is_dropped_from_positive_mining():
    trace = _trace(delta_type="SLOWER 1.0", speedup_ratio=12.0)

    cleaned, decision = clean_trace_record(trace, TraceCleaningConfig())

    assert cleaned is None
    assert decision["role"] == "negative_or_noisy"
    assert "delta_says_slower" in decision["reasons"]


def test_no_meaningful_high_score_trace_is_dropped():
    trace = _trace(delta_type="FASTER 0.0", speedup_ratio=20.0, slow_time="O(1)", fast_time="O(1)")
    trace["DeltaSummary"]["complexity_delta"]["note"] = "effectively identical; within noise"

    cleaned, decision = clean_trace_record(trace, TraceCleaningConfig())

    assert cleaned is None
    assert decision["role"] == "negative_or_noisy"
    assert "no_meaningful_change" in decision["reasons"]


def test_constant_time_positive_trace_is_kept_but_downweighted():
    trace = _trace(delta_type="FASTER 0.7", speedup_ratio=25.0, slow_time="O(1)", fast_time="O(1)")
    trace["ProblemBrief"]["problem_type_tags"] = ["constant_time", "basic_io"]

    cleaned, decision = clean_trace_record(trace, TraceCleaningConfig())

    assert cleaned is not None
    assert decision["role"] == "weak_positive"
    assert "tiny_or_constant_time" in decision["reasons"]
    assert cleaned["speedup_ratio_raw"] == 25.0
    assert cleaned["speedup_ratio"] == 2.0


def test_strong_algorithmic_positive_trace_keeps_original_score():
    trace = _trace(delta_type="FASTER 6.0", speedup_ratio=15.0)

    cleaned, decision = clean_trace_record(trace, TraceCleaningConfig())

    assert cleaned is not None
    assert decision["role"] == "positive"
    assert cleaned["speedup_ratio_raw"] == 15.0
    assert cleaned["speedup_ratio"] == 15.0


def test_schema_typo_slowaudit_colon_is_repaired():
    trace = _trace()
    trace["SlowAudit:"] = trace.pop("SlowAudit")

    cleaned, decision = clean_trace_record(trace, TraceCleaningConfig())

    assert cleaned is not None
    assert "SlowAudit" in cleaned
    assert "SlowAudit:" not in cleaned
    assert "repaired_slowaudit_colon" in decision["reasons"]


def test_classify_trace_accepts_prediction_field_for_algorithmic_delta():
    trace = _trace(delta_type="ALGORITHMIC", speedup_ratio=9.0)
    trace["DeltaSummary"]["prediction"] = "FASTER 10.0"

    decision = classify_trace(trace, TraceCleaningConfig())

    assert decision["role"] == "positive"
    assert "delta_says_faster" in decision["reasons"]
