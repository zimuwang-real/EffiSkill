from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Set


VALID_ROUTE_TYPES = {
    "algorithmic_rewrite",
    "data_structure",
    "memory_layout",
    "io",
    "constant_factor",
    "math_precompute",
    "fallback",
}

BAND_SCORE = {"unknown": 0, "mild": 1, "moderate": 2, "high": 3, "very_high": 4}
STYLE_SCORE = {"conservative": 0.0, "balanced": 0.15, "aggressive": 0.25}
ALIGNMENT_SCORE = {"weak": -0.5, "partial": 0.0, "matches": 0.5}

ROUTE_PRIORITY = {
    "algorithm": [
        "algorithmic_rewrite",
        "data_structure",
        "memory_layout",
        "math_precompute",
        "fallback",
        "constant_factor",
        "io",
    ],
    "implementation": [
        "data_structure",
        "memory_layout",
        "constant_factor",
        "io",
        "algorithmic_rewrite",
        "fallback",
        "math_precompute",
    ],
    "mixed": [
        "algorithmic_rewrite",
        "data_structure",
        "memory_layout",
        "math_precompute",
        "constant_factor",
        "io",
        "fallback",
    ],
}


@dataclass(frozen=True)
class DecodingProfile:
    s1_temperature: float
    s2_temperature: float
    s3_temperature: float
    conservative_generation_temperature: float
    balanced_generation_temperature: float
    aggressive_generation_temperature: float

    def generation_temperature(self, plan_style: str) -> float:
        style = str(plan_style or "").strip().lower()
        if style == "aggressive":
            return self.aggressive_generation_temperature
        if style == "balanced":
            return self.balanced_generation_temperature
        return self.conservative_generation_temperature


GPT5_MINI_DECODING = DecodingProfile(
    s1_temperature=0.3,
    s2_temperature=0.3,
    s3_temperature=0.5,
    conservative_generation_temperature=0.35,
    balanced_generation_temperature=0.6,
    aggressive_generation_temperature=0.8,
)

QWEN30B_DECODING = DecodingProfile(
    s1_temperature=0.2,
    s2_temperature=0.25,
    s3_temperature=0.45,
    conservative_generation_temperature=0.25,
    balanced_generation_temperature=0.5,
    aggressive_generation_temperature=0.7,
)


def decoding_profile_for(model_hint: str) -> DecodingProfile:
    hint = str(model_hint or "").strip().lower()
    if "qwen" in hint:
        return QWEN30B_DECODING
    return GPT5_MINI_DECODING


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_must_change(value: Any) -> str:
    text = clean_text(value).lower()
    if text in {"algorithm", "implementation", "mixed"}:
        return text
    return "mixed"


def normalize_route_type(value: Any) -> str:
    text = clean_text(value).lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "algorithm": "algorithmic_rewrite",
        "algorithmic": "algorithmic_rewrite",
        "structural": "algorithmic_rewrite",
        "rewrite": "algorithmic_rewrite",
        "data": "data_structure",
        "datastructure": "data_structure",
        "data_structures": "data_structure",
        "memory": "memory_layout",
        "layout": "memory_layout",
        "input_output": "io",
        "i_o": "io",
        "implementation": "constant_factor",
        "constant": "constant_factor",
        "constantfactor": "constant_factor",
        "math": "math_precompute",
        "precompute": "math_precompute",
        "combinatorics": "math_precompute",
        "safe": "fallback",
    }
    text = aliases.get(text, text)
    if text in VALID_ROUTE_TYPES:
        return text
    return "fallback"


def infer_route_type_from_text(*values: Any) -> str:
    blob = " ".join(clean_text(v).lower() for v in values)
    if any(x in blob for x in ("closed form", "formula", "combinator", "precomput", "math")):
        return "math_precompute"
    if any(x in blob for x in ("algorithm", "asymptotic", "recurrence", "offline", "sweep", "dp")):
        return "algorithmic_rewrite"
    if any(x in blob for x in ("data structure", "set", "map", "dict", "heap", "array", "vector")):
        return "data_structure"
    if any(x in blob for x in ("memory", "layout", "allocation", "cache")):
        return "memory_layout"
    if any(x in blob for x in ("io", "input", "output", "parse", "scanner")):
        return "io"
    if any(x in blob for x in ("constant", "micro", "loop", "builtin", "container overhead")):
        return "constant_factor"
    return "fallback"


