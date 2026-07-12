# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Certbot DNS-01 authenticator plugin that fulfils ACME challenges by writing exact TXT
records into **public** Oracle Cloud Infrastructure (OCI) DNS zones. It is packaged as a
`certbot.plugins` entry point (`dns-oraclecloud`) and released to PyPI under UPL-1.0. It is
deliberately **not** a drop-in replacement for `certbot-dns-oci`; the CLI/config contract differs.

## Commands

All Python work goes through `uv` (never pip/poetry/conda). CI uses `--no-editable` installs, so
prefer `--no-sync` on run commands to match it.

```bash
uv sync --locked --all-groups --no-editable   # set up env exactly as CI does
uv run --no-sync pytest                        # run the test suite
uv run --no-sync pytest tests/test_auth.py     # single test file
uv run --no-sync pytest tests/test_auth.py::test_api_key_loads_requested_file_and_profile   # single test
uv run --no-sync pytest --cov --cov-branch     # with coverage (gate: 95%, see pyproject)
uv run --no-sync ruff check .                  # lint (rule set = ALL)
uv run --no-sync ruff format .                 # format
uv run --no-sync pyright                        # type check (strict mode)
uv run --no-sync prek run --all-files          # full local quality gate (hygiene + ruff + pyright)
uv run --no-sync certbot plugins --text | grep dns-oraclecloud   # verify plugin discovery
uv run --no-sync zensical serve                # preview docs locally
```

`prek run --all-files` is the single quality entry point mirrored by CI. `./scripts/verify-python314-wheel.sh`
does an extra non-editable wheel install check on 3.14.

## Architecture

Four `_internal` modules form a strict layered boundary between Certbot and the untyped OCI SDK.
Read them together — the design is the layering, not any single file:

- **`dns_oraclecloud.py`** — the `Authenticator` (Certbot's `DNSAuthenticator` subclass, the entry
  point). Adds `--dns-oraclecloud-{auth-type,credentials,profile}` args, lazily builds the client in
  `_setup_credentials`, and implements `_perform`/`_cleanup` as exact TXT add/remove.
- **`auth.py`** — selects one of three auth modes (`api_key`, `instance_principal`,
  `resource_principal`) and constructs the client. Each mode has its own factory; unknown modes and
  init failures become `certbot.errors.PluginError` with **no** sensitive detail.
- **`dns_client.py`** — `OciDnsClient`, a narrow wrapper doing only what Certbot needs: `find_zone`
  (via `dns_common.base_domain_name_guesses`, most-specific first), `add_txt_record`,
  `remove_txt_record`. All OCI operations run in `scope="GLOBAL"` (public zones only).
- **`protocols.py`** — the **typed boundary** over the untyped `oci` SDK. Every SDK type is wrapped
  in a `Protocol`, and SDK callables/exceptions are `cast` to typed locals so no `Any` leaks into the
  app layers. This module is the *only* place allowed to import from `oci`.

### Non-negotiable invariants (enforced by tests, not just convention)

`tests/test_quality_config.py` encodes the project's engineering rules as executable contracts, and
`test_distribution.py` guards packaging. If you change these things, that test breaks by design —
update it deliberately, don't work around it:

- **Error redaction.** OCI failures must be translated into the local `OciAuthenticationError`
  / `OciRequestError` / `OciServiceError` (safe status/code only) types. Never surface raw OCI
  exception messages, config paths, credentials, or validation values in errors. `OciServiceError`
  keeps only integer `status` and a regex-validated `code`.
- **No broad exception handlers** in `src/` — catch precise types only (test asserts this via AST).
- **No `Any`** in `auth.py` / `dns_client.py` — go through the `protocols.py` boundary.
- **Strictness is locked**: ruff `select = ALL`, pyright `strict`, and mypy is deliberately absent.
  Tests assert these config values; `pyproject.toml` configures coverage `fail_under = 95`.

## Conventions

- Prefer Australian English spelling in prose.
- Conventional Commits — Python Semantic Release drives versioning/changelog off commit messages on
  `main`. `chore/ci/refactor/style/test` are excluded from the changelog. `commit -s` (sign-off) and
  GPG signing are required for developer commits (CI release commits intentionally disable signing).
- Supports Python 3.10–3.14; keep code compatible with 3.10 (`target-version = py310`).
- Docs live in `docs/` and build with `zensical` (config in `zensical.toml`), published to GitHub Pages.
