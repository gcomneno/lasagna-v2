from __future__ import annotations

from pathlib import Path

from lasagna2 import core

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "release-versioning-policy.md"
PRODUCTION = ROOT / "docs" / "production-readiness.md"
PYPROJECT = ROOT / "pyproject.toml"


def test_current_wire_constants_remain_v1_v2() -> None:
    assert core.FORMAT_VERSION_V1 == 1
    assert core.FORMAT_VERSION_V2 == 2


def test_release_policy_records_current_compatibility() -> None:
    text = POLICY.read_text(encoding="utf-8")

    required = (
        "V1 decode = SUPPORTED",
        "V2 decode = SUPPORTED",
        "default encode = V2",
        "Neither V1 nor V2 currently has a removal schedule.",
        "NEW DEFAULT != OLD DECODER REMOVAL",
        "V2 incompatible change -> V3 or later",
    )

    for value in required:
        assert value in text


def test_release_policy_freezes_required_gates() -> None:
    text = POLICY.read_text(encoding="utf-8")

    required = (
        "SEMANTIC_VERSION_POLICY_GATE=PASS",
        "WIRE_VERSION_POLICY_GATE=PASS",
        "PACKAGE_WIRE_SEPARATION_GATE=PASS",
        "DECODE_SUPPORT_LIFETIME_GATE=PASS",
        "V3_MIGRATION_GATE=PASS",
        "TAG_IMMUTABILITY_GATE=PASS",
        "RELEASE_ARTIFACT_POLICY_GATE=PASS",
        "CHANGELOG_POLICY_GATE=PASS",
        "COMPATIBILITY_DECLARATION_GATE=PASS",
        "SECURITY_FIX_RELEASE_GATE=PASS",
        "PRODUCTION_READINESS_GATE_1=PASS",
        "PRODUCTION_READINESS_GATE_2=PASS",
        "PRODUCTION_READINESS_GATE_9=PASS",
    )

    for value in required:
        assert value in text


def test_current_package_version_is_0_3_0() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")

    assert 'version = "0.3.0"' in text


def test_production_tracker_references_release_policy() -> None:
    text = PRODUCTION.read_text(encoding="utf-8")

    assert "docs/release-versioning-policy.md" in text


CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_production_runtime_matrix_is_frozen_and_matches_ci() -> None:
    policy = POLICY.read_text(encoding="utf-8")
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    pyproject = PYPROJECT.read_text(encoding="utf-8")

    assert "production-qualified Python   = 3.12" in policy
    assert "production-qualified platform = Ubuntu 24.04" in policy
    assert (
        "PACKAGE INSTALLABILITY RANGE != PRODUCTION-QUALIFIED RUNTIME MATRIX" in policy
    )

    assert 'requires-python = ">=3.10"' in pyproject
    assert "runs-on: ubuntu-24.04" in workflow
    assert 'python-version: "3.12"' in workflow
    assert "name: Lint & Test" in workflow


def test_release_policy_makes_ci_result_release_blocking() -> None:
    text = POLICY.read_text(encoding="utf-8")

    required = (
        "release-blocking job          = CI / Lint & Test",
        "exact commit intended for release",
        "failure",
        "cancelled",
        "skipped",
        "missing / not run for the release commit",
        "still pending",
        "does not substitute for the required GitHub CI result",
    )

    for value in required:
        assert value in text


def test_gate_14_is_pass_after_runtime_and_ci_policy_freeze() -> None:
    text = PRODUCTION.read_text(encoding="utf-8")

    assert "14 regression/CI reliability    PASS" in text
    assert "Python 3.12" in text
    assert "Ubuntu 24.04" in text
    assert "required workflow/job = CI / Lint & Test" in text
