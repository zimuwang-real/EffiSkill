import json


from effiskill.mining.build_registry import build_registry


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
