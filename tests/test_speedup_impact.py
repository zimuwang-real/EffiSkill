from effiskill_artifact.speedup_impact import (
    HIGH_BAND,
    MILD_BAND,
    MODERATE_BAND,
    UNKNOWN_BAND,
    VERY_HIGH_BAND,
    SpeedupWeightConfig,
    attach_speedup_impact,
    combine_trace_weights,
    parse_speedup_ratio,
    speedup_band,
    speedup_weight,
    summarize_speedup_impact,
)


def test_parse_speedup_ratio_accepts_number_and_x_suffix():
    assert parse_speedup_ratio(2.5) == 2.5
    assert parse_speedup_ratio("3.2x") == 3.2
    assert parse_speedup_ratio("") is None
    assert parse_speedup_ratio(0) is None


def test_speedup_band_thresholds():
    assert speedup_band(None) == UNKNOWN_BAND
    assert speedup_band(1.2) == MILD_BAND
    assert speedup_band(2.0) == MODERATE_BAND
    assert speedup_band(5.0) == HIGH_BAND
    assert speedup_band(10.0) == VERY_HIGH_BAND


def test_speedup_weight_is_clipped_and_monotonic():
    cfg = SpeedupWeightConfig(cap=20.0, beta=2.0)

    assert speedup_weight(None, cfg) == 1.0
    assert speedup_weight(1.0, cfg) == 1.0
    assert 1.0 < speedup_weight(2.0, cfg) < speedup_weight(5.0, cfg)
    assert speedup_weight(20.0, cfg) == speedup_weight(200.0, cfg)


def test_attach_speedup_impact_sets_trace_weight():
    trace = {"speedup_ratio": "5x"}

    attach_speedup_impact(trace, config=SpeedupWeightConfig(cap=20.0, beta=2.0))

    assert trace["speedup_ratio"] == 5.0
    assert trace["speedup_impact_band"] == HIGH_BAND
    assert trace["trace_weight"] == trace["speedup_trace_weight"]


def test_combine_trace_weights_caps_product():
    assert combine_trace_weights(3.0, 4.0, max_combined_weight=9.0) == 9.0
    assert combine_trace_weights(2.0, 1.5, max_combined_weight=9.0) == 3.0


def test_summarize_speedup_impact():
    stats = summarize_speedup_impact(
        [
            {"speedup_ratio": 1.2, "trace_weight": 1.1},
            {"speedup_ratio": 4.0, "trace_weight": 2.0},
            {"speedup_ratio": 12.0, "trace_weight": 3.0},
        ]
    )

    assert stats["impact_support_count"] == 3
    assert stats["impact_support_weight"] == 6.1
    assert stats["impact_speedup_max"] == 12.0
    assert stats["impact_expected_band"] in {HIGH_BAND, VERY_HIGH_BAND}
