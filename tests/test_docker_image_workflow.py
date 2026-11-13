"""Contract tests for the Docker image publishing workflow.

Run with:
    python -m unittest discover -s tests -p "test_docker_image_workflow.py" -v

These tests validate workflow structure only; they do not publish images.
"""

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github/workflows/docker-image.yml"


class DockerImageWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load(
            WORKFLOW_PATH.read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
        cls.build_steps = cls.workflow["jobs"]["build-and-push"]["steps"]

    def action_steps(self, action):
        return [
            step for step in self.build_steps
            if step.get("uses", "").split("@")[0] == action
        ]

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

    def test_workflow_has_expected_triggers(self):
        events = self.workflow["on"]
        self.assertEqual(set(events), {"push", "pull_request", "workflow_dispatch"})
        self.assertEqual(events["push"]["branches"], ["main"])
        self.assertEqual(events["pull_request"]["branches"], ["main"])
        self.assertIn(".github/workflows/docker-image.yml", events["pull_request"]["paths"])
        self.assertIn("tests/test_docker_image_workflow.py", events["pull_request"]["paths"])

    def test_contract_tests_are_defined(self):
        job = self.workflow["jobs"]["contract-tests"]
        actions = [step.get("uses", "") for step in job["steps"]]
        self.assertIn("actions/checkout@11d5960a326750d5838078e36cf38b85af677262", actions)
        self.assertTrue(any(action.startswith("actions/setup-python@") for action in actions))
        commands = [step.get("run", "") for step in job["steps"]]
        self.assertTrue(any("pip install" in command and "PyYAML" in command for command in commands))
        self.assertTrue(any("unittest discover" in command for command in commands))

    def test_image_publishing_is_disabled_for_pull_requests(self):
        self.assertEqual(
            self.workflow["jobs"]["build-and-push"]["if"],
            "github.event_name != 'pull_request'",
        )

    def test_build_job_has_least_required_permissions(self):
        self.assertEqual(
            self.workflow["jobs"]["build-and-push"]["permissions"],
            {
                "contents": "read",
                "packages": "write",
                "attestations": "write",
                "id-token": "write",
            },
        )

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
        positions = [self.build_steps.index(step) for step in preparation]
        self.assertEqual(positions, sorted(positions))
        for build in self.action_steps("docker/build-push-action"):
            self.assertLess(positions[-1], self.build_steps.index(build))

    def test_login_uses_repository_secret_references(self):
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
        ids = [step["id"] for step in self.build_steps if "id" in step]
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_build_consumes_its_own_metadata(self):
        for image, metadata, build in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(metadata["with"]["images"], "${{ env." + image + " }}")
                self.assertEqual(
                    build["with"]["tags"],
                    "${{ steps." + metadata["id"] + ".outputs.tags }}",
                )
                self.assertLess(self.build_steps.index(metadata), self.build_steps.index(build))

    def test_latest_and_commit_tags_are_generated_for_both_images(self):
        for image, metadata, _ in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(
                    set(metadata["with"]["tags"].splitlines()),
                    {"type=raw,value=latest", "type=sha,prefix=sha-"},
                )

    def test_both_images_target_amd64_and_arm64(self):
        for image, _, build in self.image_pairs():
            with self.subTest(image=image):
                self.assertEqual(build["with"]["push"], "true")
                self.assertEqual(
                    set(build["with"]["platforms"].split(",")),
                    {"linux/amd64", "linux/arm64"},
                )

    def test_build_contexts_and_dockerfiles_exist(self):
        for image, _, build in self.image_pairs():
            with self.subTest(image=image):
                context = (ROOT / build["with"]["context"]).resolve()
                dockerfile = (ROOT / build["with"]["file"]).resolve()
                self.assertTrue(context.is_relative_to(ROOT), "Build context escapes checkout")
                self.assertTrue(context.is_dir(), f"Missing build context: {context}")
                self.assertTrue(dockerfile.is_relative_to(context))
                self.assertTrue(dockerfile.is_file(), f"Missing Dockerfile: {dockerfile}")

    def test_all_actions_are_pinned_to_full_commit_shas(self):
        for job_name, job in self.workflow["jobs"].items():
            for step in job["steps"]:
                action = step.get("uses")
                if not action:
                    continue
                with self.subTest(job=job_name, action=action):
                    ref = action.rsplit("@", 1)[-1]
                    self.assertRegex(ref, re.compile(r"^[0-9a-fA-F]{40}$"))


if __name__ == "__main__":
    unittest.main()
