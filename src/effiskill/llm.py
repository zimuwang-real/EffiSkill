"""Provider-compatibility helpers shared by mining and inference.

OpenAI reasoning models (GPT-5 family, o-series) only accept the default
temperature, so ``temperature`` is omitted for those models. Set
``EFFISKILL_SEND_TEMPERATURE=1`` to send it anyway.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

REASONING_MODEL_PREFIXES = ("gpt-5", "o1", "o3", "o4")


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}


def is_reasoning_model(model: str) -> bool:
    name = (model or "").strip().lower().rsplit("/", 1)[-1]
    if name.startswith("gpt-5") and "chat" in name:
        return False
    return name.startswith(REASONING_MODEL_PREFIXES)


def sampling_kwargs(
    model: str,
    temperature: Optional[float],
    max_tokens: Optional[int],
    *,
    max_tokens_field: str = "max_completion_tokens",
) -> Dict[str, Any]:
    """Keyword arguments for ``client.chat.completions.create``."""
    kwargs: Dict[str, Any] = {}
    if max_tokens is not None:
        kwargs[max_tokens_field] = max_tokens
    if temperature is not None and (not is_reasoning_model(model) or _env_flag("EFFISKILL_SEND_TEMPERATURE")):
        kwargs["temperature"] = temperature
    return kwargs
