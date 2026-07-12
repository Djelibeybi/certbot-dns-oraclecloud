"""Typed boundary around the untyped OCI Python SDK."""

import json
import re
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Literal, Protocol, TypeVar, cast

from oci import config as oci_config  # pyright: ignore[reportMissingTypeStubs]
from oci.auth.signers import (  # pyright: ignore[reportMissingTypeStubs]
    InstancePrincipalsSecurityTokenSigner,
    get_resource_principals_signer,  # pyright: ignore[reportUnknownVariableType]
)
from oci.dns import DnsClient  # pyright: ignore[reportMissingTypeStubs]
from oci.dns.models import (  # pyright: ignore[reportMissingTypeStubs]
    PatchZoneRecordsDetails,
    RecordOperation,
)
from oci.exceptions import (  # pyright: ignore[reportMissingTypeStubs]
    ConfigFileNotFound,
    InvalidConfig,
    InvalidKeyFilePath,
    InvalidPrivateKey,
    MissingPrivateKeyPassphrase,
    ProfileNotFound,
    RequestException,
    ServiceError,
)

T_co = TypeVar("T_co", covariant=True)
_SAFE_OCI_CODE = re.compile(r"[A-Za-z0-9_-]+\Z")


class OciResponseProtocol(Protocol[T_co]):
    """The safe structural portion of an OCI response."""

    @property
    def data(self) -> T_co:
        """Return response data."""
        ...


class OciPaginatedResponseProtocol(OciResponseProtocol[T_co], Protocol[T_co]):
    """The safe structural portion of an OCI paginated response."""

    @property
    def next_page(self) -> str | None:
        """Return the next page token when more results are available."""
        ...


class ZoneProtocol(Protocol):
    """The OCI zone attributes relevant to this plugin."""

    @property
    def name(self) -> str:
        """Return the zone name."""
        ...


class PatchZoneRecordsResponseProtocol(OciResponseProtocol[object], Protocol):
    """The response returned by an OCI record patch operation."""


class RecordOperationProtocol(Protocol):
    """The fields used to assert exact TXT record operations."""

    @property
    def domain(self) -> str:
        """Return the record domain."""
        ...

    @property
    def rtype(self) -> str:
        """Return the record type."""
        ...

    @property
    def rdata(self) -> str:
        """Return the record data."""
        ...

    @property
    def ttl(self) -> int | None:
        """Return the record TTL."""
        ...

    @property
    def operation(self) -> str:
        """Return the patch operation."""
        ...


class DnsClientProtocol(Protocol):
    """The OCI DNS SDK methods needed by this narrow wrapper."""

    def get_zone(
        self, *, zone_name_or_id: str, scope: Literal["GLOBAL"]
    ) -> OciResponseProtocol[ZoneProtocol]:
        """Get one public DNS zone."""
        ...

    def patch_zone_records(
        self,
        *,
        zone_name_or_id: str,
        patch_zone_records_details: object,
        scope: Literal["GLOBAL"],
    ) -> PatchZoneRecordsResponseProtocol:
        """Apply one or more patch operations to a public DNS zone."""
        ...


class OciAuthenticationError(Exception):
    """A redacted OCI configuration or signer initialization failure."""


class OciRequestError(Exception):
    """A redacted OCI request or request-construction failure."""


class OciServiceError(Exception):
    """An OCI service failure retaining only safe status and code metadata."""

    def __init__(self, status: int | None, code: str | None) -> None:
        self.status = status
        self.code = code


class _OciConfigProtocol(Protocol):
    """The untyped SDK configuration methods used by this plugin."""

    def from_file(self, *, file_location: str, profile_name: str) -> dict[str, object]:
        """Read one API-key configuration profile."""
        ...

    def validate_config(self, config: Mapping[str, object]) -> None:
        """Validate an API-key configuration."""
        ...


class _ServiceErrorMetadataProtocol(Protocol):
    """The safe metadata exposed by OCI service errors."""

    @property
    def status(self) -> object:
        """Return the HTTP status supplied by OCI."""

    @property
    def code(self) -> object:
        """Return the OCI error code supplied by OCI."""


_oci_config = cast("_OciConfigProtocol", oci_config)
_dns_client_factory = cast("Callable[..., object]", DnsClient)
_instance_principal_signer = cast("Callable[[], object]", InstancePrincipalsSecurityTokenSigner)
_resource_principal_signer = cast("Callable[[], object]", get_resource_principals_signer)
_record_operation_factory = cast("Callable[..., object]", RecordOperation)
_patch_details_factory = cast("Callable[..., object]", PatchZoneRecordsDetails)

