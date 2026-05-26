#!/usr/bin/env bash
set -euo pipefail

if [ -f .env.local ]; then
  set -a
  source .env.local
  set +a
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${ROOT_DIR}/estimator-cag"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"

open_url() {
  local url="$1"

  if command -v open >/dev/null 2>&1; then
    open "$url"
    return
  fi

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  fi
}

cleanup() {
  if [ "${#PIDS[@]}" -gt 0 ]; then
    kill "${PIDS[@]}" 2>/dev/null || true
  fi
}

start_docling() {
  docker compose -f "${COMPOSE_FILE}" up -d docling
}

start_api() {
  (
    cd "${PROJECT_DIR}"
    uv run uvicorn app.main:app --reload
  ) &
  PIDS+=("$!")
}

start_portal() {
  (
    cd "${PROJECT_DIR}"
    uv run streamlit run streamlit_app.py
  ) &
  PIDS+=("$!")
  open_url "http://localhost:8501"
}

usage() {
  echo "Usage: ./launch.sh [api|portal|all]"
}

profile="${1:-all}"
PIDS=()
trap cleanup EXIT

case "$profile" in
  api)
    start_docling
    start_api
    ;;
  portal)
    start_docling
    start_portal
    ;;
  all)
    start_docling
    start_api
    start_portal
    ;;
  *)
    echo "Unknown profile: $profile"
    usage
    exit 1
    ;;
esac

wait
