"""Certbot authenticator for Oracle Cloud Infrastructure DNS."""

from collections.abc import Callable
from typing import cast

from certbot import errors
from certbot.configuration import NamespaceConfig
from certbot.plugins import dns_common

from .auth import AUTH_TYPES, create_dns_client
from .dns_client import OciDnsClient


class Authenticator(dns_common.DNSAuthenticator):
    """Fulfil DNS-01 challenges in public OCI DNS zones."""

    description = "Obtain certificates using public Oracle Cloud Infrastructure DNS."
    ttl = 60

    def __init__(self, config: NamespaceConfig, name: str) -> None:
        """Initialize a Certbot authenticator without creating an OCI client yet."""
        super().__init__(config, name)
        self._dns: OciDnsClient | None = None

    @classmethod
    def add_parser_arguments(
        cls, add: Callable[..., None], default_propagation_seconds: int = 60
    ) -> None:
        """Add OCI authentication options with explicit safe defaults."""
        super().add_parser_arguments(add, default_propagation_seconds)
        add(
            "auth-type",
            choices=AUTH_TYPES,
            default="api_key",
            help="OCI authentication mode.",
        )
        add(
            "credentials",
            default="~/.oci/config",
            help="OCI SDK config file used by API-key authentication.",
        )
        add(
            "profile",
            default="DEFAULT",
            help="Profile in the OCI SDK config file used by API-key authentication.",
        )

    def more_info(self) -> str:
        """Describe the DNS scope and exact-value lifecycle of this plugin."""
        return "This plugin creates exact DNS-01 TXT values in public OCI DNS zones."

    def _setup_credentials(self) -> None:
        """Create and cache the OCI DNS client chosen by the Certbot configuration."""
        if self._dns is not None:
            return
        auth_type = cast("str", self.conf("auth-type"))
        credentials = cast("str", self.conf("credentials"))
        profile = cast("str", self.conf("profile"))
        self._dns = OciDnsClient(create_dns_client(auth_type, credentials, profile))

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        """Create the exact TXT value required for one ACME DNS-01 challenge."""
        del domain
        self._get_dns_client().add_txt_record(validation_name, validation, self.ttl)

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        """Remove only the exact TXT value created for one ACME DNS-01 challenge."""
        del domain
        self._get_dns_client().remove_txt_record(validation_name, validation)

    def _get_dns_client(self) -> OciDnsClient:
        """Return the prepared OCI DNS client or a validation-safe Certbot error."""
        if self._dns is None:
            message = "Plugin has not been prepared."
            raise errors.Error(message)
        return self._dns
