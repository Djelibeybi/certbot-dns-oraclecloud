# Task 4: Strict Python Quality Gate Report

Date: 2026-07-12

## Scope

Implemented only Task 4 from
`docs/superpowers/plans/2026-07-12-certbot-dns-oraclecloud.md`:

- replaced mypy with prek and Pyright strict;
- enabled Ruff `ALL` with only formatter-conflict global ignores;
- added the typed, redacting OCI SDK adapter boundary;
- removed all bare and broad production exception handlers;
- added Python 3.14 non-editable and wheel verification; and
- added configuration, redaction, adapter, and coverage tests.

## Current documentation and versions

Context7 was used before configuring the tools:

- prek: `/j178/prek` confirmed `prek run --all-files` and TOML hook configuration;
- Ruff: `/astral-sh/ruff` confirmed pyproject lint and per-file-ignore syntax;
- Pyright: `/microsoft/pyright` confirmed pyproject strict-mode configuration;
- uv: `/astral-sh/uv` confirmed `uv build`, `uv sync --no-editable`, and explicit
  Python environment commands;
- Hatch: `/pypa/hatch` confirmed the src-layout wheel target; and
- OCI Python SDK: `/oracle/oci-python-sdk` confirmed `ServiceError`, documented
  configuration `ClientError` subclasses, `ValueError` for invalid SDK parameters,
  and `EnvironmentError` when resource principals are unavailable.

The first OCI Context7 request hit the monthly quota. After the supplied Context7
credential was available, the library resolution and both OCI documentation lookups
completed successfully; no credentials were read or emitted.

`uv lock --upgrade` re-resolved the registry and retained the brief's current
baselines: uv 0.11.23, prek 0.4.9, Ruff 0.15.21, Pyright 1.1.411, Hatchling 1.31.0,
and OCI SDK 2.181.1. The Python 3.10 test-config parser dependency resolved to
tomli 2.4.1. The latest `pre-commit-hooks` tag was checked with
`git ls-remote` and is pinned in `prek.toml` at v6.0.0.

## TDD evidence

RED was recorded before implementation:

```text
$ uv run pytest tests/test_quality_config.py tests/test_auth.py -v
collected 12 items
7 failed, 5 passed
```

The failing contracts demonstrated missing prek/Pyright configuration, mypy still
present, no typed OCI boundary, no Python 3.14 route, broad handlers in `auth.py`
and `dns_client.py`, and API-key error output containing the credentials path and
profile.

GREEN evidence after implementation:

```text
$ uv run pytest --cov --cov-report=term-missing
30 passed
TOTAL 207 statements, 7 missed, 18 branches, 1 partial branch, 96.44% coverage
```

The test suite includes the strict-gate contract, no-broad-handler AST check,
authentication and DNS traceback sentinel-redaction tests, typed-adapter behavior,
and exact ADD/REMOVE patch assertions.

## Quality configuration

`uv run prek run --all-files` is the single all-files gate. It runs:

1. trailing-whitespace, end-of-file, TOML/YAML/JSON, merge-conflict, and private-key
   hygiene hooks from `pre-commit-hooks` v6.0.0;
2. `uv run ruff check .`;
3. `uv run ruff format --check .`; and
4. `uv run pyright`.

Each local all-repository hook uses `pass_filenames = false`.

Ruff selects `ALL`. Its only global ignores are the formatter conflicts `COM812`,
`ISC001`, `D203`, and `D213`. The narrow test-only ignores are:

- `D100`, `D103`: pytest test modules and test functions are executable examples;
- `S101`: pytest assertions;
- `S105`: intentional non-secret sentinel strings used to prove redaction;
- `PLR2004` in `test_dns_client.py`: exact protocol payload values; and
- `SLF001` in `test_quality_config.py`: inspection of Python's protocol marker.

No production annotation, exception, import-placement, security, or type rule is
disabled. Pyright remains globally strict for both `src` and `tests`, targeting
Python 3.10. OCI does not publish type stubs; the only Pyright suppressions are
precise import/unknown-symbol suppressions in `_internal/protocols.py`, where runtime
OCI values are immediately cast behind structural protocols. No application layer
uses `Any` for the SDK boundary.

## OCI exception and redaction review

The adapter translates only documented OCI configuration/signer/service/request
categories: exact OCI configuration errors, `ServiceError`, OCI request failures,
`ValueError` for invalid SDK parameter values, and `OSError` for the documented
resource-principal `EnvironmentError`. The resulting internal errors carry no cause
or message. Certbot-facing errors are constructed after the catch block and raised
with suppressed context.

`OciServiceError` retains only an integer status and an OCI-code token matching
`[A-Za-z0-9_-]+`; it never renders an SDK message, request, validation value,
credentials path, profile, private-key material, or signer token. Production code
contains no bare `except`, `except Exception`, or `except BaseException` handler.

## Python 3.14 verification

`scripts/verify-python314-wheel.sh` is the project-owned command documented in the
README. It:

1. runs `uv sync --locked --no-editable --python 3.14`;
2. runs the full test suite with coverage;
3. builds the wheel;
4. creates a separate temporary Python 3.14 virtual environment;
5. installs only the built wheel with `uv pip install --no-deps`; and
6. imports the package, verifies import metadata matches `__version__`, and prints
   that version.

It uses no `PYTHONPATH` and restores the normal locked editable environment in an
exit trap. Fresh execution used Python 3.14.5, passed all 30 tests at 96.44%, and
printed wheel metadata version `0.1.0`.

## Files changed

- `.gitignore`, `README.md`, `pyproject.toml`, `uv.lock`, and `prek.toml`;
- `scripts/verify-python314-wheel.sh`;
- `_internal/auth.py`, `_internal/dns_client.py`, and new `_internal/protocols.py`;
- test package marker plus updated/new authentication, DNS, protocol, and quality
  configuration tests.

## Final verification and concerns

Immediately before commit, all required commands passed:

```text
$ uv lock --check
Resolved 64 packages

$ uv run prek run --all-files
10 hooks passed; YAML and JSON checks were skipped because the repository has no such files

$ uv run pyright
0 errors, 0 warnings, 0 informations

$ uv run pytest --cov --cov-report=term-missing
30 passed; total coverage 96.44% (minimum 95%)

$ git diff --check
exit 0 with no output
```

No functional concern remains. The sole integration constraint is OCI's lack of
published type stubs; it is deliberately isolated to the adapter module, with strict
Pyright maintained everywhere else.
