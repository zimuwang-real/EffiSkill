#!/usr/bin/env bash
set -euo pipefail

# Extraction-only C++ skill library iteration from existing expensive traces.
#
# Usage:
#   bash scripts/extract_cpp_skill_library_from_traces.sh [RAW_TRACES_JSONL] [OUTPUT_ROOT]
#
# Example:
#   bash scripts/extract_cpp_skill_library_from_traces.sh \
#     outputs/cpp_speedup_aware_library_v3/traces.jsonl \
#     outputs/cpp_speedup_aware_library_v5_threshold
#
# Tunable environment variables:
#   EFFISKILL_CPP_K=40
#   EFFISKILL_CPP_SUPPORT_REJECT_ALPHA=0.01
#   EFFISKILL_CPP_SUPPORT_REJECT_FLOOR=6
#   EFFISKILL_CPP_MERGE_SIMILARITY=0.76
#   EFFISKILL_CPP_SAMPLE_PER_CLUSTER=30
#   EFFISKILL_SUMMARY_WORKERS=8
#   EFFISKILL_OVERWRITE=1

RAW_TRACES="${1:-outputs/cpp_speedup_aware_library_v3/traces.jsonl}"
OUTPUT_ROOT="${2:-outputs/cpp_speedup_aware_library_v5_threshold}"
OVERWRITE="${EFFISKILL_OVERWRITE:-0}"

K_CLUSTERS="${EFFISKILL_CPP_K:-40}"
SUPPORT_REJECT_ALPHA="${EFFISKILL_CPP_SUPPORT_REJECT_ALPHA:-0.01}"
SUPPORT_REJECT_FLOOR="${EFFISKILL_CPP_SUPPORT_REJECT_FLOOR:-6}"
MERGE_SIMILARITY="${EFFISKILL_CPP_MERGE_SIMILARITY:-0.76}"
SAMPLE_PER_CLUSTER="${EFFISKILL_CPP_SAMPLE_PER_CLUSTER:-30}"
SUMMARY_WORKERS="${EFFISKILL_SUMMARY_WORKERS:-8}"

export EFFISKILL_BASE_URL="${EFFISKILL_BASE_URL:-https://YOUR_OPENAI_COMPATIBLE_ENDPOINT/v1}"
export EFFISKILL_API_KEY="${EFFISKILL_API_KEY:-YOUR_API_KEY}"
export EFFISKILL_MODEL="${EFFISKILL_MODEL:-YOUR_MODEL_NAME}"
export EFFISKILL_LLM_TIMEOUT_SEC="${EFFISKILL_LLM_TIMEOUT_SEC:-180}"

if [[ ! -f "${RAW_TRACES}" ]]; then
  echo "Raw traces not found: ${RAW_TRACES}" >&2
  exit 2
fi

if [[ "${EFFISKILL_BASE_URL}" == "https://YOUR_OPENAI_COMPATIBLE_ENDPOINT/v1" \
  || "${EFFISKILL_API_KEY}" == "YOUR_API_KEY" \
  || "${EFFISKILL_MODEL}" == "YOUR_MODEL_NAME" ]]; then
  echo "Please set EFFISKILL_BASE_URL, EFFISKILL_API_KEY, and EFFISKILL_MODEL before running." >&2
  exit 2
fi

if [[ -e "${OUTPUT_ROOT}" && "${OVERWRITE}" != "1" ]]; then
  echo "Output directory already exists: ${OUTPUT_ROOT}" >&2
  echo "Use a fresh second argument or set EFFISKILL_OVERWRITE=1 to delete and rebuild." >&2
  exit 2
fi

if [[ "${OVERWRITE}" == "1" ]]; then
  rm -rf "${OUTPUT_ROOT}"
fi

GEN_DIR="${OUTPUT_ROOT}/gen"
CLEANED_TRACES="${OUTPUT_ROOT}/traces_cleaned.jsonl"
CLEANING_REPORT="${OUTPUT_ROOT}/trace_cleaning_report.json"
mkdir -p "${OUTPUT_ROOT}"

echo "[1/2] Cleaning existing C++ traces"
PYTHONPATH=src python -m effiskill_artifact.trace_quality \
  --input "${RAW_TRACES}" \
  --output "${CLEANED_TRACES}" \
  --report "${CLEANING_REPORT}"

echo "[2/2] Extracting C++ skills from cleaned traces"
PYTHONPATH=src python -m effiskill_artifact.cli extract-skills --language cpp -- \
  --gen-dir "${GEN_DIR}" \
  --traces "${CLEANED_TRACES}" \
  --cluster-mode stage1 \
  --speedup-aware-mining \
  --speedup-weight-cap 20 \
  --speedup-weight-beta 2 \
  --max-combined-trace-weight 9 \
  --sample-per-cluster "${SAMPLE_PER_CLUSTER}" \
  --summary-workers "${SUMMARY_WORKERS}" \
  --tfidf-max-features 4096 \
  --embedding-model all-MiniLM-L6-v2 \
  --cluster-algorithm kmeans \
  --k "${K_CLUSTERS}" \
  --merge-similarity "${MERGE_SIMILARITY}" \
  --min-skills off \
  --support-reject-mode reject \
  --support-reject-alpha "${SUPPORT_REJECT_ALPHA}" \
  --support-reject-floor "${SUPPORT_REJECT_FLOOR}" \
  --min-skill-coverage 0.80 \
  --model "${EFFISKILL_MODEL}" \
  --base-url "${EFFISKILL_BASE_URL}" \
  --api-key "${EFFISKILL_API_KEY}" \
  --timeout-sec "${EFFISKILL_LLM_TIMEOUT_SEC}" \
  --fallback-model "${EFFISKILL_MODEL}" \
  --summary-temperature 0.2 \
  --summary-max-tokens 32000 \
  --example-temperature 0.2 \
  --example-max-tokens 32000 \
  --retry-fallback-examples \
  --retry-example-temperature 0.2 \
  --retry-example-max-tokens 32000 \
  --meta-temperature 0.35 \
  --meta-max-tokens 32000 \
  --reasoning-effort low \
  --seed 42

echo "Done."
echo "Cleaned traces: ${CLEANED_TRACES}"
echo "Cleaning report: ${CLEANING_REPORT}"
echo "Skills: ${GEN_DIR}/skills"
