# Certbot DNS Oracle Cloud Plugin Design

## Purpose

Build a new Certbot DNS authenticator for public Oracle Cloud Infrastructure
(OCI) DNS zones. The plugin completes ACME DNS-01 challenges using OCI's Python
SDK and is intentionally distinct from the unmaintained `certbot-dns-oci`
package.

The project will be distributed as `certbot-dns-oraclecloud`, imported as
`certbot_dns_oraclecloud`, and registered with Certbot as `dns-oraclecloud`.
It does not promise command-line or configuration compatibility with
`certbot-dns-oci`.

## Goals

- Support Python 3.10 and newer.
- Use `uv` for dependency management, locking, development, testing, and
  building.
- Integrate with current Certbot through `dns_common.DNSAuthenticator`.
- Support OCI API-key, instance-principal, and resource-principal
  authentication.
- Create and remove only the exact ACME TXT value owned by the challenge.
- Operate on public OCI DNS zones only.
- Keep OCI SDK usage behind a narrow internal interface so an internal HTTP
  signer could replace it later if a real dependency conflict emerges.

## Non-goals

- Compatibility with the legacy `certbot-dns-oci` package or its sentinel
  credential values.
- Private OCI DNS zones, views, or private-zone compartment discovery.
- Generic OCI DNS record administration.
- Automatic fallback between authentication modes.
- A custom OCI HTTP request signer while the supported SDK remains compatible
  with Certbot.

## Dependency Baseline

The design was validated on 12 July 2026 with the latest published versions:
Certbot 5.6.0, OCI Python SDK 2.181.1, and uv 0.11.23. Certbot and the OCI SDK
resolve and import together in an isolated uv environment on Python 3.10.

The implementation will declare Python `>=3.10`, use current dependency
versions when the package is scaffolded, and commit a `uv.lock` file. CI will
test Python 3.10, 3.11, 3.12, 3.13, and 3.14.

## Development Platform

The primary local development platform is arm64 macOS on Apple Silicon. This
is a relevant architecture for OCI deployments because OCI supports
Ampere-based Arm compute instances. GitHub Actions will nevertheless use the
default Ubuntu runners: the plugin is platform-independent Python, and the
standard Linux runners are substantially less expensive than macOS or hosted
Arm runners. The Python-version matrix therefore runs on `ubuntu-latest`.

## Public Command-line Interface

The authenticator will expose these Certbot options:

- `--dns-oraclecloud-auth-type`: one of `api_key`, `instance_principal`, or
  `resource_principal`; defaults to `api_key`.
- `--dns-oraclecloud-credentials`: OCI SDK configuration file; defaults to
  `~/.oci/config` and applies only to `api_key`.
- `--dns-oraclecloud-profile`: profile in the OCI SDK configuration file;
  defaults to `DEFAULT` and applies only to `api_key`.
- `--dns-oraclecloud-propagation-seconds`: Certbot's DNS propagation delay;
  defaults to 60 seconds.

Authentication selection is explicit. A resource-principal failure will not
fall through to an instance principal, and neither principal mode will fall
back to an API-key configuration.

## Architecture

### Certbot authenticator

`Authenticator` subclasses `certbot.plugins.dns_common.DNSAuthenticator` and
owns Certbot option registration and lifecycle hooks. During credential setup,
it asks the authentication factory for one configured OCI DNS client and
caches the plugin's internal DNS wrapper.

`_perform()` delegates one validation name and value to
`add_txt_record()`. `_cleanup()` delegates the same validation name and value
to `remove_txt_record()`. The authenticator does not construct OCI models or
interpret OCI exceptions.

### Authentication factory

The authentication factory has one explicit branch per mode:

- `api_key` loads and validates the requested OCI SDK config file and profile,
  then creates `oci.dns.DnsClient` from that config.
- `instance_principal` creates
  `InstancePrincipalsSecurityTokenSigner` and passes it to `DnsClient` with an
  empty config mapping.
- `resource_principal` obtains the current SDK resource-principal signer with
  `get_resource_principals_signer()` and passes it to `DnsClient` with an empty
  config mapping.

