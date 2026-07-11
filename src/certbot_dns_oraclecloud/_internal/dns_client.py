"""Narrow OCI DNS client for ACME TXT challenges."""

from certbot import errors
from certbot.plugins import dns_common

from .protocols import (
    DnsClientProtocol,
    OciRequestError,
    OciServiceError,
    RecordOperationProtocol,
    add_record_operation,
    get_zone,
    patch_zone_records,
    remove_record_operation,
)

NOT_FOUND_STATUS = 404
NO_PUBLIC_ZONE_MESSAGE = "Unable to find a public OCI DNS zone for {}."


class OciDnsClient:
    """Perform public OCI DNS operations needed by Certbot."""

    def __init__(self, client: DnsClientProtocol) -> None:
        self._client = client

    def find_zone(self, validation_name: str) -> str:
        """Return the most-specific public OCI zone for a validation name."""
        for candidate in dns_common.base_domain_name_guesses(validation_name):
            try:
                get_zone(self._client, candidate)
            except OciServiceError as failure:
                if failure.status == NOT_FOUND_STATUS:
                    continue
                message = self._service_failure_message("zone lookup", validation_name, failure)
            except OciRequestError:
                message = f"OCI DNS zone lookup failed for {validation_name}."
            else:
                return candidate
            raise errors.PluginError(message) from None
        message = NO_PUBLIC_ZONE_MESSAGE.format(validation_name)
        raise errors.PluginError(message)

    def add_txt_record(self, validation_name: str, validation: str, ttl: int) -> None:
        """Add exactly one ACME TXT value."""
        self._patch(
            validation_name,
            self._operation_or_error(validation_name, validation, ttl, "ADD"),
            "record add",
        )

    def remove_txt_record(self, validation_name: str, validation: str) -> None:
        """Remove exactly one ACME TXT value."""
        self._patch(
            validation_name,
            self._operation_or_error(validation_name, validation, None, "REMOVE"),
            "record remove",
        )

    def _operation_or_error(
        self,
        validation_name: str,
        validation: str,
        ttl: int | None,
        operation: str,
    ) -> RecordOperationProtocol:
        """Build one operation without exposing its validation value on failure."""
        try:
            if operation == "ADD":
                if ttl is None:
                    raise ValueError
                record_operation = add_record_operation(validation_name, validation, ttl)
            else:
                record_operation = remove_record_operation(validation_name, validation)
        except OciRequestError:
            message = f"OCI DNS record {operation.lower()} failed for {validation_name}."
        else:
            return record_operation
        raise errors.PluginError(message) from None

    def _patch(
        self, validation_name: str, operation: RecordOperationProtocol, operation_name: str
    ) -> None:
        """Apply one exact record operation in the public/global scope."""
        zone = self.find_zone(validation_name)
        try:
            patch_zone_records(self._client, zone, operation)
        except OciServiceError as failure:
            message = self._service_failure_message(operation_name, validation_name, failure)
        except OciRequestError:
            message = f"OCI DNS {operation_name} failed for {validation_name}."
        else:
            return
        raise errors.PluginError(message) from None

    @staticmethod
    def _service_failure_message(operation: str, record_name: str, failure: OciServiceError) -> str:
        """Render only the safe OCI status/code metadata for a service failure."""
        fields: list[str] = []
        if failure.status is not None:
            fields.append(f"status={failure.status}")
        if failure.code is not None:
            fields.append(f"code={failure.code}")
        suffix = f": {', '.join(fields)}" if fields else ""
        return f"OCI DNS {operation} failed for {record_name}{suffix}"
