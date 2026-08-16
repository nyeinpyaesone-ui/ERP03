"""Tests for the changes introduced in this PR.

This PR:
  * Replaces the previous `.gitignore` contents with a markdown-fenced
    reference to `ERP03`.
  * Adds `ERP03` to the repository as a git submodule (gitlink) pointing at
    commit `62e6f9b58a97ed42655d13424cc796385f3af3b9`.

There is no application code in this diff, so these tests validate the
repository configuration/state directly using `git` plumbing commands and
plain filesystem checks.
"""

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
)

GITIGNORE_PATH = REPO_ROOT / ".gitignore"
GITMODULES_PATH = REPO_ROOT / ".gitmodules"
SUBMODULE_NAME = "ERP03"
SUBMODULE_PATH = REPO_ROOT / SUBMODULE_NAME
EXPECTED_SUBMODULE_COMMIT = "62e6f9b58a97ed42655d13424cc796385f3af3b9"
EXPECTED_GITIGNORE_CONTENT = "```\nERP03\n```"

# Patterns that were present in the previous .gitignore and were removed by
# this PR. They are used to document/guard the resulting behavior change.
REMOVED_PATTERNS = (
    ".env",
    ".env.*",
    "!.env.example",
    "secrets/*",
    "!secrets/README.md",
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".mypy_cache/",
    "node_modules/",
    "dist/",
    "uploads/",
    "static/generated/",
    "*.log",
    ".vscode/",
    ".idea/",
    ".DS_Store",
)


class TestGitignoreChanges(unittest.TestCase):
    def setUp(self):
        self.content = GITIGNORE_PATH.read_text()

    def test_gitignore_file_exists(self):
        self.assertTrue(GITIGNORE_PATH.is_file())

    def test_gitignore_matches_expected_new_content(self):
        self.assertEqual(self.content, EXPECTED_GITIGNORE_CONTENT)

    def test_gitignore_has_no_trailing_newline(self):
        # The PR diff explicitly shows "\ No newline at end of file".
        self.assertFalse(self.content.endswith("\n"))

    def test_gitignore_contains_markdown_code_fence(self):
        lines = self.content.splitlines()
        self.assertEqual(lines.count("```"), 2)

    def test_gitignore_references_erp03(self):
        lines = self.content.splitlines()
        self.assertIn(SUBMODULE_NAME, lines)

    def test_gitignore_no_longer_contains_previously_ignored_patterns(self):
        # Regression guard: verify that none of the patterns removed by this
        # PR are still present in the current .gitignore.
        for pattern in REMOVED_PATTERNS:
            self.assertNotIn(
                pattern,
                self.content,
                msg=f"Pattern {pattern!r} unexpectedly present in .gitignore",
            )

    def test_gitignore_backtick_lines_are_not_meaningful_ignore_rules(self):
        # A line consisting solely of backticks is a valid (if odd) gitignore
        # pattern that would literally match a path named "```". It must not
        # be confused with the removed, meaningful ignore rules above.
        for line in self.content.splitlines():
            self.assertNotIn(line, REMOVED_PATTERNS)


class TestERP03SubmoduleAddition(unittest.TestCase):
    def test_erp03_tracked_as_gitlink_in_index(self):
        output = subprocess.check_output(
            ["git", "ls-files", "-s", "--", SUBMODULE_NAME],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        self.assertTrue(output, "ERP03 should be tracked in the git index")

        mode, sha, _rest = output.split(" ", 2)
        self.assertEqual(
            mode, "160000", "ERP03 should be recorded as a gitlink (submodule) entry"
        )
        self.assertEqual(sha, EXPECTED_SUBMODULE_COMMIT)

    def test_erp03_path_exists_on_disk(self):
        self.assertTrue(SUBMODULE_PATH.exists())

    def test_erp03_is_a_directory(self):
        self.assertTrue(SUBMODULE_PATH.is_dir())

    def test_no_gitmodules_file_was_added(self):
        # This PR only adds the gitlink entry for ERP03; it does not add a
        # corresponding .gitmodules mapping (no URL/branch configuration),
        # so the submodule cannot be resolved via `git submodule update
        # --init`.
        self.assertFalse(GITMODULES_PATH.exists())

    def test_erp03_is_not_a_regular_tracked_file(self):
        # A gitlink entry has no blob content of its own; git does not
        # recurse into it, so `ls-tree -r` should yield exactly the single
        # 160000 "commit" entry for the path itself and nothing else.
        output = subprocess.check_output(
            ["git", "ls-tree", "-r", "HEAD", "--", SUBMODULE_NAME],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        entries = output.splitlines()
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].startswith("160000 commit "))


if __name__ == "__main__":
    unittest.main()