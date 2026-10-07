from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "dependency-policy.md"
PYPROJECT = ROOT / "pyproject.toml"
REQUIREMENTS_DEV = ROOT / "requirements-dev.txt"
READINESS = ROOT / "docs" / "production-readiness.md"
SECURITY = ROOT / "docs" / "security-review.md"
WORKFLOWS = ROOT / ".github" / "workflows"


def _requirement_name(specifier: str) -> str:
    return re.split(r"[<>=!~]", specifier, maxsplit=1)[0].strip().lower()


def test_runtime_dependency_set_is_empty() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    assert data["project"]["dependencies"] == []


def test_dependency_policy_records_current_constraint_strategy() -> None:
    text = POLICY.read_text(encoding="utf-8")

    required = (
        "project runtime dependencies = none",
        "setuptools>=61.0",
        "gorillacompression==1.0.2",
        "Minimum constraints are intentionally accepted",
        "exact pin where required",
        "pypa/gh-action-pip-audit@v1.1.0",
        "PRODUCTION_READINESS_GATE_16=PASS",
    )

    for value in required:
        assert value in text


def test_requirements_dev_matches_core_dev_constraints() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    pyproject_dev = data["project"]["optional-dependencies"]["dev"]

    requirements = [
        line.strip()
        for line in REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    requirements_by_name = {_requirement_name(item): item for item in requirements}

    for item in pyproject_dev:
        name = _requirement_name(item)

        assert name in requirements_by_name
        assert requirements_by_name[name] == item


def test_requirements_dev_extra_entries_are_documented_tooling() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    dev_names = {
        _requirement_name(item)
        for item in data["project"]["optional-dependencies"]["dev"]
    }

    requirements = [
        line.strip()
        for line in REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    extra_names = {_requirement_name(item) for item in requirements} - dev_names

    assert extra_names == {
        "matplotlib",
        "pandas",
    }

    policy = POLICY.read_text(encoding="utf-8")

    assert "pandas" in policy
    assert "matplotlib" in policy


def test_gorilla_reproducibility_pin_is_exact_and_consistent() -> None:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    dev = data["project"]["optional-dependencies"]["dev"]
    benchmark = data["project"]["optional-dependencies"]["benchmark"]

    assert "gorillacompression==1.0.2" in dev
    assert benchmark == [
        "gorillacompression==1.0.2",
    ]

    assert "gorillacompression==1.0.2" in REQUIREMENTS_DEV.read_text(encoding="utf-8")


def test_action_reference_policy_matches_current_workflows() -> None:
    action_pattern = re.compile(
        r"^\s*uses:\s*([^@\s]+)@([^\s#]+)",
    )

    mutable = []

    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = action_pattern.match(line)

            if not match:
                continue

            action, ref = match.groups()

            if not re.fullmatch(
                r"[0-9a-fA-F]{40}",
                ref,
            ):
                mutable.append(f"{action}@{ref}")

    assert mutable == [
        "pypa/gh-action-pip-audit@v1.1.0",
    ]

    policy = POLICY.read_text(encoding="utf-8")

    assert mutable[0] in policy
    assert "accepted residual supply-chain risk" in policy


def test_gate_16_is_pass_in_final_production_ready_state() -> None:
    text = READINESS.read_text(encoding="utf-8")

    assert "16 dependency policy            PASS" in text
    assert "Current mandatory PASS count:\n\n```text\n18\n```" in text
    assert (
        "all mandatory gates are PASS; final aggregate audit completed with no blockers"
        in text
    )
    assert "PRODUCTION_READY_GATE=PASS" in text
    assert "ISSUE_12_CLOSE_GATE=PASS" in text


def test_security_review_points_to_dependency_policy() -> None:
    text = SECURITY.read_text(encoding="utf-8")

    assert "docs/dependency-policy.md" in text
    assert "pypa/gh-action-pip-audit@v1.1.0" in text
    assert "residual supply-chain risk" in text
