#!/usr/bin/env bash
set -euo pipefail

# Extract a speedup-aware C++ EffiSkill skill library from the C++ mining dataset.
#
# Usage:
#   bash scripts/extract_cpp_skill_library.sh [THREADS] [INPUT_JSONL] [OUTPUT_ROOT]
#
# Examples:
#   bash scripts/extract_cpp_skill_library.sh
#   bash scripts/extract_cpp_skill_library.sh 16
#   bash scripts/extract_cpp_skill_library.sh 16 data/mining/cpp/cpp_ab_test.jsonl outputs/cpp_speedup_library
#   EFFISKILL_RESUME=1 bash scripts/extract_cpp_skill_library.sh 16
#   EFFISKILL_OVERWRITE=1 bash scripts/extract_cpp_skill_library.sh 16
#   EFFISKILL_LIMIT=50 bash scripts/extract_cpp_skill_library.sh 8 data/mining/cpp/cpp_ab_test.jsonl outputs/cpp_smoke
#
# Current parallelism:
#   THREADS is passed to pairs-to-traces, which supports multithreaded API calls.
#   extract-skills currently has no --workers option; cluster summaries, examples,
#   and meta-skill LLM calls are executed sequentially by the current implementation.
#
# Tunable mining parameters:
#   EFFISKILL_CPP_K=40
#   EFFISKILL_CPP_SUPPORT_REJECT_ALPHA=0.01
#   EFFISKILL_CPP_SUPPORT_REJECT_FLOOR=6
#   EFFISKILL_CPP_MERGE_SIMILARITY=0.76
#   EFFISKILL_SUMMARY_WORKERS=8

THREADS="${1:-8}"
INPUT_JSONL="${2:-data/mining/cpp/cpp_ab_test.jsonl}"
OUTPUT_ROOT="${3:-outputs/cpp_speedup_aware_library}"
RESUME="${EFFISKILL_RESUME:-0}"
OVERWRITE="${EFFISKILL_OVERWRITE:-0}"
LIMIT="${EFFISKILL_LIMIT:-}"
K_CLUSTERS="${EFFISKILL_CPP_K:-40}"
SUPPORT_REJECT_ALPHA="${EFFISKILL_CPP_SUPPORT_REJECT_ALPHA:-0.01}"
SUPPORT_REJECT_FLOOR="${EFFISKILL_CPP_SUPPORT_REJECT_FLOOR:-6}"
MERGE_SIMILARITY="${EFFISKILL_CPP_MERGE_SIMILARITY:-0.76}"
SUMMARY_WORKERS="${EFFISKILL_SUMMARY_WORKERS:-8}"

# Replace these placeholders, or export the same variables before running.
export EFFISKILL_BASE_URL="${EFFISKILL_BASE_URL:-https://YOUR_OPENAI_COMPATIBLE_ENDPOINT/v1}"
export EFFISKILL_API_KEY="${EFFISKILL_API_KEY:-YOUR_API_KEY}"
export EFFISKILL_MODEL="${EFFISKILL_MODEL:-YOUR_MODEL_NAME}"
export EFFISKILL_LLM_TIMEOUT_SEC="${EFFISKILL_LLM_TIMEOUT_SEC:-180}"

if [[ "${EFFISKILL_BASE_URL}" == "https://YOUR_OPENAI_COMPATIBLE_ENDPOINT/v1" \
  || "${EFFISKILL_API_KEY}" == "YOUR_API_KEY" \
  || "${EFFISKILL_MODEL}" == "YOUR_MODEL_NAME" ]]; then
  echo "Please set EFFISKILL_BASE_URL, EFFISKILL_API_KEY, and EFFISKILL_MODEL before running." >&2
  echo "Example:" >&2
  echo "  export EFFISKILL_BASE_URL='https://.../v1'" >&2
  echo "  export EFFISKILL_API_KEY='...'" >&2
  echo "  export EFFISKILL_MODEL='...'" >&2
  echo "  bash scripts/extract_cpp_skill_library.sh ${THREADS}" >&2
  exit 2
fi

TRACES_PATH="${OUTPUT_ROOT}/traces.jsonl"
GEN_DIR="${OUTPUT_ROOT}/gen"
SKILLS_DIR="${GEN_DIR}/skills"
CACHE_DIR="${OUTPUT_ROOT}/cache_pairs_to_traces"
FAIL_DIR="${OUTPUT_ROOT}/fail_pairs_to_traces"
RESUME_ARGS=(--no-resume)

