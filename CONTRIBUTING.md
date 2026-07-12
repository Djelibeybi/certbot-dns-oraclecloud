# Contributing to certbot-dns-oraclecloud

Thanks for helping improve this Certbot DNS-01 authenticator for Oracle Cloud
Infrastructure (OCI) DNS.

## Reporting issues

Report bugs and feature requests through [GitHub
Issues](https://github.com/Djelibeybi/certbot-dns-oraclecloud/issues). Describe
the observed and expected behaviour, steps to reproduce, and the Certbot,
Python, and package versions involved.

Do not include OCI private keys, credential files, principal tokens, secrets,
or other sensitive values in an issue, pull request, or log. Redact them before
sharing diagnostics. Report potential vulnerabilities privately as described in
[SECURITY.md](SECURITY.md), not in a public issue.

## Development workflow

Create a branch from `main`, make a focused change, and use [Conventional
Commits](https://www.conventionalcommits.org/) for commit messages. Update
documentation and tests when they describe or exercise the change.

Install the locked, CI-equivalent environment and run the repository gates:

```bash
uv sync --locked --all-groups --no-editable
uv lock --check
uv run --no-sync prek run --all-files
uv run --no-sync pyright
uv run --no-sync pytest --cov --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy
uv run --no-sync zensical build --clean --strict
uv run --no-sync certbot plugins --text | grep dns-oraclecloud
uv build --clear
uv run --no-sync twine check dist/*
./scripts/verify-python314-wheel.sh
```

The test suite does not require a live OCI tenancy. If a change needs actual
OCI DNS testing, use an explicitly authorised, non-production zone with
least-privilege credentials; never exercise a user's production zone without
their permission.

## Pull requests

Keep pull requests small and explain the problem, solution, and verification
performed. A maintainer may ask for a test, documentation update, or a more
focused change before merging.

## License

By contributing, you agree that your contribution is licensed under the
[Universal Permissive License 1.0](LICENSE).
