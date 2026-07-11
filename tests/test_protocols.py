"""Tests for the typed OCI SDK adapter boundary."""

import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from certbot_dns_oraclecloud._internal import protocols


@patch("certbot_dns_oraclecloud._internal.protocols._dns_client_factory")
@patch("certbot_dns_oraclecloud._internal.protocols._oci_config")
def test_api_key_adapter_loads_and_validates_the_requested_profile(
    config: MagicMock, client_factory: MagicMock
) -> None:
    """API-key setup remains inside the typed OCI adapter boundary."""
    loaded = {"region": "us-ashburn-1"}
    config.from_file.return_value = loaded

    result = protocols.create_api_key_dns_client("~/.oci/config", "TEST")

    config.from_file.assert_called_once_with(
        file_location=str(Path("~/.oci/config").expanduser()), profile_name="TEST"
    )
    config.validate_config.assert_called_once_with(loaded)
    client_factory.assert_called_once_with(loaded)
    assert result is client_factory.return_value


@patch("certbot_dns_oraclecloud._internal.protocols._oci_config")
def test_api_key_adapter_suppresses_configuration_traceback_details(config: MagicMock) -> None:
    """The adapter suppresses untrusted OCI configuration failure context."""
    sentinel = "PRIVATE CONFIGURATION SENTINEL"
    config.from_file.side_effect = OSError(sentinel)

    with pytest.raises(protocols.OciAuthenticationError) as raised:
        protocols.create_api_key_dns_client("~/.oci/config", "TEST")

    rendered = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert sentinel not in rendered


@patch("certbot_dns_oraclecloud._internal.protocols._dns_client_factory")
@patch("certbot_dns_oraclecloud._internal.protocols._instance_principal_signer")
def test_instance_principal_adapter_uses_only_its_signer(
    signer_factory: MagicMock, client_factory: MagicMock
) -> None:
    """Instance-principal setup remains explicit at the adapter boundary."""
    result = protocols.create_instance_principal_dns_client()

    signer_factory.assert_called_once_with()
    client_factory.assert_called_once_with(config={}, signer=signer_factory.return_value)
    assert result is client_factory.return_value


@patch("certbot_dns_oraclecloud._internal.protocols._dns_client_factory")
@patch("certbot_dns_oraclecloud._internal.protocols._resource_principal_signer")
def test_resource_principal_adapter_uses_only_its_signer(
    signer_factory: MagicMock, client_factory: MagicMock
) -> None:
    """Resource-principal setup remains explicit at the adapter boundary."""
    result = protocols.create_resource_principal_dns_client()

    signer_factory.assert_called_once_with()
    client_factory.assert_called_once_with(config={}, signer=signer_factory.return_value)
    assert result is client_factory.return_value