_config_file_not_found = cast("type[Exception]", ConfigFileNotFound)
_invalid_config = cast("type[Exception]", InvalidConfig)
_invalid_key_file_path = cast("type[Exception]", InvalidKeyFilePath)
_invalid_private_key = cast("type[Exception]", InvalidPrivateKey)
_missing_private_key_passphrase = cast("type[Exception]", MissingPrivateKeyPassphrase)
_profile_not_found = cast("type[Exception]", ProfileNotFound)
_request_exception = cast("type[Exception]", RequestException)
_service_error = cast("type[Exception]", ServiceError)
_authentication_failures = (
    _config_file_not_found,
    _invalid_config,
    _invalid_key_file_path,
    _invalid_private_key,
    _missing_private_key_passphrase,
    _profile_not_found,
    _request_exception,
    _service_error,
    OSError,
    ValueError,
)


def create_api_key_dns_client(credentials: str, profile: str) -> DnsClientProtocol:
    """Create a DNS client from an explicitly requested API-key profile."""
    try:
        config = _oci_config.from_file(
            file_location=str(Path(credentials).expanduser()), profile_name=profile
        )
        _oci_config.validate_config(config)
        client = _dns_client_factory(config)
    except _authentication_failures:
        raise OciAuthenticationError from None
    return cast("DnsClientProtocol", client)


def create_instance_principal_dns_client() -> DnsClientProtocol:
    """Create a DNS client with the OCI instance-principal signer."""
    try:
        signer = _instance_principal_signer()
        client = _dns_client_factory(config={}, signer=signer)
    except _authentication_failures:
        raise OciAuthenticationError from None
    return cast("DnsClientProtocol", client)


def create_resource_principal_dns_client() -> DnsClientProtocol:
    """Create a DNS client with the OCI resource-principal signer."""
    try:
        signer = _resource_principal_signer()
        client = _dns_client_factory(config={}, signer=signer)
    except _authentication_failures:
        raise OciAuthenticationError from None
    return cast("DnsClientProtocol", client)


def get_zone(client: DnsClientProtocol, zone_name: str) -> OciResponseProtocol[ZoneProtocol]:
    """Get a public zone while stripping request bodies and error messages."""
    try:
        return client.get_zone(zone_name_or_id=zone_name, scope="GLOBAL")
    except _service_error as error:
        raise _service_error_from_exception(error) from None
    except _request_exception:
        raise OciRequestError from None


def patch_zone_records(
    client: DnsClientProtocol, zone_name: str, operation: RecordOperationProtocol
) -> PatchZoneRecordsResponseProtocol:
    """Patch one public zone record while stripping sensitive OCI error data."""
    try:
        details = _patch_details_factory(items=[operation])
        return client.patch_zone_records(
            zone_name_or_id=zone_name,
            patch_zone_records_details=details,
            scope="GLOBAL",
        )
    except _service_error as error:
        raise _service_error_from_exception(error) from None
    except (_request_exception, ValueError):
        raise OciRequestError from None


def add_record_operation(
    validation_name: str, validation: str, ttl: int
) -> RecordOperationProtocol:
    """Build an exact OCI DNS TXT add operation."""
    return _record_operation(validation_name, validation, ttl, "ADD")


def remove_record_operation(validation_name: str, validation: str) -> RecordOperationProtocol:
    """Build an exact OCI DNS TXT remove operation."""
    return _record_operation(validation_name, validation, None, "REMOVE")


def _record_operation(
    validation_name: str, validation: str, ttl: int | None, operation: Literal["ADD", "REMOVE"]
) -> RecordOperationProtocol:
    """Build one record operation without exposing failed model inputs."""
    try:
        record = _record_operation_factory(
            domain=validation_name,
            rtype="TXT",
            rdata=json.dumps(validation),
            ttl=ttl,
            operation=operation,
        )
    except ValueError:
        raise OciRequestError from None
    return cast("RecordOperationProtocol", record)


def _service_error_from_exception(error: Exception) -> OciServiceError:
    """Extract only safe OCI status/code metadata from a service failure."""
    metadata = cast("_ServiceErrorMetadataProtocol", error)
    status = metadata.status if isinstance(metadata.status, int) else None
    code = (
        metadata.code
        if isinstance(metadata.code, str) and _SAFE_OCI_CODE.fullmatch(metadata.code)
        else None
    )
    return OciServiceError(status=status, code=code)
