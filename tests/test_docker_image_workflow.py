"""Contract tests for the canonical GHCR Docker publishing workflow.

These tests inspect workflow policy and structure only. They do not publish images.
Run with:
    python -m unittest discover -s tests -p "test_docker_image_workflow.py" -v
"""

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/docker-publish.yml"
DUPLICATE_WORKFLOW_PATH = ROOT / ".github/workflows/docker-image.yml"


class DockerPublishWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(
            WORKFLOW_PATH.read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
        cls.job = cls.workflow["jobs"]["build"]
        cls.steps = cls.job["steps"]

    def action_steps(self, action):
        return [
            step for step in self.steps
            if step.get("uses", "").split("@")[0] == action
        ]

    def only_action(self, action):
        steps = self.action_steps(action)
        self.assertEqual(len(steps), 1, f"Expected exactly one {action} step")
        return steps[0]

    def named_step(self, name):
        steps = [step for step in self.steps if step.get("name") == name]
        self.assertEqual(len(steps), 1, f"Expected exactly one step named {name}")
        return steps[0]

    def test_canonical_workflow_exists_without_competing_publisher(self):
        self.assertTrue(WORKFLOW_PATH.is_file())
        self.assertFalse(DUPLICATE_WORKFLOW_PATH.exists())

    def test_workflow_triggers_cover_main_tags_pr_and_schedule(self):
        events = self.workflow["on"]
        self.assertEqual(events["push"]["branches"], ["main"])
        self.assertEqual(events["push"]["tags"], ["v*.*.*"])
        self.assertEqual(events["pull_request"]["branches"], ["main"])
        self.assertIn("schedule", events)
        self.assertEqual(events["workflow_dispatch"], "")

    def test_only_canonical_ghcr_backend_image_is_configured(self):
        self.assertEqual(self.workflow["env"]["REGISTRY"], "ghcr.io")
        self.assertEqual(
            self.workflow["env"]["IMAGE_NAME"],
            "${{ github.repository_owner }}/erp03-backend",
        )
        self.assertNotIn("D2_USER", WORKFLOW_PATH.read_text(encoding="utf-8"))
        self.assertNotIn("D2_PASS", WORKFLOW_PATH.read_text(encoding="utf-8"))

    def test_build_job_uses_least_privilege_permissions(self):
        self.assertEqual(
            self.job["permissions"],
            {
                "contents": "read",
                "packages": "write",
                "id-token": "write",
            },
        )

    def test_registry_login_is_skipped_for_pull_requests_and_uses_github_token(self):
        login = self.only_action("docker/login-action")
        self.assertEqual(login["if"], "github.event_name != 'pull_request'")
        self.assertEqual(login["with"]["registry"], "${{ env.REGISTRY }}")
        self.assertEqual(login["with"]["username"], "${{ github.actor }}")
        self.assertEqual(login["with"]["password"], "${{ secrets.GITHUB_TOKEN }}")

    def test_build_is_multi_arch_and_does_not_push_from_pull_requests(self):
        build = self.only_action("docker/build-push-action")
        self.assertEqual(build["with"]["context"], "./ERP-BACKEND")
        self.assertEqual(build["with"]["file"], "./ERP-BACKEND/Dockerfile")
        self.assertEqual(
            set(build["with"]["platforms"].split(",")),
            {"linux/amd64", "linux/arm64"},
        )
        self.assertEqual(
            build["with"]["push"],
            "${{ github.event_name != 'pull_request' }}",
        )
        self.assertEqual(build["with"]["provenance"], "mode=max")
        self.assertEqual(build["with"]["sbom"], "true")

    def test_metadata_targets_the_canonical_ghcr_image(self):
        metadata = self.only_action("docker/metadata-action")
        self.assertEqual(
            metadata["with"]["images"],
            "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}",
        )
        tags = set(metadata["with"]["tags"].splitlines())
        self.assertIn("type=sha,format=long", tags)
        self.assertIn("type=ref,event=tag", tags)

    def test_published_manifest_is_verified_for_both_architectures(self):
        step = self.named_step("Verify published backend manifest architectures")
        self.assertEqual(step["if"], "github.event_name != 'pull_request'")
        command = step["run"]
        self.assertIn("linux/amd64", command)
        self.assertIn("linux/arm64", command)
        self.assertIn("DIGEST", step["env"])

    def test_published_digest_is_signed_and_signature_verified(self):
        sign = self.named_step("Sign the published GHCR image")
        verify = self.named_step("Verify keyless image signature")
        self.assertEqual(sign["if"], "github.event_name != 'pull_request'")
        self.assertEqual(verify["if"], "github.event_name != 'pull_request'")
        self.assertIn("cosign sign --yes", sign["run"])
        self.assertIn("cosign verify", verify["run"])
        self.assertIn("certificate-identity", verify["run"])
        self.assertIn("certificate-oidc-issuer", verify["run"])

    def test_every_action_reference_is_pinned_to_a_full_commit_sha(self):
        for step in self.steps:
            action = step.get("uses")
            if not action:
                continue
            with self.subTest(action=action):
                self.assertRegex(action.rsplit("@", 1)[-1], re.compile(r"^[0-9a-fA-F]{40}$"))


if __name__ == "__main__":
    unittest.main()
