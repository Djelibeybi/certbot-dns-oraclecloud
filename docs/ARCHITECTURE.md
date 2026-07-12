<!-- generated-by: gsd-doc-writer -->
# Architecture

## System overview

`certbot-dns-oraclecloud` is a layered Certbot authenticator that receives ACME
DNS-01 challenge names and validation values from Certbot, creates and later
removes exact TXT records in public OCI DNS zones, and reports failures through
Certbot's plugin error types. The Certbot-facing layer owns lifecycle integration,
an authentication layer makes one explicit OCI authentication choice, a DNS layer
implements zone discovery and record mutation, and a typed boundary isolates the
rest of the package from the OCI Python SDK's untyped surface.

## Component diagram

```text
Certbot / ACME DNS-01 lifecycle
              |
              v
  dns_oraclecloud.Authenticator
              |
              +--------------------+
              |                    |
              v                    v
       auth.create_dns_client   dns_client.OciDnsClient
              |                    |
              +---------+----------+
                        |
                        v
             protocols typed boundary
                        |
                        v
                 OCI Python SDK
                        |
                        v
              OCI public DNS service
```

The package entry point registered in `pyproject.toml` loads
`certbot_dns_oraclecloud._internal.dns_oraclecloud:Authenticator` as Certbot's
`dns-oraclecloud` plugin.

## Data flow

1. Certbot discovers `Authenticator` through the `certbot.plugins` entry-point
   group and parses the plugin's authentication, credentials, profile, and DNS
   propagation options.
2. During credential setup, `Authenticator._setup_credentials()` passes the
   explicitly selected authentication mode to `auth.create_dns_client()`.
   API-key authentication loads one named OCI SDK profile; instance- and
   resource-principal modes create only their corresponding signer. Authentication
   modes do not fall back to one another.
3. The selected OCI SDK client is wrapped in `OciDnsClient`. For challenge setup,
   `Authenticator._perform()` delegates the exact validation name, value, and
   60-second record TTL to `OciDnsClient.add_txt_record()`.
4. `OciDnsClient.find_zone()` asks Certbot for progressively less-specific base
   domain candidates and queries each candidate in OCI's `GLOBAL` scope. It moves
   to the next candidate only after a 404 response; other service or transport
   failures stop the operation.
5. The protocol boundary constructs one OCI `RecordOperation`: `ADD` for setup or
   `REMOVE` for cleanup. TXT data is JSON-quoted, and `patch_zone_records()` sends
   the single operation to the discovered public zone in `GLOBAL` scope.
6. Certbot waits for the configured propagation interval before ACME validation.
   Cleanup follows the same path from `Authenticator._cleanup()`, but removes only
   the matching TXT value.
7. OCI SDK exceptions are translated at the protocol boundary. Error messages
   returned to Certbot retain only validated status and error-code metadata and
   do not include validation values, credential paths, profiles, private keys, or
   raw SDK exception messages.

## Key abstractions

| Abstraction | Location | Responsibility |
| --- | --- | --- |
| `Authenticator` | `src/certbot_dns_oraclecloud/_internal/dns_oraclecloud.py` | Implements Certbot's `DNSAuthenticator` lifecycle, plugin arguments, client setup, challenge creation, and cleanup. |
| `create_dns_client()` | `src/certbot_dns_oraclecloud/_internal/auth.py` | Selects exactly one of API-key, instance-principal, or resource-principal authentication and converts initialization failures to safe Certbot errors. |
| `OciDnsClient` | `src/certbot_dns_oraclecloud/_internal/dns_client.py` | Finds the most-specific public zone and applies exact TXT `ADD` and `REMOVE` operations. |
| `DnsClientProtocol` | `src/certbot_dns_oraclecloud/_internal/protocols.py` | Defines the narrow OCI DNS client surface used by the plugin: public zone lookup and record patching. |
| `RecordOperationProtocol` | `src/certbot_dns_oraclecloud/_internal/protocols.py` | Describes the TXT record operation fields needed by the DNS layer and its tests. |
| `OciResponseProtocol` and `ZoneProtocol` | `src/certbot_dns_oraclecloud/_internal/protocols.py` | Model the small structural portions of OCI responses and zones that the plugin consumes. |
| `OciAuthenticationError` | `src/certbot_dns_oraclecloud/_internal/protocols.py` | Redacted internal failure used when SDK configuration or signer initialization fails. |
| `OciRequestError` and `OciServiceError` | `src/certbot_dns_oraclecloud/_internal/protocols.py` | Separate transport or construction failures from service failures while retaining only safe service metadata. |
| `add_record_operation()` and `remove_record_operation()` | `src/certbot_dns_oraclecloud/_internal/protocols.py` | Construct exact, quoted OCI TXT record operations without exposing failed model inputs. |

The protocol types are structural rather than wrappers around the full SDK model
hierarchy. This keeps SDK-specific casts, factories, and exception classes in one
module while allowing strict type checking throughout the rest of the package.

## Directory structure rationale

```text
certbot-dns-oraclecloud/
|-- src/certbot_dns_oraclecloud/   Installable, typed Python package
|   `-- _internal/                 Certbot, authentication, DNS, and SDK boundary layers
|-- tests/                         Unit, distribution, and quality-configuration tests
|-- docs/                          User, operator, and contributor documentation
|-- scripts/                       Standalone compatibility verification helpers
|-- .github/workflows/             CI, release, coverage, and documentation automation
|-- pyproject.toml                 Package metadata, entry point, dependencies, and tool settings
`-- zensical.toml                  Documentation-site configuration
```

The `src` layout prevents the repository root from accidentally satisfying
package imports during development. The public package surface is deliberately
small: `src/certbot_dns_oraclecloud/__init__.py` exposes distribution version metadata,
while operational code remains under `_internal` and Certbot reaches it through
the registered plugin entry point. Tests mirror the internal module boundaries,
with additional checks for the built distribution and repository quality policy.
