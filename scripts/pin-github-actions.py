#!/usr/bin/env python3
"""Audit and optionally pin GitHub Actions to immutable commit SHAs.

Usage:
  python scripts/pin-github-actions.py --check
  python scripts/pin-github-actions.py --fix

The script uses only the Python standard library. It scans .github/workflows/*.yml
and *.yaml, resolves action refs through GitHub's commit API, and replaces mutable
refs (for example @v6 or @main) with the corresponding 40-character commit SHA.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"

USES_RE = re.compile(
    r"^(?P<indent>\s*)uses:\s*(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)@(?P<ref>[^\s#]+)(?P<comment>\s+#.*)?$"
)
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def github_get(url: str) -> dict:
    """
    Fetch and parse a JSON response from the GitHub API.
    
    Parameters:
    	url (str): GitHub API endpoint to request.
    
    Returns:
    	dict: Parsed JSON response.
    
    Raises:
    	RuntimeError: If the request receives an HTTP error or cannot be completed.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ERP03-pin-github-actions",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            import json
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {url}: {body[:300]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API request failed for {url}: {exc}") from exc


def resolve_ref(owner: str, repo: str, ref: str) -> str:
    """Resolve a tag/branch/ref to the commit SHA that GitHub Actions will execute."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{ref}"
    data = github_get(url)
    sha = data.get("sha", "")
    if not SHA_RE.fullmatch(sha):
        raise RuntimeError(f"Invalid commit SHA returned for {owner}/{repo}@{ref}: {sha!r}")
    return sha


def workflow_files() -> list[Path]:
    """
    Find workflow files in the configured workflow directory.
    
    Returns:
    	list[Path]: Sorted paths to `.yml` and `.yaml` workflow files, or an empty list if the directory does not exist.
    """
    if not WORKFLOW_DIR.is_dir():
        return []
    return sorted([*WORKFLOW_DIR.glob("*.yml"), *WORKFLOW_DIR.glob("*.yaml")])


def scan_file(path: Path, fix: bool) -> tuple[str, list[str]]:
    """
    Scan a workflow file for mutable GitHub Actions references and optionally pin them.
    
    Parameters:
        path (Path): Workflow file to inspect.
        fix (bool): Whether to replace mutable references with resolved commit SHAs.
    
    Returns:
        tuple[str, list[str]]: The resulting file content and the mutable references found.
    """
    original = path.read_text(encoding="utf-8")
    changed = original
    findings: list[str] = []

    lines = original.splitlines(keepends=True)
    output: list[str] = []

    for line in lines:
        match = USES_RE.match(line.rstrip("\r\n"))
        if not match:
            output.append(line)
            continue

        owner = match.group("owner")
        repo = match.group("repo")
        ref = match.group("ref")

        # Local actions and reusable workflows do not use owner/repo@ref and are
        # therefore already excluded by USES_RE.
        if SHA_RE.fullmatch(ref):
            output.append(line)
            continue

        findings.append(f"{path.relative_to(ROOT)}: {owner}/{repo}@{ref}")

        if not fix:
            output.append(line)
            continue

        sha = resolve_ref(owner, repo, ref)
        comment = match.group("comment") or ""
        newline = "\n" if line.endswith("\n") else ""
        output.append(
            f"{match.group('indent')}uses: {owner}/{repo}@{sha}{comment}{newline}"
        )

    if fix:
        changed = "".join(output)
        if changed != original:
            path.write_text(changed, encoding="utf-8")

    return changed, findings


def main() -> int:
    """
    Run the GitHub Actions reference audit or replace mutable references with commit SHAs.
    
    Returns:
    	int: Exit status: 0 for success, 1 when unpinned references are found in check mode, or 2 when processing errors occur.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="fail if any action is not SHA pinned")
    mode.add_argument("--fix", action="store_true", help="replace mutable refs with commit SHAs")
    args = parser.parse_args()

    files = workflow_files()
    if not files:
        print("No GitHub Actions workflow files found.")
        return 0

    total = 0
    errors = 0

    for path in files:
        try:
            _, findings = scan_file(path, fix=args.fix)
            total += len(findings)
            for finding in findings:
                print(("PINNED" if args.fix else "UNPINNED") + f": {finding}")
        except RuntimeError as exc:
            errors += 1
            print(f"ERROR: {exc}", file=sys.stderr)

    if errors:
        return 2

    if args.check and total:
        print(f"\nFAIL: {total} GitHub Action reference(s) are not pinned to full-length SHAs.")
        print("Run: python scripts/pin-github-actions.py --fix")
        return 1

    if args.check:
        print("PASS: all GitHub Actions are pinned to full-length commit SHAs.")
    else:
        print(f"DONE: resolved {total} mutable GitHub Action reference(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
