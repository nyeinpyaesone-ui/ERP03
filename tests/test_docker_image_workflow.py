"""Contract tests for PR #254's Docker publishing workflow.

Run without backend services: python -m unittest discover -s tests -v
PyYAML is required (also used by the repository's deployment checks).
These checks inspect configuration; they do not build or publish images.
"""

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/docker-image.yml"


class DockerImageWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # BaseLoader preserves GitHub's `on` key and avoids YAML 1.1's conversion
        # of it to True. Scalar inputs (including push) remain strings.
        cls.workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        cls.steps = cls.workflow["jobs"]["build-and-push"]["steps"]

    def action_steps(self, action):
        return [step for step in self.steps if step.get("uses", "").split("@")[0] == action]

    def only_action(self, action):
        steps = self.action_steps(action)
        self.assertEqual(len(steps), 1, f"Expected exactly one {action} step")
        return steps[0]

    def image_pairs(self):
        metadata = self.action_steps("docker/metadata-action")
        builds = self.action_steps("docker/build-push-action")
        self.assertEqual(len(metadata), 2)
        self.assertEqual(len(builds), 2)
        return zip(("BACKEND_IMAGE", "FRONTEND_IMAGE"), metadata, builds, strict=True)

    def test_publishing_runs_only_on_main_push_or_manual_dispatch(self):
        events = self.workflow["on"]
        self.assertEqual(set(events), {"push", "workflow_dispatch"})
        self.assertEqual(events["push"], {"branches": ["main"]})
        self.assertIn(events["workflow_dispatch"], ("", {}))

    def test_job_has_required_token_permissions(self):
        self.assertEqual(
            self.workflow["permissions"],
            {
                "contents": "read",
                "packages": "write",
                "attestations": "write",
                "id-token": "write",
            },
        )
        self.assertEqual(self.workflow["jobs"]["build-and-push"]["runs-on"], "ubuntu-latest")

    def test_checkout_emulation_builder_and_login_precede_builds(self):
        preparation = [
            self.only_action(action)
            for action in (
                "actions/checkout",
                "docker/setup-qemu-action",
                "docker/setup-buildx-action",
                "docker/login-action",
            )
        ]
        positions = [self.steps.index(step) for step in preparation]
        self.assertEqual(positions, sorted(positions))
        for build in self.action_steps("docker/build-push-action"):
            self.assertLess(positions[-1], self.steps.index(build))

    def test_login_uses_secret_references(self):
        inputs = self.only_action("docker/login-action")["with"]
        self.assertEqual(inputs["username"], "${{ secrets.D2_USER }}")
        self.assertEqual(inputs["password"], "${{ secrets.D2_PASS }}")

    def test_images_are_distinct_docker_hub_repositories(self):
        env = self.workflow["env"]
        self.assertEqual(env["REGISTRY"], "docker.io")
        self.assertNotEqual(env["BACKEND_IMAGE"], env["FRONTEND_IMAGE"])
        for key in ("BACKEND_IMAGE", "FRONTEND_IMAGE"):
            with self.subTest(image=key):
                self.assertRegex(env[key], r"^[a-z0-9_-]+/[a-z0-9_-]+$")

    def test_step_ids_are_unique(self):
        ids = [step["id"] for step in self.steps if "id" in step]
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_build_consumes_its_own_metadata(self):
        for image, metadata, build in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(metadata["with"]["images"], "${{ env." + image + " }}")
                self.assertEqual(
                    build["with"]["tags"],
                    "${{ steps." + metadata["id"] + ".outputs.tags }}",
                )
                self.assertLess(self.steps.index(metadata), self.steps.index(build))

    def test_latest_and_commit_tags_are_generated_for_both_images(self):
        for image, metadata, _ in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(
                    set(metadata["with"]["tags"].splitlines()),
                    {"type=raw,value=latest", "type=sha,prefix=sha-"},
                )

    def test_both_images_are_published_for_amd64_and_arm64(self):
        for image, _, build in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(build["with"]["push"], "true")
                self.assertEqual(
                    set(build["with"]["platforms"].split(",")),
                    {"linux/amd64", "linux/arm64"},
                )

    def test_both_builds_import_and_export_github_actions_cache(self):
        for image, _, build in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(build["with"]["cache-from"], "type=gha")
                self.assertEqual(build["with"]["cache-to"], "type=gha,mode=max")

    def test_both_builds_enable_sbom_and_provenance(self):
        for image, _, build in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(
                    set(build["with"]["attestations"].splitlines()),
                    {"type=sbom,enabled=true", "type=provenance,enabled=true"},
                )

    def test_build_contexts_and_dockerfiles_exist_inside_checkout(self):
        for image, _, build in self.image_pairs():
            with self.subTest(image=image):
                context = (ROOT / build["with"]["context"]).resolve()
                dockerfile = (ROOT / build["with"]["file"]).resolve()
                self.assertTrue(context.is_relative_to(ROOT), "Build context escapes checkout")
                self.assertTrue(context.is_dir(), f"Missing build context: {context}")
                self.assertTrue(dockerfile.is_relative_to(context))
                self.assertTrue(dockerfile.is_file(), f"Missing Dockerfile: {dockerfile}")

    def test_actions_follow_repository_immutable_sha_policy(self):
        for step in self.steps:
            with self.subTest(action=step["uses"]):
                ref = step["uses"].rsplit("@", 1)[-1]
                self.assertIsNotNone(
                    re.fullmatch(r"[0-9a-fA-F]{40}", ref),
                    f"Action must be pinned to a full commit SHA: {step['uses']}",
                )
