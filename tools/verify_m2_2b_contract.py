#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import re


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "rate-distortion-design.md"
MANIFEST = ROOT / "docs" / "m2-2b-anchors.tsv"

HASH_RE = re.compile(r"EXPECTED_M2_2B_ANCHOR_MANIFEST_SHA256 = ([0-9a-f]{64})")


def main() -> int:
    if not DOC.is_file():
        print("CLASSIFICATION=HARNESS_INVALID")
        print("DOCUMENT_GATE=FAIL")
        return 2

    if not MANIFEST.is_file():
        print("CLASSIFICATION=HARNESS_INVALID")
        print("MANIFEST_GATE=FAIL")
        return 2

    doc = DOC.read_text(encoding="utf-8")
    manifest_bytes = MANIFEST.read_bytes()

    matches = HASH_RE.findall(doc)

    if len(matches) != 1:
        print("CLASSIFICATION=CONTRACT_INCOMPLETE")
        print("EXPECTED_MANIFEST_HASH_DECLARATION_GATE=FAIL")
        return 3

    expected_sha = matches[0]
    actual_sha = hashlib.sha256(manifest_bytes).hexdigest()

    print(f"EXPECTED_MANIFEST_SHA256={expected_sha}")
    print(f"ACTUAL_MANIFEST_SHA256={actual_sha}")

    if actual_sha != expected_sha:
        print("CLASSIFICATION=HARNESS_INVALID")
        print("MANIFEST_HASH_GATE=FAIL")
        return 4

    print("MANIFEST_HASH_GATE=PASS")

    anchors: list[tuple[str, str]] = []
    seen_ids: set[str] = set()

    try:
        text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError:
        print("CLASSIFICATION=HARNESS_INVALID")
        print("MANIFEST_UTF8_GATE=FAIL")
        return 5

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line or raw_line.startswith("#"):
            continue

        if "\t" not in raw_line:
            print(f"MALFORMED_LINE={lineno}")
            print("CLASSIFICATION=HARNESS_INVALID")
            print("MANIFEST_SCHEMA_GATE=FAIL")
            return 5

        anchor_id, phrase = raw_line.split("\t", 1)

        if not anchor_id or not phrase or anchor_id in seen_ids or "\t" in phrase:
            print(f"MALFORMED_LINE={lineno}")
            print("CLASSIFICATION=HARNESS_INVALID")
            print("MANIFEST_SCHEMA_GATE=FAIL")
            return 5

        seen_ids.add(anchor_id)
        anchors.append((anchor_id, phrase))

    if not anchors:
        print("CLASSIFICATION=HARNESS_INVALID")
        print("MANIFEST_SCHEMA_GATE=FAIL")
        return 5

    print(f"ANCHOR_COUNT={len(anchors)}")
    print("MANIFEST_SCHEMA_GATE=PASS")

    for anchor_id, phrase in anchors:
        count = doc.count(phrase)

        if count == 0:
            print(f"MISSING_ANCHOR={anchor_id}")
            print("CLASSIFICATION=CONTRACT_INCOMPLETE")
            print("CANONICAL_ANCHOR_GATE=FAIL")
            return 6

        if count != 1:
            print(f"AMBIGUOUS_ANCHOR={anchor_id}")
            print(f"OCCURRENCES={count}")
            print("CLASSIFICATION=CONTRACT_INCOMPLETE")
            print("CANONICAL_ANCHOR_GATE=FAIL")
            return 6

    print("CANONICAL_ANCHOR_GATE=PASS")
    print("CLASSIFICATION=VALID")
    print("M2_2B_CONTRACT_VERIFIER_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
