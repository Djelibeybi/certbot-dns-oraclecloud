"""Tests for narrow public OCI DNS record operations."""

from unittest.mock import MagicMock, call

import pytest
from certbot import errors
from oci.exceptions import ServiceError

from certbot_dns_oraclecloud._internal.dns_client import OciDnsClient


def service_error(status: int, code: str = "ServiceError") -> ServiceError:
    """Build an OCI service error with a non-sensitive message."""
    return ServiceError(status=status, code=code, headers={}, message="safe OCI message")


def test_find_zone_uses_most_specific_public_zone() -> None:
    sdk = MagicMock()
    sdk.get_zone.return_value = object()
    client = OciDnsClient(sdk)

    assert client.find_zone("_acme-challenge.www.example.com") == (
        "_acme-challenge.www.example.com"
    )
    sdk.get_zone.assert_called_once_with(
        zone_name_or_id="_acme-challenge.www.example.com", scope="GLOBAL"
    )


def test_find_zone_continues_only_on_404() -> None:
    sdk = MagicMock()
    sdk.get_zone.side_effect = [service_error(404), object()]
    client = OciDnsClient(sdk)

    assert client.find_zone("_acme-challenge.example.com") == "example.com"
    assert sdk.get_zone.call_args_list == [
        call(zone_name_or_id="_acme-challenge.example.com", scope="GLOBAL"),
        call(zone_name_or_id="example.com", scope="GLOBAL"),
    ]


def test_find_zone_fails_immediately_on_non_404() -> None:
    sdk = MagicMock()
    sdk.get_zone.side_effect = service_error(403, "NotAuthorized")
    client = OciDnsClient(sdk)

    with pytest.raises(errors.PluginError, match="status=403"):
        client.find_zone("_acme-challenge.example.com")

    assert sdk.get_zone.call_count == 1


def test_find_zone_reports_when_no_public_zone_exists() -> None:
    sdk = MagicMock()
    sdk.get_zone.side_effect = service_error(404)
    client = OciDnsClient(sdk)

    with pytest.raises(errors.PluginError, match="Unable to find a public OCI DNS zone"):
        client.find_zone("_acme-challenge.example.com")


def test_find_zone_wraps_non_service_failures() -> None:
    sdk = MagicMock()
    sdk.get_zone.side_effect = RuntimeError("transport internals")
    client = OciDnsClient(sdk)

    with pytest.raises(errors.PluginError, match="zone lookup failed") as raised:
        client.find_zone("_acme-challenge.example.com")

    assert "transport internals" not in str(raised.value)


def test_add_txt_record_patches_one_exact_quoted_value() -> None:
    sdk = MagicMock()
    sdk.get_zone.return_value = object()
    client = OciDnsClient(sdk)

    client.add_txt_record("_acme-challenge.example.com", 'token"value', 60)

    sdk.patch_zone_records.assert_called_once()
    kwargs = sdk.patch_zone_records.call_args.kwargs
    assert kwargs["zone_name_or_id"] == "_acme-challenge.example.com"
    assert kwargs["scope"] == "GLOBAL"
    operations = kwargs["patch_zone_records_details"].items
    assert len(operations) == 1
    operation = operations[0]
    assert operation.operation == "ADD"
    assert operation.domain == "_acme-challenge.example.com"
    assert operation.rtype == "TXT"
    assert operation.rdata == '"token\\"value"'
    assert operation.ttl == 60


def test_remove_txt_record_patches_only_the_matching_value() -> None:
    sdk = MagicMock()
    sdk.get_zone.return_value = object()
    client = OciDnsClient(sdk)

    client.remove_txt_record("_acme-challenge.example.com", "owned-token")

    kwargs = sdk.patch_zone_records.call_args.kwargs
    operations = kwargs["patch_zone_records_details"].items
    assert len(operations) == 1
    operation = operations[0]
    assert operation.operation == "REMOVE"
    assert operation.domain == "_acme-challenge.example.com"
    assert operation.rtype == "TXT"
    assert operation.rdata == '"owned-token"'
    assert operation.ttl is None


def test_mutation_error_does_not_expose_validation_value() -> None:
    sdk = MagicMock()
    sdk.get_zone.return_value = object()
    secret_validation = "do-not-log-this-token"
    sdk.patch_zone_records.side_effect = ServiceError(
        status=409,
        code="Conflict",
        headers={},
        message=f"rejected value {secret_validation}",
    )
    client = OciDnsClient(sdk)

    with pytest.raises(errors.PluginError) as raised:
        client.add_txt_record("_acme-challenge.example.com", secret_validation, 60)

    assert secret_validation not in str(raised.value)
    assert "status=409" in str(raised.value)


def test_transport_mutation_error_does_not_expose_validation_value() -> None:
    sdk = MagicMock()
    sdk.get_zone.return_value = object()
    sdk.patch_zone_records.side_effect = RuntimeError("transport internals")
    client = OciDnsClient(sdk)
    secret_validation = "do-not-log-this-token"

    with pytest.raises(errors.PluginError, match="record add failed") as raised:
        client.add_txt_record("_acme-challenge.example.com", secret_validation, 60)

    assert secret_validation not in str(raised.value)
    assert "transport internals" not in str(raised.value)
