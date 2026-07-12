# Security Policy

## Supported versions

This project is currently alpha (`0.1.0`). Until a stable release is available,
security fixes are considered for the latest release and the `main` branch.
Older tags and branches are not supported.

## Reporting a vulnerability

Do not open a public GitHub issue for a suspected vulnerability. Use GitHub
private vulnerability reporting when it is enabled for this repository;
otherwise email [me@dje.li](mailto:me@dje.li). Include a clear description,
affected versions, reproduction steps, and impact, while keeping credentials
and other secrets out of the report.

Reports are acknowledged on a best-effort basis. Investigation and remediation
timing depend on reproducibility, impact, and maintainer availability; no
specific response-time commitment is implied.

## Security considerations

- Treat OCI API keys, instance or resource principal tokens, and credential
  files as secrets. Keep them out of source control and diagnostics.
- Ensure errors and logs do not disclose secret values or private key material.
- Use least-privilege OCI IAM policies for DNS zones and compartments used by
  this plugin.
- DNS-01 validation mutates public DNS records. Limit the plugin's OCI
  credentials to the intended zones and protect the hosts and files that hold
  those credentials.

## Scope

This policy covers this plugin and vulnerabilities caused by its Certbot or OCI
integration. Report defects in OCI services, the OCI SDK, Certbot, or other
dependencies to their respective maintainers unless this plugin's integration
is the cause.
