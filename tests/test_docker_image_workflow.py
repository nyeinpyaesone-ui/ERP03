"""Tests for the new `.github/workflows/docker-image.yml` GitHub Actions
workflow introduced by this PR.

This PR adds a brand new workflow file that builds and pushes the backend
and frontend Docker images to Docker Hub whenever `main` is updated (or the
workflow is dispatched manually). There is no application/library code in
this diff, so - consistent with the existing
`tests/test_gitignore_and_erp03_submodule.py` convention in this
repository - these tests validate the workflow file's contents directly
using plain text/regex inspection (no third-party YAML dependency is
installed in this repository, mirroring `scripts/pin-github-actions.py`,
which also parses workflow files with regular expressions instead of a
YAML library).
"""

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()
)

WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "docker-image.yml"

# Full-length (40 hex character) commit SHA, as required by this repo's
# action-pinning policy (see .github/workflows/action-pinning.yml and
# scripts/pin-github-actions.py).
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")

# Matches a `uses: owner/repo@ref` line (ignoring leading indentation),
# mirroring USES_RE from scripts/pin-github-actions.py.
USES_RE = re.compile(
    r"uses:\s*(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)@(?P<ref>[^\s#]+)"
)

# The exact, ordered sequence of `uses:` references expected in the
# workflow. This doubles as a regression guard against accidental
# reordering, duplication, or removal of steps.
EXPECTED_USES_IN_ORDER = [
    "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5",
    "docker/setup-qemu-action@8d2750c68a42422c14e847fe6c8ac0403b4cbd6f",
    "docker/setup-buildx-action@8d2750c68a42422c14e847fe6c8ac0403b4cbd6f",
    "docker/login-action@465a07811f14bebb1938fbed4728c6a1ff8901fc",
    "docker/metadata-action@v5",
    "docker/build-push-action@676cae2f85471aeff6776463c72881ebd902dcf9",
    "docker/metadata-action@v5",
    "docker/build-push-action@676cae2f85471aeff6776463c72881ebd902dcf9",
]

# References that are intentionally NOT pinned to a full commit SHA. Every
# other `uses:` entry in the file is expected to be SHA-pinned.
KNOWN_UNPINNED_REFS = {"v5"}


