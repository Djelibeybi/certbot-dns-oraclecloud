"""Contracts for the repository-wide Python quality gate."""

import ast
import importlib
import inspect
import re
from collections.abc import Iterator
from pathlib import Path

import tomli

from certbot_dns_oraclecloud._internal import auth, dns_client

ROOT = Path(__file__).resolve().parents[1]


def _workflow_job(workflow: str, job_name: str) -> str:
    """Return one top-level GitHub Actions job definition."""
    match = re.search(
        rf"^  {re.escape(job_name)}:\n.*?(?=^  [a-z][a-z0-9_-]*:\n|\Z)",
        workflow,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, f"{job_name!r} job is missing"
    return match.group(0)


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
    """Prek runs hygiene without replacing the CI non-editable project install."""
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
        "uv run --no-sync ruff check .",
        "uv run --no-sync ruff format --check .",
        "uv run --no-sync pyright",
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
    """Python 3.14 verification is isolated from the development environment."""
    script = (ROOT / "scripts" / "verify-python314-wheel.sh").read_text(encoding="utf-8")
    cleanup = script.split("cleanup() {", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert 'temporary_root="$(mktemp -d' in script
    assert 'project_venv="$temporary_root/project-venv"' in script
    sync_command = "uv sync --locked --no-editable --python 3.14"
    assert f'UV_PROJECT_ENVIRONMENT="$project_venv" {sync_command}' in script
    assert 'UV_PROJECT_ENVIRONMENT="$project_venv" uv run --no-sync --python 3.14 pytest' in script
    assert "uv sync --locked --no-editable --python 3.14" in script
    assert "uv build --wheel" in script
    assert "uv venv --clear --python 3.14" in script
    assert "uv pip install" in script
    assert "import certbot_dns_oraclecloud" in script
    assert "PYTHONPATH" not in script
    assert "uv sync" not in cleanup
    assert 'exit "$exit_status"' in cleanup


def test_documentation_workflow_validates_pull_requests_without_deploying() -> None:
    """Documentation builds strictly on PRs but publishes only from trusted events."""
    workflow = (ROOT / ".github" / "workflows" / "docs.yml").read_text(encoding="utf-8")

    assert "  pull_request:\n" in workflow
    assert "run: uv run zensical build --clean --strict" in workflow
    assert (
        """      - name: Configure GitHub Pages
        if: github.event_name != 'pull_request'
        uses: actions/configure-pages@"""
        in workflow
    )
    assert (
        """      - name: Upload Pages artifact
        if: github.event_name != 'pull_request'
        uses: actions/upload-pages-artifact@"""
        in workflow
    )
    assert (
        """  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    needs: build
    if: github.event_name != 'pull_request'
    runs-on: ubuntu-latest"""
        in workflow
    )


def test_semantic_release_configuration_keeps_version_and_lock_in_sync() -> None:
    """PSR stamps the package version, rebuilds the lock, and writes the changelog."""
    pyproject = tomli.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["dependency-groups"]["dev"]
    semantic_release = pyproject["tool"]["semantic_release"]

    assert "python-semantic-release>=10.6.1" in dependencies
    assert semantic_release["version_toml"] == ["pyproject.toml:project.version"]
    assert 'uv lock --upgrade-package "$PACKAGE_NAME"' in semantic_release["build_command"]
    assert "git add uv.lock" in semantic_release["build_command"]
    assert "uv build" in semantic_release["build_command"]
    assert semantic_release["branches"]["main"] == {"match": "main", "prerelease": False}
    assert semantic_release["branches"]["dev"] == {
        "match": "(?!main$).*",
        "prerelease": True,
        "prerelease_token": "dev",
    }
    assert semantic_release["changelog"]["exclude_commit_patterns"] == [
        r"chore(?:\([^)]*?\))?: .+",
        r"ci(?:\([^)]*?\))?: .+",
        r"refactor(?:\([^)]*?\))?: .+",
        r"style(?:\([^)]*?\))?: .+",
        r"test(?:\([^)]*?\))?: .+",
        r"build\((?!deps\): .+)",
        r"Initial [Cc]ommit.*",
    ]
    assert semantic_release["changelog"]["default_templates"] == {
        "changelog_file": "docs/changelog.md",
        "output_format": "md",
    }
    assert semantic_release["remote"] == {"ignore_token_for_push": True}


def test_release_job_only_runs_after_main_matrix_success_and_preserves_release_assets() -> None:
    """Release has its own write scope and only follows a successful main-branch matrix."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release = _workflow_job(workflow, "release")

    assert "  push:\n    tags-ignore: ['**']\n" in workflow
    assert "  pull_request:\n" in workflow
    assert "needs: test" in release
    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in release
    assert "permissions:\n      contents: write" in release
    assert "id-token: write" not in release
    assert "env:\n      PACKAGE_NAME: certbot-dns-oraclecloud" in release
    assert "group: ${{ github.workflow }}-release-${{ github.ref_name }}" in release
    assert "cancel-in-progress: false" in release
    assert "fetch-depth: 0" in release
    assert "ssh-key: ${{ secrets.DEPLOY_KEY }}" in release
    assert 'git config --local user.email "github-actions@github.com"' in release
    assert 'git config --local user.name "GitHub Actions"' in release
    assert "git config --local commit.gpgsign false" in release
    assert "git config --local tag.gpgsign false" in release
    assert "id: release" in release
    assert "uv run --no-sync semantic-release version" in release
    assert "uv run --no-sync semantic-release publish" in release
    assert "uv run --with python-semantic-release" not in release
    assert "if: steps.release.outputs.released == 'true'" in release
    assert re.search(
        r"uses: actions/upload-artifact@[0-9a-f]{40} # v7\.0\.1",
        release,
    )
    assert "name: distribution-artifacts" in release
    assert "path: dist" in release
    assert "if-no-files-found: error" in release


def test_pypi_deploy_job_is_trusted_and_consumes_only_release_artifacts() -> None:
    """PyPI credentials are available only to the gated trusted-publishing job."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    deploy = _workflow_job(workflow, "deploy")

    assert "needs: release" in deploy
    assert "if: needs.release.outputs.released == 'true'" in deploy
    assert "permissions:\n      contents: read\n      id-token: write" in deploy
    assert (
        "environment:\n      name: pypi\n"
        "      url: https://pypi.org/p/certbot-dns-oraclecloud" in deploy
    )
    assert re.search(
        r"uses: actions/download-artifact@[0-9a-f]{40} # v8\.0\.1",
        deploy,
    )
    assert "name: distribution-artifacts" in deploy
    assert "path: dist" in deploy
    assert "test -n \"$(find dist -type f -name '*.whl' -print -quit)\"" in deploy
    assert "test -n \"$(find dist -type f -name '*.tar.gz' -print -quit)\"" in deploy
    assert re.search(
        r"uses: pypa/gh-action-pypi-publish@[0-9a-f]{40} # v1\.14\.0",
        deploy,
    )
    assert "packages-dir: dist" in deploy


def test_ci_matrix_uploads_one_coverage_report_and_per_interpreter_test_results() -> None:
    """Only 3.14 uploads aggregate coverage; every non-cancelled run uploads JUnit."""
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    test = _workflow_job(workflow, "test")
    pytest_command = (
        "uv run --no-sync pytest --cov --cov-branch --cov-report=xml "
        "--junitxml=junit.xml -o junit_family=legacy"
    )
    representative_condition = "${{ !cancelled() && matrix.python-version == '3.14' }}"

    assert pytest_command in test
    assert test.count("pytest") == 1
    assert (
        """      - uses: codecov/codecov-action@0fb7174895f61a3b6b78fc075e0cd60383518dac # v5.5.5
        if: ${{ !cancelled() && matrix.python-version == '3.14' }}
        with:
          files: coverage.xml
          token: ${{ secrets.CODECOV_TOKEN }}
          slug: Djelibeybi/certbot-dns-oraclecloud"""
        in test
    )
    assert (
        """      - name: Upload test results to Codecov
        if: ${{ !cancelled() }}
        uses: codecov/test-results-action@0fa95f0e1eeaafde2c782583b36b28ad0d8c77d3 # v1.2.1
        with:
          files: junit.xml
          token: ${{ secrets.CODECOV_TOKEN }}"""
        in test
    )
    assert representative_condition in test
