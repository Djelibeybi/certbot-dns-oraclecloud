# Authentication

Authentication is deliberately explicit. Set
`--dns-oraclecloud-auth-type` to exactly one of `api_key`,
`instance_principal`, or `resource_principal`. There is no auto-detection or
fallback: a failing resource principal never falls back to an instance
principal, and principal modes never fall back to an API-key config.

## API key

`api_key` is the default. Create an OCI API signing key and configure the OCI
SDK file and profile that Certbot will use, for example:

```ini
[CERTBOT]
user=ocid1.user.oc1..example
fingerprint=aa:bb:cc:dd
tenancy=ocid1.tenancy.oc1..example
region=us-ashburn-1
key_file=~/.oci/certbot_api_key.pem
```

Protect the private key and configuration file using the operating system's
normal file permissions. Choose both the file and profile explicitly when they
are not the defaults:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type api_key \
  --dns-oraclecloud-credentials ~/.oci/config \
  --dns-oraclecloud-profile CERTBOT \
  -d example.com
```

The OCI SDK loads and validates only the requested file and profile. An
API-key initialization failure stops the command; plugin errors do not include
the config mapping, private key, or other credential material.

## Instance principal

Run Certbot on an OCI compute instance that belongs to a dynamic group with
the DNS permissions in [OCI IAM](iam.md). OCI must make the instance-principal
signer available to that workload. Select `instance_principal` explicitly:

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type instance_principal \
  -d example.com
```

`--dns-oraclecloud-credentials` and `--dns-oraclecloud-profile` are not read
in this mode. If signer initialization fails, Certbot stops; it does not try an
API key or a resource principal.

## Resource principal

Run Certbot in an OCI resource environment that provides a resource-principal
signer, and grant that resource's dynamic group the DNS permissions in
[OCI IAM](iam.md):

```bash
certbot certonly --authenticator dns-oraclecloud \
  --dns-oraclecloud-auth-type resource_principal \
  -d example.com
```

The plugin requests the resource-principal signer only. If OCI cannot provide
it, the run fails immediately: it never falls back from a resource principal
to an instance principal or API-key authentication.
