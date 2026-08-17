"""Tests for the `.github/workflows/` directory changes introduced by this
PR.

This PR removes four previously-existing workflow files:

  * `.github/workflows/action-pinning.yml`
  * `.github/workflows/ci.yml`
  * `.github/workflows/release.yml`
  * `.github/workflows/security.yml`

and adds a single new workflow file, `.github/workflows/docker-image.yml`
(exercised in detail by `tests/test_docker_image_workflow.py`).

There is no application/library code involved, so - consistent with the
existing `tests/test_gitignore_and_erp03_submodule.py` and
`tests/test_docker_image_workflow.py` conventions in this repository -
these tests validate the resulting repository/filesystem state directly.
"""

import unittest
from pathlib import Path

import subprocess

REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
)

WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

REMOVED_WORKFLOW_FILENAMES = (
    "action-pinning.yml",
    "ci.yml",
    "release.yml",
    "security.yml",
)

REMAINING_WORKFLOW_FILENAME = "docker-image.yml"


class TestRemovedWorkflowFiles(unittest.TestCase):
    """The four legacy workflow files must no longer exist on disk."""

    def test_action_pinning_workflow_removed(self):
        self.assertFalse(
            (WORKFLOWS_DIR / "action-pinning.yml").exists(),
            "action-pinning.yml should have been deleted by this PR",
        )

    def test_ci_workflow_removed(self):
        self.assertFalse(
            (WORKFLOWS_DIR / "ci.yml").exists(),
            "ci.yml should have been deleted by this PR",
        )

    def test_release_workflow_removed(self):
        self.assertFalse(
            (WORKFLOWS_DIR / "release.yml").exists(),
            "release.yml should have been deleted by this PR",
        )

    def test_security_workflow_removed(self):
        self.assertFalse(
            (WORKFLOWS_DIR / "security.yml").exists(),
            "security.yml should have been deleted by this PR",
        )

    def test_all_removed_workflow_files_absent(self):
        # Belt-and-suspenders regression guard covering every filename
        # removed by this PR in a single assertion.
        for filename in REMOVED_WORKFLOW_FILENAMES:
            self.assertFalse(
                (WORKFLOWS_DIR / filename).exists(),
                f"{filename} unexpectedly still present in {WORKFLOWS_DIR}",
            )

    def test_no_git_tracked_entries_for_removed_workflows(self):
        # Verify removal at the git index level too, not just on the
        # filesystem, to guard against a file being merely untracked
        # (e.g. via .gitignore) rather than actually deleted from the repo.
        for filename in REMOVED_WORKFLOW_FILENAMES:
            output = subprocess.check_output(
                [
                    "git",
                    "ls-files",
                    "--",
                    f".github/workflows/{filename}",
                ],
                cwd=REPO_ROOT,
                text=True,
            ).strip()
            self.assertEqual(
                output,
                "",
                f".github/workflows/{filename} is still tracked by git",
            )


class TestWorkflowsDirectoryFinalState(unittest.TestCase):
    """After this PR, `.github/workflows/` should contain exactly one
    workflow file: `docker-image.yml`."""

    def setUp(self):
        self.workflow_files = sorted(
            p.name for p in WORKFLOWS_DIR.glob("*.yml")
        )

    def test_workflows_directory_exists(self):
        self.assertTrue(WORKFLOWS_DIR.is_dir())

    def test_only_docker_image_workflow_remains(self):
        self.assertEqual(self.workflow_files, [REMAINING_WORKFLOW_FILENAME])

    def test_docker_image_workflow_present(self):
        self.assertIn(REMAINING_WORKFLOW_FILENAME, self.workflow_files)

    def test_no_leftover_yaml_extension_variants(self):
        # Guard against a stray `.yaml` (as opposed to `.yml`) copy of any
        # removed or new workflow being left behind.
        yaml_variant_files = sorted(
            p.name for p in WORKFLOWS_DIR.glob("*.yaml")
        )
        self.assertEqual(yaml_variant_files, [])


class TestActionPinningPolicyNoLongerAutomated(unittest.TestCase):
    """Documents a behavioral consequence of removing action-pinning.yml.

    Previously, `action-pinning.yml` ran a grep-based CI check on every
    push/PR touching `.github/workflows/**` that failed the build if any
    `uses:` reference was not pinned to a full 40-character commit SHA.
    With that workflow removed, this policy is no longer enforced by CI;
    `tests/test_docker_image_workflow.py` is what now guards SHA-pinning
    for the sole remaining workflow file.
    """

    def test_action_pinning_check_script_is_gone(self):
        # The workflow that used to run the pinning check no longer
        # exists, so there is no CI job left in this repo that enforces
        # SHA-pinning automatically.
        self.assertFalse((WORKFLOWS_DIR / "action-pinning.yml").exists())

    def test_remaining_workflow_still_manually_verified_as_pinned(self):
        # Even without the automated action-pinning workflow, the sole
        # remaining workflow file should still follow the SHA-pinning
        # convention it enforced (mutable "v5" metadata-action ref
        # excepted, as already covered by test_docker_image_workflow.py).
        docker_image_workflow = WORKFLOWS_DIR / REMAINING_WORKFLOW_FILENAME
        self.assertTrue(docker_image_workflow.is_file())
        content = docker_image_workflow.read_text()
        import re

        uses_refs = re.findall(
            r"uses:\s*[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@([^\s#]+)", content
        )
        self.assertTrue(uses_refs, "expected at least one 'uses:' reference")
        unpinned = [ref for ref in uses_refs if not re.fullmatch(r"[0-9a-fA-F]{40}", ref)]
        self.assertEqual(unpinned, ["v5", "v5"])


if __name__ == "__main__":
    unittest.main()