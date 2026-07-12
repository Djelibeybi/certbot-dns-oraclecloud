#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/certbot-dns-oraclecloud-python314.XXXXXX")"
project_venv="$temporary_root/project-venv"
wheel_venv="$temporary_root/wheel-venv"

cleanup() {
  local exit_status=$?
  rm -rf -- "$temporary_root" || printf 'Could not remove temporary verification root\n' >&2
  trap - EXIT
  exit "$exit_status"
}
trap cleanup EXIT

cd "$project_root"
UV_PROJECT_ENVIRONMENT="$project_venv" uv sync --locked --no-editable --python 3.14
UV_PROJECT_ENVIRONMENT="$project_venv" uv run --no-sync --python 3.14 pytest --cov --cov-report=term-missing
uv build --wheel

wheel="$(find dist -maxdepth 1 -name 'certbot_dns_oraclecloud-*.whl' -print -quit)"
test -n "$wheel"
uv venv --clear --python 3.14 "$wheel_venv"
uv pip install --python "$wheel_venv/bin/python" --no-deps "$wheel"
"$wheel_venv/bin/python" -c 'from importlib.metadata import version; import certbot_dns_oraclecloud; assert version("certbot-dns-oraclecloud") == certbot_dns_oraclecloud.__version__; print(version("certbot-dns-oraclecloud"))'
