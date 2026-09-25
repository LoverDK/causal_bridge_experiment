# Meager OpenICPSR package inventory

Date: 2026-09-25

This is a metadata-only inventory of the locally downloaded OpenICPSR version
`10.3886/E116357V1`. The raw archive is not copied into this repository.

## Download identity

| Item | Value |
|---|---|
| Local file | `C:\Users\Qiutian\Downloads\116357-V1.zip` |
| Archive SHA-256 | `1EC66E45ED401C7CC476548B0AE77DF0AF765942D7D8914202797D6FA4C61BFE` |
| Compressed size | 95,043,384 bytes |
| Files in archive | 306 regular files, 54 directory entries |
| Uncompressed file bytes | 513,106,670 bytes |
| Version | OpenICPSR V1, DOI `10.3886/E116357V1` |

The counts and hash were computed locally from the downloaded archive. They are
not claims that every file is independently licensed for redistribution.

## Package contents

| File type | Count | Interpretation |
|---|---:|---|
| `.dta` | 95 | Stata data files, including baseline, follow-up, cleaned and study-specific files |
| `.RData` | 1 | `data/microcredit_project_data.RData`, the cleaned project object used by the R/Stan scripts |
| `.zip` | 12 | Original or study-level source packages retained inside the project archive |
| `.R` | 20 | Import, replication, analysis and graphics scripts |
| `.stan` | 20 | Stan model files |
| `.pdf` | 18 | Papers, readmes and survey/materials PDFs |
| `.do` | 36 | Stata analysis and cleaning scripts |

The archive also contains code support files, tables, survey material, text
readmes and a root `LICENSE.txt`.

## Seven study units

The official supplement identifies the seven study units as Mexico, Mongolia,
Bosnia, India, Morocco, the Philippines and Ethiopia. The downloaded package
contains corresponding study directories or source packages:

| Study | Package evidence | Initial use status |
|---|---|---|
| Angelucci et al. (2015), Mexico | `angelucci-et-al-2015/` and `angelucci_et_al_2015.dta` | Candidate for outcome-blind design/data inventory; estimand still needs coding |
| Attanasio et al. (2015), Mongolia | `attanasio-et-al-2015/` with baseline/follow-up `.dta` files | Candidate; estimand and horizon still need coding |
| Augsburg et al. (2015), Bosnia | `augsberg-et-al-2015/` with baseline `.dta` files and source ZIPs | Candidate; estimand and horizon still need coding |
| Banerjee et al. (2015), India | `banerjee-et-al-2015/` with baseline, census and endline `.dta` files | Candidate; estimand and horizon still need coding |
| Crépon et al. (2015), Morocco | `crepon-et-al-2015/` with anonymized baseline/endline `.dta` files and survey instruments | Candidate; estimand and horizon still need coding |
| Karlan and Zinman (2011), Philippines | `karlan-and-zinman-2010.zip` and related paper/code files | Candidate source package; unpacked variables and access terms still need coding |
| Tarozzi et al. (2015), Ethiopia | `tarozzi-et-al-2015/` with `data.dta` and `data_stata12.dta` | Candidate; estimand and horizon still need coding |

For auditability, the archive entries under `data/microcredit-rct-data/` group as
follows. The counts include code and PDFs inside each study path, so they are
inventory counts rather than counts of independent datasets.

| Study path | Files | `.dta` | Nested `.zip` | Uncompressed bytes |
|---|---:|---:|---:|---:|
| Angelucci / Mexico | 80 | 2 | 2 | 17,769,975 |
| Attanasio / Mongolia | 98 | 59 | 1 | 82,115,921 |
| Augsburg / Bosnia | 22 | 16 | 3 | 14,139,361 |
| Banerjee / India | 11 | 5 | 1 | 11,299,277 |
| Crépon / Morocco | 32 | 11 | 1 | 351,158,219 |
| Karlan--Zinman / Philippines | 4 | 0 | 1 | 1,281,097 |
| Tarozzi / Ethiopia | 6 | 2 | 1 | 27,544,313 |

These per-path counts were computed from the ZIP central directory and do not
open or publish individual observations.

The package `data/README.md` states that the cleaned project data were compiled
from seven online datasets and that the supplied input does not import every
variable available in the original data. This supports a feasibility inventory,
but it does not by itself establish a complete implementation-mechanism
archive or a common causal estimand.

## License and governance status

The root `LICENSE.txt` states that code is under a Modified BSD license and
databases, images, tables and text are under CC BY 4.0, with American Economic
Association copyright attribution. We will preserve attribution and the
license text in any permitted derived release.

This package-level license does not settle every upstream restriction on the
original trial files, participant confidentiality, consent, or permitted
linkage. Before using individual-level records for a new analysis, we still
need to inspect the study-specific readmes/source terms and confirm that the
proposed use is covered. No raw `.dta`, `.RData`, nested ZIP, or individual
record has been added to GitHub.

## What this establishes

The earlier claim that the package file inventory and individual-level coverage
were completely unverified is now superseded: the local archive demonstrably
contains individual-level-looking Stata files and a cleaned project object for
the seven-study synthesis. The inventory does **not** yet establish that every
file is suitable for mechanism coding, that all seven studies share the target
invitation-ITT estimand, or that the seven units can support a 95% independent
calibration archive. Those questions require study-level codebook and design
review before outcomes are used.
