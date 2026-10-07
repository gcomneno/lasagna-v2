import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS = ROOT / "docs" / "production-operations.md"
README = ROOT / "README.md"
READINESS = ROOT / "docs" / "production-readiness.md"


def test_operations_guide_covers_required_topics() -> None:
    text = OPERATIONS.read_text(encoding="utf-8")

    required_headings = (
        "## Supported input and numeric domain",
        "## Runtime and CI qualification",
        "## Lossy semantics",
        "## Error and quality controls",
        "## Wire versions",
        "## Compatibility and deprecation",
        "## Python API",
        "## CLI",
        "## Failure modes",
        "## Malformed input and security limitations",
        "## Resource limits",
        "## Performance expectations",
        "## Operational observability",
        "## Migration guidance",
        "## Known non-goals and unsupported capabilities",
        "## Operator checklist",
        "## Authority map",
        "## Production-readiness boundary",
    )

    for heading in required_headings:
        assert heading in text


def test_operations_guide_links_authoritative_contracts() -> None:
    text = OPERATIONS.read_text(encoding="utf-8")

    required = (
        "docs/production-readiness.md",
        "docs/public-api-contract.md",
        "docs/release-versioning-policy.md",
        "docs/resource-limits.md",
        "docs/security-review.md",
        "docs/performance-benchmark.md",
        "docs/large-file-qualification.md",
        "docs/external-qualification.md",
    )

    for reference in required:
        assert reference in text


def test_operations_guide_documents_qualified_numeric_domain() -> None:
    text = OPERATIONS.read_text(encoding="utf-8")

    assert "finite real-valued Python int/float values" in text
    assert "signed int32" in text
    assert "docs/public-api-contract.md" in text
    assert "Historical decoder compatibility" in text


def test_operations_guide_keeps_experimental_boundary() -> None:
    text = OPERATIONS.read_text(encoding="utf-8").lower()

    assert "continues to identify itself as experimental" in text
    assert "does not by itself make lasagna production-ready" in text


def test_readme_points_to_operations_guide_and_has_no_stale_claims() -> None:
    text = README.read_text(encoding="utf-8")

    assert "docs/production-operations.md" in text
    assert "42 passing tests" not in text
    assert "synthetic canonical validation corpus;" not in text
    assert "no stability guarantee for future protocol revisions;" not in text


def test_final_audit_statuses_after_ci_and_numeric_qualification() -> None:
    text = READINESS.read_text(encoding="utf-8")

    assert re.search(
        r"(?m)^\s*12\s+documentation completeness\s+PASS\s*$",
        text,
    )

    assert re.search(
        r"(?m)^\s*14\s+regression/CI reliability\s+PASS\s*$",
        text,
    )

    assert re.search(
        r"(?m)^\s*17\s+supported numeric domain\s+PASS\s*$",
        text,
    )

    assert re.search(
        r"(?m)^\s*18\s+operational observability\s+PASS\s*$",
        text,
    )

    assert re.search(
        r"Current mandatory PASS count:\s*" r"\n\s*```text\s*\n17\s*\n```",
        text,
    )
