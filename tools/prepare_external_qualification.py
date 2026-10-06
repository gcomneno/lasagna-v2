from __future__ import annotations

import argparse
import csv
import hashlib
import io
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DatasetSpec:
    qualification_id: str
    dataset_id: str
    download_url: str
    archive_sha256: str
    source_member: str
    member_sha256: str
    encoding: str
    source_rows: int
    selected_entity: str
    selected_field: str
    selected_rows: int
    missing_selected: int
    expected_samples: int


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_manifest(path: Path) -> list[DatasetSpec]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as stream:
        rows = list(
            csv.DictReader(
                stream,
                delimiter="\t",
            )
        )

    return [
        DatasetSpec(
            qualification_id=row["qualification_id"],
            dataset_id=row["dataset_id"],
            download_url=row["download_url"],
            archive_sha256=row["archive_sha256"],
            source_member=row["source_member"],
            member_sha256=row["member_sha256"],
            encoding=row["encoding"],
            source_rows=int(row["source_rows"]),
            selected_entity=row["selected_entity"],
            selected_field=row["selected_field"],
            selected_rows=int(row["selected_rows"]),
            missing_selected=int(row["missing_selected"]),
            expected_samples=int(row["expected_samples"]),
        )
        for row in rows
    ]


def require_hash(
    data: bytes,
    expected: str,
    label: str,
) -> None:
    actual = sha256_bytes(data)

    if actual != expected:
        raise ValueError(
            f"{label} SHA256 mismatch: " f"expected={expected} actual={actual}"
        )


def acquire_archive(
    spec: DatasetSpec,
    source_dir: Path,
) -> bytes:
    path = source_dir / (f"{spec.qualification_id}-" f"{spec.dataset_id}.zip")

    if path.exists():
        data = path.read_bytes()
    else:
        request = urllib.request.Request(
            spec.download_url,
            headers={"User-Agent": "lasagna-v2-external-qualification/0.3.0"},
        )

        with urllib.request.urlopen(
            request,
            timeout=120,
        ) as response:
            data = response.read()

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(data)

    require_hash(
        data,
        spec.archive_sha256,
        f"{spec.dataset_id} archive",
    )

    return data


def extract_rows(
    spec: DatasetSpec,
    archive_bytes: bytes,
) -> list[dict[str, str]]:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        member_bytes = archive.read(spec.source_member)

    require_hash(
        member_bytes,
        spec.member_sha256,
        f"{spec.dataset_id} member",
    )

    text = member_bytes.decode(spec.encoding)

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise ValueError(f"{spec.dataset_id}: no CSV header")

    rows = list(reader)

    if len(rows) != spec.source_rows:
        raise ValueError(
            f"{spec.dataset_id}: source row mismatch "
            f"expected={spec.source_rows} "
            f"actual={len(rows)}"
        )

    if spec.selected_field not in reader.fieldnames:
        raise ValueError(
            f"{spec.dataset_id}: missing field " f"{spec.selected_field!r}"
        )

    return rows


def select_rows(
    spec: DatasetSpec,
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    if spec.dataset_id != ("dow-jones-weekly-return"):
        selected = rows
    else:
        selected = [row for row in rows if row["stock"].strip() == spec.selected_entity]

        dates = []

        for row in selected:
            month, day, year = (int(part) for part in row["date"].strip().split("/"))

            dates.append(
                (
                    year,
                    month,
                    day,
                )
            )

        if len(dates) != len(set(dates)):
            raise ValueError("Dow Jones selected entity " "contains duplicate dates")

        selected = [
            row
            for _, row in sorted(
                zip(
                    dates,
                    selected,
                    strict=True,
                ),
                key=lambda pair: pair[0],
            )
        ]

    if len(selected) != spec.selected_rows:
        raise ValueError(
            f"{spec.dataset_id}: selected row mismatch "
            f"expected={spec.selected_rows} "
            f"actual={len(selected)}"
        )

    return selected


def canonical_values(
    spec: DatasetSpec,
    rows: list[dict[str, str]],
) -> list[str]:
    values: list[str] = []
    missing = 0

    for row in rows:
        raw = row[spec.selected_field].strip()

        if not raw or raw.upper() in {
            "NA",
            "NAN",
            "NULL",
        }:
            missing += 1
            continue

        value = float(raw)
        values.append(format(value, ".17g"))

    if missing != spec.missing_selected:
        raise ValueError(
            f"{spec.dataset_id}: missing count mismatch "
            f"expected={spec.missing_selected} "
            f"actual={missing}"
        )

    if len(values) != spec.expected_samples:
        raise ValueError(
            f"{spec.dataset_id}: sample mismatch "
            f"expected={spec.expected_samples} "
            f"actual={len(values)}"
        )

    return values


def write_canonical(
    spec: DatasetSpec,
    values: list[str],
    output_dir: Path,
) -> tuple[Path, str]:
    path = output_dir / (f"{spec.dataset_id}.csv")

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        "".join(f"{value}\n" for value in values),
        encoding="utf-8",
        newline="\n",
    )

    digest = sha256_bytes(path.read_bytes())

    return path, digest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/external-qualification/" "acquisition.tsv"),
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data/external-qualification/source"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/external-qualification/canonical"),
    )

    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    for spec in load_manifest(args.manifest):
        archive_bytes = acquire_archive(
            spec,
            args.source_dir,
        )

        rows = extract_rows(
            spec,
            archive_bytes,
        )

        selected = select_rows(
            spec,
            rows,
        )

        values = canonical_values(
            spec,
            selected,
        )

        path, digest = write_canonical(
            spec,
            values,
            args.output_dir,
        )

        print(
            f"QUALIFICATION_ID="
            f"{spec.qualification_id} "
            f"DATASET={spec.dataset_id} "
            f"SAMPLES={len(values)} "
            f"SHA256={digest} "
            f"OUTPUT={path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
