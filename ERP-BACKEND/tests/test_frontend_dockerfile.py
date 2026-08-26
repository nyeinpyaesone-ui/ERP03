"""
Unit tests for `frontend/Dockerfile`.

This PR makes the following changes to this file:

1. Renames the stage-1 comment for clarity.
2. Changes the builder-stage dependency install from
   `npm ci --only=production` to `npm ci --include=dev`. This is a
   functional fix: the frontend build script (`tsc && vite build`) relies
   on devDependencies (typescript, vite), so installing only production
   dependencies would have caused the build step to fail.
3. Combines the `apk add`/`rm` and `chown`/`chmod` RUN instructions in the
   production stage into single instructions using `&&` continuations
   (fewer image layers), without changing their behavior.

These tests validate the resulting file using lightweight text-based
assertions, consistent with this repo's existing conventions for testing
config files (see tests/test_env_file.py and tests/test_gitignore.py).
"""
import os

import pytest


FRONTEND_DOCKERFILE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "Dockerfile")
)


@pytest.fixture(scope="module")
def dockerfile_text():
    """Read and return the complete text content of the frontend Dockerfile."""
    with open(FRONTEND_DOCKERFILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def dockerfile_lines(dockerfile_text):
    """Split the Dockerfile text into individual lines for line-based assertions."""
    return dockerfile_text.splitlines()


class TestFrontendDockerfileIntegrity:
    def test_dockerfile_exists(self):
        """Verify that the frontend Dockerfile exists at the expected path."""
        assert os.path.isfile(FRONTEND_DOCKERFILE_PATH)

    def test_dockerfile_is_not_empty(self, dockerfile_text):
        """Verify that the Dockerfile contains non-whitespace content."""
        assert len(dockerfile_text.strip()) > 0

    def test_still_has_two_named_stages(self, dockerfile_text):
        """Verify that both the builder and production stages are defined."""
        assert "FROM node:20-alpine AS builder" in dockerfile_text
        assert "FROM nginx:1.25-alpine AS production" in dockerfile_text


class TestFrontendDockerfileStageComment:
    def test_stage_one_comment_updated(self, dockerfile_text):
        """Verify that the stage 1 comment was updated to the new wording."""
        assert "# Stage 1: deterministic production build" in dockerfile_text

    def test_old_stage_one_comment_removed(self, dockerfile_text):
        """Verify that the old stage 1 comment wording is no longer present."""
        assert "# Stage 1: Build Environment" not in dockerfile_text


class TestFrontendDockerfileNpmInstallFix:
    """Regression tests for the npm install flag fix.

    `npm ci --only=production` would have skipped devDependencies, but the
    frontend's `npm run build` script (`tsc && vite build`) requires
    typescript/vite, which are devDependencies. `--include=dev` ensures
    they are installed for the build stage.
    """

    def test_npm_ci_includes_dev_dependencies(self, dockerfile_text):
        """Verify that npm ci includes dev dependencies for the build."""
        assert "npm ci --include=dev" in dockerfile_text

    def test_production_only_flag_removed(self, dockerfile_text):
        """Verify that the --only=production flag is no longer present."""
        assert "--only=production" not in dockerfile_text

    def test_npm_cache_still_cleaned_after_install(self, dockerfile_text):
        """Verify that npm cache is cleaned after installation."""
        assert "npm ci --include=dev && npm cache clean --force" in dockerfile_text

    def test_npm_install_happens_before_source_copy(self, dockerfile_text):
        """Ensure dependencies are installed before application source files are copied to preserve Docker layer caching."""
        install_index = dockerfile_text.index("npm ci --include=dev")
        copy_source_index = dockerfile_text.index("COPY . .")
        assert install_index < copy_source_index

    def test_build_runs_after_install(self, dockerfile_text):
        """Verify that the build step runs after dependency installation."""
        install_index = dockerfile_text.index("npm ci --include=dev")
        build_index = dockerfile_text.index("RUN npm run build")
        assert install_index < build_index


class TestFrontendDockerfileProductionStageConsolidation:
    """The apk add/rm and chown/chmod pairs were merged into single RUN
    instructions via `&&` continuations; behavior should be unchanged."""

    def test_apk_add_and_remove_default_conf_combined(self, dockerfile_text):
        """Verify that apk add and rm default.conf are combined in one RUN instruction."""
        assert (
            "RUN apk add --no-cache bash \\\n    && rm /etc/nginx/conf.d/default.conf"
            in dockerfile_text
        )

    def test_only_one_run_instruction_for_apk_and_rm(self, dockerfile_lines):
        """Verify that only one RUN instruction exists for apk add."""
        apk_run_lines = [
            line for line in dockerfile_lines if line.strip().startswith("RUN apk add")
        ]
        assert len(apk_run_lines) == 1

    def test_chown_and_chmod_combined(self, dockerfile_text):
        """Verify that chown and chmod are combined in one RUN instruction."""
        assert (
            "RUN chown -R nginx:nginx /usr/share/nginx/html \\\n    && chmod -R 755 /usr/share/nginx/html"
            in dockerfile_text
        )

    def test_only_one_run_instruction_for_chown_and_chmod(self, dockerfile_lines):
        """Verify that only one RUN instruction exists for chown."""
        chown_run_lines = [
            line for line in dockerfile_lines if line.strip().startswith("RUN chown")
        ]
        assert len(chown_run_lines) == 1


class TestFrontendDockerfileUnrelatedInstructionsUnaffected:
    """Sanity checks that unrelated instructions untouched by this PR are
    still intact."""

    def test_default_nginx_conf_still_replaced(self, dockerfile_text):
        """Verify that nginx.conf is still copied to the default location."""
        assert "COPY nginx.conf /etc/nginx/conf.d/default.conf" in dockerfile_text

    def test_dist_still_copied_from_builder(self, dockerfile_text):
        """Verify that the dist directory is still copied from the builder stage."""
        assert "COPY --from=builder /app/dist /usr/share/nginx/html" in dockerfile_text

    def test_healthcheck_unchanged(self, dockerfile_text):
        """Verify that the HEALTHCHECK instruction remains unchanged."""
        assert (
            "HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3"
            in dockerfile_text
        )
        assert (
            "CMD wget --quiet --tries=1 --spider http://localhost:80/ || exit 1"
            in dockerfile_text
        )

    def test_expose_80_present(self, dockerfile_text):
        """Verify that port 80 is exposed."""
        assert "EXPOSE 80" in dockerfile_text

    def test_cmd_runs_nginx_in_foreground(self, dockerfile_text):
        """Verify that CMD runs nginx in foreground mode."""
        assert 'CMD ["nginx", "-g", "daemon off;"]' in dockerfile_text
