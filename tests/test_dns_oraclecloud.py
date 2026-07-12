"""Tests for Certbot's Oracle Cloud Infrastructure DNS authenticator."""

from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest
from certbot import errors

from certbot_dns_oraclecloud._internal.auth import AUTH_TYPES
from certbot_dns_oraclecloud._internal.dns_client import OciDnsClient
from certbot_dns_oraclecloud._internal.dns_oraclecloud import Authenticator

EXPECTED_TTL = 60


class AuthenticatorHarness(Authenticator):
    """Expose Certbot lifecycle hooks through public test-only methods."""

    def setup_credentials(self) -> None:
        """Invoke Certbot's credential lifecycle hook."""
        self._setup_credentials()

    def set_dns_client(self, client: OciDnsClient) -> None:
        """Inject a prepared OCI DNS client for lifecycle delegation tests."""
        self._dns = client

    def invoke_perform(self, domain: str, validation_name: str, validation: str) -> None:
        """Invoke Certbot's perform lifecycle hook."""
        self._perform(domain, validation_name, validation)

    def invoke_cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        """Invoke Certbot's cleanup lifecycle hook."""
        self._cleanup(domain, validation_name, validation)


def test_parser_arguments_have_exact_explicit_defaults() -> None:
    """The plugin provides its complete Certbot command-line contract."""
    arguments: dict[str, dict[str, object]] = {}

    def add(name: str, **kwargs: object) -> None:
        arguments[name] = kwargs

    Authenticator.add_parser_arguments(add)

    assert set(arguments) == {"auth-type", "credentials", "profile", "propagation-seconds"}
    assert arguments["auth-type"]["choices"] == AUTH_TYPES
    assert arguments["auth-type"]["default"] == "api_key"
    assert arguments["credentials"]["default"] == "~/.oci/config"
    assert arguments["profile"]["default"] == "DEFAULT"
    assert arguments["propagation-seconds"]["default"] == EXPECTED_TTL


@patch("certbot_dns_oraclecloud._internal.dns_oraclecloud.OciDnsClient")
@patch("certbot_dns_oraclecloud._internal.dns_oraclecloud.create_dns_client")
def test_setup_builds_and_caches_selected_client(
    create_client: MagicMock, wrapper: MagicMock
) -> None:
    """Setup builds one client for the explicitly selected OCI authentication mode."""
    config = MagicMock(
        dns_oraclecloud_auth_type="resource_principal",
        dns_oraclecloud_credentials="/ignored",
        dns_oraclecloud_profile="IGNORED",
    )
    authenticator = AuthenticatorHarness(config, "dns-oraclecloud")

    authenticator.setup_credentials()
    authenticator.setup_credentials()

    create_client.assert_called_once_with("resource_principal", "/ignored", "IGNORED")
    wrapper.assert_called_once_with(create_client.return_value)


def test_perform_and_cleanup_delegate_exact_validation() -> None:
    """Challenge lifecycle calls use the exact requested validation name and value."""
    authenticator = AuthenticatorHarness(MagicMock(), "dns-oraclecloud")
    dns = MagicMock()
    authenticator.set_dns_client(dns)

    authenticator.invoke_perform("example.com", "_acme-challenge.example.com", "token")
    authenticator.invoke_cleanup("example.com", "_acme-challenge.example.com", "token")

    dns.add_txt_record.assert_called_once_with("_acme-challenge.example.com", "token", 60)
    dns.remove_txt_record.assert_called_once_with("_acme-challenge.example.com", "token")


@pytest.mark.parametrize(
    "operation", [AuthenticatorHarness.invoke_perform, AuthenticatorHarness.invoke_cleanup]
)
def test_lifecycle_requires_initialized_client_without_exposing_validation(
    operation: Callable[[AuthenticatorHarness, str, str, str], None],
) -> None:
    """Unprepared hooks fail safely before a validation value reaches OCI operations."""
    authenticator = AuthenticatorHarness(MagicMock(), "dns-oraclecloud")
    validation = "do-not-expose-this-acme-value"

    with pytest.raises(errors.Error, match="not been prepared") as raised:
        operation(authenticator, "example.com", "_acme-challenge.example.com", validation)

    assert validation not in str(raised.value)


def test_plugin_metadata_describes_public_oci_dns() -> None:
    """Certbot users receive an accurate, stable description of the plugin."""
    authenticator = Authenticator(MagicMock(), "dns-oraclecloud")

    assert authenticator.ttl == EXPECTED_TTL
    assert "public Oracle Cloud Infrastructure DNS" in authenticator.description
    assert "public OCI DNS zones" in authenticator.more_info()
