"""Trace cleaning utilities for extraction-only skill library iterations."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .speedup_impact import parse_speedup_ratio


FASTER_RE = re.compile(r"\bFASTER\b(?:\s+([0-9]+(?:\.[0-9]+)?))?", re.IGNORECASE)
SLOWER_RE = re.compile(r"\bSLOWER\b(?:\s+([0-9]+(?:\.[0-9]+)?))?", re.IGNORECASE)
O_ONE_RE = re.compile(r"\b(?:O|Theta|Θ)\s*\(\s*1\s*\)", re.IGNORECASE)
NO_MEANINGFUL_PATTERNS = (
    "no meaningful",
    "effectively identical",
    "within noise",
    "code is identical",
    "visible portions are identical",
    "no material performance",
    "does not change asymptotic or practical runtime",
    "same number and type",
)


@dataclass(frozen=True)
class TraceCleaningConfig:
    """Policy knobs for deriving a positive mining trace set."""

    weak_speedup_cap: float = 2.0
    zero_delta_threshold: float = 0.1
    high_score_threshold: float = 3.0
    drop_no_meaningful: bool = True
    drop_slower: bool = True


def _listify(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _flatten_text(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (int, float, bool)):
        return [str(value)]
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            out.extend(_flatten_text(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(_flatten_text(item))
        return out
    return [str(value)]


def _delta_texts(trace: Dict[str, Any]) -> List[str]:
    delta = trace.get("DeltaSummary") or {}
    texts: List[str] = []
    for key in ("delta_type", "prediction", "direction", "verdict"):
        texts.extend(_flatten_text(delta.get(key)))
    for key in ("prediction", "verdict"):
        texts.extend(_flatten_text(trace.get(key)))
    return [x for x in texts if x.strip()]


def _delta_summary_text(trace: Dict[str, Any]) -> str:
    delta = trace.get("DeltaSummary") or {}
    return " ".join(_flatten_text(delta)).lower()


def _parse_delta_signal(trace: Dict[str, Any]) -> Tuple[str, Optional[float]]:
    texts = _delta_texts(trace)
    joined = " | ".join(texts)
    slower = SLOWER_RE.search(joined)
    faster = FASTER_RE.search(joined)
    if slower:
        return "slower", _parse_optional_float(slower.group(1))
    if faster:
        return "faster", _parse_optional_float(faster.group(1))
    return "unknown", None


def _parse_optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _time_text(trace: Dict[str, Any], audit_key: str) -> str:
    audit = trace.get(audit_key) or {}
    complexity = audit.get("complexity") or {}
    if isinstance(complexity, dict):
        return str(complexity.get("time") or "")
    return str(complexity)


def _problem_tags(trace: Dict[str, Any]) -> List[str]:
    problem = trace.get("ProblemBrief") or {}
    return [str(x).lower() for x in _listify(problem.get("problem_type_tags"))]


def _is_tiny_or_constant_time(trace: Dict[str, Any]) -> bool:
    tags = _problem_tags(trace)
    if any(tag in {"constant_time", "constant-time", "basic_io", "constant"} for tag in tags):
        return True
    slow_time = _time_text(trace, "SlowAudit")
    fast_time = _time_text(trace, "FastAudit")
    return bool(O_ONE_RE.search(slow_time) and O_ONE_RE.search(fast_time))


def _has_no_meaningful_change(trace: Dict[str, Any]) -> bool:
    text = _delta_summary_text(trace)
    return any(pattern in text for pattern in NO_MEANINGFUL_PATTERNS)


def _repair_schema(trace: Dict[str, Any], reasons: List[str]) -> Dict[str, Any]:
    repaired = dict(trace)
    if "SlowAudit" not in repaired and "SlowAudit:" in repaired:
        repaired["SlowAudit"] = repaired.pop("SlowAudit:")
        if "repaired_slowaudit_colon" not in reasons:
            reasons.append("repaired_slowaudit_colon")
    return repaired


def classify_trace(trace: Dict[str, Any], config: TraceCleaningConfig) -> Dict[str, Any]:
    """Classify one trace for positive skill mining."""

    reasons: List[str] = []
    repaired = _repair_schema(trace, reasons)
    raw_ratio = parse_speedup_ratio(repaired.get("speedup_ratio"))
    direction, delta_log = _parse_delta_signal(repaired)

    if direction == "slower":
        reasons.append("delta_says_slower")
    elif direction == "faster":
        reasons.append("delta_says_faster")
    else:
        reasons.append("delta_direction_unknown")

    if _has_no_meaningful_change(repaired):
        reasons.append("no_meaningful_change")

    if _is_tiny_or_constant_time(repaired):
        reasons.append("tiny_or_constant_time")

    if (
        delta_log is not None
        and delta_log <= config.zero_delta_threshold
        and raw_ratio is not None
        and raw_ratio >= config.high_score_threshold
    ):
        reasons.append("zero_delta_high_score")

    if config.drop_slower and "delta_says_slower" in reasons:
        role = "negative_or_noisy"
    elif config.drop_no_meaningful and "no_meaningful_change" in reasons:
        role = "negative_or_noisy"
    elif "zero_delta_high_score" in reasons:
        role = "negative_or_noisy"
    elif "tiny_or_constant_time" in reasons:
        role = "weak_positive"
    else:
        role = "positive"

    return {
        "role": role,
        "reasons": reasons,
        "raw_speedup_ratio": raw_ratio,
        "delta_direction": direction,
        "delta_log_speedup": delta_log,
    }


def clean_trace_record(
    trace: Dict[str, Any], config: TraceCleaningConfig
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Return a cleaned trace record, or None when excluded from positive mining."""

    decision = classify_trace(trace, config)
    repaired = _repair_schema(trace, decision["reasons"])
    if decision["role"] == "negative_or_noisy":
        return None, decision

    cleaned = dict(repaired)
    raw_ratio = decision["raw_speedup_ratio"]
    adjusted_ratio = raw_ratio
    if raw_ratio is not None and decision["role"] == "weak_positive":
        adjusted_ratio = min(float(raw_ratio), float(config.weak_speedup_cap))

    cleaned["speedup_ratio_raw"] = raw_ratio
    cleaned["speedup_ratio_adjusted"] = adjusted_ratio
    cleaned["speedup_ratio"] = adjusted_ratio
    cleaned["trace_quality_role"] = decision["role"]
    cleaned["trace_quality_reasons"] = list(dict.fromkeys(decision["reasons"]))
    return cleaned, decision


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def clean_traces_file(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    config: TraceCleaningConfig,
) -> Dict[str, Any]:
    os.makedirs(output_path.parent, exist_ok=True)
    os.makedirs(report_path.parent, exist_ok=True)

    role_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    kept = 0
    total = 0

    with output_path.open("w", encoding="utf-8") as f_out:
        for trace in _iter_jsonl(input_path):
            total += 1
            cleaned, decision = clean_trace_record(trace, config)
            role_counts[decision["role"]] += 1
            reason_counts.update(decision["reasons"])
            if cleaned is None:
                continue
            kept += 1
            f_out.write(json.dumps(cleaned, ensure_ascii=False) + "\n")

    report = {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "total_traces": total,
        "kept_traces": kept,
        "dropped_traces": total - kept,
        "role_counts": dict(role_counts),
        "reason_counts": dict(reason_counts),
        "config": {
            "weak_speedup_cap": config.weak_speedup_cap,
            "zero_delta_threshold": config.zero_delta_threshold,
            "high_score_threshold": config.high_score_threshold,
            "drop_no_meaningful": config.drop_no_meaningful,
            "drop_slower": config.drop_slower,
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean mined traces for positive skill extraction.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--weak-speedup-cap", type=float, default=2.0)
    parser.add_argument("--zero-delta-threshold", type=float, default=0.1)
    parser.add_argument("--high-score-threshold", type=float, default=3.0)
    parser.add_argument("--keep-slower", action="store_true")
    parser.add_argument("--keep-no-meaningful", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    config = TraceCleaningConfig(
        weak_speedup_cap=args.weak_speedup_cap,
        zero_delta_threshold=args.zero_delta_threshold,
        high_score_threshold=args.high_score_threshold,
        drop_slower=not args.keep_slower,
        drop_no_meaningful=not args.keep_no_meaningful,
    )
    report = clean_traces_file(
        input_path=Path(args.input),
        output_path=Path(args.output),
        report_path=Path(args.report),
        config=config,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
