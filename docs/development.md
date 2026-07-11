# Development

The primary development platform is arm64 macOS on Apple Silicon. That matches
the architecture used by OCI Ampere Arm compute, while the project CI uses the
cheaper standard GitHub-hosted `ubuntu-latest` runners. CI covers Python 3.10,
3.11, 3.12, 3.13, and 3.14.

Install the locked development and documentation environment, then run the
same local quality and release checks as CI:

```bash
uv sync --locked --all-groups
uv lock --check
uv run prek run --all-files
uv run pyright
uv run pytest --cov --cov-report=term-missing
uv run zensical build --clean --strict
uv run certbot plugins --text
uv build --clear
uv run twine check dist/*
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

To preview the documentation while editing, run `uv run zensical serve`.
