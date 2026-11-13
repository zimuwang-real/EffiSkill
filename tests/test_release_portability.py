"""Public-installation behavior; these tests must never make model requests."""
import importlib
import json
from pathlib import Path

import pytest

from effiskill_artifact import paths


def test_frozen_assets_resolve_inside_installed_package():
    # A wheel must not resolve its data through the caller's repository layout.
    package = Path(paths.__file__).resolve().parent
    assert paths.data_root() == package / "data"
    registry = json.loads((paths.data_root() / "rq4/fix-version/skills/registry.json").read_text())
    assert sum(r["skill_id"].startswith("O") for r in registry) == 29


def test_default_outputs_follow_working_directory(tmp_path, monkeypatch):
    # Site-packages can be read-only; output belongs to the current workspace.
    monkeypatch.chdir(tmp_path)
    assert paths.outputs_root() == tmp_path / "outputs"


@pytest.mark.parametrize("module_name", ["paper_rq1", "paper_rq4"])
def test_reproduction_help_does_not_create_outputs(tmp_path, monkeypatch, module_name):
    monkeypatch.chdir(tmp_path)
    module = importlib.import_module("effiskill_artifact." + module_name)
    with pytest.raises(SystemExit) as error:
        module.main(["--help"])
    assert error.value.code == 0
    assert not (tmp_path / "outputs").exists()


@pytest.mark.parametrize("module_name", ["build_registry", "build_registry_cpp"])
def test_registry_can_write_bare_filename(tmp_path, monkeypatch, module_name):
    # --out registry.json is an ordinary, valid user path.
    monkeypatch.chdir(tmp_path)
    card = tmp_path / "skills/demo/SKILL.md"
    card.parent.mkdir(parents=True)
    card.write_text("---\nskill_id: O001\ntype: operator\nname: Demo\nlanguage: python\n---\nDemo\n")
    module = importlib.import_module("effiskill_artifact." + module_name)
    module.build_registry("skills", "registry.json")
    assert json.loads(Path("registry.json").read_text())[0]["skill_id"] == "O001"
