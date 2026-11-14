from effiskill.inference import impact_python as infer_noexec, impact_cpp as infer_noexec_cpp


def test_inference_prompts_request_impact_schema_fields():
    s2 = infer_noexec.build_s2_messages(
        "",
        {"must_change": "algorithm"},
        [{"skill_id": "O001", "impact_expected_band": "high"}],
        num_skill_sets=1,
        skills_per_set=3,
    )[0]["content"]
    s3 = infer_noexec.build_s3_messages(
        "",
        "statement",
        "code",
        {"must_change": "algorithm"},
        {"selected_skills": [{"skill_id": "O001"}]},
        [],
    )[0]["content"]

    assert "expected_role" in s2
    assert "impact fields" in s2
    assert "route_type" in s2
    assert "expected_change" in s2
    assert "expected_speedup_band" in s3
    assert "optimization_mechanism" in s3
    assert "must_change_alignment" in s3
    assert "old_hot_path" in s3
    assert "new_mechanism" in s3


def test_cpp_inference_prompts_request_cpp_impact_schema_fields():
    s2 = infer_noexec_cpp.build_s2_messages(
        "",
        {"must_change": "algorithm"},
        [{"skill_id": "O001", "impact_expected_band": "very_high"}],
        num_skill_sets=1,
        skills_per_set=3,
    )[0]["content"]
    s3 = infer_noexec_cpp.build_s3_messages(
        "",
        "statement",
        "code",
        {"must_change": "algorithm"},
        {"selected_skills": [{"skill_id": "O001"}]},
        [],
    )[0]["content"]

    assert "expected_role" in s2
    assert "C++" in s2
    assert "route_type" in s2
    assert "expected_change" in s2
    assert "expected_speedup_band" in s3
    assert "optimization_mechanism" in s3
    assert "must_change_alignment" in s3
    assert "old_hot_path" in s3
    assert "new_mechanism" in s3
