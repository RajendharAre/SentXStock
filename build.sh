#!/usr/bin/env sh

set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
frontend_root="$repo_root/frontend"

task="${1:-help}"

run_in_dir() {
  dir="$1"
  shift
  (cd "$dir" && "$@")
}

show_help() {
  cat <<'EOF'
SentXStock commands:
  ./build.sh setup            Install backend + frontend dependencies
  ./build.sh backend          Run Flask backend on http://localhost:5000
  ./build.sh frontend-dev     Run Vite dev server on http://localhost:5173
  ./build.sh frontend-build   Build the React frontend
  ./build.sh frontend-lint    Run the frontend linter
  ./build.sh frontend-preview Preview the production frontend build
  ./build.sh clean            Remove generated frontend dist assets
EOF
}

case "$task" in
  help)
    show_help
    ;;
  setup)
    run_in_dir "$repo_root" python -m pip install -r requirements.txt
    run_in_dir "$frontend_root" npm install
    ;;
  backend)
    run_in_dir "$repo_root" python server.py
    ;;
  frontend-dev)
    run_in_dir "$frontend_root" npm run dev
    ;;
  frontend-build)
    run_in_dir "$frontend_root" npm run build
    ;;
  frontend-lint)
    run_in_dir "$frontend_root" npm run lint
    ;;
  frontend-preview)
    run_in_dir "$frontend_root" npm run preview
    ;;
  clean)
    rm -rf "$frontend_root/dist"
    ;;
  *)
    echo "Unknown task: $task" >&2
    exit 1
    ;;
esac