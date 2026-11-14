"""Locations of bundled assets.

EffiSkill is meant to be installed from a clone (``pip install -e .``); the
frozen skill libraries live at the repository root so
they are easy to browse. Set ``EFFISKILL_HOME`` to point at a checkout when the
package is installed elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """The EffiSkill checkout: ``EFFISKILL_HOME``, the source tree, or the working directory."""
    env = os.getenv("EFFISKILL_HOME", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    source_tree = Path(__file__).resolve().parents[2]
    if (source_tree / "skills").is_dir():
        return source_tree
    if (Path.cwd() / "skills").is_dir():
        return Path.cwd()
    return source_tree


def skills_root(language: str) -> Path:
    """Frozen skill library used in the paper for ``python`` or ``cpp``."""
    if language not in {"python", "cpp"}:
        raise ValueError(f"unknown language: {language!r}")
    return repo_root() / "skills" / language


def outputs_root() -> Path:
    """Default output directory, relative to the caller's working directory."""
    return Path.cwd() / "outputs"
