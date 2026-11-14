import json
import sys

import pytest

from effiskill.mining.pair_record_adapter import normalize_pair_row
from effiskill.mining import pairs_to_traces, pairs_to_traces_cpp


def test_standard_pair_row_is_preserved():
    row = {
        "statement": "Optimize it.",
        "slow_code": "slow()",
        "fast_code": "fast()",
        "speedup_ratio": "3.0",
    }

    adapted = normalize_pair_row(row)

    assert adapted["slow_code"] == "slow()"
    assert adapted["fast_code"] == "fast()"
    assert adapted["speedup_ratio"] == "3.0"


def test_ab_style_row_uses_input_as_slow_by_default():
    row = {
        "instruction": "Optimize it.",
        "input": "slow()",
        "output": "fast()",
        "speedup_ratio": "5.0",
    }

    adapted = normalize_pair_row(row)

    assert adapted["statement"] == "Optimize it."
    assert adapted["slow_code"] == "slow()"
    assert adapted["fast_code"] == "fast()"
    assert adapted["speedup_ratio"] == "5.0"


def test_ab_style_reverse_direction_swaps_pair_orientation():
    row = {
        "instruction": "Optimize it.",
        "input": "fast()",
        "output": "slow()",
        "direction": "reverse",
        "speedup_ratio": "5.0",
    }

    adapted = normalize_pair_row(row)

    assert adapted["slow_code"] == "slow()"
    assert adapted["fast_code"] == "fast()"


def test_performance_label_ab_row_extracts_code_blocks_and_uses_faster_label():
    row = {
        "instruction": "Predict performance.",
        "input": """=== Code A (Original) ===
```cpp
int main(){ return slow(); }
```

=== Code B (Modified) ===
```cpp
int main(){ return fast(); }
```""",
        "output": "FASTER 5.0",
        "direction": "forward",
        "speedup_ratio": "5.0",
    }

    adapted = normalize_pair_row(row)

    assert adapted["statement"] == "Predict performance."
    assert adapted["slow_code"] == "int main(){ return slow(); }"
    assert adapted["fast_code"] == "int main(){ return fast(); }"
    assert "FASTER" not in adapted["fast_code"]


def test_performance_label_ab_row_extracts_code_blocks_and_uses_slower_label():
    row = {
        "instruction": "Predict performance.",
        "input": """=== Code A (Original) ===
```cpp
int main(){ return fast(); }
```

=== Code B (Modified) ===
```cpp
int main(){ return slow(); }
```""",
        "output": "SLOWER 5.0",
        "direction": "forward",
        "speedup_ratio": "5.0",
    }

    adapted = normalize_pair_row(row)

    assert adapted["slow_code"] == "int main(){ return slow(); }"
    assert adapted["fast_code"] == "int main(){ return fast(); }"


def test_custom_columns_are_supported():
    row = {
        "prompt": "Optimize it.",
        "before": "slow()",
        "after": "fast()",
        "ratio": "2.0",
    }

    adapted = normalize_pair_row(
        row,
        statement_column="prompt",
        slow_column="before",
        fast_column="after",
        speedup_ratio_column="ratio",
    )

    assert adapted["before"] == "slow()"
    assert adapted["after"] == "fast()"
    assert adapted["speedup_ratio"] == "2.0"


def test_python_pair_to_trace_normalizer_accepts_ab_style_row():
    row = {
        "instruction": "Optimize it.",
        "input": "slow()",
        "output": "fast()",
        "speedup_ratio": "4.0",
    }

    item = pairs_to_traces._normalize_record(
        row,
        1,
        statement_column="statement",
        slow_column="slow_code",
        fast_column="fast_code",
        problem_id_column="problem_id",
        speedup_ratio_column="speedup_ratio",
        max_statement_chars=100,
        max_code_chars=100,
    )

    assert item is not None
    record, _ = item
    assert record["statement"] == "Optimize it."
    assert record["slow_code"] == "slow()"
    assert record["fast_code"] == "fast()"
    assert record["speedup_ratio"] == "4.0"


def test_cpp_pair_to_trace_normalizer_accepts_ab_style_row():
    row = {
        "instruction": "Optimize it.",
        "input": "slow_cpp();",
        "output": "fast_cpp();",
        "speedup_ratio": "8.0",
    }

    item = pairs_to_traces_cpp._normalize_record(
        row,
        1,
        statement_column="statement",
        slow_column="slow_code",
        fast_column="fast_code",
        problem_id_column="problem_id",
        speedup_ratio_column="speedup_ratio",
        max_statement_chars=100,
        max_code_chars=100,
    )

    assert item is not None
    record, _ = item
    assert record["statement"] == "Optimize it."
    assert record["slow_code"] == "slow_cpp();"
    assert record["fast_code"] == "fast_cpp();"
    assert record["speedup_ratio"] == "8.0"


@pytest.mark.parametrize("module", [pairs_to_traces, pairs_to_traces_cpp])
def test_pairs_to_traces_skips_duplicate_source_hashes_in_same_run(
    tmp_path, monkeypatch, module
):
    code_slow = "int main(){ return slow(); }"
    code_fast = "int main(){ return fast(); }"
    rows = [
        {
            "problem_id": "P_DUP",
            "instruction": "Predict performance.",
            "input": f"""=== Code A (Original) ===
```cpp
{code_slow}
```

=== Code B (Modified) ===
```cpp
{code_fast}
```""",
            "output": "FASTER 5.0",
            "speedup_ratio": "5.0",
        },
        {
            "problem_id": "P_DUP",
            "instruction": "Predict performance.",
            "input": f"""=== Code A (Original) ===
```cpp
{code_fast}
```

=== Code B (Modified) ===
```cpp
{code_slow}
```""",
            "output": "SLOWER 5.0",
            "speedup_ratio": "5.0",
        },
    ]
    input_path = tmp_path / "pairs.jsonl"
    input_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )
    output_path = tmp_path / "traces.jsonl"
    calls = []

    def fake_llm_json_call(**kwargs):
        calls.append(kwargs)
        return {
            "ProblemBrief": {"constraints_guess": {}, "problem_type_tags": ["test"]},
            "SlowAudit": {"dominant_ops": [], "complexity": {}, "bottlenecks": []},
            "FastAudit": {"core_idea": "faster code", "complexity": {}},
            "DeltaSummary": {
                "delta_type": ["FASTER"],
                "complexity_delta": {},
                "transformation_steps": [],
                "trigger_signals": [],
                "pitfalls": [],
            },
        }

    monkeypatch.setattr(module, "_llm_json_call", fake_llm_json_call)
    monkeypatch.setattr(module, "configure_default_client", lambda **kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pairs-to-traces",
            "--input",
            str(input_path),
            "--input-format",
            "jsonl",
            "--output",
            str(output_path),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--fail-dir",
            str(tmp_path / "fail"),
            "--model",
            "test-model",
            "--workers",
            "1",
            "--no-resume",
        ],
    )

    module.main()

    written = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert len(calls) == 1
    assert len(written) == 1
    assert written[0]["speedup_ratio"] == "5.0"
