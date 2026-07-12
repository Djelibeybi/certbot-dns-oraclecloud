<!-- generated-by: gsd-doc-writer -->
# Testing

The test suite verifies Certbot integration, OCI authentication selection, public
DNS record operations, error redaction, distribution metadata, and the repository's
quality and release configuration. Tests do not contact OCI: SDK clients, signers,
and service failures are replaced with mocks or test doubles.

## Test framework and setup

The project uses [pytest](https://docs.pytest.org/) 9.1.1 with
[pytest-cov](https://pytest-cov.readthedocs.io/) 7.1.0. Dependencies are managed by
uv and locked in `uv.lock`. From the repository root, install every dependency group:

```bash
uv sync --locked --all-groups
```

Pytest configuration lives in `pyproject.toml`:

- Tests are collected from `tests/`.
- `--strict-config` rejects unknown configuration options.
- `--strict-markers` rejects unregistered pytest markers.
- Coverage measures `certbot_dns_oraclecloud`, including branch coverage.
- Total coverage below 95% fails the test run.

No external service, OCI credential file, or environment variable is required for
the test suite.

## Running tests

Run the full suite:

```bash
uv run pytest
```

Run the full suite with the terminal coverage report used during local verification:

```bash
uv run pytest --cov --cov-report=term-missing
```

Run one test module:

```bash
uv run pytest tests/test_auth.py
```

Run one test by its node ID:

```bash
uv run pytest tests/test_auth.py::test_resource_principal_does_not_fall_back
```

Select tests by a case-insensitive keyword expression:

```bash
uv run pytest -k "resource_principal or instance_principal"
```

The project does not configure a watch-mode command. To reproduce CI's coverage and
test-result artifacts locally, run:

```bash
uv run pytest --cov --cov-branch --cov-report=xml \
  --junitxml=junit.xml -o junit_family=legacy
```

This writes `coverage.xml` and `junit.xml` in the repository root.

## Writing new tests

Place tests in `tests/` using the existing `test_<area>.py` module convention and
name test functions `test_<behaviour>()`. Add a new module when testing a new
component; add focused cases to the matching module when extending existing
behaviour.

There is no shared `conftest.py` or helper module. Existing tests use:

- `unittest.mock.patch` and `MagicMock` to isolate OCI SDK calls and Certbot
  lifecycle dependencies;
- `pytest.raises` to assert typed failures and confirm sensitive values are absent;
- `pytest.mark.parametrize` for the same contract across multiple operations;
- pytest's `tmp_path` fixture for temporary credential-file scenarios; and
- small test-local exception classes and factory functions for redacted OCI failure
  paths.

Keep unit tests offline and deterministic. For authentication, assert that only the
selected signer or profile path is consulted. For DNS mutations, inspect the exact
OCI record operation rather than making a live request. When exercising an error
path, assert that credentials, ACME validation values, raw SDK messages, and signer
data do not appear in either the exception message or its formatted traceback.

`tests/test_distribution.py` depends on installed distribution metadata and the
registered `certbot.plugins` entry point. Run tests through the uv project environment
instead of adding `src/` to `PYTHONPATH`.

## Coverage requirements

Coverage settings are defined in `pyproject.toml` under `[tool.coverage.run]` and
`[tool.coverage.report]`.

| Type | Threshold |
| --- | --- |
| Total project coverage | 95% |
| Branch coverage | Measured; no separate branch-only threshold |
| Line, function, and statement coverage | No separate thresholds |

The 95% floor applies to the aggregate report for the
`certbot_dns_oraclecloud` package. Missing lines are shown in terminal reports.

## CI integration

The `CI` workflow in `.github/workflows/ci.yml` runs the `test` job for pull
requests and branch pushes; tag pushes are ignored. The matrix covers Python 3.10,
3.11, 3.12, 3.13, and 3.14 on GitHub's default Ubuntu runner. Each matrix job:

1. installs the locked dependency set without editable project imports;
2. runs the Prek quality gate and strict Pyright checking;
3. executes:

   ```bash
   uv run --no-sync pytest --cov --cov-branch --cov-report=xml \
     --junitxml=junit.xml -o junit_family=legacy
   ```

4. uploads its JUnit result to Codecov unless the job was cancelled; and
5. verifies Certbot discovery, builds the distributions, and validates them with
   Twine.

Only the Python 3.14 matrix job uploads `coverage.xml` to Codecov, avoiding duplicate
aggregate coverage uploads. That job also runs
`scripts/verify-python314-wheel.sh`, which creates isolated temporary environments,
reruns the suite without editable imports, builds a wheel, installs that wheel without
its dependencies, verifies that the package imports, and confirms that its distribution
metadata version equals `certbot_dns_oraclecloud.__version__`. The same job verifies
that Certbot discovers the plugin.
