# Development

The primary development platform is arm64 macOS on Apple Silicon. That matches
the architecture used by OCI Ampere Arm compute, while the project CI uses the
cheaper standard GitHub-hosted `ubuntu-latest` runners. CI covers Python 3.10,
3.11, 3.12, 3.13, and 3.14.

Install the locked development and documentation environment, then run the
same local quality and release checks as CI:

```bash
uv sync --locked --all-groups --no-editable
uv lock --check
uv run --no-sync prek run --all-files
uv run --no-sync pyright
uv run --no-sync pytest --cov --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy
uv run --no-sync zensical build --clean --strict
uv run --no-sync certbot plugins --text
uv build --clear
uv run --no-sync twine check dist/*
```

The Certbot output must list `dns-oraclecloud`, and Twine must accept both the
wheel and source distribution. Verify the built wheel in a clean isolated
environment as well:

```bash
uv run --isolated --no-project \
  --with certbot \
  --with ./dist/certbot_dns_oraclecloud-0.1.0-py3-none-any.whl \
  certbot plugins --text
```

Python 3.14 gets an additional non-editable check so test imports cannot rely
on an editable `.pth` file:

```bash
./scripts/verify-python314-wheel.sh
```

To preview the documentation while editing, run `uv run --no-sync zensical serve`.

## Releases and PyPI publishing

On a push to `main`, CI runs the complete Python test matrix before Python
Semantic Release evaluates conventional commits. When a release is due, it
updates the project version and `uv.lock`, builds the distributions, creates
the GitHub release and its assets, and then publishes the downloaded build
artifacts to PyPI. The generated history is available in the
[changelog](changelog.md).

Repository administrators must configure these external integrations:

- Add a `DEPLOY_KEY` repository secret containing a write-capable SSH deploy
  key. CI uses it only to push the Semantic Release commit and tag; the bot
  deliberately disables local GPG signing because hosted CI has no developer
  signing key.
- Create a PyPI trusted publisher for project `certbot-dns-oraclecloud` with
  owner `Djelibeybi`, repository `certbot-dns-oraclecloud`, workflow
  `.github/workflows/ci.yml`, and environment `pypi`. Protect that GitHub
  environment as appropriate. No PyPI API token is stored in the repository.
- Add a `CODECOV_TOKEN` repository secret for the CI coverage and JUnit report
  uploads. This supports quality reporting and is not a release credential.

For a local release decision check that changes no files, run:

```bash
uv run --no-sync semantic-release --noop version
```
