"""Export exactly the hash-pinned release manifest to a fresh local ZIP."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "provenance/release_manifest.json"
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".py",
                   ".tex", ".bib", ".yml", ".yaml", ".svg", ".xml", ".html",
                   ".toml", ".log", ".sty", ".bst", ".cls", ".cfg", ".ini",
                   ".sh", ".ps1", ".r", ".do"}
TEXT_FILENAMES = {".gitignore", ".gitattributes", "license", "makefile"}
FORBIDDEN_PARTS = {".git", ".codex", ".venv", "__pycache__", ".pytest_cache", "reproduced", "scratch"}
WINDOWS_RESERVED = re.compile(r"(?i)^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)")
LOCAL_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]+(?:Users|study)[\\/]+|/(?:Users|home)/[^ /\\]+/)")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_path(name: str) -> Path:
    relative = PurePosixPath(name)
    if (not name or relative.as_posix() != name or relative.is_absolute()
            or ".." in relative.parts or "\\" in name or ":" in name
            or any(ord(char) < 32 for char in name)
            or any(char in name for char in '<>"|?*')):
        raise ValueError(f"Unsafe manifest path: {name}")
    if any(part.casefold() in FORBIDDEN_PARTS for part in relative.parts):
        raise ValueError(f"Transient file in manifest: {name}")
    if any(part.endswith((" ", ".")) or WINDOWS_RESERVED.match(part) for part in relative.parts):
        raise ValueError(f"Non-portable manifest path: {name}")
    path = ROOT.joinpath(*relative.parts)
    root = ROOT.resolve()
    for component in (path, *path.parents):
        if component == ROOT:
            break
        if component.is_symlink() or (hasattr(component, "is_junction") and component.is_junction()):
            raise ValueError(f"Linked path in manifest: {name}")
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError(f"Missing or unsafe file: {name}")
    return path


def local_path_findings(name: str, content: bytes) -> list[dict]:
    text = content.decode("utf-8", errors="replace")
    return [{"file": name, "line": index}
            for index, line in enumerate(text.splitlines(), 1) if LOCAL_PATH.search(line)]


def export(output: Path) -> dict:
    output = output.resolve()
    report_path = output.with_suffix(".audit.json")
    if output.exists() or report_path.exists():
        raise FileExistsError("Choose a new output path; existing exports are preserved")
    manifest_bytes = checked_path(MANIFEST).read_bytes()
    manifest = json.loads(manifest_bytes)
    files = manifest["files"]
    if MANIFEST in files:
        raise ValueError("The manifest cannot hash itself")
    if not files:
        raise ValueError("Empty release manifest")
    paths = {}
    privacy_findings = local_path_findings(MANIFEST, manifest_bytes)
    member_names = {MANIFEST.casefold()}
    for name, expected in sorted(files.items()):
        path = checked_path(name)
        key = name.casefold()
        if key in member_names:
            raise ValueError(f"Colliding archive member: {name}")
        member_names.add(key)
        content = path.read_bytes()
        if digest(content) != expected["sha256"] or len(content) != expected["bytes"]:
            raise ValueError(f"Release hash or length mismatch: {name}")
        if path.suffix.lower() in TEXT_EXTENSIONS or path.name.casefold() in TEXT_FILENAMES:
            privacy_findings.extend(local_path_findings(name, content))
        paths[name] = path
    if privacy_findings:
        raise ValueError("Local author path candidates require review: " + json.dumps(privacy_findings))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in paths.items():
            content = path.read_bytes()
            if digest(content) != files[name]["sha256"]:
                raise RuntimeError(f"File changed during export: {name}")
            archive.writestr(name, content)
        archive.writestr(MANIFEST, manifest_bytes)
    with zipfile.ZipFile(output) as archive:
        if set(archive.namelist()) != set(files) | {MANIFEST}:
            raise AssertionError("ZIP inventory differs from release manifest")
        if len(archive.namelist()) != len(files) + 1:
            raise AssertionError("Duplicate archive entries")
        if archive.testzip() is not None:
            raise AssertionError("ZIP integrity test failed")
        for name, expected in files.items():
            if digest(archive.read(name)) != expected["sha256"]:
                raise AssertionError(f"ZIP byte mismatch: {name}")
    report = {
        "archive": output.name,
        "archive_sha256": digest(output.read_bytes()),
        "archive_bytes": output.stat().st_size,
        "release_manifest_sha256": digest(manifest_bytes),
        "manifest_files_verified": len(files),
        "zip_entries": len(files) + 1,
        "local_author_path_candidates": privacy_findings,
        "zip_integrity": "passed",
        "scope": "File integrity and local-path scan; not a complete anonymity or policy certification",
    }
    with report_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(export(parser.parse_args().output), indent=2))
