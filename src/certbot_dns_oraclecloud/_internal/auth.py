"""OCI authentication selection and DNS client construction."""

from pathlib import Path
from typing import Any, Final

from certbot import errors
from oci import config as oci_config
from oci.auth.signers import (
    InstancePrincipalsSecurityTokenSigner,
    get_resource_principals_signer,
)
from oci.dns import DnsClient

AUTH_TYPES: Final = ("api_key", "instance_principal", "resource_principal")


def create_dns_client(auth_type: str, credentials: str, profile: str) -> Any:
    """Create an OCI DNS client for one explicitly selected authentication mode."""
    try:
        if auth_type == "api_key":
            config_path = str(Path(credentials).expanduser())
            loaded = oci_config.from_file(file_location=config_path, profile_name=profile)
            oci_config.validate_config(loaded)
            return DnsClient(loaded)

        if auth_type == "instance_principal":
            return DnsClient(config={}, signer=InstancePrincipalsSecurityTokenSigner())

        if auth_type == "resource_principal":
            return DnsClient(config={}, signer=get_resource_principals_signer())
    except Exception:
        label = {
            "api_key": "API-key",
            "instance_principal": "instance-principal",
            "resource_principal": "resource-principal",
        }[auth_type]
        if auth_type == "api_key":
            config_path = str(Path(credentials).expanduser())
            detail = f" from {config_path!r} using profile {profile!r}"
        else:
            detail = ""
        message = f"Unable to initialize OCI {label} authentication{detail}."
        plugin_error = errors.PluginError(message)
    else:
        raise errors.PluginError(f"Unsupported OCI authentication mode: {auth_type}")

    raise plugin_error from None
