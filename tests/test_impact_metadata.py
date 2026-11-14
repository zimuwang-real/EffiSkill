from effiskill.inference import impact_python as infer_noexec, impact_cpp as infer_noexec_cpp


def test_python_registry_meta_exposes_impact_fields():
    meta = infer_noexec._op_registry_meta(
        [
            {
                "skill_id": "O001",
                "name": "Example",
                "description": "Example",
                "family": "data_structure",
                "optimization_scope": "data_structure",
                "impact_expected_band": "high",
                "impact_speedup_p75": 5.0,
                "impact_speedup_max": 12.0,
            }
        ]
    )

    assert meta[0]["impact_expected_band"] == "high"
    assert meta[0]["impact_speedup_p75"] == 5.0
    assert meta[0]["optimization_scope"] == "data_structure"


def test_cpp_registry_meta_exposes_impact_fields():
    meta = infer_noexec_cpp._op_registry_meta(
        [
            {
                "skill_id": "O001",
                "language": "cpp",
                "name": "Example",
                "description": "Example",
                "family": "data_structure",
                "optimization_scope": "data_structure",
                "impact_expected_band": "very_high",
                "impact_speedup_max": 30.0,
            }
        ]
    )

    assert meta[0]["language"] == "cpp"
    assert meta[0]["impact_expected_band"] == "very_high"
    assert meta[0]["impact_speedup_max"] == 30.0


def test_skill_set_normalization_preserves_expected_role():
    raw = {
        "skill_sets": [
            {
                "set_id": "S",
                "selected_skills": [
                    {
                        "skill_id": "O001",
                        "reason": "matches",
                        "expected_role": "primary_high_impact",
                    }
                ],
            }
        ]
    }

    normalized = infer_noexec._normalize_skill_sets(
        raw,
        valid_operator_ids={"O001"},
        num_skill_sets=1,
        skills_per_set=3,
    )

    assert normalized[0]["selected_skills"][0]["expected_role"] == "primary_high_impact"


def test_plan_normalization_preserves_impact_fields():
    raw = {
        "plans": [
            {
                "plan_id": "P1",
                "plan_style": "aggressive",
                "name": "Rewrite",
                "core_idea": "Change algorithm.",
                "target_complexity": "O(n)",
                "optimization_mechanism": "algorithmic",
                "expected_speedup_band": "high",
                "impact_skill_ids": ["O001"],
                "must_change_alignment": "matches",
            }
        ]
    }

    plans = infer_noexec._normalize_plans(raw, set_id="S")
    plan = next(p for p in plans if p["plan_id"] == "P1")

    assert plan["optimization_mechanism"] == "algorithmic"
    assert plan["expected_speedup_band"] == "high"
    assert plan["impact_skill_ids"] == ["O001"]
    assert plan["must_change_alignment"] == "matches"


def test_plan_allocation_prioritizes_high_impact_plan_when_budget_is_tight():
    plans = [
        {
            "plan_id": "low",
            "plan_style": "conservative",
            "expected_speedup_band": "mild",
            "must_change_alignment": "partial",
            "impact_skill_ids": [],
        },
        {
            "plan_id": "high",
            "plan_style": "aggressive",
            "expected_speedup_band": "high",
            "must_change_alignment": "matches",
            "impact_skill_ids": ["O001"],
        },
    ]

    assert infer_noexec._allocate_plan_slots(plans, k=1) == [0, 1]


def test_cpp_registry_language_validation_counts_mixed_and_unlabeled_skills():
    stats = infer_noexec_cpp._validate_cpp_registry_language(
        [
            {"skill_id": "O001", "language": "cpp"},
            {"skill_id": "O002", "language": "python"},
            {"skill_id": "O003"},
        ]
    )

    assert stats == {
        "operator_count": 3,
        "cpp_count": 1,
        "other_language_count": 1,
        "unlabeled_count": 1,
    }
