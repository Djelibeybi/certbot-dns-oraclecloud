#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
wheel_venv="$(mktemp -d "${TMPDIR:-/tmp}/certbot-dns-oraclecloud-python314.XXXXXX")"

cleanup() {
  rm -rf -- "$wheel_venv"
  uv sync --locked
}
trap cleanup EXIT

cd "$project_root"
uv sync --locked --no-editable --python 3.14
uv run --no-sync --python 3.14 pytest --cov --cov-report=term-missing
uv build --wheel

wheel="$(find dist -maxdepth 1 -name 'certbot_dns_oraclecloud-*.whl' -print -quit)"
test -n "$wheel"
uv venv --clear --python 3.14 "$wheel_venv"
uv pip install --python "$wheel_venv/bin/python" --no-deps "$wheel"
"$wheel_venv/bin/python" -c 'from importlib.metadata import version; import certbot_dns_oraclecloud; assert version("certbot-dns-oraclecloud") == certbot_dns_oraclecloud.__version__; print(version("certbot-dns-oraclecloud"))'