def op_registry_meta(operator_registry: List[Dict[str, Any]], *, include_language: bool = False) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in operator_registry:
        item = {
            "skill_id": row.get("skill_id"),
            "name": row.get("name"),
            "description": row.get("description"),
            "family": row.get("family"),
            "optimization_scope": row.get("optimization_scope"),
            "primary_change": row.get("primary_change"),
            "risk_band": row.get("risk_band"),
            "implementation_cost": row.get("implementation_cost"),
            "applicability_precision": row.get("applicability_precision"),
            "impact_percentile_in_library": row.get("impact_percentile_in_library"),
            "impact_reliability": row.get("impact_reliability"),
            "tags": (row.get("tags") or [])[:10],
            "aliases": (row.get("aliases") or [])[:8],
            "triggers": (row.get("triggers") or [])[:6],
            "negative_triggers": (row.get("negative_triggers") or [])[:6],
            "impact_expected_band": row.get("impact_expected_band"),
            "impact_speedup_median": row.get("impact_speedup_median"),
            "impact_speedup_p75": row.get("impact_speedup_p75"),
            "impact_speedup_max": row.get("impact_speedup_max"),
            "impact_weight": row.get("impact_weight"),
        }
        if include_language:
            item["language"] = row.get("language")
        out.append(item)
    return out


def normalize_skill_sets(
    raw: Any,
    *,
    valid_operator_ids: Set[str],
    num_skill_sets: int,
    skills_per_set: int,
) -> List[Dict[str, Any]]:
    skill_sets = raw.get("skill_sets") if isinstance(raw, dict) else []
    if not isinstance(skill_sets, list):
        skill_sets = []

    normalized: List[Dict[str, Any]] = []
    for idx, skill_set in enumerate(skill_sets, start=1):
        if not isinstance(skill_set, dict):
            continue
        selected = []
        raw_selected = skill_set.get("selected_skills") or []
        if not isinstance(raw_selected, list):
            raw_selected = []
        for item in raw_selected:
            if not isinstance(item, dict):
                continue
            skill_id = clean_text(item.get("skill_id"))
            if skill_id not in valid_operator_ids:
                continue
            role = clean_text(item.get("expected_role")).lower()
            if role not in {"primary_high_impact", "supporting", "fallback_safe"}:
                role = "supporting"
            selected.append(
                {
                    "skill_id": skill_id,
                    "reason": clean_text(item.get("reason")) or "matched diagnosis",
                    "expected_role": role,
                }
            )
            if len(selected) >= skills_per_set:
                break
        if not selected:
            continue
        route_type = normalize_route_type(skill_set.get("route_type"))
        if route_type == "fallback":
            route_type = infer_route_type_from_text(
                skill_set.get("selection_theme"),
                skill_set.get("expected_change"),
                " ".join(x["reason"] for x in selected),
            )
        normalized.append(
            {
                "set_id": clean_text(skill_set.get("set_id")) or f"S{idx}",
                "route_type": route_type,
                "confidence": clean_text(skill_set.get("confidence")) or "medium",
                "selection_theme": clean_text(skill_set.get("selection_theme")) or route_type,
                "expected_change": clean_text(skill_set.get("expected_change")),
                "selected_skills": selected,
            }
        )
    return normalized[:num_skill_sets]


def normalize_plan_style(value: Any) -> str:
    text = clean_text(value).lower()
    if text in {"conservative", "balanced", "aggressive"}:
        return text
    return "balanced"


