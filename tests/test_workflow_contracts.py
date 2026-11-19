"""Contract tests for ERP03's canonical GHCR backend publishing workflow."""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_workflow(path: str):
    return yaml.load((ROOT / path).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


class DockerPublishWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = load_workflow(".github/workflows/docker-publish.yml")
        cls.job = cls.workflow["jobs"]["build"]
        cls.steps = cls.job["steps"]

    def action(self, name):
        found = [step for step in self.steps if step.get("uses", "").split("@")[0] == name]
        self.assertEqual(len(found), 1, f"Expected exactly one {name} step")
        return found[0]

    def named(self, name):
        found = [step for step in self.steps if step.get("name") == name]
        self.assertEqual(len(found), 1, f"Expected exactly one {name} step")
        return found[0]

    def test_single_canonical_publisher_and_triggers(self):
        self.assertFalse((ROOT / ".github/workflows/docker-image.yml").exists())
        events = self.workflow["on"]
        self.assertEqual(events["push"]["branches"], ["main"])
        self.assertEqual(events["push"]["tags"], ["v*.*.*"])
        self.assertEqual(events["pull_request"]["branches"], ["main"])
        self.assertIn("schedule", events)
        self.assertEqual(set(events), {"schedule", "push", "pull_request"})

    def test_least_privilege_permissions_and_canonical_image(self):
        self.assertEqual(self.job["permissions"], {
            "contents": "read", "packages": "write", "id-token": "write"
        })
        self.assertEqual(self.workflow["env"]["REGISTRY"], "ghcr.io")
        self.assertEqual(self.workflow["env"]["IMAGE_NAME"], "${{ github.repository_owner }}/erp03-backend")
        source = (ROOT / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8")
        self.assertNotIn("D2_USER", source)
        self.assertNotIn("D2_PASS", source)

    def test_pr_build_does_not_publish_and_build_is_multiarch(self):
        login = self.action("docker/login-action")
        self.assertEqual(login["if"], "github.event_name != 'pull_request'")
        self.assertEqual(login["with"]["password"], "${{ secrets.GITHUB_TOKEN }}")
        build = self.action("docker/build-push-action")
        self.assertEqual(build["with"]["context"], "./ERP-BACKEND")
        self.assertEqual(set(build["with"]["platforms"].split(",")), {"linux/amd64", "linux/arm64"})
        self.assertEqual(build["with"]["push"], "${{ github.event_name != 'pull_request' }}")
        self.assertEqual(build["with"]["provenance"], "mode=max")
        self.assertEqual(build["with"]["sbom"], "true")

    def test_publish_is_serialized_and_revision_is_recorded(self):
        self.assertEqual(self.workflow["concurrency"]["group"], "backend-image-publish-${{ github.ref }}")
        self.assertEqual(self.workflow["concurrency"]["cancel-in-progress"], "false")
        build = self.action("docker/build-push-action")
        self.assertIn("org.opencontainers.image.revision=${{ github.sha }}", build["with"]["labels"])

    def test_metadata_targets_the_backend_and_tags_by_sha(self):
        metadata = self.action("docker/metadata-action")
        self.assertEqual(metadata["with"]["images"], "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}")
        tags = set(metadata["with"]["tags"].splitlines())
        self.assertIn("type=sha,format=long", tags)
        self.assertIn("type=ref,event=tag", tags)

    def test_published_architecture_and_signature_are_verified(self):
        architecture = self.named("Verify published backend manifest architectures")
        self.assertEqual(architecture["if"], "github.event_name != 'pull_request'")
        self.assertIn("linux/amd64", architecture["run"])
        self.assertIn("linux/arm64", architecture["run"])
        sign = self.named("Sign the published GHCR image")
        verify = self.named("Verify keyless image signature")
        self.assertIn("cosign sign --yes", sign["run"])
        self.assertIn("cosign verify", verify["run"])
        self.assertIn("certificate-identity", verify["run"])
        self.assertIn("certificate-oidc-issuer", verify["run"])

    def test_current_buildx_and_cosign_versions_are_pinned(self):
        build = self.action("docker/build-push-action")
        self.assertEqual(build["uses"], "docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc")
        cosign = self.named("Install cosign")
        self.assertEqual(cosign["uses"], "sigstore/cosign-installer@756fe2d284c7292c4e9b62c8a28f1e5629c59532")
        self.assertEqual(cosign["with"]["cosign-release"], "v3.1.4")

    def test_every_action_is_pinned_to_a_full_commit_sha(self):
        for step in self.steps:
            action = step.get("uses")
            if action:
                with self.subTest(action=action):
                    self.assertRegex(action.rsplit("@", 1)[-1], re.compile(r"^[0-9a-fA-F]{40}$"))


class RelatedWorkflowDependencyTests(unittest.TestCase):
    def test_all_image_build_workflows_use_buildx_v7_4_0(self):
        paths = (
            ".github/workflows/container.yml",
            ".github/workflows/devcontainer.yml",
            ".github/workflows/docker-publish.yml",
        )
        build_actions = []
        for path in paths:
            workflow = load_workflow(path)
            build_actions.extend(
                step["uses"]
                for job in workflow["jobs"].values()
                for step in job["steps"]
                if step.get("uses", "").startswith("docker/build-push-action@")
            )
        self.assertGreaterEqual(len(build_actions), 5)
        self.assertEqual(set(build_actions), {"docker/build-push-action@c3c9e263c25d99ce0380d002d59b67737d91b0dc"})

    def test_codecov_v7_uses_the_current_files_input(self):
        workflow = load_workflow(".github/workflows/coverage.yml")
        uploads = [
            step for job in workflow["jobs"].values() for step in job["steps"]
            if step.get("uses", "").startswith("codecov/codecov-action@")
        ]
        self.assertEqual(len(uploads), 1)
        self.assertEqual(uploads[0]["uses"], "codecov/codecov-action@303a32d7a59b442fa8d48b6a1cc6825c09c847a5")
        self.assertEqual(uploads[0]["with"]["files"], "ERP-BACKEND/coverage.xml")
        self.assertNotIn("file", uploads[0]["with"])


class KubernetesPreflightWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = load_workflow(".github/workflows/kubernetes-preflight.yml")
        cls.job = cls.workflow["jobs"]["preflight"]
        cls.steps = cls.job["steps"]

    def named(self, name):
        found = [step for step in self.steps if step.get("name") == name]
        self.assertEqual(len(found), 1, f"Expected exactly one step named {name}")
        return found[0]

    def test_manual_dispatch_and_dedicated_runner_only(self):
        events = self.workflow["on"]
        self.assertEqual(set(events), {"workflow_dispatch"})
        self.assertEqual(
            events["workflow_dispatch"]["inputs"]["namespace"]["options"],
            ["erp03-staging", "erp03"],
        )
        self.assertEqual(self.job["runs-on"], ["self-hosted", "linux", "erp03-k8s"])
        self.assertEqual(self.job["if"], "github.ref == 'refs/heads/main'")

    def test_read_only_permissions_and_namespace_rbac_are_explicit(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        context = self.named("Validate runner context and read-only RBAC")["run"]
        self.assertIn("kubectl auth can-i get namespaces", context)
        for resource in ("deployments", "pods", "persistentvolumeclaims", "services", "ingresses"):
            self.assertIn(f'kubectl auth can-i list "$resource"', context)

    def test_no_cluster_mutation_commands_are_present(self):
        commands = "\n".join(step.get("run", "") for step in self.steps)
        self.assertIsNone(re.search(r"\bkubectl\s+(apply|create|patch|delete|exec|run|rollout|scale|set)\b", commands))

    def test_production_gate_is_target_specific(self):
        step = self.named("Render overlays and enforce the selected environment's image policy")
        self.assertEqual(step["env"]["TARGET_NAMESPACE"], "${{ inputs.namespace }}")
        self.assertIn('erp03-staging) target_environment="staging"', step["run"])
        self.assertIn('erp03) target_environment="production"', step["run"])
        self.assertIn('if [[ "$target_environment" == "production" ]]; then', step["run"])
        self.assertIn("::warning::Staging base images still contain digest placeholders", step["run"])

    def test_action_references_are_pinned(self):
        for step in self.steps:
            action = step.get("uses")
            if action:
                with self.subTest(action=action):
                    self.assertRegex(action.rsplit("@", 1)[-1], re.compile(r"^[0-9a-fA-F]{40}$"))


if __name__ == "__main__":
    unittest.main()
