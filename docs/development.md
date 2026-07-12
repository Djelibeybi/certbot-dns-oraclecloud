<!-- generated-by: gsd-doc-writer -->
# Development

This guide describes the repository workflow for developing and validating
`certbot-dns-oraclecloud`. For end-user installation and plugin configuration,
see [Getting started](GETTING-STARTED.md) and
[Configuration](CONFIGURATION.md).

## Local setup

The project requires Python 3.10 or newer and uses
[uv](https://docs.astral.sh/uv/) for dependency and environment management.
The primary development platform is arm64 macOS on Apple Silicon. CI uses
standard GitHub-hosted `ubuntu-latest` runners and covers Python 3.10 through
3.14.

1. Fork `Djelibeybi/certbot-dns-oraclecloud` on GitHub.
2. Clone your fork and enter the repository:

   ```bash
   git clone git@github.com:YOUR-USERNAME/certbot-dns-oraclecloud.git
   cd certbot-dns-oraclecloud
   ```

3. Add the upstream repository:

   ```bash
   git remote add upstream git@github.com:Djelibeybi/certbot-dns-oraclecloud.git
   ```

4. Install the exact locked development and documentation dependencies. The
   non-editable install matches CI and prevents imports from succeeding only
   because the source tree is present:

   ```bash
   uv sync --locked --all-groups --no-editable
   ```

No OCI credentials or live tenancy are needed for the unit test suite. If a
change requires integration testing against OCI DNS, use an explicitly
authorised non-production public zone and least-privilege credentials. Never
place OCI private keys, principal tokens, credential files, or validation
values in source control, test fixtures, issues, or logs.

## Build commands

The repository does not use a task runner; invoke its uv-managed tools
directly. Commands containing `--no-sync` assume the local setup step has
already installed the locked environment.

| Command | Description |
| --- | --- |
| `uv sync --locked --all-groups --no-editable` | Install the locked runtime, development, and documentation dependencies without an editable project import. |
| `uv lock --check` | Confirm that `uv.lock` agrees with `pyproject.toml`. |
| `uv run --no-sync prek run --all-files` | Run repository hygiene, Ruff linting and formatting checks, and strict Pyright checks over all files. |
| `uv run --no-sync pyright` | Run strict static type checking over `src/` and `tests/`. |
| `uv run --no-sync pytest --cov --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy` | Run the full test suite with branch coverage plus Codecov-compatible XML and JUnit reports. |
| `uv run --no-sync zensical build --clean --strict` | Build the documentation site and fail on documentation errors. |
| `uv run --no-sync zensical serve` | Serve a local documentation preview while editing. |
| `uv run --no-sync certbot plugins --text \| grep dns-oraclecloud` | Verify that Certbot discovers the installed `dns-oraclecloud` entry point. |
| `uv build --clear` | Build a fresh wheel and source distribution in `dist/`. |
| `uv run --no-sync twine check dist/*` | Validate the metadata and rendered descriptions of built distributions. |
| `./scripts/verify-python314-wheel.sh` | Test under Python 3.14, build a wheel, install it into a clean environment, and verify its package version. |
| `uv run --no-sync semantic-release --noop version` | Preview the next semantic-release decision without changing files. |

To reproduce the complete local quality gate, run the check, test,
documentation, discovery, and distribution commands above before opening a
pull request. The coverage configuration in `pyproject.toml` requires at least
95% total coverage and records branch coverage.

## Code style

[Ruff](https://docs.astral.sh/ruff/) provides linting and formatting. Its
configuration is in `pyproject.toml`, targets Python 3.10, uses a 100-character
line length, and enables all lint rule families except the explicitly listed
formatter conflicts. This includes import ordering and guards against imports
placed outside the top level. Format code locally with:

```bash
uv run --no-sync ruff format .
uv run --no-sync ruff check --fix .
```

[Pyright](https://microsoft.github.io/pyright/) runs in strict mode across both
production and test code. Public and internal interfaces should therefore have
precise annotations; the OCI SDK boundary is isolated behind protocols in
`src/certbot_dns_oraclecloud/_internal/protocols.py`.

The `prek.toml` configuration is the canonical all-files quality entry point.
In addition to Ruff and Pyright, it checks whitespace, final newlines, TOML,
YAML, JSON, merge-conflict markers, and accidentally committed private keys.
Repository contract tests also reject bare handlers and handlers for broad
`Exception` or `BaseException` types in production modules.

## Branch conventions

Create branches from `main`; it is the default and release branch. Keep each
branch focused on one coherent change. No branch-name pattern is currently
documented, so use a short descriptive name that makes the branch's purpose
clear.

Commit messages must follow [Conventional
Commits](https://www.conventionalcommits.org/). The semantic-release workflow
uses those messages to determine whether a push to `main` produces a release
and how the version changes.

## Pull request process

The repository has no pull-request template, so include the necessary context
in the pull-request description:

- Explain the problem, the chosen solution, and any relevant trade-offs.
- Keep the change focused; separate unrelated work into another pull request.
- Add or update tests for changed behaviour, and preserve the configured 95%
  coverage floor.
- Update user or developer documentation when commands, configuration, or
  behaviour change.
- Report the exact validation commands you ran and their outcomes.
- Remove or redact credentials, private keys, principal tokens, challenge
  values, and sensitive OCI identifiers before sharing logs.
- Respond to review feedback with focused follow-up commits; maintainers may
  request additional tests, documentation, or a narrower change before merge.

CI validates the complete Python 3.10-3.14 matrix, static quality gates,
coverage and test-result generation, Certbot plugin discovery, distribution
builds, and the Python 3.14 wheel path. Documentation is also built strictly on
pull requests without deploying the preview.

## Releases

After the test matrix succeeds on a push to `main`, Python Semantic Release
evaluates the conventional commits. When a release is due, the workflow updates
the version in `pyproject.toml`, refreshes `uv.lock`, builds the distributions,
creates a GitHub release, and passes the same artifacts to PyPI trusted
publishing. Release history is written to the [changelog](changelog.md).

Repository administrators must provide the external credentials and trust
relationships used by that workflow:

- `DEPLOY_KEY`, containing a write-capable SSH deploy key for the semantic
  release commit and tag;
- `CODECOV_TOKEN`, used for coverage and JUnit report uploads; and
- a PyPI trusted publisher for this repository's `.github/workflows/ci.yml`
  workflow and `pypi` environment.

Hosted CI disables commit and tag GPG signing for its automated release because
the runner does not receive a developer signing key. PyPI publication uses
OpenID Connect trusted publishing rather than a stored PyPI API token.
