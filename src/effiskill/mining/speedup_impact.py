"""Speedup-aware mining and retrieval metadata helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import median
from typing import Any, Dict, Iterable, List, Optional

UNKNOWN_BAND = "unknown"
MILD_BAND = "mild"
MODERATE_BAND = "moderate"
HIGH_BAND = "high"
VERY_HIGH_BAND = "very_high"


@dataclass(frozen=True)
class SpeedupWeightConfig:
    cap: float = 20.0
    beta: float = 2.0
    enabled: bool = True


def parse_speedup_ratio(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().lower().removesuffix("x").strip()
        if not value:
            return None
    try:
        ratio = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(ratio) or ratio <= 0:
        return None
    return ratio


def speedup_band(speedup_ratio: Optional[float]) -> str:
    if speedup_ratio is None:
        return UNKNOWN_BAND
    if speedup_ratio >= 10.0:
        return VERY_HIGH_BAND
    if speedup_ratio >= 3.0:
        return HIGH_BAND
    if speedup_ratio >= 1.5:
        return MODERATE_BAND
    return MILD_BAND


def speedup_weight(speedup_ratio: Optional[float], config: SpeedupWeightConfig) -> float:
    if not config.enabled:
        return 1.0
    if speedup_ratio is None or speedup_ratio <= 1.0:
        return 1.0
    cap = max(1.000001, float(config.cap))
    beta = max(0.0, float(config.beta))
    clipped = min(float(speedup_ratio), cap)
    normalized = math.log(clipped) / math.log(cap)
    return float(1.0 + beta * normalized)


def attach_speedup_impact(
    trace: Dict[str, Any],
    *,
    ratio_key: str = "speedup_ratio",
    config: SpeedupWeightConfig,
) -> Dict[str, Any]:
    ratio = parse_speedup_ratio(trace.get(ratio_key))
    weight = speedup_weight(ratio, config)
    trace["speedup_ratio"] = ratio
    trace["speedup_impact_band"] = speedup_band(ratio)
    trace["speedup_trace_weight"] = round(weight, 6)
    trace["trace_weight"] = round(weight, 6)
    return trace


def combine_trace_weights(
    speedup_weight_value: Any,
    feedback_weight_value: Any,
    *,
    max_combined_weight: float = 9.0,
) -> float:
    speedup_w = float(speedup_weight_value or 1.0)
    feedback_w = float(feedback_weight_value or 1.0)
    combined = speedup_w * feedback_w
    return float(min(max(combined, 0.000001), max_combined_weight))


def _percentile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(values[lo])
    frac = pos - lo
    return float(values[lo] * (1 - frac) + values[hi] * frac)


def summarize_speedup_impact(traces: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    trace_list = list(traces)
    ratios = [
        ratio
        for ratio in (parse_speedup_ratio(t.get("speedup_ratio")) for t in trace_list)
        if ratio is not None
    ]
    weights = [float(t.get("trace_weight", 1.0) or 1.0) for t in trace_list]
    band_counts: Dict[str, int] = {
        UNKNOWN_BAND: 0,
        MILD_BAND: 0,
        MODERATE_BAND: 0,
        HIGH_BAND: 0,
        VERY_HIGH_BAND: 0,
    }
    for trace in trace_list:
        band = speedup_band(parse_speedup_ratio(trace.get("speedup_ratio")))
        band_counts[band] += 1
    expected = UNKNOWN_BAND if not ratios else speedup_band(_percentile(ratios, 0.75))
    return {
        "impact_support_count": len(trace_list),
        "impact_support_weight": round(sum(weights), 6),
        "impact_speedup_median": round(float(median(ratios)), 6) if ratios else 0.0,
        "impact_speedup_p75": round(_percentile(ratios, 0.75), 6) if ratios else 0.0,
        "impact_speedup_max": round(max(ratios), 6) if ratios else 0.0,
        "impact_expected_band": expected,
        "impact_band_counts": band_counts,
    }
