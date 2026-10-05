from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    download_url: str
    outer_sha256: str
    source_member: str
    nested_sha256: str | None
    value_column: str
    source_rows: int
    source_missing: int
    expected_samples: int
    missing_policy: str
    canonical_file: str
    canonical_sha256: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(path: Path) -> list[DatasetSpec]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as stream:
        reader = csv.DictReader(
            stream,
            delimiter="\t",
        )

        rows = list(reader)

    specs: list[DatasetSpec] = []

    for row in rows:
        specs.append(
            DatasetSpec(
                dataset_id=row["dataset_id"],
                download_url=row["download_url"],
                outer_sha256=row["outer_sha256"],
                source_member=row["source_member"],
                nested_sha256=(
                    None
                    if row["nested_sha256"] == "-"
                    else row["nested_sha256"]
                ),
                value_column=row["value_column"],
                source_rows=int(row["source_rows"]),
                source_missing=int(row["source_missing"]),
                expected_samples=int(row["expected_samples"]),
                missing_policy=row["missing_policy"],
                canonical_file=row["canonical_file"],
                canonical_sha256=row["canonical_sha256"],
            )
        )

    return specs


def download_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def require_sha256(
    data: bytes,
    expected: str,
    label: str,
) -> None:
    actual = sha256_bytes(data)

    if actual != expected:
        raise ValueError(
            f"{label} SHA256 mismatch: "
            f"expected={expected} actual={actual}"
        )


def read_csv_rows(
    raw: io.BufferedIOBase,
) -> list[dict[str, str]]:
    text = io.TextIOWrapper(
        raw,
        encoding="utf-8",
        newline="",
    )

    reader = csv.DictReader(text)

    if reader.fieldnames is None:
        raise ValueError("CSV has no header")

    return list(reader)


def extract_rows(
    spec: DatasetSpec,
    outer_bytes: bytes,
) -> list[dict[str, str]]:
    with zipfile.ZipFile(
        io.BytesIO(outer_bytes)
    ) as outer:
        if spec.nested_sha256 is None:
            member_bytes = outer.read(
                spec.source_member
            )

            if spec.source_member.endswith(".gz"):
                with gzip.GzipFile(
                    fileobj=io.BytesIO(member_bytes)
                ) as raw:
                    return read_csv_rows(raw)

            return read_csv_rows(
                io.BytesIO(member_bytes)
            )

        nested_name = (
            "PRSA2017_Data_20130301-20170228.zip"
        )
        nested_bytes = outer.read(nested_name)

        require_sha256(
            nested_bytes,
            spec.nested_sha256,
            f"{spec.dataset_id} nested archive",
        )

        with zipfile.ZipFile(
            io.BytesIO(nested_bytes)
        ) as nested:
            member_bytes = nested.read(
                spec.source_member
            )

        return read_csv_rows(
            io.BytesIO(member_bytes)
        )


def canonical_values(
    spec: DatasetSpec,
    rows: Iterable[dict[str, str]],
) -> list[str]:
    rows = list(rows)

    if len(rows) != spec.source_rows:
        raise ValueError(
            f"{spec.dataset_id} source row mismatch: "
            f"expected={spec.source_rows} actual={len(rows)}"
        )

    values: list[str] = []
    missing = 0

    for row in rows:
        if spec.value_column not in row:
            raise ValueError(
                f"{spec.dataset_id} missing column "
                f"{spec.value_column!r}"
            )

        raw = row[spec.value_column].strip()

        is_missing = (
            not raw
            or raw.upper() == "NA"
        )

        if is_missing:
            missing += 1

            if spec.missing_policy.startswith(
                "drop rows"
            ):
                continue

            raise ValueError(
                f"{spec.dataset_id} unexpected missing value"
            )

        value = float(raw)

        values.append(format(value, ".17g"))

    if missing != spec.source_missing:
        raise ValueError(
            f"{spec.dataset_id} missing-count mismatch: "
            f"expected={spec.source_missing} actual={missing}"
        )

    if len(values) != spec.expected_samples:
        raise ValueError(
            f"{spec.dataset_id} sample-count mismatch: "
            f"expected={spec.expected_samples} actual={len(values)}"
        )

    return values


def write_canonical(
    path: Path,
    values: list[str],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        "".join(f"{value}\n" for value in values),
        encoding="utf-8",
        newline="\n",
    )


def prepare_dataset(
    spec: DatasetSpec,
    source_dir: Path,
    output_dir: Path,
) -> Path:
    archive_path = (
        source_dir
        / f"{spec.dataset_id}.zip"
    )

    if archive_path.exists():
        outer_bytes = archive_path.read_bytes()
    else:
        outer_bytes = download_bytes(
            spec.download_url
        )
        archive_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        archive_path.write_bytes(
            outer_bytes
        )

    require_sha256(
        outer_bytes,
        spec.outer_sha256,
        f"{spec.dataset_id} outer archive",
    )

    rows = extract_rows(
        spec,
        outer_bytes,
    )

    values = canonical_values(
        spec,
        rows,
    )

    output_path = (
        output_dir
        / spec.canonical_file
    )

    write_canonical(
        output_path,
        values,
    )

    canonical_bytes = output_path.read_bytes()
    canonical_sha256 = sha256_bytes(
        canonical_bytes
    )

    if canonical_sha256 != spec.canonical_sha256:
        raise ValueError(
            f"{spec.dataset_id} canonical SHA256 mismatch: "
            f"expected={spec.canonical_sha256} "
            f"actual={canonical_sha256}"
        )

    print(
        f"DATASET={spec.dataset_id} "
        f"SAMPLES={len(values)} "
        f"SHA256={canonical_sha256} "
        f"OUTPUT={output_path}"
    )

    return output_path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the frozen Lasagna 2 real-world "
            "validation corpus."
        )
    )

    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "data/real-world/manifest.tsv"
        ),
    )

    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "data/real-world/canonical"
        ),
    )

    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    specs = load_manifest(
        args.manifest
    )

    for spec in specs:
        prepare_dataset(
            spec,
            args.source_dir,
            args.output_dir,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
