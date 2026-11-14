"""Shared diagnostics for mined skill libraries."""

from __future__ import annotations

import ast
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


GENERIC_SUMMARY_DESCRIPTION = "Reusable optimization pattern distilled from weighted traces."

PLACEHOLDER_PATTERN = re.compile(
    r"\b(?:slow_op|fast_op|preprocess\(data\)|baseline approach|TODO)\b",
    re.I,
)

INCOMPLETE_TAIL_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "because",
    "be",
    "by",
    "can",
    "could",
    "for",
    "from",
    "if",
    "in",
    "instead",
    "into",
    "is",
    "may",
    "of",
    "or",
    "such",
    "that",
    "the",
    "to",
    "up",
    "using",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
}


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_text(v) for v in value if _clean_text(v)]
    text = _clean_text(value)
    return [text] if text else []


def normalize_skill_name_key(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)
    text = re.sub(r"[^A-Za-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def _tail_word(text: str) -> str:
    words = re.findall(r"[A-Za-z]+", _clean_text(text).lower())
    return words[-1] if words else ""


def looks_incomplete_text(text: Any) -> bool:
    value = _clean_text(text)
    if not value:
        return True
    low = value.lower().rstrip("`'\" )].,:;-")
    if low.endswith(":"):
        return True
    if re.search(r"[=+\-*/]\s*$", low):
        return True
    if _tail_word(low) in INCOMPLETE_TAIL_WORDS:
        return True
    if value.count("(") > value.count(")"):
        return True
    if value.count("[") > value.count("]"):
        return True
    if value.count("{") > value.count("}"):
        return True
    return False


def sentence_safe_truncate(
    text: Any,
    max_chars: int,
    *,
    max_sentences: int = 2,
    min_boundary_chars: int = 80,
) -> str:
    value = _clean_text(text)
    if not value:
        return ""
    if len(value) <= max_chars:
        return value

    candidates: List[int] = []
    for match in re.finditer(r"(?<=[.!?])(?:[\"')\]]+)?\s+", value):
        boundary = match.end()
        if boundary <= max_chars:
            candidates.append(boundary)
    if candidates:
        if max_sentences > 0:
            chosen = candidates[min(len(candidates), max_sentences) - 1]
            if chosen <= max_chars and chosen >= min_boundary_chars:
                return value[:chosen].strip()
        chosen = candidates[-1]
        if chosen >= min_boundary_chars:
            return value[:chosen].strip()

    cut = value[:max_chars].rstrip()
    boundary = max(cut.rfind("; "), cut.rfind(", "), cut.rfind(" "))
    if boundary >= max(min_boundary_chars, int(max_chars * 0.65)):
        cut = cut[:boundary].rstrip()
    return cut.rstrip(" .,:;-")


def validate_cluster_summary_quality(summary: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    name = _clean_text(summary.get("proposed_name"))
    desc = _clean_text(summary.get("description"))
    primary = _clean_text(summary.get("primary_mechanism"))

    if not name:
        warnings.append("missing_proposed_name")
    if not desc:
        warnings.append("missing_description")
    elif desc.lower() == GENERIC_SUMMARY_DESCRIPTION.lower():
        warnings.append("generic_description")
    elif looks_incomplete_text(desc):
        warnings.append("incomplete_description")
    elif len(desc) > 80 and desc[-1] not in ".!?)]}'\"`":
        warnings.append("incomplete_description")

    if not primary:
        warnings.append("missing_primary_mechanism")
    elif primary.lower() == GENERIC_SUMMARY_DESCRIPTION.lower():
        warnings.append("generic_primary_mechanism")
    elif looks_incomplete_text(primary):
        warnings.append("incomplete_primary_mechanism")

    if name and len(normalize_skill_name_key(name).split()) < 2:
        warnings.append("underspecified_name")

    return sorted(set(warnings))


def infer_mechanism_family(summary: Dict[str, Any]) -> str:
    doc = " ".join(
        [
            normalize_skill_name_key(summary.get("proposed_name")),
            normalize_skill_name_key(summary.get("primary_mechanism")),
            normalize_skill_name_key(summary.get("description")),
            " ".join(normalize_skill_name_key(x) for x in _listify(summary.get("tags"))),
            " ".join(
                normalize_skill_name_key(x) for x in _listify(summary.get("canonical_triggers"))
            ),
        ]
    )
    if not doc:
        return "unknown"
    if "forward star" in doc or ("adjacency" in doc and {"flat", "contiguous"} & set(doc.split())):
        return "flat_adjacency"
    if "fast io" in doc or "iostream" in doc or "getchar" in doc or "fread" in doc:
        return "fast_io"
    if "recursive" in doc and "dp" in doc and ("bottom up" in doc or "iterative" in doc):
        return "recursive_dp_to_iterative"
    if "dijkstra" in doc and ("bfs" in doc or "0 1" in doc or "01" in doc):
        return "shortest_path_specialization"
    if ("map" in doc or "set" in doc or "associative" in doc) and (
        "flat" in doc or "array" in doc or "sort" in doc
    ):
        return "associative_to_flat_array"
    if "radix" in doc and "sort" in doc:
        return "integer_radix_sort"
    if "union find" in doc or "dsu" in doc:
        return "union_find"
    if "prefix" in doc and ("aggregation" in doc or "fusion" in doc):
        return "prefix_aggregation"
    if "closed form" in doc or "formula" in doc:
        return "closed_form_math"
    return "other"


def _balanced_delimiters(text: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    opens = set(pairs.values())
    stack: List[str] = []
    quote: str | None = None
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch in opens:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack and quote is None


def _looks_like_complete_python(code: str) -> bool:
    stripped = code.strip()
    if not stripped or stripped.startswith((">>>", "...")):
        return False
    if stripped.startswith(("def ", "class ", "import ", "from ", "for ", "while ", "if ")):
        return True
    if "\n" in stripped and not code.startswith((" ", "\t")):
        return True
    return bool(re.search(r"(^|\n)\s*[A-Za-z_][A-Za-z0-9_]*\s*=", code))


def example_sanity_warnings(language: str, before_code: str, after_code: str) -> List[str]:
    warnings: List[str] = []
    before = str(before_code or "").strip()
    after = str(after_code or "").strip()
    combined = f"{before}\n{after}"

    if not before:
        warnings.append("missing_before")
    if not after:
        warnings.append("missing_after")
    if before and after and before == after:
        warnings.append("identical_before_after")
    if PLACEHOLDER_PATTERN.search(combined):
        warnings.append("placeholder_token")
    if "..." in combined or "…" in combined:
        warnings.append("ellipsis_artifact")
    if "std: :" in combined:
        warnings.append("cpp_formatting_artifact")
    if not _balanced_delimiters(combined):
        warnings.append("unbalanced_delimiters")

    lang = str(language or "").strip().lower()
    if lang in {"python", "py"} and (
        _looks_like_complete_python(before) or _looks_like_complete_python(after)
    ):
        for label, code in (("before", before), ("after", after)):
            if _looks_like_complete_python(code):
                try:
                    ast.parse(code)
                except SyntaxError:
                    warnings.append("python_ast_parse_error")
                    break

    return sorted(set(warnings))


def write_example_sanity_report(
    path: str | Path,
    items: Sequence[Dict[str, Any]],
    mode: str = "warn",
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    warning_count = 0
    for item in items:
        warnings = example_sanity_warnings(
            str(item.get("language", "")),
            str(item.get("before_code", "")),
            str(item.get("after_code", "")),
        )
        warning_count += len(warnings)
        rows.append(
            {
                "skill_id": item.get("skill_id"),
                "language": item.get("language"),
                "warnings": warnings,
                "warning_count": len(warnings),
            }
        )

    report = {
        "mode": str(mode or "warn"),
        "item_count": len(rows),
        "warning_count": warning_count,
        "items": rows,
    }
    path = Path(path)
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _summary_doc(summary: Dict[str, Any]) -> str:
    return " ".join(
        [
            _clean_text(summary.get("proposed_name")),
            _clean_text(summary.get("primary_mechanism")),
            " ".join(_listify(summary.get("secondary_mechanisms"))),
            " ".join(_listify(summary.get("tags"))),
            " ".join(_listify(summary.get("canonical_triggers"))),
            " ".join(_listify(summary.get("canonical_steps"))),
        ]
    )


def build_library_diversity_report(
    summaries: Sequence[Dict[str, Any]],
    near_duplicate_threshold: float = 0.78,
    high_overlap_threshold: float = 0.65,
) -> Dict[str, Any]:
    rows = list(summaries)
    docs = [_summary_doc(s) for s in rows]
    near_pairs: List[Dict[str, Any]] = []
    high_pairs: List[Dict[str, Any]] = []
    name_keys = [normalize_skill_name_key(s.get("proposed_name")) for s in rows]
    families = [infer_mechanism_family(s) for s in rows]
    if len(rows) >= 2 and any(docs):
        matrix = TfidfVectorizer(max_features=2048, ngram_range=(1, 2)).fit_transform(docs)
        sim = cosine_similarity(matrix)
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                score = float(sim[i, j])
                reason = "tfidf"
                if name_keys[i] and name_keys[i] == name_keys[j]:
                    reason = "same_normalized_name"
                    score = max(score, 1.0)
                elif (
                    families[i] not in {"", "unknown", "other"}
                    and families[i] == families[j]
                    and score >= high_overlap_threshold * 0.5
                ):
                    reason = "same_mechanism_family"
                    score = max(score, high_overlap_threshold)
                pair = {
                    "left_cluster_id": rows[i].get("cluster_id"),
                    "right_cluster_id": rows[j].get("cluster_id"),
                    "left_name": rows[i].get("proposed_name"),
                    "right_name": rows[j].get("proposed_name"),
                    "similarity": round(score, 4),
                    "reason": reason,
                }
                if reason == "same_normalized_name" or score >= near_duplicate_threshold:
                    near_pairs.append(pair)
                elif score >= high_overlap_threshold:
                    high_pairs.append(pair)

    primary_counts = Counter(
        _clean_text(s.get("primary_mechanism")).lower()
        for s in rows
        if _clean_text(s.get("primary_mechanism"))
    )
    scope_counts = Counter(_clean_text(s.get("optimization_scope")) or "unknown" for s in rows)
    family_counts = Counter(families)
    return {
        "operator_count": len(rows),
        "near_duplicate_threshold": near_duplicate_threshold,
        "high_overlap_threshold": high_overlap_threshold,
        "near_duplicate_pairs": sorted(
            near_pairs, key=lambda x: x["similarity"], reverse=True
        ),
        "high_overlap_pairs": sorted(
            high_pairs, key=lambda x: x["similarity"], reverse=True
        ),
        "scope_distribution": dict(sorted(scope_counts.items())),
        "primary_mechanism_duplicate_counts": {
            k: v for k, v in sorted(primary_counts.items()) if v > 1
        },
        "mechanism_family_distribution": dict(sorted(family_counts.items())),
        "mechanism_family_duplicate_counts": {
            k: v
            for k, v in sorted(family_counts.items())
            if k not in {"unknown", "other"} and v > 1
        },
    }


def write_library_diversity_report(
    path: str | Path,
    summaries: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    report = build_library_diversity_report(summaries)
    path = Path(path)
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
