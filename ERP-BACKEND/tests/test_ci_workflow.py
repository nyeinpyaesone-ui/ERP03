"""
Unit tests for the new `.github/workflows/ci.yml` GitHub Actions workflow.

This PR introduces the CI workflow from scratch with four jobs: `backend`,
`frontend`, `production-config`, and `docker-build`. These tests validate the
structure and content of the resulting file using lightweight text-based
assertions, consistent with this repo's existing conventions for validating
config files (see tests/test_env_file.py and tests/test_gitignore.py),
without requiring a YAML parsing dependency that isn't already part of the
project.
"""
import os
import re

import pytest


CI_WORKFLOW_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".github", "workflows", "ci.yml")
)

JOB_ORDER = ["backend", "frontend", "production-config", "docker-build"]


@pytest.fixture(scope="module")
def ci_workflow_text():
    with open(CI_WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _job_section(text, job_name):
    """Return the text of a single top-level job block (from its header up
    to, but not including, the next top-level job header)."""
    header = f"\n  {job_name}:\n"
    start = text.index(header)
    other_headers = [f"\n  {j}:\n" for j in JOB_ORDER if j != job_name]
    search_from = start + len(header)
    ends = [text.index(h, search_from) for h in other_headers if h in text[search_from:]]
    end = min(ends) if ends else len(text)
    return text[start:end]


class TestCiWorkflowFileIntegrity:
    """Structural sanity checks on the workflow file itself."""

    def test_ci_workflow_file_exists(self):
        assert os.path.isfile(CI_WORKFLOW_PATH)

    def test_ci_workflow_is_not_empty(self, ci_workflow_text):
        assert len(ci_workflow_text.strip()) > 0

    def test_workflow_name_is_ci(self, ci_workflow_text):
        assert ci_workflow_text.startswith("name: CI\n")

    def test_permissions_restricted_to_read(self, ci_workflow_text):
        """Least-privilege check: the workflow should not request broader
        permissions than reading repo contents."""
        assert "permissions:\n  contents: read\n" in ci_workflow_text


class TestCiWorkflowTriggers:
    def test_triggers_on_pull_request_to_main(self, ci_workflow_text):
        assert "pull_request:\n    branches: [main]" in ci_workflow_text

    def test_triggers_on_push_to_main(self, ci_workflow_text):
        assert "push:\n    branches: [main]" in ci_workflow_text


class TestCiWorkflowJobsPresence:
    @pytest.mark.parametrize("job_name", JOB_ORDER)
    def test_job_defined_exactly_once(self, ci_workflow_text, job_name):
        header = f"\n  {job_name}:\n"
        assert ci_workflow_text.count(header) == 1

    def test_jobs_appear_in_expected_order(self, ci_workflow_text):
        positions = [ci_workflow_text.index(f"\n  {j}:\n") for j in JOB_ORDER]
        assert positions == sorted(positions), (
            "Jobs are not declared in the expected order: "
            f"{JOB_ORDER}"
        )


class TestCiWorkflowBackendJob:
    @pytest.fixture(scope="class")
    def backend_job(self, ci_workflow_text):
        return _job_section(ci_workflow_text, "backend")

    def test_working_directory_is_erp_backend(self, backend_job):
        assert "working-directory: ERP-BACKEND" in backend_job

    def test_uses_python_3_11(self, backend_job):
        assert "python-version: '3.11'" in backend_job

    def test_pip_cache_configured_for_requirements(self, backend_job):
        assert "cache: pip" in backend_job
        assert "cache-dependency-path: ERP-BACKEND/requirements.txt" in backend_job

    def test_installs_requirements(self, backend_job):
        assert "pip install -r requirements.txt" in backend_job

    def test_compiles_app_package(self, backend_job):
        """Regression guard: a syntax error anywhere in `app` should fail CI
        before the (potentially slower) test suite runs."""
        assert "python -m compileall -q app" in backend_job

    def test_runs_pytest_quietly(self, backend_job):
        assert "pytest -q" in backend_job

    def test_test_mode_env_is_true(self, backend_job):
        assert "TEST_MODE: 'true'" in backend_job

    def test_secret_key_env_present(self, backend_job):
        match = re.search(r"SECRET_KEY:\s*(\S+)", backend_job)
        assert match, "SECRET_KEY env var not found in backend job"

    def test_secret_key_meets_minimum_length(self, backend_job):
        """The app's settings validation requires SECRET_KEY to be at least
        32 characters; CI must supply a value that satisfies this or the
        test suite will fail to even boot the app settings."""
        match = re.search(r"SECRET_KEY:\s*(\S+)", backend_job)
        assert match
        secret_value = match.group(1)
        assert len(secret_value) >= 32, (
            f"CI SECRET_KEY value is only {len(secret_value)} characters, "
            "expected at least 32"
        )


class TestCiWorkflowFrontendJob:
    @pytest.fixture(scope="class")
    def frontend_job(self, ci_workflow_text):
        return _job_section(ci_workflow_text, "frontend")

    def test_working_directory_is_frontend(self, frontend_job):
        assert "working-directory: frontend" in frontend_job

    def test_uses_node_20(self, frontend_job):
        assert "node-version: '20'" in frontend_job

    def test_npm_cache_configured_for_lockfile(self, frontend_job):
        assert "cache: npm" in frontend_job
        assert "cache-dependency-path: frontend/package-lock.json" in frontend_job

    def test_runs_npm_ci(self, frontend_job):
        assert "npm ci" in frontend_job

    def test_runs_lint(self, frontend_job):
        assert "npm run lint" in frontend_job

    def test_runs_build(self, frontend_job):
        assert "npm run build" in frontend_job

    def test_lint_runs_before_build(self, frontend_job):
        assert frontend_job.index("npm run lint") < frontend_job.index("npm run build")


class TestCiWorkflowProductionConfigJob:
    @pytest.fixture(scope="class")
    def production_config_job(self, ci_workflow_text):
        return _job_section(ci_workflow_text, "production-config")

    def test_validates_compose_config(self, production_config_job):
        assert "docker compose -f docker-compose.prod.yml config" in production_config_job

    def test_validates_compose_config_quietly_too(self, production_config_job):
        assert "docker compose -f docker-compose.prod.yml config --quiet" in production_config_job

    def test_referenced_compose_file_exists_in_repo(self):
        """Cross-file sanity check: the file this job validates must exist
        at the repo root path referenced by the workflow."""
        compose_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose.prod.yml")
        )
        assert os.path.isfile(compose_path)