Invalid options and signer initialization failures are surfaced immediately.
There is no auto-detection or authentication fallback.

### OCI DNS wrapper

The DNS wrapper exposes only:

```python
add_txt_record(validation_name: str, validation: str, ttl: int) -> None
remove_txt_record(validation_name: str, validation: str) -> None
```

It accepts an SDK DNS client through its constructor. This boundary makes the
DNS behavior testable without network access and isolates the rest of the
plugin from OCI SDK types.

## DNS Operation Flow

### Public-zone discovery

For each validation FQDN, the wrapper generates candidate suffixes from most
specific to least specific and calls `get_zone` with public/global scope. A 404
means the candidate is not a zone and advances the search. Any authentication,
authorization, transport, throttling, or other service failure aborts the
operation. Failure to find a public zone produces a clear Certbot plugin error.

Using the validation name rather than only the requested certificate domain
also permits a more-specific `_acme-challenge` public zone when one exists.
CNAME-target discovery is outside this design.

### Adding a challenge

TXT content is encoded into DNS presentation-format RDATA, including quotation
marks and escaping. The wrapper calls `patch_zone_records` with exactly one
`ADD` operation containing:

- the absolute validation name;
- record type `TXT`;
- the encoded validation value; and
- TTL 60.

The plugin does not read, replace, or rewrite the surrounding RRset.

### Removing a challenge

The wrapper calls `patch_zone_records` with exactly one `REMOVE` operation
containing the same absolute name, `TXT` type, and encoded validation value.
It does not delete the RRset or remove other values. Removing a value that is
already absent is treated as a successful cleanup if OCI accepts the request.

## Error Handling and Logging

Configuration and OCI SDK failures are converted to `certbot.errors.PluginError`
at the plugin boundary. Messages identify the failed operation and record name
and, when available, include safe OCI status, service code, and message fields.

Logs and exceptions must not contain:

- private-key contents or passphrases;
- security tokens or signer internals;
- the ACME validation value; or
- full credential configuration mappings.

Zone discovery continues only after a confirmed 404. Other errors are not
relabelled as a missing zone.

## Testing Strategy

Unit tests use fake or mocked SDK clients at the internal boundaries and cover:

- parser defaults and all public command-line options;
- API-key config path and profile selection;
- explicit instance-principal and resource-principal signer creation;
- rejection of unsupported authentication modes and confirmation that
  API-key-only options are not consulted in principal modes;
- most-specific public-zone discovery and suffix fallback on 404;
- immediate failure on non-404 discovery errors;
- DNS presentation-format encoding of TXT values;
- exact single-operation `ADD` and `REMOVE` patch payloads;
- cleanup of only the matching validation value;
- conversion of SDK failures to useful Certbot errors; and
- redaction of credentials, tokens, and validation values.

Package-level verification will build a wheel, install it into an isolated uv
environment with current Certbot, and confirm that Certbot discovers the
`dns-oraclecloud` plugin. CI will run formatting, linting, static typing, unit
tests, and distribution validation for every supported Python version.

An optional live smoke-test command may be provided for maintainers. Given an
explicit public zone and selected OCI authentication mode, it will add a unique
TXT value, verify it through the OCI API, and remove that exact value in a
finally-style cleanup. Live OCI credentials are never required by the normal
test suite or CI.

## Documentation

The README will include:

- uv-based installation and development commands;
- Certbot invocation examples for each authentication mode;
- API-key config and profile setup;
- OCI IAM policy examples for reading public zones and managing DNS records;
- the 60-second propagation default and override;
- public-zone-only behavior;
- the lack of authentication fallback; and
- migration guidance explaining that this is not a drop-in replacement for
  `certbot-dns-oci`.

## Release Boundary

The first release is complete when the package builds reproducibly with uv,
the full Python-version CI matrix passes, current Certbot discovers the plugin,
all three authentication paths are covered by tests, and exact public DNS TXT
add/remove behavior is verified without live OCI credentials. Publishing to
PyPI and performing a live OCI smoke test require separate credentials and are
not part of the initial implementation unless explicitly requested.
