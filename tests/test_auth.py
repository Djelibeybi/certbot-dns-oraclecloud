"""Tests for OCI DNS client authentication selection."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from certbot import errors

from certbot_dns_oraclecloud._internal.auth import create_dns_client


@patch("certbot_dns_oraclecloud._internal.auth.DnsClient")
@patch("certbot_dns_oraclecloud._internal.auth.oci_config.validate_config")
@patch("certbot_dns_oraclecloud._internal.auth.oci_config.from_file")
def test_api_key_loads_requested_file_and_profile(
    from_file: MagicMock, validate_config: MagicMock, dns_client: MagicMock, tmp_path: Path
) -> None:
    config_file = tmp_path / "config"
    config_file.write_text("[TEST]\n", encoding="utf-8")
    loaded = {"region": "us-ashburn-1"}
    from_file.return_value = loaded

    result = create_dns_client("api_key", str(config_file), "TEST")

    from_file.assert_called_once_with(file_location=str(config_file), profile_name="TEST")
    validate_config.assert_called_once_with(loaded)
    dns_client.assert_called_once_with(loaded)
    assert result is dns_client.return_value


@patch("certbot_dns_oraclecloud._internal.auth.oci_config.from_file")
def test_api_key_error_does_not_expose_sdk_exception(from_file: MagicMock) -> None:
    secret = "PRIVATE KEY MATERIAL"
    from_file.side_effect = ValueError(secret)

    with pytest.raises(errors.PluginError) as raised:
        create_dns_client("api_key", "~/.oci/config", "DEFAULT")

    assert secret not in str(raised.value)
    assert "API-key" in str(raised.value)


@patch("certbot_dns_oraclecloud._internal.auth.DnsClient")
@patch("certbot_dns_oraclecloud._internal.auth.InstancePrincipalsSecurityTokenSigner")
@patch("certbot_dns_oraclecloud._internal.auth.oci_config.from_file")
def test_instance_principal_does_not_consult_api_key_config(
    from_file: MagicMock, signer_class: MagicMock, dns_client: MagicMock
) -> None:
    result = create_dns_client("instance_principal", "/must/not/be/read", "IGNORED")

    from_file.assert_not_called()
    signer_class.assert_called_once_with()
    dns_client.assert_called_once_with(config={}, signer=signer_class.return_value)
    assert result is dns_client.return_value


@patch("certbot_dns_oraclecloud._internal.auth.DnsClient")
@patch("certbot_dns_oraclecloud._internal.auth.get_resource_principals_signer")
@patch("certbot_dns_oraclecloud._internal.auth.oci_config.from_file")
def test_resource_principal_does_not_fall_back(
    from_file: MagicMock, signer_factory: MagicMock, dns_client: MagicMock
) -> None:
    result = create_dns_client("resource_principal", "/must/not/be/read", "IGNORED")

    from_file.assert_not_called()
    signer_factory.assert_called_once_with()
    dns_client.assert_called_once_with(config={}, signer=signer_factory.return_value)
    assert result is dns_client.return_value


@patch("certbot_dns_oraclecloud._internal.auth.get_resource_principals_signer")
@patch("certbot_dns_oraclecloud._internal.auth.InstancePrincipalsSecurityTokenSigner")
def test_unknown_authentication_mode_uses_no_fallback(
    instance_signer: MagicMock, resource_signer: MagicMock
) -> None:
    with pytest.raises(errors.PluginError, match="Unsupported OCI authentication mode"):
        create_dns_client("auto", "~/.oci/config", "DEFAULT")

    instance_signer.assert_not_called()
    resource_signer.assert_not_called()


@patch("certbot_dns_oraclecloud._internal.auth.get_resource_principals_signer")
@patch("certbot_dns_oraclecloud._internal.auth.InstancePrincipalsSecurityTokenSigner")
def test_resource_principal_failure_does_not_fall_back(
    instance_signer: MagicMock, resource_signer: MagicMock
) -> None:
    secret = "RESOURCE PRINCIPAL TOKEN"
    resource_signer.side_effect = RuntimeError(secret)

    with pytest.raises(errors.PluginError) as raised:
        create_dns_client("resource_principal", "/ignored", "IGNORED")

    instance_signer.assert_not_called()
    assert secret not in str(raised.value)
