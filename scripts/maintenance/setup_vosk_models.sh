#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODELS_DIR="${ROOT_DIR}/models/vosk"
SAMPLES_DIR="${ROOT_DIR}/data/sample"
TMP_DIR="${ROOT_DIR}/artifacts/temp/vosk_setup"

RU_URL="https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
EN_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
TEST_WAV_URL="https://raw.githubusercontent.com/alphacep/vosk-api/master/python/example/test.wav"

mkdir -p "${MODELS_DIR}" "${SAMPLES_DIR}" "${TMP_DIR}"

download_and_unpack() {
  local url="$1"
  local archive_name="$2"
  local target_dir="$3"
  local archive_path="${TMP_DIR}/${archive_name}"

  if [ -d "${target_dir}" ] && [ -n "$(find "${target_dir}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
    echo "Using existing model: ${target_dir}"
    return 0
  fi

  rm -f "${archive_path}"
  rm -rf "${target_dir}"

  echo "Downloading ${url}"
  curl -L --fail --retry 3 --retry-delay 2 "${url}" -o "${archive_path}"

  echo "Unpacking ${archive_name}"
  unzip -q "${archive_path}" -d "${MODELS_DIR}"
}

download_sample() {
  local url="$1"
  local out_path="$2"

  if [ -f "${out_path}" ]; then
    echo "Using existing sample WAV: ${out_path}"
    return 0
  fi

  echo "Downloading Vosk sample WAV"
  curl -L --fail --retry 3 --retry-delay 2 "${url}" -o "${out_path}"
}

download_and_unpack "${RU_URL}" "vosk-model-small-ru-0.22.zip" "${MODELS_DIR}/vosk-model-small-ru-0.22"
download_and_unpack "${EN_URL}" "vosk-model-small-en-us-0.15.zip" "${MODELS_DIR}/vosk-model-small-en-us-0.15"
download_sample "${TEST_WAV_URL}" "${SAMPLES_DIR}/vosk_test.wav"

echo
echo "Vosk assets are ready:"
echo "  - ${MODELS_DIR}/vosk-model-small-ru-0.22"
echo "  - ${MODELS_DIR}/vosk-model-small-en-us-0.15"
echo "  - ${SAMPLES_DIR}/vosk_test.wav"
