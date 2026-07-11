# certbot-dns-oraclecloud

> **Status: alpha.** A Certbot DNS-01 authenticator for public Oracle Cloud
> Infrastructure (OCI) DNS zones, released under UPL-1.0.

Install Certbot and the plugin with uv, then confirm discovery:

```bash
uv tool install --with certbot-dns-oraclecloud certbot
certbot plugins --text | grep dns-oraclecloud
```

This project is **not** a drop-in replacement for `certbot-dns-oci`: its
configuration and command-line contract are intentionally different.

Read the [documentation](https://djelibeybi.github.io/certbot-dns-oraclecloud/)
for installation, authentication, OCI IAM, and development guidance.
