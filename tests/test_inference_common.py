from effiskill.inference import python as infer_noexec, cpp as infer_noexec_cpp
from effiskill.inference.common import (
    allocate_plan_slots,
    decoding_profile_for,
    normalize_plans,
    normalize_skill_sets,
)


def test_normalize_skill_sets_preserves_route_type_and_expected_change():
    raw = {
        "skill_sets": [
            {
                "set_id": "S1",
                "route_type": "algorithmic_rewrite",
                "selection_theme": "replace nested loops",
                "expected_change": "O(n^2) to O(n)",
                "selected_skills": [
                    {
                        "skill_id": "O001",
                        "reason": "matches nested-loop bottleneck",
                        "expected_role": "primary_high_impact",
                    }
                ],
            }
        ]
    }

    out = normalize_skill_sets(
        raw,
        valid_operator_ids={"O001"},
        num_skill_sets=1,
        skills_per_set=3,
    )

    assert out[0]["route_type"] == "algorithmic_rewrite"
    assert out[0]["expected_change"] == "O(n^2) to O(n)"
    assert out[0]["selected_skills"][0]["expected_role"] == "primary_high_impact"


def test_normalize_plans_preserves_route_and_hot_path_fields():
    raw = {
        "plans": [
            {
                "plan_id": "P1",
                "route_type": "data_structure",
                "plan_style": "balanced",
                "old_hot_path": "repeated map lookups",
                "new_mechanism": "direct-address frequency array",
                "expected_speedup_band": "high",
                "impact_skill_ids": ["O003"],
                "must_change_alignment": "matches",
            }
        ]
    }

    plans = normalize_plans(raw, set_id="S1", default_route_type="fallback")

    plan = next(p for p in plans if p["plan_id"] == "P1")

    assert plan["route_type"] == "data_structure"
    assert plan["old_hot_path"] == "repeated map lookups"
    assert plan["new_mechanism"] == "direct-address frequency array"


def test_allocate_plan_slots_prefers_mechanism_diversity_for_algorithmic_tasks():
    plans = [
        {
            "plan_id": "alg",
            "route_type": "algorithmic_rewrite",
            "plan_style": "aggressive",
            "expected_speedup_band": "high",
            "must_change_alignment": "matches",
            "impact_skill_ids": ["O001"],
        },
        {
            "plan_id": "ds",
            "route_type": "data_structure",
            "plan_style": "balanced",
            "expected_speedup_band": "high",
            "must_change_alignment": "matches",
            "impact_skill_ids": ["O002"],
        },
        {
            "plan_id": "io",
            "route_type": "io",
            "plan_style": "conservative",
            "expected_speedup_band": "high",
            "must_change_alignment": "matches",
            "impact_skill_ids": ["O003"],
        },
    ]

    assert allocate_plan_slots(plans, k=3, must_change="algorithm") == [1, 1, 1]


def test_allocate_plan_slots_gives_extra_algorithmic_slot_before_io_for_algorithmic_tasks():
    plans = [
        {
            "plan_id": "alg",
            "route_type": "algorithmic_rewrite",
            "plan_style": "aggressive",
            "expected_speedup_band": "very_high",
            "must_change_alignment": "matches",
            "impact_skill_ids": ["O001"],
        },
        {
            "plan_id": "ds",
            "route_type": "data_structure",
            "plan_style": "balanced",
            "expected_speedup_band": "high",
            "must_change_alignment": "matches",
            "impact_skill_ids": ["O002"],
        },
        {
            "plan_id": "io",
            "route_type": "io",
            "plan_style": "conservative",
            "expected_speedup_band": "high",
            "must_change_alignment": "partial",
            "impact_skill_ids": ["O003"],
        },
    ]

    assert allocate_plan_slots(plans, k=4, must_change="algorithm") == [2, 1, 1]


def test_decoding_profile_is_model_specific_not_language_specific():
    gpt = decoding_profile_for("gpt-5-mini")
    qwen = decoding_profile_for("qwen30b")

    assert gpt.s1_temperature == 0.3
    assert gpt.aggressive_generation_temperature == 0.8
    assert qwen.s1_temperature == 0.2
    assert qwen.aggressive_generation_temperature == 0.7


