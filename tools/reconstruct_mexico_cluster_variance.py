"""Reconstruct the Mexico profit coefficient and cluster-robust SE locally.

The authorized OpenICPSR ZIP is supplied by the user and is never copied into
the repository. The script reads the nested Angelucci analysis file in memory
and writes only aggregate coefficient/SE metadata. The regression specification
matches the published Stata file:
``Compartamos-AEJ-tables-2-8.do`` lines 3, 5, and 31--33.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat


DATA_SUFFIX = "analysis_data_AEJ_pub.dta"
MODEL_SOURCE = (
    "data/microcredit-rct-data/angelucci-et-al-2015/Compartamos_AEJ/"
    "Main/Compartamos-AEJ-tables-2-8.do:3,5,31-33"
)
CONVERSION = (1.0 / 9.18) * (100.0 / 106.121)


def _cluster_covariance(x: np.ndarray, y: np.ndarray, clusters: np.ndarray) -> tuple[np.ndarray, int]:
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    bread = np.linalg.inv(x.T @ x)
    meat = np.zeros((x.shape[1], x.shape[1]))
    unique = np.unique(clusters)
    for group in unique:
        mask = clusters == group
        score = x[mask].T @ residual[mask]
        meat += np.outer(score, score)
    n, k, g = len(y), x.shape[1], len(unique)
    correction = (g / (g - 1.0)) * ((n - 1.0) / (n - k))
    return correction * (bread @ meat @ bread), int(g)


def reconstruct(archive: Path) -> dict[str, object]:
    archive_bytes = archive.read_bytes()
    archive_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as package:
        candidates = [name for name in package.namelist() if name.endswith(DATA_SUFFIX)]
        if len(candidates) != 1:
            raise ValueError(f"expected one {DATA_SUFFIX}, found {candidates}")
        data_name = candidates[0]
        data, _ = pyreadstat.read_dta(io.BytesIO(package.read(data_name)), apply_value_formats=False)

    endline = data.loc[data["survey"] == "Endline"].copy()
    columns = [
        "Q10_9_toprof", "Treatment", "BE_Q10_9_toprof",
        "BE_Q10_9_toprof_mdum", "InPanel", "cluster", "supercluster_xi",
    ]
    sample = endline[columns].dropna().copy()
    fixed_effects = pd.get_dummies(
        sample["supercluster_xi"].astype(str), drop_first=True, dtype=float
    )
    design = pd.concat(
        [
            pd.Series(1.0, index=sample.index, name="_cons"),
            sample[["Treatment", "BE_Q10_9_toprof", "BE_Q10_9_toprof_mdum", "InPanel"]].astype(float),
            fixed_effects,
        ],
        axis=1,
    ).to_numpy(float)
    outcome = sample["Q10_9_toprof"].to_numpy(float)
    covariance, n_clusters = _cluster_covariance(
        design, outcome, sample["cluster"].to_numpy()
    )
    beta = np.linalg.lstsq(design, outcome, rcond=None)[0]
    treatment_index = 1
    coefficient = float(beta[treatment_index])
    se = float(np.sqrt(covariance[treatment_index, treatment_index]))
    return {
        "archive_sha256": archive_sha256,
        "archive_bytes": len(archive_bytes),
        "data_path": data_name,
        "model_source": MODEL_SOURCE,
        "outcome": "Q10_9_toprof",
        "assignment": "Treatment",
        "cluster": "cluster",
        "sample_filter": "survey == Endline; complete model-case rows",
        "n_observations": int(len(outcome)),
        "n_clusters": n_clusters,
        "n_regressors": int(design.shape[1]),
        "coefficient_local_currency_per_fortnight": coefficient,
        "cluster_robust_se_local_currency_per_fortnight": se,
        "conversion_to_usd_ppp_per_fortnight": CONVERSION,
        "coefficient_usd_ppp_per_fortnight": coefficient * CONVERSION,
        "se_usd_ppp_per_fortnight": se * CONVERSION,
        "python": platform.python_version(),
        "raw_records_committed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = reconstruct(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
