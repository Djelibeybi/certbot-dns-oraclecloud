<!-- generated-by: gsd-doc-writer -->
# Configuration

`certbot-dns-oraclecloud` is configured through Certbot plugin options. API-key
authentication additionally reads one profile from an OCI SDK configuration
file. Authentication selection is explicit: the plugin does not auto-detect a
mode or fall back to another mode when authentication fails.

## Environment variables

The plugin does not read any environment variables directly. In particular,
API-key authentication uses the file and profile selected by the Certbot
options below.

Instance-principal and resource-principal signers are constructed by the OCI
Python SDK. Any workload metadata or environment supplied to those signers is
owned by the OCI runtime and SDK, not parsed by this plugin. Consult the OCI SDK
documentation for the signer requirements of the environment where Certbot
runs.

The repository's release workflow defines these job-scoped variables; they are
not end-user plugin settings:

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `PACKAGE_NAME` | Release job only | `certbot-dns-oraclecloud` | Used by the semantic-release build command when updating the uv lockfile. |
| `GITHUB_TOKEN` | Release job only | Supplied by GitHub Actions | Authorizes Python Semantic Release to create the GitHub release. |
| `GH_TOKEN` | Release job only | Supplied by GitHub Actions | Makes the same workflow token available to GitHub CLI-compatible release tooling. |

## Config file format

API-key mode uses the OCI SDK's INI-style configuration file. The plugin passes
the selected file and profile to `oci.config.from_file`, validates the returned
mapping with `oci.config.validate_config`, and constructs the DNS client only
after validation succeeds.

A minimal profile has this shape:

```ini
[CERTBOT]
user=ocid1.user.oc1..example
fingerprint=aa:bb:cc:dd
tenancy=ocid1.tenancy.oc1..example
region=your-oci-region
key_file=/secure/path/certbot_api_key.pem
```

Select it explicitly:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type api_key \
  --dns-oraclecloud-credentials ~/.oci/config \
  --dns-oraclecloud-profile CERTBOT \
  -d example.com
```

The plugin expands `~` in the credentials path before passing it to the OCI
SDK. Protect both the configuration file and private key with appropriate
filesystem permissions.

## Required vs optional settings

| Setting | Required | Accepted values | Behaviour |
| --- | --- | --- | --- |
| `--dns-oraclecloud-auth-type` | Optional | `api_key`, `instance_principal`, `resource_principal` | Defaults to `api_key`. The selected mode must initialize successfully; there is no fallback. |
| `--dns-oraclecloud-credentials` | API-key mode only | Path to an OCI SDK config file | Defaults to `~/.oci/config`. Ignored by principal modes. |
| `--dns-oraclecloud-profile` | API-key mode only | Profile section name | Defaults to `DEFAULT`. Ignored by principal modes. |
| `--dns-oraclecloud-propagation-seconds` | Optional | Number of seconds | Defaults to `60`; controls how long Certbot waits before ACME validation. |

For API-key mode, the chosen OCI configuration must exist, the chosen profile
must exist, and the OCI SDK must accept its contents and private key. The plugin
intentionally reports these failures as `Unable to initialize OCI API-key
authentication.` without echoing credential details.

Instance-principal mode requires the OCI SDK to initialize an instance-principal
signer. Resource-principal mode likewise requires a resource-principal signer.
Signer initialization failures stop Certbot with a redacted plugin error.

## Defaults

| Setting | Default | Defined in |
| --- | --- | --- |
| Authentication mode | `api_key` | `Authenticator.add_parser_arguments` |
| OCI configuration path | `~/.oci/config` | `Authenticator.add_parser_arguments` |
| OCI profile | `DEFAULT` | `Authenticator.add_parser_arguments` |
| DNS propagation wait | `60` seconds | `Authenticator.add_parser_arguments` |
| TXT record TTL | `60` seconds | `Authenticator.ttl` |
| OCI DNS scope | `GLOBAL` | DNS client adapter calls |

The TXT TTL is fixed by the plugin. The propagation wait is independently
configurable and does not change the record TTL.

## Per-environment overrides

The project has no `.env` layering and no development, staging, or production
configuration files. Supply the appropriate plugin options to each Certbot
invocation.

For multiple API-key environments, keep separate OCI profiles and select the
desired profile with `--dns-oraclecloud-profile`; use
`--dns-oraclecloud-credentials` as well when the profiles are stored in
different files. For OCI workloads, select `instance_principal` or
`resource_principal` explicitly and configure that workload's identity and DNS
permissions as described in [Authentication](authentication.md) and
[OCI IAM](iam.md).

Only public/global OCI DNS zones are supported. Private DNS views and zones are
not a configurable target because they cannot satisfy public ACME DNS-01
validation.
