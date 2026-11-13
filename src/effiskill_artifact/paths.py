from __future__ import annotations

from pathlib import Path


def artifact_root() -> Path:
    """Source checkout root (legacy helper; packaged data uses data_root)."""
    return Path(__file__).resolve().parents[2]


def data_root() -> Path:
    """Frozen reference inputs shipped in both editable installs and wheels."""
    return Path(__file__).resolve().parent / "data"


def outputs_root() -> Path:
    """Resolve output without writing during argument parsing or --help."""
    return Path.cwd() / "outputs"
