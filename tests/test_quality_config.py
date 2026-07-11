"""Contracts for the repository-wide Python quality gate."""

import ast
import importlib
import inspect
from collections.abc import Iterator
from pathlib import Path

import tomli

from certbot_dns_oraclecloud._internal import auth, dns_client

ROOT = Path(__file__).resolve().parents[1]


def _production_modules() -> Iterator[Path]:
    """Yield the production modules that must not use broad handlers."""
    yield from (ROOT / "src" / "certbot_dns_oraclecloud").rglob("*.py")


def _broad_handlers(source_path: Path) -> list[int]:
    """Return line numbers for forbidden broad exception handlers."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    lines: list[int] = []
    for handler in (node for node in ast.walk(tree) if isinstance(node, ast.ExceptHandler)):
        if handler.type is None:
            lines.append(handler.lineno)
            continue
        exception_names = [node.id for node in ast.walk(handler.type) if isinstance(node, ast.Name)]
        if {"BaseException", "Exception"} & set(exception_names):
            lines.append(handler.lineno)
    return lines


def test_pyproject_declares_current_strict_tools_without_mypy() -> None:
    """The dev group has only the agreed strict Python quality tools."""
    pyproject = tomli.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["dependency-groups"]["dev"]

    assert "prek>=0.4.9" in dependencies
    assert "pyright>=1.1.411" in dependencies
    assert "ruff>=0.15.21" in dependencies
    assert all(not dependency.startswith("mypy") for dependency in dependencies)
    assert "mypy" not in pyproject.get("tool", {})


def test_ruff_and_pyright_are_strict_and_cover_source_and_tests() -> None:
    """Lint all rules while preserving only formatter-conflict global ignores."""
    pyproject = tomli.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    tool_config = pyproject["tool"]
    ruff_lint = tool_config["ruff"]["lint"]
    pyright = tool_config["pyright"]

    assert ruff_lint["select"] == ["ALL"]
    assert ruff_lint["ignore"] == ["COM812", "D203", "D213", "ISC001"]
    assert pyright["include"] == ["src", "tests"]
    assert pyright["pythonVersion"] == "3.10"
    assert pyright["typeCheckingMode"] == "strict"


def test_prek_is_the_all_files_quality_entry_point() -> None:
    """Prek runs hygiene, lint, format checking, and strict type checking."""
    config_path = ROOT / "prek.toml"
    config = tomli.loads(config_path.read_text(encoding="utf-8"))
    hooks = [hook for repo in config["repos"] for hook in repo["hooks"]]
    hook_ids = {hook["id"] for hook in hooks}
    entries = {hook.get("entry") for hook in hooks}

    assert {
        "trailing-whitespace",
        "end-of-file-fixer",
        "check-toml",
        "check-yaml",
        "check-json",
        "check-merge-conflict",
        "detect-private-key",
    } <= hook_ids
    quality_entries = {
        "uv run ruff check .",
        "uv run ruff format --check .",
        "uv run pyright",
    }
    assert quality_entries <= entries
    for hook in hooks:
        if hook.get("entry") in quality_entries:
            assert hook["pass_filenames"] is False


def test_production_code_has_no_broad_exception_handlers() -> None:
    """Sensitive OCI failures must be translated from precise exception types."""
    violations = {
        str(path.relative_to(ROOT)): _broad_handlers(path)
        for path in _production_modules()
        if _broad_handlers(path)
    }

    assert violations == {}


def test_oci_sdk_types_are_isolated_behind_precise_protocols() -> None:
    """Application layers use the typed OCI boundary rather than ``Any``."""
    assert (ROOT / "src" / "certbot_dns_oraclecloud" / "_internal" / "protocols.py").is_file()
    protocols = importlib.import_module("certbot_dns_oraclecloud._internal.protocols")

    assert protocols.DnsClientProtocol._is_protocol
    assert protocols.ZoneProtocol._is_protocol
    assert protocols.OciPaginatedResponseProtocol._is_protocol
    assert protocols.PatchZoneRecordsResponseProtocol._is_protocol
    annotation = inspect.signature(auth.create_dns_client).return_annotation
    assert annotation is protocols.DnsClientProtocol
    assert "Any" not in inspect.getsource(auth)
    assert "Any" not in inspect.getsource(dns_client)


def test_python314_wheel_verification_is_project_owned() -> None:
    """Python 3.14 verification avoids editable-install path injection."""
    script = (ROOT / "scripts" / "verify-python314-wheel.sh").read_text(encoding="utf-8")

    assert "uv sync --locked --no-editable --python 3.14" in script
    assert "uv build --wheel" in script
    assert "uv venv --clear --python 3.14" in script
    assert "uv pip install" in script
    assert "import certbot_dns_oraclecloud" in script
    assert "PYTHONPATH" not in script
