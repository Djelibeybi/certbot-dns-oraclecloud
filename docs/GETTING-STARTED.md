<!-- generated-by: gsd-doc-writer -->
# Getting started

This guide sets up a source checkout for development and verifies that Certbot
can discover the `dns-oraclecloud` authenticator.

## Prerequisites

- Python `>=3.10`; the project tests Python 3.10 through 3.14.
- [uv](https://docs.astral.sh/uv/) for Python and dependency management.
- Git for cloning the repository.
- To request a certificate, access to a public OCI DNS zone and an OCI identity
  with permission to read zones and manage DNS records. Private DNS zones are
  intentionally unsupported because public ACME servers cannot verify them.

No additional system packages are required by the repository.

## Installation steps

1. Clone the repository:

   ```bash
   git clone https://github.com/Djelibeybi/certbot-dns-oraclecloud.git
   ```

2. Enter the checkout:

   ```bash
   cd certbot-dns-oraclecloud
   ```

3. Install the locked development and documentation dependencies. The
   non-editable install matches CI and prevents tests from succeeding through
   an editable-import path:

   ```bash
   uv sync --locked --all-groups --no-editable
   ```

4. Before contributing, complete the Git hook step in
   [Development](development.md#local-setup).

## First run

Run the test suite from the repository root:

```bash
uv run --no-sync pytest
```

Then confirm that Certbot discovers the installed plugin:

```bash
uv run --no-sync certbot plugins --text | grep dns-oraclecloud
```

The discovery output should list `dns-oraclecloud` as an authenticator.

To issue a certificate, first configure one of the supported OCI
authentication modes, then invoke Certbot. For example, using an API-key
profile named `CERTBOT`:

```bash
uv run --no-sync certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type api_key \
  --dns-oraclecloud-credentials ~/.oci/config \
  --dns-oraclecloud-profile CERTBOT \
  --dns-oraclecloud-propagation-seconds 60 \
  -d example.com
```

See [Authentication](authentication.md) and [OCI IAM](iam.md) before using
instance-principal or resource-principal authentication, or before granting
production DNS permissions.

## Common setup issues

### uv rejects the Python version

The package requires Python 3.10 or newer. Ask uv to install and use a supported
interpreter, then repeat the sync:

```bash
uv python install 3.14
uv sync --python 3.14 --locked --all-groups --no-editable
```

### The lockfile check or sync reports stale dependencies

Use the committed `uv.lock` rather than resolving a different environment. If
you did not intentionally change dependencies, restore the lockfile and run
`uv sync --locked --all-groups --no-editable` again. When changing dependencies
intentionally, update `pyproject.toml` and regenerate `uv.lock` together.

### Certbot cannot find `dns-oraclecloud`

Run Certbot through the synced uv environment:

```bash
uv run --no-sync certbot plugins --text
```

A system-wide `certbot` command may belong to a different Python environment
where the plugin is not installed.

### OCI authentication initialization fails

Authentication selection is explicit and failures do not fall back to another
mode. For API-key authentication, verify the credentials path, profile name,
private-key access, and OCI configuration fields. For principal authentication,
verify that the OCI workload supplies the selected principal and that its
dynamic group and IAM policies permit the required public DNS operations.

## Next steps

- Read [Development](development.md) for the complete local quality, build,
  documentation, and release checks.
- Read [Testing](TESTING.md) for test organization, coverage requirements, and
  CI behavior.
- Read [Configuration](CONFIGURATION.md) for every Certbot plugin option and
  its default.
- Read [Architecture](ARCHITECTURE.md) for the authentication, DNS adapter, and
  Certbot integration boundaries.
