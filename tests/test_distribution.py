from importlib.metadata import version


def test_distribution_version() -> None:
    assert version("certbot-dns-oraclecloud") == "0.1.0"
