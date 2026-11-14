"""Shared skill-mining selection rules."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import normalize

DEFAULT_CLUSTER_SIMILARITY_THRESHOLD = "auto"
DEFAULT_THRESHOLD_SWEEP_HIGH = 0.90
DEFAULT_THRESHOLD_SWEEP_LOW = 0.20
DEFAULT_THRESHOLD_SWEEP_STEP = 0.02
DEFAULT_SUPPORT_REJECT_ALPHA = 0.01
DEFAULT_SUPPORT_REJECT_FLOOR = 6


@dataclass
class ThresholdClusterResult:
    labels: List[int]
    k: int


@dataclass
class ThresholdSelectionResult:
    labels: List[int]
    k: int
    selected_threshold: Optional[float]
    supported_coverage: float
    report_rows: List[Dict[str, Any]]


def parse_cluster_similarity_threshold(value: Any) -> Any:
    text = str(value).strip().lower()
    if text == "auto":
        return "auto"
    try:
        threshold = float(text)
    except ValueError as exc:
        raise ValueError("--cluster-similarity-threshold must be 'auto' or a float") from exc
    if not (0.0 < threshold < 1.0):
        raise ValueError("--cluster-similarity-threshold must be between 0 and 1")
    return threshold


def resolve_min_support(
    n_clean: int,
    alpha: float = DEFAULT_SUPPORT_REJECT_ALPHA,
    floor: int = DEFAULT_SUPPORT_REJECT_FLOOR,
) -> int:
    if n_clean < 0:
        raise ValueError("n_clean must be non-negative")
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    if floor < 0:
        raise ValueError("floor must be non-negative")
    return int(max(floor, math.ceil(float(alpha) * int(n_clean))))


def default_similarity_threshold_candidates(
    high: float = DEFAULT_THRESHOLD_SWEEP_HIGH,
    low: float = DEFAULT_THRESHOLD_SWEEP_LOW,
    step: float = DEFAULT_THRESHOLD_SWEEP_STEP,
) -> List[float]:
    if not (0.0 < low <= high < 1.0):
        raise ValueError("threshold sweep bounds must satisfy 0 < low <= high < 1")
    if step <= 0.0:
        raise ValueError("threshold sweep step must be positive")
    values: List[float] = []
    current = float(high)
    while current >= float(low) - 1e-12:
        values.append(round(current, 4))
        current -= float(step)
    return sorted(set(values), reverse=True)


def _stable_relabel(labels: Sequence[int]) -> List[int]:
    mapping: Dict[int, int] = {}
    out: List[int] = []
    for raw in labels:
        raw_int = int(raw)
        if raw_int not in mapping:
            mapping[raw_int] = len(mapping)
        out.append(mapping[raw_int])
    return out


def cluster_by_similarity_threshold(
    features: Any,
    similarity_threshold: float = DEFAULT_CLUSTER_SIMILARITY_THRESHOLD,
) -> ThresholdClusterResult:
    threshold = float(similarity_threshold)
    if threshold <= 0.0 or threshold >= 1.0:
        raise ValueError("similarity_threshold must be between 0 and 1")

    if hasattr(features, "toarray"):
        matrix = features.toarray()
    else:
        matrix = np.asarray(features, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("features must be a 2D matrix")
    n = int(matrix.shape[0])
    if n == 0:
        return ThresholdClusterResult(labels=[], k=0)
    if n == 1:
        return ThresholdClusterResult(labels=[0], k=1)

    matrix = normalize(matrix)
    distance_threshold = 1.0 - threshold
    try:
        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            metric="cosine",
            linkage="average",
            compute_full_tree=True,
        )
    except TypeError:
        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            affinity="cosine",
            linkage="average",
            compute_full_tree=True,
        )
    labels = _stable_relabel(model.fit_predict(matrix).tolist())
    return ThresholdClusterResult(labels=labels, k=len(set(labels)))


def _cluster_size_report(labels: List[int], min_support: int, n: int) -> Dict[str, Any]:
    counts = np.bincount(np.asarray(labels, dtype=int)) if labels else np.array([], dtype=int)
    supported = counts[counts >= int(min_support)] if counts.size else np.array([], dtype=int)
    supported_trace_count = int(supported.sum()) if supported.size else 0
    return {
        "k": int(len(counts)),
        "singleton_count": int((counts == 1).sum()) if counts.size else 0,
        "supported_cluster_count": int(len(supported)),
        "supported_trace_count": supported_trace_count,
        "supported_coverage": float(supported_trace_count / n) if n > 0 else 0.0,
        "min_cluster_size": int(counts.min()) if counts.size else 0,
        "median_cluster_size": float(np.median(counts)) if counts.size else 0.0,
        "max_cluster_size": int(counts.max()) if counts.size else 0,
    }


def select_similarity_threshold_by_support_coverage(
    features: Any,
    candidate_thresholds: Optional[Sequence[float]] = None,
    min_support: int = 1,
    min_coverage: float = 0.80,
) -> ThresholdSelectionResult:
    min_support = int(min_support)
    if min_support <= 0:
        raise ValueError("min_support must be positive")
    min_coverage = float(min_coverage)
    if not (0.0 < min_coverage <= 1.0):
        raise ValueError("min_coverage must be in (0, 1]")

    thresholds = (
        list(candidate_thresholds)
        if candidate_thresholds is not None
        else default_similarity_threshold_candidates()
    )
    thresholds = sorted({float(x) for x in thresholds}, reverse=True)
    if not thresholds:
        raise ValueError("candidate_thresholds must not be empty")

    if hasattr(features, "shape"):
        n = int(features.shape[0])
    else:
        n = int(np.asarray(features).shape[0])

    rows: List[Dict[str, Any]] = []
    best_row: Optional[Dict[str, Any]] = None
    best_labels: List[int] = []
    best_k = 0
    best_threshold: Optional[float] = None

    for threshold in thresholds:
        result = cluster_by_similarity_threshold(features, similarity_threshold=threshold)
        row = {
            "threshold": round(float(threshold), 4),
            **_cluster_size_report(result.labels, min_support=min_support, n=n),
        }
        row["meets_coverage"] = bool(row["supported_coverage"] >= min_coverage)
        rows.append(row)
        if best_row is None or row["supported_coverage"] > best_row["supported_coverage"]:
            best_row = row
        if row["meets_coverage"]:
            best_labels = result.labels
            best_k = result.k
            best_threshold = row["threshold"]
            return ThresholdSelectionResult(
                labels=best_labels,
                k=best_k,
                selected_threshold=best_threshold,
                supported_coverage=float(row["supported_coverage"]),
                report_rows=rows,
            )

    return ThresholdSelectionResult(
        labels=[],
        k=0,
        selected_threshold=None,
        supported_coverage=float(best_row["supported_coverage"] if best_row else 0.0),
        report_rows=rows,
    )


def _support_count(summary: Dict[str, Any]) -> int:
    try:
        return int(summary.get("support_count", 0) or 0)
    except Exception:
        return 0


def apply_support_reject(
    summaries: List[Dict[str, Any]],
    min_support: int,
    mode: str = "off",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    mode = str(mode or "off").strip().lower()
    if mode not in {"off", "warn", "reject"}:
        raise ValueError("mode must be one of: off, warn, reject")
    min_support = int(min_support)
    low_support = [s for s in summaries if _support_count(s) < min_support]

    if mode == "reject":
        kept = [s for s in summaries if _support_count(s) >= min_support]
        rejected_count = len(low_support)
        warned_count = 0
    else:
        kept = list(summaries)
        rejected_count = 0
        warned_count = len(low_support) if mode == "warn" else 0

    report = {
        "mode": mode,
        "min_support": min_support,
        "input_count": len(summaries),
        "low_support_count": len(low_support),
        "warned_count": warned_count,
        "rejected_count": rejected_count,
        "kept_count": len(kept),
    }
    return kept, report


def _clean_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_text(v) for v in value if _clean_text(v)]
    return [_clean_text(value)] if _clean_text(value) else []


def _token_set(items: Iterable[str]) -> set:
    out = set()
    for item in items:
        for tok in re.findall(r"[a-z][a-z0-9_]{2,}", _clean_text(item).lower()):
            out.add(tok)
    return out


def _normalize_name_key(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)
    text = re.sub(r"[^A-Za-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _mechanism_family(summary: Dict[str, Any]) -> str:
    doc = " ".join(
        [
            _normalize_name_key(summary.get("proposed_name")),
            _normalize_name_key(summary.get("primary_mechanism")),
            _normalize_name_key(summary.get("description")),
            " ".join(_normalize_name_key(x) for x in _listify(summary.get("tags"))),
            " ".join(_normalize_name_key(x) for x in _listify(summary.get("canonical_triggers"))),
        ]
    )
    if not doc:
        return ""
    words = set(doc.split())
    if "forward star" in doc or ("adjacency" in words and {"flat", "contiguous"} & words):
        return "flat_adjacency"
    if "fast io" in doc or "iostream" in words or "getchar" in words or "fread" in words:
        return "fast_io"
    if "recursive" in words and "dp" in words and ("bottom up" in doc or "iterative" in words):
        return "recursive_dp_to_iterative"
    if "dijkstra" in words and ("bfs" in words or "0 1" in doc or "01" in words):
        return "shortest_path_specialization"
    if ("map" in words or "set" in words or "associative" in words) and (
        "flat" in words or "array" in words or "sort" in words
    ):
        return "associative_to_flat_array"
    if "radix" in words and "sort" in words:
        return "integer_radix_sort"
    if "union find" in doc or "dsu" in words:
        return "union_find"
    if "prefix" in words and ("aggregation" in words or "fusion" in words):
        return "prefix_aggregation"
    if "closed form" in doc or "formula" in words:
        return "closed_form_math"
    return ""


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return float(len(a & b) / len(a | b))


def _scope_compatible(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    a = _clean_text(left.get("optimization_scope", "mixed")).lower() or "mixed"
    b = _clean_text(right.get("optimization_scope", "mixed")).lower() or "mixed"
    return a == b or a == "mixed" or b == "mixed"


def _trigger_or_tag_overlap(left: Dict[str, Any], right: Dict[str, Any]) -> float:
    left_triggers = _token_set(_listify(left.get("canonical_triggers")))
    right_triggers = _token_set(_listify(right.get("canonical_triggers")))
    if left_triggers and right_triggers:
        return _jaccard(left_triggers, right_triggers)
    return _jaccard(_token_set(_listify(left.get("tags"))), _token_set(_listify(right.get("tags"))))


def can_merge_summaries(
    left: Dict[str, Any],
    right: Dict[str, Any],
    text_similarity: float,
    similarity_threshold: float,
    overlap_threshold: float = 0.20,
) -> bool:
    if not _scope_compatible(left, right):
        return False
    left_name = _normalize_name_key(left.get("proposed_name"))
    right_name = _normalize_name_key(right.get("proposed_name"))
    if left_name and left_name == right_name:
        return True

    if float(text_similarity) < float(similarity_threshold):
        return False
    overlap = _trigger_or_tag_overlap(left, right)
    return overlap >= float(overlap_threshold)