if [[ -n "${LIMIT}" ]]; then
  if ! [[ "${LIMIT}" =~ ^[0-9]+$ ]]; then
    echo "EFFISKILL_LIMIT must be a non-negative integer." >&2
    exit 2
  fi
fi

if [[ "${RESUME}" == "1" && "${OVERWRITE}" == "1" ]]; then
  echo "EFFISKILL_RESUME=1 and EFFISKILL_OVERWRITE=1 are mutually exclusive." >&2
  exit 2
fi

if [[ -e "${OUTPUT_ROOT}" && "${RESUME}" != "1" && "${OVERWRITE}" != "1" ]]; then
  echo "Output directory already exists: ${OUTPUT_ROOT}" >&2
  echo "Use a fresh third argument, set EFFISKILL_RESUME=1 to continue, or set EFFISKILL_OVERWRITE=1 to delete and rebuild." >&2
  exit 2
fi

if [[ "${OVERWRITE}" == "1" ]]; then
  rm -rf "${OUTPUT_ROOT}"
elif [[ "${RESUME}" == "1" ]]; then
  RESUME_ARGS=(--resume)
fi

echo "[1/4] Building C++ traces"
PAIR_CMD=(python -m effiskill_artifact.cli pairs-to-traces --language cpp --)
PAIR_CMD+=(
  --input "${INPUT_JSONL}"
  --input-format auto
  --statement-column statement
  --slow-column slow_code
  --fast-column fast_code
  --problem-id-column problem_id
  --speedup-ratio-column speedup_ratio
  --output "${TRACES_PATH}"
  --cache-dir "${CACHE_DIR}"
  --fail-dir "${FAIL_DIR}"
  --base-url "${EFFISKILL_BASE_URL}"
  --api-key "${EFFISKILL_API_KEY}"
  --timeout-sec "${EFFISKILL_LLM_TIMEOUT_SEC}"
  --model "${EFFISKILL_MODEL}"
  --max-tokens 8192
  --max-statement-chars 1500
  --max-code-chars 1500
  --reasoning-effort medium
  --workers "${THREADS}"
)
if [[ -n "${LIMIT}" ]]; then
  PAIR_CMD+=(--limit "${LIMIT}")
fi
PAIR_CMD+=("${RESUME_ARGS[@]}")
PYTHONPATH=src "${PAIR_CMD[@]}"

echo "[2/4] Extracting speedup-aware C++ skills"
EXTRACT_CMD=(python -m effiskill_artifact.cli extract-skills --language cpp --)
EXTRACT_CMD+=(
  --gen-dir "${GEN_DIR}"
  --traces "${TRACES_PATH}"
  --cluster-mode stage1
  --speedup-aware-mining
  --speedup-weight-cap 20
  --speedup-weight-beta 2
  --max-combined-trace-weight 9
  --sample-per-cluster 30
  --summary-workers "${SUMMARY_WORKERS}"
  --tfidf-max-features 4096
  --embedding-model all-MiniLM-L6-v2
  --cluster-algorithm kmeans
  --k "${K_CLUSTERS}"
  --merge-similarity "${MERGE_SIMILARITY}"
  --min-skills off
  --support-reject-mode reject
  --support-reject-alpha "${SUPPORT_REJECT_ALPHA}"
  --support-reject-floor "${SUPPORT_REJECT_FLOOR}"
  --min-skill-coverage 0.80
  --model "${EFFISKILL_MODEL}"
  --base-url "${EFFISKILL_BASE_URL}"
  --api-key "${EFFISKILL_API_KEY}"
  --timeout-sec "${EFFISKILL_LLM_TIMEOUT_SEC}"
  --fallback-model "${EFFISKILL_MODEL}"
  --summary-temperature 0.2
  --summary-max-tokens 32000
  --example-temperature 0.2
  --example-max-tokens 32000
  --meta-temperature 0.35
  --meta-max-tokens 32000
  --reasoning-effort low
  --seed 42
)
if [[ -n "${LIMIT}" ]]; then
  EXTRACT_CMD+=(--limit "${LIMIT}")
fi
PYTHONPATH=src "${EXTRACT_CMD[@]}"

echo "[3/4] Rebuilding registry"
PYTHONPATH=src python -m effiskill_artifact.cli build-registry --language cpp -- \
  --skills_dir "${SKILLS_DIR}" \
  --out "${SKILLS_DIR}/registry.json"

echo "[4/4] Done"
echo "Traces:   ${TRACES_PATH}"
echo "Library:  ${SKILLS_DIR}"
echo "Registry: ${SKILLS_DIR}/registry.json"
