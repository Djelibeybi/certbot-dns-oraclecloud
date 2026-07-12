<!-- generated-by: gsd-doc-writer -->
# certbot-dns-oraclecloud

A Certbot authenticator for completing DNS-01 challenges in public Oracle Cloud Infrastructure (OCI) DNS zones.

[![CI](https://github.com/Djelibeybi/certbot-dns-oraclecloud/actions/workflows/ci.yml/badge.svg)](https://github.com/Djelibeybi/certbot-dns-oraclecloud/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: UPL-1.0](https://img.shields.io/badge/license-UPL--1.0-blue.svg)](LICENSE)

> [!WARNING]
> This project is alpha software. Test issuance and renewal in a non-production environment before relying on it for production certificates.

The plugin supports API-key, instance-principal, and resource-principal authentication. It discovers the most-specific matching public OCI DNS zone, adds the exact TXT value required by Certbot, and removes only that value during cleanup. Private DNS zones are intentionally unsupported because they cannot satisfy public ACME validation.

This project is not a drop-in replacement for `certbot-dns-oci`; its configuration and command-line contract are intentionally different.

## Installation

Python 3.10 or newer is required. Install Certbot and the plugin together with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install --with certbot-dns-oraclecloud certbot
```

Confirm that Certbot can discover the authenticator:

```bash
certbot plugins --text | grep dns-oraclecloud
```

## Quick start

1. Configure an OCI API-key profile with permission to read public DNS zones and manage their records.
2. Install Certbot with the plugin and verify discovery:

   ```bash
   uv tool install --with certbot-dns-oraclecloud certbot
   certbot plugins --text | grep dns-oraclecloud
   ```

3. Request a certificate using that profile:

   ```bash
   certbot certonly --authenticator dns-oraclecloud \
     --dns-oraclecloud-auth-type api_key \
     --dns-oraclecloud-credentials ~/.oci/config \
     --dns-oraclecloud-profile CERTBOT \
     --dns-oraclecloud-propagation-seconds 60 \
     -d example.com
   ```

## Usage

### API-key authentication

`api_key` is the default authentication mode. The credentials file defaults to `~/.oci/config`, and the profile defaults to `DEFAULT`:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type api_key \
  --dns-oraclecloud-credentials ~/.oci/config \
  --dns-oraclecloud-profile CERTBOT \
  -d example.com
```

### Instance-principal authentication

Run Certbot on an OCI compute instance whose dynamic group has the required DNS permissions. The authenticator reads the configured credentials and profile values before selecting this mode, but the instance-principal client factory does not use them:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type instance_principal \
  -d example.com
```

### Resource-principal authentication

Run Certbot in an OCI resource environment that supplies a resource-principal signer:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type resource_principal \
  -d example.com
```

Authentication selection is explicit. A failed principal mode does not fall back to another principal or to an API key.

## Plugin options

| Option | Default | Purpose |
| --- | --- | --- |
| `--dns-oraclecloud-auth-type` | `api_key` | Select `api_key`, `instance_principal`, or `resource_principal`. |
| `--dns-oraclecloud-credentials` | `~/.oci/config` | OCI SDK configuration file used by API-key authentication. |
| `--dns-oraclecloud-profile` | `DEFAULT` | Profile in the OCI SDK configuration file used by API-key authentication. |
| `--dns-oraclecloud-propagation-seconds` | `60` | Time Certbot waits for public DNS propagation. |

## Documentation

The [project documentation](https://djelibeybi.github.io/certbot-dns-oraclecloud/) covers installation, authentication, least-privilege OCI IAM policies, development, and releases.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Security issues should be reported privately as described in [SECURITY.md](SECURITY.md).

## License

This project is licensed under the [Universal Permissive License 1.0](LICENSE).
