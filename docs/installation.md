# Installation and use

The plugin supports Python 3.10 and newer and is managed with
[uv](https://docs.astral.sh/uv/). It is alpha software; test a renewal flow in
a non-production environment before relying on it for production certificates.

## Install and discover

For an indexed release, install Certbot with the plugin as an additional tool
requirement, then confirm that Certbot sees the authenticator:

```bash
uv tool install --with certbot-dns-oraclecloud certbot
certbot plugins --text | grep dns-oraclecloud
```

From a source checkout, first build the wheel and use that exact artifact:

```bash
uv build --clear
uv tool install --with ./dist/certbot_dns_oraclecloud-0.1.0-py3-none-any.whl certbot
certbot plugins --text | grep dns-oraclecloud
```

The discovery output identifies `dns-oraclecloud` as an authenticator.

## Plugin options

| Option | Default | Purpose |
| --- | --- | --- |
| `--dns-oraclecloud-auth-type` | `api_key` | Explicit OCI authentication mode: `api_key`, `instance_principal`, or `resource_principal`. |
| `--dns-oraclecloud-credentials` | `~/.oci/config` | OCI SDK config path for `api_key` mode only. |
| `--dns-oraclecloud-profile` | `DEFAULT` | OCI SDK profile for `api_key` mode only. |
| `--dns-oraclecloud-propagation-seconds` | `60` | Seconds Certbot waits for public DNS propagation. |

Use all four options when selecting an API-key profile:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type api_key \
  --dns-oraclecloud-credentials ~/.oci/config \
  --dns-oraclecloud-profile CERTBOT \
  --dns-oraclecloud-propagation-seconds 60 \
  -d example.com
```

For an instance principal, omit API-key-only options. The plugin does not read
an OCI config file in this mode:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type instance_principal \
  --dns-oraclecloud-propagation-seconds 90 \
  -d example.com
```

For a resource principal, use the OCI resource environment that supplies its
signer and select it explicitly:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type resource_principal \
  --dns-oraclecloud-propagation-seconds 60 \
  -d example.com
```

The plugin only manages public/global zones. It does not support OCI private
DNS views or zones, because a private DNS-01 record cannot satisfy public ACME
validation.
