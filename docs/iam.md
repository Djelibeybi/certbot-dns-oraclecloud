# OCI IAM

<!-- VERIFY: Confirm the OCI IAM verbs and resource types required for public DNS zone discovery and record updates. -->
Grant the identity used by Certbot access only to the compartment that contains
the public DNS zones it must validate. Zone discovery reads DNS zones; each
DNS-01 lifecycle patches records, so it also needs DNS-record management.

For a user group using API-key authentication, replace the names with your
group and target compartment:

```text
Allow group CertbotDnsOperators to read dns-zones in compartment CertbotDns
Allow group CertbotDnsOperators to manage dns-records in compartment CertbotDns
```

<!-- VERIFY: Confirm whether OCI instance and resource principals must be assigned through dynamic groups. -->
<!-- VERIFY: Confirm whether dynamic groups use the same DNS IAM permissions as API-key user groups. -->
For an instance principal or resource principal, assign the corresponding OCI
workload to a dynamic group and grant the same least-privilege permissions:

```text
Allow dynamic-group CertbotDnsWorkloads to read dns-zones in compartment CertbotDns
Allow dynamic-group CertbotDnsWorkloads to manage dns-records in compartment CertbotDns
```

Use a dynamic-group matching rule that identifies only the instances or
resources that run Certbot. These policies intentionally scope by compartment;
this documentation does not rely on an unverified zone-name condition. Do not
grant private DNS permissions: the plugin queries and patches public/global
DNS zones only.
