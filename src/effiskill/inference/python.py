"""No-execution inference pipeline (skills-first, multi-skill-set, no ranking).

Pipeline:
- S1-lite diagnose
- One-pass model-routed multi-skill-set selection from metadata
- Per-set strategize (conservative/balanced/aggressive)
- Generate K candidates
- Static sanity + static correctness filter
- Output all candidates/survivors (no ranking)
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import textwrap
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from openai import OpenAI

from ..llm import sampling_kwargs
from ..paths import skills_root

CACHE_INCLUDE_PAYLOAD = os.getenv("EFFISKILL_CACHE_INCLUDE_PAYLOAD", "0").lower() in {
    "1",
    "true",
    "yes",
}


# -----------------------------
# Basic I/O helpers
# -----------------------------
def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _iter_rows(path: str) -> Iterable[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def _is_resume_terminal_status(status: Any) -> bool:
    return _clean_text(status).lower() in {"ok", "no_survivor"}


def _load_existing_ids(out_path: str) -> Set[str]:
    if not os.path.exists(out_path):
        return set()
    seen: Set[str] = set()
    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            pid = obj.get("problem_id")
            if pid and _is_resume_terminal_status(obj.get("status")):
                seen.add(pid)
    return seen


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


# -----------------------------
# Skill loading
# -----------------------------
def _find_skill_id(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.strip().startswith("skill_id:"):
            return line.split(":", 1)[1].strip()
    return None


def load_skills_index(skills_root: str) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for root, _, files in os.walk(skills_root):
        if "SKILL.md" not in files:
            continue
        path = os.path.join(root, "SKILL.md")
        text = _read_text(path)
        sid = _find_skill_id(text)
        if not sid:
            continue
        index[sid] = {"path": path, "content": text}
    return index


def load_registry(skills_root: str) -> List[Dict[str, Any]]:
    path = os.path.join(skills_root, "registry.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# LLM utilities (failure logging only; success cache disabled)
# -----------------------------
def create_client(base_url: str, api_key: str) -> OpenAI:
    return OpenAI(base_url=base_url, api_key=api_key)


def _hash_payload(payload: Dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _read_cache(cache_path: str) -> Optional[str]:
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    content = obj.get("content")
    if isinstance(content, str) and content.strip():
        return content
    return None


def _write_cache(cache_path: str, content: str, payload: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    cache_obj: Dict[str, Any] = {"content": content}
    if CACHE_INCLUDE_PAYLOAD:
        cache_obj["payload"] = payload
    else:
        cache_obj["payload_hash"] = _hash_payload(payload)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_obj, f, ensure_ascii=False, indent=2)


def _is_non_retryable_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    return status in {400, 401, 403, 404}


def _is_rate_limited_error(exc: Exception) -> bool:
    txt = str(exc).lower()
    status = getattr(exc, "status_code", None)
    return status == 429 or "429" in txt or "rate limit" in txt or "too many requests" in txt


def cached_chat_completion(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    cache_dir: str,
    stage: str,
    timeout: int = 180,
) -> str:
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    # Keep cache_dir/stage parameters for call-site compatibility, but do not
    # read or write successful-response cache in inference mode.
    _ = cache_dir
    _ = stage

    max_attempts = 4
    last_exc: Optional[Exception] = None
    response = None
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=timeout,
                **sampling_kwargs(model, temperature, max_tokens),
            )
            break
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if _is_non_retryable_error(exc):
                raise
            if attempt < max_attempts - 1:
                if _is_rate_limited_error(exc):
                    delay = min(20.0, 2.0 * (attempt + 1))
                else:
                    delay = min(8.0, 1.0 * (attempt + 1))
                time.sleep(delay)

    if response is None:
        raise RuntimeError(f"chat completion failed after retries: {last_exc}")

    content = response.choices[0].message.content or ""
    if not content.strip():
        raise RuntimeError("empty response from LLM")

    return content


def log_llm_failure(stage: str, payload: Dict[str, Any], response_text: str, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    base = f"{stage}_{ts}_{_hash_payload(payload)[:8]}"
    jpath = os.path.join(out_dir, f"json_fail_{base}.json")
    tpath = os.path.join(out_dir, f"json_fail_{base}.txt")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump({"payload": payload}, f, ensure_ascii=False, indent=2)
    with open(tpath, "w", encoding="utf-8") as f:
        f.write(response_text)


def extract_json(text: str) -> Optional[Any]:
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*", "", cleaned).strip("`\n ")
    s_obj = cleaned.find("{")
    s_arr = cleaned.find("[")
    starts = [x for x in (s_obj, s_arr) if x != -1]
    if not starts:
        return None
    start = min(starts)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if end <= start:
        return None
    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return None


def llm_json_call(
    client: OpenAI,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
    cache_dir: str,
    stage: str,
    out_fail_dir: str,
) -> Optional[Any]:
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }

    try:
        content = cached_chat_completion(
            client=client,
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            cache_dir=cache_dir,
            stage=stage,
        )
    except Exception as exc:  # noqa: BLE001
        log_llm_failure(stage + "_error", payload, str(exc), out_fail_dir)
        return None

    obj = extract_json(content)
    if obj is not None:
        return obj

    fix_messages = [
        {
            "role": "system",
            "content": "Fix this to valid strict JSON. Return JSON only.",
        },
        {"role": "user", "content": content},
    ]
    fix_payload = {
        "model": model,
        "temperature": 1.0,
        "max_tokens": max_tokens,
        "messages": fix_messages,
    }
    try:
        fix_content = cached_chat_completion(
            client=client,
            messages=fix_messages,
            model=model,
            temperature=1.0,
            max_tokens=max_tokens,
            cache_dir=cache_dir,
            stage=stage + "_fix",
        )
    except Exception as exc:  # noqa: BLE001
        log_llm_failure(stage + "_fix_error", fix_payload, str(exc), out_fail_dir)
        return None

    obj = extract_json(fix_content)
    if obj is not None:
        return obj

    log_llm_failure(stage + "_json", fix_payload, fix_content, out_fail_dir)
    return None


# -----------------------------
# Prompt builders
# -----------------------------
def build_s1_messages(meta_skill: str, statement: str, slow_code: str) -> List[Dict[str, str]]:
    system = textwrap.dedent(
        f"""
        You are a Python code optimization diagnostician.
        Follow the meta skill guidance below.

        {meta_skill}

        Return strict JSON only.
        Required fields:
        - constraints_guess: {{n_max, q_max, notes}}
        - problem_type_tags: [string]
        - dominant_ops: [string]
        - complexity: {{time, space, why}}
        - bottlenecks: [{{kind, detail}}]
        - must_change: "algorithm"|"implementation"|"mixed"
        - risks: [string]
        - confidence: "high"|"medium"|"low"
        """
    ).strip()

    user = textwrap.dedent(
        f"""
        Problem statement:
        {statement}

        Baseline code:
        ```python
        {slow_code}
        ```
        """
    ).strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_s2_messages(
    meta_skill: str,
    optimization_brief: Dict[str, Any],
    operator_registry_meta: List[Dict[str, Any]],
    num_skill_sets: int,
    skills_per_set: int,
) -> List[Dict[str, str]]:
    system = textwrap.dedent(
        f"""
        You are a skill router for Python optimization.
        Follow the meta skill guidance below.

        {meta_skill}

        Select multiple DIFFERENT skill sets in one pass.
        Return strict JSON only.
        Required fields:
        - skill_sets: [
            {{
              set_id,
              confidence: "high"|"medium"|"low",
              selection_theme,
              selected_skills: [{{skill_id, reason}}]
            }}
          ]
        - global_coverage_gaps: [string]

        Constraints:
        - Produce exactly {num_skill_sets} skill sets.
        - Max {skills_per_set} skills per set.
        - Skill sets should be meaningfully different in optimization mechanism.
        - Use only skill_ids from provided registry metadata.
        """
    ).strip()

    user = (
        textwrap.dedent(
            """
        OptimizationBrief:
        {opt}

        Operator registry metadata:
        {registry}
        """
        )
        .strip()
        .format(
            opt=json.dumps(optimization_brief, ensure_ascii=False),
            registry=json.dumps(operator_registry_meta, ensure_ascii=False),
        )
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_s3_messages(
    meta_skill: str,
    statement: str,
    slow_code: str,
    optimization_brief: Dict[str, Any],
    skill_set: Dict[str, Any],
    skill_bodies: List[str],
) -> List[Dict[str, str]]:
    system = textwrap.dedent(
        f"""
        You generate plans from selected optimization skills.
        Follow the meta skill guidance below.

        {meta_skill}

        Return strict JSON only.
        Required fields:
        - plans: [
            {{
              plan_id,
              plan_style: "conservative"|"balanced"|"aggressive",
              name,
              core_idea,
              target_complexity,
              risks: [string],
              steps: [string]
            }}
          ]

        Constraints:
        - Produce exactly 3 plans: conservative, balanced, aggressive.
        - All plans must preserve the external code interface style.
        """
    ).strip()

    user = (
        textwrap.dedent(
            """
        Problem statement:
        {statement}

        Baseline code:
        ```python
        {slow_code}
        ```

        OptimizationBrief:
        {opt}

        Skill set:
        {skill_set}

        Selected skill bodies:
        {skill_bodies}
        """
        )
        .strip()
        .format(
            statement=statement,
            slow_code=slow_code,
            opt=json.dumps(optimization_brief, ensure_ascii=False),
            skill_set=json.dumps(skill_set, ensure_ascii=False),
            skill_bodies="\n\n".join(skill_bodies),
        )
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_generate_messages(
    statement: str, slow_code: str, plan: Dict[str, Any]
) -> List[Dict[str, str]]:
    system = textwrap.dedent(
        """
        Generate optimized Python code for the given plan.
        Return strict JSON only.

        Required fields:
        - code: string
        - complexity: {time, space, why}
        - dominant_ops: [string]
        - notes: short explanation
        - static_verdict: "pass"|"fail"
        - interface_match: true|false
        - complexity_plausible: true|false
        - static_issues: [string]
        - static_confidence: 0-1

        Critical interface rule:
        - Generate code based on the version of the input code.
        - Preserve callable style and external interface exactly.
          Examples:
          - if input is class/method style, keep class/method style;
          - if input is function style, keep function style;
          - if input is script stdin/stdout style, keep script style.
        - Do not convert between these styles.

        Header/style guidance (soft):
        - Try to preserve the input module header format (leading comments/docstring),
          import section structure/order, and overall top-level layout unless a change
          is necessary for correctness or the optimization plan.
        - Avoid unnecessary reformatting or cosmetic rewrites.

        Assume baseline logic is valid and keep semantics.
        """
    ).strip()

    user = (
        textwrap.dedent(
            """
        Problem statement:
        {statement}

        Baseline code:
        ```python
        {slow_code}
        ```

        Plan:
        {plan}
        """
        )
        .strip()
        .format(
            statement=statement,
            slow_code=slow_code,
            plan=json.dumps(plan, ensure_ascii=False),
        )
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_sanity_messages(
    statement: str, slow_code: str, candidate_code: str
) -> List[Dict[str, str]]:
    system = textwrap.dedent(
        """
        Perform static sanity cleanup only (no execution).
        Preserve external interface style exactly as baseline.
        Softly preserve module header/comments/import structure from baseline unless
        required to fix correctness.

        Return strict JSON only.
        Required fields:
        - code: fixed code
        - fixes: [string]
        """
    ).strip()

    user = (
        textwrap.dedent(
            """
        Problem statement:
        {statement}

        Baseline code (interface reference):
        ```python
        {slow_code}
        ```

        Candidate code:
        ```python
        {code}
        ```
        """
        )
        .strip()
        .format(statement=statement, slow_code=slow_code, code=candidate_code)
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# -----------------------------
# Normalization helpers
# -----------------------------
def _clean_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return re.sub(r"\s+", " ", x).strip()
    return re.sub(r"\s+", " ", str(x)).strip()


def _clean_code(x: Any) -> str:
    """Preserve code layout while trimming obvious wrapper whitespace."""
    if x is None:
        return ""
    if not isinstance(x, str):
        x = str(x)
    x = x.replace("\r\n", "\n").replace("\r", "\n")
    return x.strip("\n")


def _python_syntax_error(code: str) -> Optional[str]:
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return f"SyntaxError: {exc.msg} (line {exc.lineno})"


def _is_public_name(name: str) -> bool:
    return bool(name) and not name.startswith("_")


def _signature_shape(args: ast.arguments, *, drop_first: bool = False) -> Dict[str, Any]:
    posonly = [a.arg for a in args.posonlyargs]
    positional = [a.arg for a in args.args]
    if drop_first and positional:
        positional = positional[1:]
    return {
        "posonly": posonly,
        "positional": positional,
        "kwonly": [a.arg for a in args.kwonlyargs],
        "defaults": len(args.defaults),
        "kw_defaults": sum(default is not None for default in args.kw_defaults),
        "has_vararg": args.vararg is not None,
        "has_kwarg": args.kwarg is not None,
    }


def _extract_interface_contract(code: str) -> Optional[Dict[str, Any]]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    functions: Dict[str, Dict[str, Any]] = {}
    classes: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public_name(node.name):
            functions[node.name] = _signature_shape(node.args)
            continue
        if isinstance(node, ast.ClassDef) and _is_public_name(node.name):
            methods: Dict[str, Dict[str, Any]] = {}
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public_name(
                    item.name
                ):
                    methods[item.name] = _signature_shape(item.args, drop_first=True)
            classes[node.name] = methods

    if classes and not functions:
        style = "class"
    elif functions and not classes:
        style = "function"
    elif not classes and not functions:
        style = "script"
    else:
        style = "mixed"

    return {
        "style": style,
        "functions": functions,
        "classes": classes,
    }


def _check_interface_match(baseline_code: str, candidate_code: str) -> Tuple[bool, List[str]]:
    baseline = _extract_interface_contract(baseline_code)
    candidate = _extract_interface_contract(candidate_code)

    if baseline is None:
        # Do not penalize the candidate if the baseline itself is not parseable.
        return True, []
    if candidate is None:
        return False, ["Candidate interface could not be verified because the code does not parse."]

    issues: List[str] = []
    baseline_style = baseline["style"]
    candidate_style = candidate["style"]

    if baseline_style == "class" and not candidate["classes"]:
        issues.append("Candidate no longer exposes the baseline class-style interface.")
    if baseline_style == "function" and not candidate["functions"]:
        issues.append("Candidate no longer exposes the baseline function-style interface.")
    if baseline_style == "script" and candidate["classes"]:
        issues.append("Candidate changed baseline script-style code into a class-based interface.")
    if baseline_style in {"function", "script"} and candidate_style == "class":
        issues.append(f"Candidate changed interface style from {baseline_style} to class.")

    for func_name, expected_sig in baseline["functions"].items():
        actual_sig = candidate["functions"].get(func_name)
        if actual_sig is None:
            issues.append(f"Missing top-level function `{func_name}` from baseline interface.")
            continue
        if actual_sig != expected_sig:
            issues.append(f"Function signature drift for `{func_name}`.")

    for class_name, expected_methods in baseline["classes"].items():
        actual_methods = candidate["classes"].get(class_name)
        if actual_methods is None:
            issues.append(f"Missing class `{class_name}` from baseline interface.")
            continue
        for method_name, expected_sig in expected_methods.items():
            actual_sig = actual_methods.get(method_name)
            if actual_sig is None:
                issues.append(f"Missing method `{class_name}.{method_name}` from baseline interface.")
                continue
            if actual_sig != expected_sig:
                issues.append(f"Method signature drift for `{class_name}.{method_name}`.")

    return not issues, issues


def _op_registry_meta(operator_registry: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for r in operator_registry:
        out.append(
            {
                "skill_id": r.get("skill_id"),
                "name": r.get("name"),
                "description": r.get("description"),
                "family": r.get("family"),
                "triggers": (r.get("triggers") or [])[:6],
            }
        )
    return out


def _normalize_skill_sets(
    raw: Any,
    valid_operator_ids: Set[str],
    num_skill_sets: int,
    skills_per_set: int,
) -> List[Dict[str, Any]]:
    skill_sets = []
    if isinstance(raw, dict):
        skill_sets = raw.get("skill_sets") or []

    norm: List[Dict[str, Any]] = []
    used_signatures = set()

    for idx, ss in enumerate(skill_sets, start=1):
        if not isinstance(ss, dict):
            continue
        selected = ss.get("selected_skills") or []
        cleaned_selected = []
        seen = set()
        for item in selected:
            if not isinstance(item, dict):
                continue
            sid = _clean_text(item.get("skill_id"))
            if sid not in valid_operator_ids or sid in seen:
                continue
            seen.add(sid)
            cleaned_selected.append(
                {
                    "skill_id": sid,
                    "reason": _clean_text(item.get("reason")) or "matched diagnosis",
                }
            )
            if len(cleaned_selected) >= skills_per_set:
                break

        if not cleaned_selected:
            continue

        sig = tuple(sorted(x["skill_id"] for x in cleaned_selected))
        if sig in used_signatures:
            continue
        used_signatures.add(sig)

        norm.append(
            {
                "set_id": _clean_text(ss.get("set_id")) or f"SET{idx}",
                "confidence": _clean_text(ss.get("confidence")).lower() or "medium",
                "selection_theme": _clean_text(ss.get("selection_theme")) or "general",
                "selected_skills": cleaned_selected,
            }
        )

    if not norm:
        return []
    # Do not clone identical skill sets just to hit the target count; duplicate
    # retrieval burns generation budget without adding new optimization paths.
    return norm[:num_skill_sets]


def _normalize_plan_style(x: Any) -> str:
    s = _clean_text(x).lower()
    if "conserv" in s:
        return "conservative"
    if "aggr" in s:
        return "aggressive"
    return "balanced"


def _normalize_plans(raw: Any, set_id: str) -> List[Dict[str, Any]]:
    plans = []
    if isinstance(raw, dict):
        plans = raw.get("plans") or []

    norm: List[Dict[str, Any]] = []
    for i, p in enumerate(plans, start=1):
        if not isinstance(p, dict):
            continue
        style = _normalize_plan_style(p.get("plan_style"))
        norm.append(
            {
                "plan_id": _clean_text(p.get("plan_id")) or f"{set_id}_P{i}",
                "set_id": set_id,
                "plan_style": style,
                "name": _clean_text(p.get("name")) or f"{style.title()} Plan",
                "core_idea": _clean_text(p.get("core_idea")),
                "target_complexity": _clean_text(p.get("target_complexity")),
                "risks": [_clean_text(x) for x in (p.get("risks") or []) if _clean_text(x)][:6],
                "steps": [_clean_text(x) for x in (p.get("steps") or []) if _clean_text(x)][:8],
            }
        )

    # Ensure each style exists at least once via fallback clones.
    style_to_plan = {p["plan_style"]: p for p in norm}
    for style in ("conservative", "balanced", "aggressive"):
        if style in style_to_plan:
            continue
        norm.append(
            {
                "plan_id": f"{set_id}_{style[:3].upper()}",
                "set_id": set_id,
                "plan_style": style,
                "name": f"{style.title()} Plan",
                "core_idea": "Apply selected skills while preserving interface and semantics.",
                "target_complexity": "(improved vs baseline where applicable)",
                "risks": ["Static-only validation may miss subtle bugs."],
                "steps": ["Apply the selected skills coherently to baseline code."],
            }
        )

    # Keep deterministic order.
    style_order = {"conservative": 0, "balanced": 1, "aggressive": 2}
    norm = sorted(norm, key=lambda p: (style_order.get(p["plan_style"], 9), p["plan_id"]))
    return norm


def _allocate_plan_slots(plans: List[Dict[str, Any]], k: int) -> List[int]:
    if k <= 0 or not plans:
        return []
    n = len(plans)
    alloc = [0] * n
    if n <= k:
        for i in range(n):
            alloc[i] = 1
        remain = k - n
        i = 0
        while remain > 0:
            alloc[i % n] += 1
            i += 1
            remain -= 1
        return alloc

    # More plans than budget: prioritize conservative/balanced/aggressive cycling.
    order = sorted(
        range(n),
        key=lambda i: {"conservative": 0, "balanced": 1, "aggressive": 2}.get(
            plans[i].get("plan_style", "balanced"), 9
        ),
    )
    for i in order[:k]:
        alloc[i] = 1
    return alloc


# -----------------------------
# Core problem runner
# -----------------------------
def run_problem(
    *,
    problem_id: str,
    statement: str,
    slow_code: str,
    model: str,
    client: OpenAI,
    cache_dir: str,
    fail_dir: str,
    meta_skills: Dict[str, str],
    skills_index: Dict[str, Dict[str, str]],
    operator_registry: List[Dict[str, Any]],
    num_skill_sets: int,
    skills_per_set: int,
    k: int,
    sanity_fix: bool,
    require_syntax: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {"status": "ok"}

    stage_prefix = f"{problem_id or 'unknown'}"

    # S1 Diagnose
    s1 = llm_json_call(
        client,
        messages=build_s1_messages(meta_skills["S1"], statement, slow_code),
        model=model,
        temperature=0.8,
        max_tokens=25000,
        cache_dir=cache_dir,
        stage=f"{stage_prefix}_s1_diagnose",
        out_fail_dir=fail_dir,
    )
    if s1 is None:
        return {"status": "failed", "error_stage": "s1"}
    result["optimization_brief"] = s1

    # S2 One-pass multi-set retrieval from metadata
    valid_operator_ids = {str(r.get("skill_id")) for r in operator_registry if r.get("skill_id")}
    s2 = llm_json_call(
        client,
        messages=build_s2_messages(
            meta_skills["S2"],
            s1,
            _op_registry_meta(operator_registry),
            num_skill_sets=num_skill_sets,
            skills_per_set=skills_per_set,
        ),
        model=model,
        temperature=0.8,
        max_tokens=30000,
        cache_dir=cache_dir,
        stage=f"{stage_prefix}_s2_multi_retrieve",
        out_fail_dir=fail_dir,
    )
    if s2 is None:
        return {**result, "status": "failed", "error_stage": "s2"}

    skill_sets = _normalize_skill_sets(
        s2,
        valid_operator_ids=valid_operator_ids,
        num_skill_sets=num_skill_sets,
        skills_per_set=skills_per_set,
    )
    if not skill_sets:
        return {**result, "status": "failed", "error_stage": "s2_empty"}
    result["skill_sets"] = skill_sets

    # S3 Plans per skill set
    all_plans: List[Dict[str, Any]] = []
    for ss in skill_sets:
        set_id = ss["set_id"]
        skill_bodies = []
        for item in ss["selected_skills"]:
            sid = item["skill_id"]
            body = skills_index.get(sid, {}).get("content")
            if body:
                skill_bodies.append(body)

        s3 = llm_json_call(
            client,
            messages=build_s3_messages(
                meta_skills["S3"], statement, slow_code, s1, ss, skill_bodies
            ),
            model=model,
            temperature=0.8,
            max_tokens=35000,
            cache_dir=cache_dir,
            stage=f"{stage_prefix}_s3_plan_{set_id}",
            out_fail_dir=fail_dir,
        )
        plans = _normalize_plans(s3 if isinstance(s3, dict) else {}, set_id=set_id)
        all_plans.extend(plans)

    if not all_plans:
        return {**result, "status": "failed", "error_stage": "s3_empty"}
    result["plans"] = all_plans

    # S4 Generate candidates (no ranking later)
    alloc = _allocate_plan_slots(all_plans, k)
    candidates: List[Dict[str, Any]] = []
    cid = 1

    for plan, cnt in zip(all_plans, alloc):
        for j in range(cnt):
            temp = 0.5
            if plan.get("plan_style") == "balanced":
                temp = 0.75
            elif plan.get("plan_style") == "aggressive":
                temp = 1.0

            gen = llm_json_call(
                client,
                messages=build_generate_messages(statement, slow_code, plan),
                model=model,
                temperature=temp,
                max_tokens=35000,
                cache_dir=cache_dir,
                stage=f"{stage_prefix}_s4_gen_{plan['plan_id']}_{j+1}",
                out_fail_dir=fail_dir,
            )
            if not isinstance(gen, dict):
                cid += 1
                continue

            code = _clean_code(gen.get("code"))
            if not code:
                cid += 1
                continue

            cand = {
                "candidate_id": f"C{cid}",
                "set_id": plan.get("set_id"),
                "plan_id": plan.get("plan_id"),
                "plan_style": plan.get("plan_style"),
                "code": code,
                "complexity": gen.get("complexity"),
                "dominant_ops": gen.get("dominant_ops"),
                "notes": gen.get("notes"),
            }

            # Optional static sanity fix.
            cand["sanity_fixes"] = []
            if sanity_fix:
                sanity = llm_json_call(
                    client,
                    messages=build_sanity_messages(statement, slow_code, cand["code"]),
                    model=model,
                    temperature=0.15,
                    max_tokens=20000,
                    cache_dir=cache_dir,
                    stage=f"{stage_prefix}_s45_sanity_{cand['candidate_id']}",
                    out_fail_dir=fail_dir,
                )
                if isinstance(sanity, dict) and _clean_code(sanity.get("code")):
                    cand["code"] = _clean_code(sanity.get("code"))
                    cand["sanity_fixes"] = sanity.get("fixes", [])

            # Use generation-time static self-check, then verify key constraints locally.
            cand["static_verdict"] = _clean_text(gen.get("static_verdict")).lower() or "unknown"
            cand["interface_match_model"] = bool(gen.get("interface_match", False))
            cand["complexity_plausible"] = bool(gen.get("complexity_plausible", False))
            cand["static_issues"] = (
                list(gen.get("static_issues", [])) if isinstance(gen.get("static_issues"), list) else []
            )
            cand["static_confidence"] = gen.get("static_confidence", 0.0)

            local_interface_match, local_interface_issues = _check_interface_match(
                slow_code, cand["code"]
            )
            cand["interface_match_local"] = local_interface_match
            cand["interface_match"] = cand["interface_match_model"] and local_interface_match
            for issue in local_interface_issues:
                if issue not in cand["static_issues"]:
                    cand["static_issues"].append(issue)
            if not local_interface_match:
                cand["static_verdict"] = "fail"

            syntax_err = _python_syntax_error(cand["code"])
            cand["syntax_valid"] = syntax_err is None
            if syntax_err:
                if syntax_err not in cand["static_issues"]:
                    cand["static_issues"].append(syntax_err)
                cand["static_verdict"] = "fail"

            candidates.append(cand)
            cid += 1

    if not candidates:
        return {**result, "status": "failed", "error_stage": "s4_empty"}

    survivors = [
        c for c in candidates if c.get("static_verdict") == "pass" and c.get("interface_match")
    ]
    if require_syntax:
        survivors = [c for c in survivors if c.get("syntax_valid", False)]

    result["candidates"] = candidates
    result["survivor_candidates"] = survivors
    result["candidate_count"] = len(candidates)
    result["survivor_count"] = len(survivors)

    if not survivors:
        result["status"] = "no_survivor"

    return result


# -----------------------------
# Dataset/model configuration
# -----------------------------
def resolve_dataset_config(args: argparse.Namespace) -> Tuple[str, str]:
    if not args.data:
        raise ValueError(
            "Missing --data. Create an EffiBench-X task CSV with `effiskill prepare-effibench`, "
            "or pass any CSV with problem_id, statement and slow-code columns."
        )
    return args.data, args.slow_column


def resolve_model_config(args: argparse.Namespace) -> Tuple[str, str, str]:
    base_url = (args.base_url or os.environ.get("EFFISKILL_BASE_URL", "")).strip()
    api_key = (args.api_key or os.environ.get("EFFISKILL_API_KEY", "")).strip()
    model = (args.model or os.environ.get("EFFISKILL_MODEL", "")).strip()
    if not base_url:
        raise ValueError("Missing base URL. Pass --base-url or set EFFISKILL_BASE_URL.")
    if not api_key:
        raise ValueError("Missing API key. Pass --api-key or set EFFISKILL_API_KEY.")
    if not model:
        raise ValueError("Missing model. Pass --model or set EFFISKILL_MODEL.")
    return base_url, api_key, model


# -----------------------------
# Main
# -----------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No-exec multi-skill-set inference pipeline")

    parser.add_argument("--dataset", default="effibench-x", help="Dataset label recorded in each output record.")
    parser.add_argument("--data", default=None, help="Task CSV (see `effiskill prepare-effibench`).")
    parser.add_argument("--statement-column", default="description")
    parser.add_argument("--slow-column", default="canonical_solution", help="Column holding the program to optimize.")

    parser.add_argument("--skills-root", default=str(skills_root("python")), help="Skill library (default: bundled frozen python library).")
    parser.add_argument("--out", default="outputs/runs_python.jsonl")
    parser.add_argument(
        "--cache-dir",
        default="outputs/llm_cache",
        help="Ignored in inference: successful LLM cache is disabled.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Deprecated in inference: successful LLM cache is already disabled.",
    )
    parser.add_argument("--fail-dir", default="outputs/llm_failures")

    parser.add_argument("--base-url", default=None, help="OpenAI-compatible base URL; can also come from env.")
    parser.add_argument("--api-key", default=None, help="Provider API key; can also come from env.")
    parser.add_argument("--model", default=None, help="Model name; can also come from env.")

    parser.add_argument("--k", type=int, default=8, help="Total candidates per problem")
    parser.add_argument("--skill-sets", type=int, default=3, help="Number of skill sets from S2")
    parser.add_argument("--skills-per-set", type=int, default=6)

    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--sanity-fix",
        action="store_true",
        help="Enable extra static sanity-fix stage before static check",
    )
    parser.add_argument(
        "--require-syntax",
        action="store_true",
        help="Require Python syntax-valid candidates to survive filtering.",
    )
    parser.add_argument("--limit", type=int, default=-1, help="-1 means full dataset")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--problem-id", default=None)

    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        data_path, slow_column = resolve_dataset_config(args)
        base_url, api_key, model = resolve_model_config(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    _ensure_parent_dir(args.out)
    os.makedirs(args.fail_dir, exist_ok=True)

    registry = load_registry(args.skills_root)
    operator_registry = [r for r in registry if r.get("type") == "operator"]
    skills_index = load_skills_index(args.skills_root)

    meta_skills = {}
    for sid in ("S1", "S2", "S3"):
        if sid not in skills_index:
            raise RuntimeError(f"Missing meta skill {sid} in {args.skills_root}")
        meta_skills[sid] = skills_index[sid]["content"]

    seen_ids = _load_existing_ids(args.out) if args.resume else set()

    rows: List[Dict[str, str]] = []
    taken = 0
    for idx, row in enumerate(_iter_rows(data_path)):
        if idx < args.start:
            continue
        if args.limit >= 0 and taken >= args.limit:
            break

        problem_id = row.get("problem_id")
        if args.problem_id and problem_id != args.problem_id:
            continue
        if args.resume and problem_id in seen_ids:
            continue

        statement = row.get(args.statement_column, "")
        slow_code = row.get(slow_column, "")
        if not _clean_text(statement) or not _clean_text(slow_code):
            continue

        rows.append(row)
        taken += 1

    out_lock = threading.Lock()
    workers = max(1, int(args.workers))

    def _process_row(row: Dict[str, str]) -> Dict[str, Any]:
        problem_id = row.get("problem_id") or ""
        statement = row.get(args.statement_column, "")
        slow_code = row.get(slow_column, "")

        client = create_client(base_url=base_url, api_key=api_key)
        result = run_problem(
            problem_id=problem_id,
            statement=statement,
            slow_code=slow_code,
            model=model,
            client=client,
            cache_dir="",
            fail_dir=args.fail_dir,
            meta_skills=meta_skills,
            skills_index=skills_index,
            operator_registry=operator_registry,
            num_skill_sets=args.skill_sets,
            skills_per_set=args.skills_per_set,
            k=args.k,
            sanity_fix=args.sanity_fix,
            require_syntax=args.require_syntax,
        )
        return {
            "problem_id": problem_id,
            "dataset": args.dataset,
            "data_path": data_path,
            "statement": statement,
            "slow_code": slow_code,
            "model": model,
            **result,
        }

    def _failed_record(row: Dict[str, str], exc: Exception) -> Dict[str, Any]:
        return {
            "problem_id": row.get("problem_id"),
            "dataset": args.dataset,
            "data_path": data_path,
            "statement": row.get(args.statement_column, ""),
            "slow_code": row.get(slow_column, ""),
            "model": model,
            "status": "failed",
            "error_stage": "runtime",
            "error_message": str(exc),
        }

    def _log_done(rec: Dict[str, Any]) -> None:
        print(
            f"[done] problem_id={rec.get('problem_id')} status={rec.get('status')} "
            f"candidates={rec.get('candidate_count', 0)} survivors={rec.get('survivor_count', 0)}",
            flush=True,
        )

    with open(args.out, "a", encoding="utf-8") as out_f:
        if workers == 1:
            for row in rows:
                try:
                    rec = _process_row(row)
                except Exception as exc:  # noqa: BLE001
                    rec = _failed_record(row, exc)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()
                _log_done(rec)
        else:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(_process_row, row): row for row in rows}
                for fut in as_completed(futs):
                    row = futs[fut]
                    try:
                        rec = fut.result()
                    except Exception as exc:  # noqa: BLE001
                        rec = _failed_record(row, exc)
                    with out_lock:
                        out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        out_f.flush()
                    _log_done(rec)


if __name__ == "__main__":
    main()
