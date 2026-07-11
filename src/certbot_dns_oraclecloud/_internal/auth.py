"""OCI authentication selection and DNS client construction."""

from typing import Final

from certbot import errors

from .protocols import (
    DnsClientProtocol,
    OciAuthenticationError,
    create_api_key_dns_client,
    create_instance_principal_dns_client,
    create_resource_principal_dns_client,
)

AUTH_TYPES: Final = ("api_key", "instance_principal", "resource_principal")
UNSUPPORTED_AUTHENTICATION_MESSAGE: Final = "Unsupported OCI authentication mode: {}"


def create_dns_client(auth_type: str, credentials: str, profile: str) -> DnsClientProtocol:
    """Create a DNS client for one explicitly selected authentication mode."""
    if auth_type == "api_key":
        return _api_key_client(credentials, profile)
    if auth_type == "instance_principal":
        return _instance_principal_client()
    if auth_type == "resource_principal":
        return _resource_principal_client()
    message = UNSUPPORTED_AUTHENTICATION_MESSAGE.format(auth_type)
    raise errors.PluginError(message)


def _api_key_client(credentials: str, profile: str) -> DnsClientProtocol:
    """Create an API-key client without reflecting sensitive configuration data."""
    try:
        return create_api_key_dns_client(credentials, profile)
    except OciAuthenticationError:
        message = "Unable to initialize OCI API-key authentication."
    raise errors.PluginError(message) from None


def _instance_principal_client() -> DnsClientProtocol:
    """Create an instance-principal client without changing authentication mode."""
    try:
        return create_instance_principal_dns_client()
    except OciAuthenticationError:
        message = "Unable to initialize OCI instance-principal authentication."
    raise errors.PluginError(message) from None


def _resource_principal_client() -> DnsClientProtocol:
    """Create a resource-principal client without falling back to another mode."""
    try:
        return create_resource_principal_dns_client()
    except OciAuthenticationError:
        message = "Unable to initialize OCI resource-principal authentication."
    raise errors.PluginError(message) from None
