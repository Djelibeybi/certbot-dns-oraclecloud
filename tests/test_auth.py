"""Tests for OCI DNS client authentication selection."""

import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from certbot import errors

from certbot_dns_oraclecloud._internal.auth import create_dns_client
from certbot_dns_oraclecloud._internal.protocols import OciAuthenticationError


@patch("certbot_dns_oraclecloud._internal.auth.create_api_key_dns_client")
def test_api_key_loads_requested_file_and_profile(
    api_key_client: MagicMock, tmp_path: Path
) -> None:
    config_file = tmp_path / "config"
    config_file.write_text("[TEST]\n", encoding="utf-8")

    result = create_dns_client("api_key", str(config_file), "TEST")

    api_key_client.assert_called_once_with(str(config_file), "TEST")
    assert result is api_key_client.return_value


@patch("certbot_dns_oraclecloud._internal.auth.create_api_key_dns_client")
def test_api_key_error_does_not_expose_sdk_exception(api_key_client: MagicMock) -> None:
    credential_path = "/private/credentials/config"
    profile = "PRIVATE-PROFILE"
    secret = "PRIVATE KEY MATERIAL"
    api_key_client.side_effect = OciAuthenticationError(secret)

    with pytest.raises(errors.PluginError) as raised:
        create_dns_client("api_key", credential_path, profile)

    assert secret not in str(raised.value)
    assert credential_path not in str(raised.value)
    assert profile not in str(raised.value)
    rendered = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert secret not in rendered
    assert credential_path not in rendered
    assert profile not in rendered
    assert "API-key" in str(raised.value)


@patch("certbot_dns_oraclecloud._internal.auth.create_instance_principal_dns_client")
@patch("certbot_dns_oraclecloud._internal.auth.create_api_key_dns_client")
def test_instance_principal_does_not_consult_api_key_config(
    api_key_client: MagicMock, instance_client: MagicMock
) -> None:
    result = create_dns_client("instance_principal", "/must/not/be/read", "IGNORED")

    api_key_client.assert_not_called()
    instance_client.assert_called_once_with()
    assert result is instance_client.return_value


@patch("certbot_dns_oraclecloud._internal.auth.create_resource_principal_dns_client")
@patch("certbot_dns_oraclecloud._internal.auth.create_api_key_dns_client")
def test_resource_principal_does_not_fall_back(
    api_key_client: MagicMock, resource_client: MagicMock
) -> None:
    result = create_dns_client("resource_principal", "/must/not/be/read", "IGNORED")

    api_key_client.assert_not_called()
    resource_client.assert_called_once_with()
    assert result is resource_client.return_value


@patch("certbot_dns_oraclecloud._internal.auth.create_resource_principal_dns_client")
@patch("certbot_dns_oraclecloud._internal.auth.create_instance_principal_dns_client")
def test_unknown_authentication_mode_uses_no_fallback(
    instance_client: MagicMock, resource_client: MagicMock
) -> None:
    with pytest.raises(errors.PluginError, match="Unsupported OCI authentication mode"):
        create_dns_client("auto", "~/.oci/config", "DEFAULT")

    instance_client.assert_not_called()
    resource_client.assert_not_called()


@patch("certbot_dns_oraclecloud._internal.auth.create_resource_principal_dns_client")
@patch("certbot_dns_oraclecloud._internal.auth.create_instance_principal_dns_client")
def test_resource_principal_failure_does_not_fall_back(
    instance_client: MagicMock, resource_client: MagicMock
) -> None:
    secret = "RESOURCE PRINCIPAL TOKEN"
    resource_client.side_effect = OciAuthenticationError(secret)

    with pytest.raises(errors.PluginError) as raised:
        create_dns_client("resource_principal", "/ignored", "IGNORED")

    instance_client.assert_not_called()
    assert secret not in str(raised.value)
    rendered = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert secret not in rendered


@patch("certbot_dns_oraclecloud._internal.auth.create_instance_principal_dns_client")
def test_instance_principal_failure_does_not_expose_signer_data(
    instance_client: MagicMock,
) -> None:
    """Instance-principal signer details never reach Certbot tracebacks."""
    sentinel = "INSTANCE PRINCIPAL TOKEN"
    instance_client.side_effect = OciAuthenticationError(sentinel)

    with pytest.raises(errors.PluginError) as raised:
        create_dns_client("instance_principal", "/ignored", "IGNORED")

    rendered = "".join(traceback.format_exception(raised.type, raised.value, raised.tb))
    assert sentinel not in str(raised.value)
    assert sentinel not in rendered
