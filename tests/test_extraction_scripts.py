from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cpp_extraction_scripts_default_to_fixed_kmeans_k40():
    for rel_path in (
        "scripts/extract_cpp_skill_library.sh",
        "scripts/extract_cpp_skill_library_from_traces.sh",
    ):
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert 'EFFISKILL_CPP_K:-40' in text
        assert '--cluster-algorithm kmeans' in text
        assert '--k "${K_CLUSTERS}"' in text
        assert '--cluster-algorithm threshold' not in text
        assert '--cluster-similarity-threshold' not in text


def test_cpp_extraction_scripts_default_to_one_percent_support_reject():
    for rel_path in (
        "scripts/extract_cpp_skill_library.sh",
        "scripts/extract_cpp_skill_library_from_traces.sh",
    ):
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert 'EFFISKILL_CPP_SUPPORT_REJECT_ALPHA:-0.01' in text
        assert 'EFFISKILL_CPP_SUPPORT_REJECT_ALPHA=0.01' in text


def test_cpp_extraction_scripts_default_to_eight_summary_workers():
    for rel_path in (
        "scripts/extract_cpp_skill_library.sh",
        "scripts/extract_cpp_skill_library_from_traces.sh",
    ):
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        assert 'EFFISKILL_SUMMARY_WORKERS:-8' in text
        assert '--summary-workers "${SUMMARY_WORKERS}"' in text