class TestCiWorkflowDockerBuildJob:
    @pytest.fixture(scope="class")
    def docker_build_job(self, ci_workflow_text):
        return _job_section(ci_workflow_text, "docker-build")

    def test_builds_backend_image_with_correct_context_and_file(self, docker_build_job):
        assert "context: ./ERP-BACKEND" in docker_build_job
        assert "file: ./ERP-BACKEND/Dockerfile" in docker_build_job
        assert "tags: erp03/backend:ci" in docker_build_job

    def test_builds_frontend_image_with_correct_context_and_file(self, docker_build_job):
        assert "context: ./frontend" in docker_build_job
        assert "file: ./frontend/Dockerfile" in docker_build_job
        assert "tags: erp03/frontend:ci" in docker_build_job

    def test_neither_image_is_pushed(self, docker_build_job):
        """Security/regression guard: CI should only validate that images
        build successfully, never publish them."""
        assert docker_build_job.count("push: false") == 2
        assert "push: true" not in docker_build_job

    def test_referenced_dockerfiles_exist_in_repo(self):
        backend_dockerfile = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
        )
        frontend_dockerfile = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "Dockerfile")
        )
        assert os.path.isfile(backend_dockerfile)
        assert os.path.isfile(frontend_dockerfile)


class TestCiWorkflowPinnedActionVersions:
    """Regression guard against unpinned/downgraded third-party actions."""

    def test_checkout_pinned_to_v4_in_every_job(self, ci_workflow_text):
        assert ci_workflow_text.count("actions/checkout@v4") == len(JOB_ORDER)

    def test_setup_python_pinned_to_v5(self, ci_workflow_text):
        assert "actions/setup-python@v5" in ci_workflow_text

    def test_setup_node_pinned_to_v4(self, ci_workflow_text):
        assert "actions/setup-node@v4" in ci_workflow_text

    def test_setup_buildx_pinned_to_v3(self, ci_workflow_text):
        assert ci_workflow_text.count("docker/setup-buildx-action@v3") == 2

    def test_build_push_action_pinned_to_v6(self, ci_workflow_text):
        assert ci_workflow_text.count("docker/build-push-action@v6") == 2
