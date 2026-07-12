<!-- generated-by: gsd-doc-writer -->
# Contributing to certbot-dns-oraclecloud

Thanks for helping improve this Certbot DNS-01 authenticator for Oracle Cloud
Infrastructure (OCI) DNS.

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Development setup

See [Getting started](docs/GETTING-STARTED.md) for prerequisites and first-run
instructions, and [Development](docs/development.md) for local setup and the
complete validation workflow.

The project requires Python 3.10 or newer and uses uv for dependency and
environment management. Install the locked development environment with:

```bash
uv sync --locked --all-groups --no-editable
```

The unit test suite does not require OCI credentials or access to a live
tenancy. If integration testing is necessary, use an explicitly authorised,
non-production public DNS zone and least-privilege credentials.

## Coding standards

- Run `uv run --no-sync prek run --all-files` before submitting a change. Prek
  checks repository hygiene and invokes Ruff and Pyright; CI enforces the same
  gate.
- Ruff provides formatting, linting, and import-order checks. Use
  `uv run --no-sync ruff format .` and `uv run --no-sync ruff check --fix .`
  while developing.
- Keep production and test code fully typed. Strict Pyright checks run with
  `uv run --no-sync pyright`.
- Add or update tests for behavioural changes and preserve the configured 95%
  coverage floor. See [Testing](docs/TESTING.md) for the test and coverage
  commands used by CI.

## Pull request guidelines

- Create a short, descriptive branch from `main` and keep the change focused
  on one coherent problem.
- Write commit messages using [Conventional
  Commits](https://www.conventionalcommits.org/); semantic release uses them to
  determine release versions.
- Explain the problem, solution, and relevant trade-offs in the pull request.
- Include tests and documentation when behaviour, configuration, or commands
  change, and report the validation commands you ran.
- Ensure the Python 3.10-3.14 CI matrix, static checks, tests, package build,
  plugin discovery, and documentation build pass.
- Respond to review feedback with focused follow-up commits. A maintainer may
  request additional tests, documentation, or a narrower change before merge.

Never include OCI private keys, credential files, principal tokens, DNS
challenge values, or other secrets in commits, issues, pull requests, or logs.
Redact sensitive diagnostics before sharing them.

## Reporting issues

Report bugs and feature requests through [GitHub
Issues](https://github.com/Djelibeybi/certbot-dns-oraclecloud/issues). Include:

- a clear description of the problem or proposed behaviour;
- steps to reproduce and the expected and actual results;
- the Certbot, Python, plugin, and OCI SDK versions involved; and
- relevant logs with credentials and sensitive OCI identifiers removed.

Do not report suspected vulnerabilities publicly. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contribution is licensed under the
[Universal Permissive License 1.0](LICENSE).