class TestWorkflowFileBasics(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()
        self.lines = self.content.splitlines()

    def test_workflow_file_exists(self):
        self.assertTrue(WORKFLOW_PATH.is_file())

    def test_workflow_file_is_not_empty(self):
        self.assertTrue(self.content.strip())

    def test_workflow_file_has_no_tabs(self):
        # YAML forbids tab-based indentation.
        self.assertNotIn("\t", self.content)

    def test_workflow_file_ends_with_newline(self):
        self.assertTrue(self.content.endswith("\n"))

    def test_workflow_name(self):
        self.assertIn("name: Build and Push Docker Images", self.lines)


class TestWorkflowTriggers(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_triggers_on_push_to_main(self):
        self.assertRegex(
            self.content,
            r"on:\s*\n\s*push:\s*\n\s*branches:\s*\[main\]",
        )

    def test_supports_manual_workflow_dispatch(self):
        self.assertRegex(self.content, r"workflow_dispatch:\s*\n")

    def test_does_not_trigger_on_pull_request(self):
        # This workflow pushes images with real registry credentials; it
        # must not run on pull_request events (which could expose secrets
        # to untrusted forks).
        self.assertNotIn("pull_request:", self.content)


class TestWorkflowPermissions(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_permissions_block_present(self):
        self.assertIn("permissions:", self.content)

    def test_permissions_are_least_privilege_and_complete(self):
        expected = {
            "contents": "read",
            "packages": "write",
            "attestations": "write",
            "id-token": "write",
        }
        for key, value in expected.items():
            pattern = re.compile(
                rf"^\s*{re.escape(key)}:\s*{re.escape(value)}\s*$", re.MULTILINE
            )
            self.assertRegex(
                self.content,
                pattern,
                msg=f"expected permission '{key}: {value}' not found",
            )

    def test_contents_permission_is_read_only(self):
        # The job only checks out code and builds/pushes images; it should
        # not be granted write access to repository contents.
        self.assertNotRegex(
            self.content, re.compile(r"^\s*contents:\s*write\s*$", re.MULTILINE)
        )


class TestWorkflowEnv(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_registry_env_var(self):
        self.assertIn("REGISTRY: docker.io", self.content)

    def test_backend_image_env_var(self):
        self.assertIn(
            "BACKEND_IMAGE: powerrangeranikg/erp03-backend", self.content
        )

    def test_frontend_image_env_var(self):
        self.assertIn(
            "FRONTEND_IMAGE: powerrangeranikg/erp03-frontend", self.content
        )


class TestWorkflowJob(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_single_job_defined(self):
        jobs_section = self.content.split("\njobs:\n", 1)[1]
        job_headers = re.findall(r"^  ([a-zA-Z0-9_-]+):\s*$", jobs_section, re.MULTILINE)
        self.assertEqual(job_headers, ["build-and-push"])

    def test_job_runs_on_ubuntu_latest(self):
        self.assertIn("runs-on: ubuntu-latest", self.content)

    def test_login_uses_docker_hub_secrets(self):
        self.assertIn("username: ${{ secrets.D2_USER }}", self.content)
        self.assertIn("password: ${{ secrets.D2_PASS }}", self.content)

    def test_no_hardcoded_credentials(self):
        # Guard against accidentally hardcoding a username/password instead
        # of referencing GitHub secrets.
        self.assertNotRegex(self.content, r"username:\s*(?!\$\{\{)\S")
        self.assertNotRegex(self.content, r"password:\s*(?!\$\{\{)\S")


class TestActionReferences(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()
        self.uses = [
            f"{m.group('owner')}/{m.group('repo')}@{m.group('ref')}"
            for m in USES_RE.finditer(self.content)
        ]

    def test_expected_actions_used_in_expected_order(self):
        self.assertEqual(self.uses, EXPECTED_USES_IN_ORDER)

    def test_all_actions_are_pinned_except_known_exceptions(self):
        for reference in self.uses:
            _, _, ref = reference.rpartition("@")
            if ref in KNOWN_UNPINNED_REFS:
                continue
            self.assertTrue(
                SHA_RE.fullmatch(ref),
                msg=f"{reference} is not pinned to a full-length commit SHA",
            )

    def test_metadata_action_is_the_only_unpinned_reference(self):
        # Regression guard: today `docker/metadata-action@v5` is the sole
        # action in this workflow that is not SHA-pinned, which is why
        # `.github/workflows/action-pinning.yml`'s grep-based check
        # (`grep -vE '@[0-9a-f]{40}'`) would flag it. If additional
        # unpinned refs are introduced, this test should fail so the
        # deviation is noticed.
        unpinned = [u for u in self.uses if not SHA_RE.fullmatch(u.rpartition("@")[2])]
        self.assertEqual(unpinned, ["docker/metadata-action@v5", "docker/metadata-action@v5"])

    def test_checkout_action_used_exactly_once(self):
        self.assertEqual(self.uses.count("actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5"), 1)

    def test_build_push_action_used_exactly_twice(self):
        self.assertEqual(
            self.uses.count("docker/build-push-action@676cae2f85471aeff6776463c72881ebd902dcf9"),
            2,
        )

    def test_metadata_action_used_exactly_twice(self):
        self.assertEqual(self.uses.count("docker/metadata-action@v5"), 2)


class TestMetadataSteps(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_backend_metadata_step_id(self):
        self.assertRegex(self.content, r"id:\s*meta_backend\s*\n")

    def test_frontend_metadata_step_id(self):
        self.assertRegex(self.content, r"id:\s*meta_frontend\s*\n")

    def test_metadata_step_ids_are_unique(self):
        ids = re.findall(r"^\s*id:\s*(\S+)\s*$", self.content, re.MULTILINE)
        self.assertEqual(len(ids), len(set(ids)), f"duplicate step ids found: {ids}")

    def test_backend_metadata_uses_backend_image_env(self):
        self.assertRegex(
            self.content,
            r"id:\s*meta_backend[\s\S]*?images:\s*\$\{\{\s*env\.BACKEND_IMAGE\s*\}\}",
        )

    def test_frontend_metadata_uses_frontend_image_env(self):
        self.assertRegex(
            self.content,
            r"id:\s*meta_frontend[\s\S]*?images:\s*\$\{\{\s*env\.FRONTEND_IMAGE\s*\}\}",
        )

    def test_metadata_tags_include_latest_and_sha(self):
        # Both metadata blocks should tag images with a stable "latest"
        # pointer as well as an immutable per-commit sha-prefixed tag.
        self.assertEqual(self.content.count("type=raw,value=latest"), 2)
        self.assertEqual(self.content.count("type=sha,prefix=sha-"), 2)


class TestBuildPushSteps(unittest.TestCase):
    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_backend_build_context_and_dockerfile(self):
        self.assertRegex(
            self.content,
            r"context:\s*\./ERP-BACKEND\s*\n\s*file:\s*\./ERP-BACKEND/Dockerfile\s*\n",
        )

    def test_frontend_build_context_and_dockerfile(self):
        self.assertRegex(
            self.content,
            r"context:\s*\./ERP-BACKEND/frontend-react\s*\n\s*file:\s*\./ERP-BACKEND/frontend-react/Dockerfile\s*\n",
        )

    def test_both_images_built_for_multiple_platforms(self):
        self.assertEqual(
            self.content.count("platforms: linux/amd64,linux/arm64"), 2
        )

    def test_both_build_steps_push_true(self):
        self.assertEqual(self.content.count("push: true"), 2)

    def test_backend_tags_reference_backend_metadata_output(self):
        self.assertIn(
            "tags: ${{ steps.meta_backend.outputs.tags }}", self.content
        )

    def test_frontend_tags_reference_frontend_metadata_output(self):
        self.assertIn(
            "tags: ${{ steps.meta_frontend.outputs.tags }}", self.content
        )

    def test_gha_cache_configured_for_both_builds(self):
        self.assertEqual(self.content.count("cache-from: type=gha"), 2)
        self.assertEqual(self.content.count("cache-to: type=gha,mode=max"), 2)

    def test_sbom_and_provenance_attestations_enabled_for_both_builds(self):
        self.assertEqual(self.content.count("type=sbom,enabled=true"), 2)
        self.assertEqual(self.content.count("type=provenance,enabled=true"), 2)

    def test_frontend_context_is_nested_inside_backend_context(self):
        # Boundary/edge case: the frontend build context is a subdirectory
        # of the backend context, not a sibling top-level directory. This
        # guards against an accidental path change (e.g. to a top-level
        # `./frontend-react`) that would silently break the frontend image
        # build.
        self.assertIn("./ERP-BACKEND/frontend-react", self.content)


class TestWorkflowKnownGapsAndRegressions(unittest.TestCase):
    """Additional boundary/regression tests documenting a couple of
    noteworthy properties of this new workflow, to guard against silent
    behavioral drift in either direction.
    """

    def setUp(self):
        self.content = WORKFLOW_PATH.read_text()

    def test_registry_env_var_is_defined_but_unreferenced(self):
        # `REGISTRY: docker.io` is declared in `env:`, but neither the
        # `images:` metadata inputs nor the `tags:` outputs reference
        # `${{ env.REGISTRY }}` anywhere in the file (Docker Hub is used
        # implicitly as the default registry). This test documents that
        # fact so that, if `REGISTRY` is later wired into an image
        # reference, this test is updated deliberately rather than the
        # dead config going unnoticed indefinitely.
        self.assertIn("REGISTRY: docker.io", self.content)
        self.assertNotIn("env.REGISTRY", self.content)

    def test_no_concurrency_control_configured(self):
        # Unlike the previously-existing `ci.yml`/`release.yml` workflows
        # (which both defined a `concurrency:` group), this workflow does
        # not define one. Because it triggers on every push to `main`,
        # rapid successive pushes could run overlapping build-and-push
        # jobs concurrently. This test documents the current behavior as a
        # known gap rather than an assumption.
        self.assertNotIn("concurrency:", self.content)

    def test_workflow_has_exactly_one_trigger_section(self):
        # Sanity/boundary check that the `on:` block is only declared
        # once, guarding against an accidental duplicate top-level key
        # that YAML would otherwise silently resolve by taking the last
        # occurrence.
        self.assertEqual(len(re.findall(r"^on:\s*$", self.content, re.MULTILINE)), 1)


if __name__ == "__main__":
    unittest.main()