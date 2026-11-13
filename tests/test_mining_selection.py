import numpy as np

from effiskill_artifact.mining_selection import (
    apply_support_reject,
    cluster_by_similarity_threshold,
    resolve_min_support,
    select_similarity_threshold_by_support_coverage,
)


def test_resolve_min_support_scales_with_clean_trace_count():
    assert resolve_min_support(749, alpha=0.01, floor=6) == 8
    assert resolve_min_support(100, alpha=0.01, floor=6) == 6
    assert resolve_min_support(1200, alpha=0.01, floor=6) == 12


def test_resolve_min_support_default_uses_one_percent_of_trace_count():
    assert resolve_min_support(749) == 8
    assert resolve_min_support(100) == 6
    assert resolve_min_support(1200) == 12


def test_threshold_clustering_derives_cluster_count_from_similarity():
    features = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.97, 0.03, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.97, 0.03],
        ],
        dtype=float,
    )

    result = cluster_by_similarity_threshold(features, similarity_threshold=0.90)

    assert result.k == 2
    assert result.labels[0] == result.labels[1]
    assert result.labels[2] == result.labels[3]
    assert result.labels[0] != result.labels[2]


def test_support_reject_removes_low_support_after_merge():
    summaries = [
        {"proposed_name": "Strong", "support_count": 8, "support_weight": 11.0},
        {"proposed_name": "Weak", "support_count": 7, "support_weight": 20.0},
    ]

    kept, report = apply_support_reject(
        summaries=summaries,
        min_support=8,
        mode="reject",
    )

    assert [s["proposed_name"] for s in kept] == ["Strong"]
    assert report["mode"] == "reject"
    assert report["min_support"] == 8
    assert report["rejected_count"] == 1


def test_support_warn_reports_without_filtering():
    summaries = [
        {"proposed_name": "Strong", "support_count": 8, "support_weight": 11.0},
        {"proposed_name": "Weak", "support_count": 7, "support_weight": 20.0},
    ]

    kept, report = apply_support_reject(
        summaries=summaries,
        min_support=8,
        mode="warn",
    )

    assert [s["proposed_name"] for s in kept] == ["Strong", "Weak"]
    assert report["warned_count"] == 1
    assert report["rejected_count"] == 0


def test_auto_threshold_selects_highest_supported_coverage_threshold():
    angles = np.deg2rad([0, 20, 40, 120, 140, 160])
    features = np.column_stack([np.cos(angles), np.sin(angles)])

    selection = select_similarity_threshold_by_support_coverage(
        features,
        candidate_thresholds=[0.90, 0.70],
        min_support=3,
        min_coverage=1.0,
    )

    assert selection.selected_threshold == 0.70
    assert selection.k == 2
    assert selection.supported_coverage == 1.0
    assert len(selection.report_rows) == 2
    assert selection.report_rows[0]["threshold"] == 0.90
    assert selection.report_rows[0]["meets_coverage"] is False
    assert selection.report_rows[1]["meets_coverage"] is True


def test_auto_threshold_reports_failure_without_selection():
    features = np.eye(5)

    selection = select_similarity_threshold_by_support_coverage(
        features,
        candidate_thresholds=[0.90, 0.80],
        min_support=2,
        min_coverage=0.50,
    )

    assert selection.selected_threshold is None
    assert selection.labels == []
    assert selection.supported_coverage == 0.0
    assert [row["supported_trace_count"] for row in selection.report_rows] == [0, 0]
