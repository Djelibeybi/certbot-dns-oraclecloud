"""Tests for installed distribution metadata and Certbot discovery."""

from importlib.metadata import entry_points, version

from certbot_dns_oraclecloud._internal.dns_oraclecloud import Authenticator


def test_distribution_version() -> None:
    assert version("certbot-dns-oraclecloud") == "0.1.0"


def test_certbot_entry_point_is_registered() -> None:
    """The distribution advertises the authenticator at Certbot's public entry point."""
    plugins = {entry.name: entry for entry in entry_points(group="certbot.plugins")}

    assert plugins["dns-oraclecloud"].value == (
        "certbot_dns_oraclecloud._internal.dns_oraclecloud:Authenticator"
    )


def test_certbot_entry_point_loads_authenticator() -> None:
    """Certbot can import the published authenticator without package-local setup."""
    plugin = next(
        entry for entry in entry_points(group="certbot.plugins") if entry.name == "dns-oraclecloud"
    )

    assert plugin.load() is Authenticator