def test_language_wrappers_use_shared_route_normalizers_and_allocator():
    raw = {
        "skill_sets": [
            {
                "route_type": "math_precompute",
                "selected_skills": [{"skill_id": "O001"}],
            }
        ]
    }

    py_sets = infer_noexec._normalize_skill_sets(
        raw,
        valid_operator_ids={"O001"},
        num_skill_sets=1,
        skills_per_set=2,
    )
    cpp_sets = infer_noexec_cpp._normalize_skill_sets(
        raw,
        valid_operator_ids={"O001"},
        num_skill_sets=1,
        skills_per_set=2,
    )

    assert py_sets[0]["route_type"] == "math_precompute"
    assert cpp_sets[0]["route_type"] == "math_precompute"
    assert infer_noexec._allocate_plan_slots(
        [{"route_type": "algorithmic_rewrite", "expected_speedup_band": "high"}],
        1,
        must_change="algorithm",
    ) == [1]
    assert infer_noexec_cpp._allocate_plan_slots(
        [{"route_type": "algorithmic_rewrite", "expected_speedup_band": "high"}],
        1,
        must_change="algorithm",
    ) == [1]


def test_python_runner_keeps_generated_candidates_even_when_diagnostics_fail(monkeypatch):
    calls = []

    def fake_llm_json_call(*args, **kwargs):
        stage = kwargs["stage"]
        calls.append((stage, kwargs["temperature"]))
        if stage.endswith("_s1_diagnose"):
            return {"must_change": "algorithm"}
        if stage.endswith("_s2_multi_retrieve"):
            return {
                "skill_sets": [
                    {
                        "set_id": "S1",
                        "route_type": "algorithmic_rewrite",
                        "selected_skills": [{"skill_id": "O001"}],
                    }
                ]
            }
        if "_s3_plan_" in stage:
            return {
                "plans": [
                    {
                        "plan_id": "P1",
                        "route_type": "algorithmic_rewrite",
                        "plan_style": "aggressive",
                        "expected_speedup_band": "high",
                    }
                ]
            }
        if "_s4_gen_" in stage:
            return {
                "code": "def solve():\n    return 1\n",
                "complexity": {},
                "dominant_ops": [],
                "notes": "intentionally failed self-check",
                "change_summary": {"removed_hot_path": ""},
                "static_verdict": "fail",
                "interface_match": False,
                "complexity_plausible": False,
                "static_issues": ["plan_not_implemented"],
                "static_confidence": 0.0,
            }
        raise AssertionError(stage)

    monkeypatch.setattr(infer_noexec, "llm_json_call", fake_llm_json_call)

    result = infer_noexec.run_problem(
        problem_id="p",
        statement="statement",
        slow_code="def solve():\n    return 0\n",
        model="gpt-5-mini",
        client=object(),
        cache_dir="",
        fail_dir="",
        meta_skills={"S1": "", "S2": "", "S3": ""},
        skills_index={"O001": {"content": "skill"}},
        operator_registry=[{"skill_id": "O001"}],
        num_skill_sets=1,
        skills_per_set=1,
        k=1,
        sanity_fix=False,
        require_syntax=True,
    )

    assert result["status"] == "ok"
    assert result["candidate_count"] == 1
    assert result["survivor_count"] == 1
    assert result["survivor_candidates"][0]["static_verdict"] == "fail"
    assert result["survivor_candidates"][0]["change_summary"] == {"removed_hot_path": ""}
    assert calls[0][1] == 0.3


def test_allocate_plan_slots_penalizes_repeated_mechanisms():
    def plan(pid, set_id, mechanism, band):
        return {
            "plan_id": pid,
            "set_id": set_id,
            "route_type": "data_structure",
            "plan_style": "balanced",
            "expected_speedup_band": band,
            "must_change_alignment": "matches",
            "optimization_mechanism": mechanism,
        }

    plans = [
        plan("a1", "A", "prefix sums over counts", "very_high"),
        plan("a2", "A", "prefix sums over counts", "very_high"),
        plan("b1", "B", "two-pointer sweep", "moderate"),
    ]
    # One slot per distinct mechanism first, so the moderate but distinct plan is covered.
    assert allocate_plan_slots(plans, k=2, must_change="implementation") == [1, 0, 1]


def test_whole_program_simplification_plan_uses_diagnosis():
    from effiskill.inference.common import whole_program_simplification_plan

    plan = whole_program_simplification_plan(
        {
            "must_change": "algorithm",
            "complexity": {"time": "O(n^2)"},
            "bottlenecks": [{"kind": "loop", "detail": "nested scan over pairs"}],
            "risks": ["overflow"],
        }
    )
    assert plan["plan_id"] == "WPS"
    assert plan["route_type"] == "algorithmic_rewrite"
    assert plan["old_hot_path"] == "nested scan over pairs"
    assert plan["risks"] == ["overflow"]
    assert len(plan["steps"]) == 4
