"""Shared pair-row normalization for trace mining inputs."""

from __future__ import annotations

import re
from typing import Any, Dict


_CODE_FENCE_RE = re.compile(r"```[^\n`]*\n?(.*?)```", re.DOTALL)
_PERFORMANCE_LABEL_RE = re.compile(r"^\s*(FASTER|SLOWER)\b", re.IGNORECASE)


def _strip_code_block(text: str) -> str:
    value = str(text or "").strip()
    match = _CODE_FENCE_RE.search(value)
    if match:
        return match.group(1).strip()
    return value


def _extract_ab_code_blocks(text: str) -> tuple[str, str] | None:
    """Return Code A and Code B bodies from the released AB prompt format."""

    value = str(text or "")
    if "Code A" not in value or "Code B" not in value:
        return None
    blocks = [_strip_code_block(match.group(0)) for match in _CODE_FENCE_RE.finditer(value)]
    if len(blocks) < 2:
        return None
    code_a = blocks[0].strip()
    code_b = blocks[1].strip()
    if not code_a or not code_b:
        return None
    return code_a, code_b


def _performance_label(text: str) -> str:
    match = _PERFORMANCE_LABEL_RE.match(str(text or ""))
    return match.group(1).lower() if match else ""


def normalize_pair_row(
    row: Dict[str, Any],
    *,
    statement_column: str = "statement",
    slow_column: str = "slow_code",
    fast_column: str = "fast_code",
    speedup_ratio_column: str = "speedup_ratio",
) -> Dict[str, Any]:
    """Normalize standard slow/fast rows and AB-style rows into one shape."""

    adapted = dict(row)
    slow_code = str(adapted.get(slow_column, "") or "").strip()
    fast_code = str(adapted.get(fast_column, "") or "").strip()
    if slow_code and fast_code:
        if speedup_ratio_column in adapted and "speedup_ratio" not in adapted:
            adapted["speedup_ratio"] = adapted.get(speedup_ratio_column)
        return adapted

    input_text = str(adapted.get("input", "") or "").strip()
    output_text = str(adapted.get("output", "") or "").strip()
    if not input_text or not output_text:
        return adapted

    label = _performance_label(output_text)
    ab_blocks = _extract_ab_code_blocks(input_text)
    if ab_blocks is not None and label:
        code_a, code_b = ab_blocks
        if label == "faster":
            slow_code, fast_code = code_a, code_b
        else:
            slow_code, fast_code = code_b, code_a
        adapted[slow_column] = slow_code
        adapted[fast_column] = fast_code
        if not str(adapted.get(statement_column, "") or "").strip():
            adapted[statement_column] = str(
                adapted.get("instruction", "") or adapted.get("prompt", "") or ""
            ).strip()
        if speedup_ratio_column in adapted and "speedup_ratio" not in adapted:
            adapted["speedup_ratio"] = adapted.get(speedup_ratio_column)
        return adapted

    if label:
        return adapted

    direction = str(adapted.get("direction", "") or "").strip().lower()
    if direction in {"reverse", "fast_to_slow", "output_to_input"}:
        slow_code, fast_code = output_text, input_text
    else:
        slow_code, fast_code = input_text, output_text

    adapted[slow_column] = slow_code
    adapted[fast_column] = fast_code
    if not str(adapted.get(statement_column, "") or "").strip():
        adapted[statement_column] = str(
            adapted.get("instruction", "") or adapted.get("prompt", "") or ""
        ).strip()
    if speedup_ratio_column in adapted and "speedup_ratio" not in adapted:
        adapted["speedup_ratio"] = adapted.get(speedup_ratio_column)
    return adapted
