"""Narrow OCI DNS client for ACME TXT challenges."""

import json
from typing import Any, Protocol

from certbot import errors
from certbot.plugins import dns_common
from oci.dns.models import PatchZoneRecordsDetails, RecordOperation
from oci.exceptions import ServiceError


class DnsClientProtocol(Protocol):
    """The OCI DNS SDK methods needed by this narrow wrapper."""

    def get_zone(self, **kwargs: Any) -> Any: ...

    def patch_zone_records(self, **kwargs: Any) -> Any: ...


class OciDnsClient:
    """Perform public OCI DNS operations needed by Certbot."""

    def __init__(self, client: DnsClientProtocol) -> None:
        self._client = client

    def find_zone(self, validation_name: str) -> str:
        """Return the most-specific public OCI zone for a validation name."""
        for candidate in dns_common.base_domain_name_guesses(validation_name):
            try:
                self._client.get_zone(zone_name_or_id=candidate, scope="GLOBAL")
                return candidate
            except ServiceError as exc:
                if exc.status == 404:
                    continue
                plugin_error = self._plugin_error("zone lookup", validation_name, exc)
            except Exception:
                plugin_error = errors.PluginError(
                    f"OCI DNS zone lookup failed for {validation_name}."
                )
            raise plugin_error from None
        raise errors.PluginError(f"Unable to find a public OCI DNS zone for {validation_name}.")

    def add_txt_record(self, validation_name: str, validation: str, ttl: int) -> None:
        """Add exactly one ACME TXT value."""
        operation = RecordOperation(
            domain=validation_name,
            rtype="TXT",
            rdata=json.dumps(validation),
            ttl=ttl,
            operation="ADD",
        )
        self._patch(validation_name, operation, "record add")

    def remove_txt_record(self, validation_name: str, validation: str) -> None:
        """Remove exactly one ACME TXT value."""
        operation = RecordOperation(
            domain=validation_name,
            rtype="TXT",
            rdata=json.dumps(validation),
            operation="REMOVE",
        )
        self._patch(validation_name, operation, "record remove")

    def _patch(
        self, validation_name: str, operation: Any, operation_name: str
    ) -> None:
        zone = self.find_zone(validation_name)
        details = PatchZoneRecordsDetails(items=[operation])
        try:
            self._client.patch_zone_records(
                zone_name_or_id=zone,
                patch_zone_records_details=details,
                scope="GLOBAL",
            )
        except ServiceError as exc:
            plugin_error = self._plugin_error(
                operation_name, validation_name, exc, include_message=False
            )
        except Exception:
            plugin_error = errors.PluginError(
                f"OCI DNS {operation_name} failed for {validation_name}."
            )
        else:
            return
        raise plugin_error from None

    @staticmethod
    def _plugin_error(
        operation: str,
        record_name: str,
        exc: Any,
        *,
        include_message: bool = True,
    ) -> errors.PluginError:
        fields = [f"status={exc.status}"]
        if exc.code:
            fields.append(f"code={exc.code}")
        if include_message and exc.message:
            fields.append(f"message={exc.message}")
        return errors.PluginError(
            f"OCI DNS {operation} failed for {record_name}: {', '.join(fields)}"
        )
