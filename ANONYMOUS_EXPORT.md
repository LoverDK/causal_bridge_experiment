# Anonymous supplementary export

The supplementary ZIP is made from the explicitly reviewed files pinned in
`provenance/release_manifest.json`. Do not zip the working directory directly.
The release may contain reviewed local changes not yet committed to Git;
`git archive HEAD` would silently omit them and is not the export command for
this release.

From the repository root, create an archive with:

```bash
python tools/export_submission.py --output ../causal_bridge_experiment_supplementary.zip
```

Choose a fresh destination. The exporter refuses existing ZIP or audit-report
paths, checks every manifest hash and byte length, excludes transient paths,
scans for local author-path candidates, and verifies the resulting ZIP bytes.
It writes an adjacent `.audit.json` outside the ZIP. This is an integrity check,
not a complete anonymity or policy certification. Before submission, extract
the ZIP into a new directory and check that:

```bash
python reproduce.py verify
```

The extracted directory should contain exactly the reviewed manifest files and
the manifest itself. Git metadata, historical microcredit outputs not accepted
for this release, private audit files, and rerun caches are not part of that
allowlist. Search the
extracted tree for absolute Windows or Unix paths, personal names, email
addresses, account names, and repository-specific URLs. Remove any file that
fails this audit from the release allowlist, investigate its provenance, and
regenerate the manifest and a new archive. Do not delete original research
files or rewrite historical run manifests to hide a mismatch.

The archive includes public-data provenance and citation information. Those
references identify upstream datasets and are not author-identifying metadata.

One historical NSW run manifest contained an absolute output directory. Its
original bytes are preserved locally and excluded from the allowlist. The
labelled derivative `provenance/nsw_real_proxy_truth_v2_public_manifest.json`
replaces only that command argument with a relative path and records the
original SHA-256 and transformation. Historical source and output hashes are
retained; the derivative is not represented as the original run manifest.