def normalize_plans(raw: Any, *, set_id: str, default_route_type: str = "fallback") -> List[Dict[str, Any]]:
    plans = raw.get("plans") if isinstance(raw, dict) else []
    if not isinstance(plans, list):
        plans = []

    normalized: List[Dict[str, Any]] = []
    for idx, plan in enumerate(plans, start=1):
        if not isinstance(plan, dict):
            continue
        band = clean_text(plan.get("expected_speedup_band")).lower()
        if band not in BAND_SCORE:
            band = "unknown"
        alignment = clean_text(plan.get("must_change_alignment")).lower()
        if alignment not in ALIGNMENT_SCORE:
            alignment = "partial"
        route_type = normalize_route_type(plan.get("route_type"))
        if route_type == "fallback":
            route_type = normalize_route_type(default_route_type)
        if route_type == "fallback":
            route_type = infer_route_type_from_text(
                plan.get("optimization_mechanism"),
                plan.get("core_idea"),
                plan.get("new_mechanism"),
            )
        normalized.append(
            {
                "set_id": set_id,
                "plan_id": clean_text(plan.get("plan_id")) or f"{set_id}_P{idx}",
                "route_type": route_type,
                "plan_style": normalize_plan_style(plan.get("plan_style")),
                "name": clean_text(plan.get("name")) or "Optimization plan",
                "core_idea": clean_text(plan.get("core_idea")),
                "target_complexity": plan.get("target_complexity"),
                "optimization_mechanism": clean_text(plan.get("optimization_mechanism")),
                "old_hot_path": clean_text(plan.get("old_hot_path")),
                "new_mechanism": clean_text(plan.get("new_mechanism")),
                "expected_speedup_band": band,
                "impact_skill_ids": [
                    clean_text(x) for x in (plan.get("impact_skill_ids") or []) if clean_text(x)
                ],
                "must_change_alignment": alignment,
                "risks": plan.get("risks") if isinstance(plan.get("risks"), list) else [],
                "steps": plan.get("steps") if isinstance(plan.get("steps"), list) else [],
            }
        )

    existing_styles = {p["plan_style"] for p in normalized}
    route_type = normalize_route_type(default_route_type)
    for style in ("conservative", "balanced", "aggressive"):
        if style in existing_styles:
            continue
        normalized.append(
            {
                "set_id": set_id,
                "plan_id": f"{set_id}_{style}",
                "route_type": route_type,
                "plan_style": style,
                "name": f"{style.title()} route",
                "core_idea": "Apply selected skills while preserving interface and semantics.",
                "target_complexity": "unknown",
                "optimization_mechanism": "apply selected skills while preserving interface",
                "old_hot_path": "",
                "new_mechanism": "",
                "expected_speedup_band": "unknown",
                "impact_skill_ids": [],
                "must_change_alignment": "partial",
                "risks": [],
                "steps": [],
            }
        )

    style_order = {"conservative": 0, "balanced": 1, "aggressive": 2}
    return sorted(normalized, key=lambda p: (p["set_id"], style_order.get(p["plan_style"], 9), p["plan_id"]))


def plan_impact_score(plan: Dict[str, Any]) -> float:
    return (
        BAND_SCORE.get(str(plan.get("expected_speedup_band", "unknown")), 0)
        + STYLE_SCORE.get(str(plan.get("plan_style", "balanced")), 0.0)
        + ALIGNMENT_SCORE.get(str(plan.get("must_change_alignment", "partial")), 0.0)
        + min(len(plan.get("impact_skill_ids") or []), 3) * 0.1
    )


def _route_rank(route_type: str, must_change: str) -> int:
    priority = ROUTE_PRIORITY.get(normalize_must_change(must_change), ROUTE_PRIORITY["mixed"])
    try:
        return priority.index(normalize_route_type(route_type))
    except ValueError:
        return len(priority)


def allocate_plan_slots(plans: List[Dict[str, Any]], k: int, *, must_change: str = "mixed") -> List[int]:
    if k <= 0 or not plans:
        return []
    alloc = [0] * len(plans)

    by_route: Dict[str, List[int]] = {}
    for idx, plan in enumerate(plans):
        route = normalize_route_type(plan.get("route_type"))
        by_route.setdefault(route, []).append(idx)

    # First pass: allocate one slot to the best plan in each relevant route so the
    # generated top-k covers mechanisms, not only style variants.
    route_order = sorted(by_route, key=lambda r: (_route_rank(r, must_change), r))
    for route in route_order:
        if sum(alloc) >= k:
            break
        best_idx = max(
            by_route[route],
            key=lambda i: (plan_impact_score(plans[i]), -i),
        )
        alloc[best_idx] += 1

    # Remaining budget goes to highest-impact plans, with route priority as a tie
    # breaker. This still favors high-upside plans while preserving diversity.
    while sum(alloc) < k:
        best_idx = max(
            range(len(plans)),
            key=lambda i: (
                plan_impact_score(plans[i]),
                -_route_rank(str(plans[i].get("route_type")), must_change),
                -alloc[i],
                -i,
            ),
        )
        alloc[best_idx] += 1

    return alloc
