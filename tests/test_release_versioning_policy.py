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
