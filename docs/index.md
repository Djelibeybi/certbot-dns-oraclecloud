# certbot-dns-oraclecloud

`certbot-dns-oraclecloud` is an alpha [UPL-1.0](https://spdx.org/licenses/UPL-1.0.html)
Certbot DNS-01 authenticator for public Oracle Cloud Infrastructure (OCI) DNS
zones. Its distribution name is `certbot-dns-oraclecloud`; Certbot discovers
the plugin as `dns-oraclecloud`.

The plugin finds the most-specific public/global OCI DNS zone for a challenge
name. It never uses private DNS: DNS-01 validation records must be publicly
resolvable. It creates one exact TXT value with an OCI `PatchZoneRecords` `ADD`
operation, and cleanup issues the matching `REMOVE`. Other TXT values in the
same RRset are not replaced or deleted.

This project is intentionally **not** a drop-in replacement for the legacy
`certbot-dns-oci` package. Do not reuse that package's configuration, sentinel
values, or command-line assumptions.

Start with [installation](installation.md), then select an
[authentication mode](authentication.md) and grant the required
[OCI IAM permissions](iam.md).
