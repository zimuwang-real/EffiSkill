import json

import yaml

from effiskill_artifact.build_registry import build_registry
from effiskill_artifact.extract_skills import _render_operator_skill_text


def test_rendered_operator_skill_contains_impact_frontmatter():
    text, card = _render_operator_skill_text(
        summary={
            "proposed_name": "Replace Enumeration With Counting",
            "description": "Collapse repeated enumeration into counting.",
            "tags": ["counting"],
            "canonical_triggers": ["Nested loops enumerate countable cases."],
            "canonical_steps": ["Replace enumeration with grouped counting."],
            "complexity_time": "O(n^2) -> O(n)",
            "complexity_space": "O(1)",
            "optimization_scope": "algorithmic",
            "expected_speedup_band": "high",
            "impact_support_count": 4,
            "impact_support_weight": 8.5,
            "impact_speedup_median": 3.0,
            "impact_speedup_p75": 6.0,
            "impact_speedup_max": 12.0,
        },
        skill_id="O001",
        example_override="Before:\n```py\nslow()\n```\nAfter:\n```py\nfast()\n```",
    )

    front = yaml.safe_load(text.split("---", 2)[1])

    assert front["optimization_scope"] == "algorithmic"
    assert front["impact_expected_band"] == "high"
    assert front["impact_speedup_max"] == 12.0
    assert card["impact_speedup_p75"] == 6.0
    assert "## Evidence and expected impact" in text


def test_registry_preserves_flat_impact_fields(tmp_path):
    skill_dir = tmp_path / "skills" / "operators" / "O001_example"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
skill_id: O001
type: operator
language: python
family: data_structure
optimization_scope: data_structure
name: Example Skill
description: Example.
impact_support_count: 4
impact_support_weight: 7.5
impact_speedup_median: 2.0
impact_speedup_p75: 5.0
impact_speedup_max: 12.0
impact_expected_band: high
impact_weight: 7.5
impact_source: mined_pair_speedup_ratio
---

## When to use
- Example trigger.
""",
        encoding="utf-8",
    )
    out = tmp_path / "skills" / "registry.json"

    cards = build_registry(str(tmp_path / "skills"), str(out))

    assert cards[0]["impact_expected_band"] == "high"
    assert cards[0]["impact_speedup_max"] == 12.0
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded[0]["impact_support_weight"] == 7.5
