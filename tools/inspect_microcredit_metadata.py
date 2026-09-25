"""Extract outcome-blind labels from an authorized Meager ZIP archive.

The script reads Stata headers only (`metadataonly=True`). It never loads
individual observations and writes variable names/labels, not data values.
Requires `pyreadstat` in the local analysis environment.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import zipfile
from pathlib import Path

import pyreadstat


FILES = {
    "angelucci_2015": "data/microcredit-rct-data/angelucci_et_al_2015.dta",
    "attanasio_2015": "data/microcredit-rct-data/attanasio-et-al-2015/Analysis-files/data/attanasio_processed_for_rm_analysis.dta",
    "augsberg_2015": "data/microcredit-rct-data/augsberg-et-al-2015/Analysis-files_AEJApp-2013-0272/data/Baseline/BL---SECTION-2---Loans-cl.dta",
    "banerjee_2015": "data/microcredit-rct-data/banerjee-et-al-2015/2013-0533_data--TO-SUBMIT-/2013-0533_data_endlines1and2_stata12.dta",
    "crepon_2015": "data/microcredit-rct-data/crepon-et-al-2015/Data-Code_AEJApp_MicrocreditMorocco/Output/endline_baseline_outcomes.dta",
    "tarozzi_2015": "data/microcredit-rct-data/tarozzi-et-al-2015/TarozziEtAlReplicationFiles/data.dta",
}
NESTED_KARLAN = (
    "data/microcredit-rct-data/karlan-and-zinman-2010.zip",
    "1200138sdataset_clean.dta",
)
FIELD_RE = re.compile(
    r"(treat|assign|random|control|offer|eligib|promot|loan|credit|"
    r"baseline|follow|endline|wave|outcome|profit|revenue|income|consum|"
    r"business|collateral|interest|term|repay)",
    re.IGNORECASE,
)


def inspect_bytes(raw: bytes, study: str, path: str) -> list[dict[str, object]]:
    import tempfile

    handle = tempfile.NamedTemporaryFile(suffix=".dta", delete=False)
    try:
        handle.write(raw)
        handle.close()
        _, meta = pyreadstat.read_dta(handle.name, metadataonly=True)
    finally:
        Path(handle.name).unlink(missing_ok=True)
    labels = dict(zip(meta.column_names, meta.column_labels))
    value_labels = getattr(meta, "variable_value_labels", {}) or {}
    rows = []
    for rank, variable in enumerate(
        name for name in meta.column_names if FIELD_RE.search(name)
    ):
        rows.append(
            {
                "study_id": study,
                "archive_path": path,
                "rows": meta.number_rows,
                "columns": len(meta.column_names),
                "selection_rank": rank,
                "variable": variable,
                "variable_label": labels.get(variable, "") or "",
                "value_label_count": len(value_labels.get(variable, {}) or {}),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    records: list[dict[str, object]] = []
    with zipfile.ZipFile(args.archive) as archive:
        for study, path in FILES.items():
            records.extend(inspect_bytes(archive.read(path), study, path))
        outer, nested = NESTED_KARLAN
        with zipfile.ZipFile(io.BytesIO(archive.read(outer))) as source:
            records.extend(
                inspect_bytes(
                    source.read(nested),
                    "karlan_zinman_2011",
                    f"{outer}!{nested}",
                )
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "study_id",
        "archive_path",
        "rows",
        "columns",
        "selection_rank",
        "variable",
        "variable_label",
        "value_label_count",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"wrote {len(records)} metadata records to {args.output}")


if __name__ == "__main__":
    main()
