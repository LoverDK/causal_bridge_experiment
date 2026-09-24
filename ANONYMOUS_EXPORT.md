# Anonymous supplementary export

The supplementary ZIP should be made from a clean archive of the current tracked
files. Do not zip the working directory directly.

From the repository root, create an archive with:

```bash
git archive --format=zip --output=causal_bridge_experiment_supplementary.zip HEAD
```

The archive produced by `git archive` does not contain `.git`, Git logs, remotes,
untracked files, ignored caches, or generated `reproduced/` output. Before
submission, extract the ZIP into a new directory and check that:

```bash
python reproduce.py verify
```

The extracted directory should contain only tracked research files. Search the
extracted tree for absolute Windows or Unix paths, personal names, email
addresses, account names, and repository-specific URLs. Remove any file that
fails this audit and regenerate the archive.

The archive includes public-data provenance and citation information. Those
references identify upstream datasets and are not author-identifying metadata.
