"""
Unit tests for the repository-root `.gitignore` file.

This PR rewrote `.gitignore` from scratch (see diff), reorganizing the
sections and changing several patterns. These tests validate the resulting
file's structure and its ability to actually keep sensitive/generated files
out of version control.
"""
import os

import pytest


GITIGNORE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".gitignore")
)


@pytest.fixture(scope="module")
def gitignore_lines():
    with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
        return f.read().splitlines()


@pytest.fixture(scope="module")
def gitignore_patterns(gitignore_lines):
    """Non-empty, non-comment lines, i.e. the actual ignore patterns."""
    return [
        line.strip()
        for line in gitignore_lines
        if line.strip() and not line.strip().startswith("#")
    ]


class TestGitignoreFileIntegrity:
    """Structural sanity checks on the .gitignore file itself."""

    def test_gitignore_file_exists(self):
        assert os.path.isfile(GITIGNORE_PATH)

    def test_gitignore_has_no_markdown_code_fence_artifacts(self, gitignore_lines):
        """Regression: earlier revisions of this file accidentally included
        stray markdown code-fence markers (```) as literal lines, which git
        would otherwise interpret as a literal ignore pattern for a file or
        directory named '```'."""
        fence_lines = [line for line in gitignore_lines if line.strip() == "```"]
        assert fence_lines == [], (
            "Found stray markdown code-fence marker(s) in .gitignore: "
            f"{fence_lines!r}. These are not valid/intended ignore patterns."
        )

    def test_gitignore_is_not_empty(self, gitignore_patterns):
        assert len(gitignore_patterns) > 0


class TestGitignorePythonArtifacts:
    """Patterns that keep Python build/cache artifacts out of the repo."""

    @pytest.mark.parametrize("expected", ["__pycache__/", "*.py[cod]", "*.so"])
    def test_contains_python_bytecode_and_native_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns

    def test_contains_build_and_dist_directories(self, gitignore_patterns):
        for expected in ("build/", "dist/", "*.egg-info/"):
            assert expected in gitignore_patterns


class TestGitignoreEnvironmentAndIde:
    """Patterns for virtual environments, IDE files, logs and caches."""

    @pytest.mark.parametrize("expected", [".venv/", "venv/"])
    def test_contains_virtualenv_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns

    @pytest.mark.parametrize("expected", [".vscode/", ".idea/"])
    def test_contains_ide_directory_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns

    def test_contains_log_pattern(self, gitignore_patterns):
        assert "*.log" in gitignore_patterns

    @pytest.mark.parametrize("expected", [".pytest_cache/", ".mypy_cache/", ".coverage"])
    def test_contains_test_and_coverage_cache_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns


class TestGitignoreNativeAndExecutableArtifacts:
    """Patterns added in this revision for compiled/native and executable
    artifacts across ecosystems (not just Python)."""

    @pytest.mark.parametrize(
        "expected", ["*.pyc", "*.o", "*.obj", "*.dll", "*.exe", "*.class", "*.out"]
    )
    def test_contains_native_and_executable_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns


class TestGitignoreSystemFiles:
    """OS-specific junk files that should never be committed."""

    @pytest.mark.parametrize("expected", [".DS_Store", "Thumbs.db"])
    def test_contains_os_specific_file_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns


class TestGitignoreEditorAndTempFiles:
    """Editor swap/backup files and generic temp files."""

    @pytest.mark.parametrize("expected", ["*.tmp", "*.swp", "*.swo"])
    def test_contains_temp_and_swap_file_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns


class TestGitignoreBuildAndCoverageDirectories:
    """Additional build/coverage directories introduced in this revision."""

    @pytest.mark.parametrize(
        "expected", ["target/", ".gradle/", "coverage/", "htmlcov/", ".coverage"]
    )
    def test_contains_build_and_coverage_directory_patterns(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns


class TestGitignoreArchivePatterns:
    """This revision adds an entirely new 'Archives' section covering a wide
    range of compressed/archive file extensions. Every pattern listed there
    should be present verbatim."""

    ARCHIVE_PATTERNS = [
        "*.zip", "*.gz", "*.tar", "*.tgz", "*.bz2", "*.xz", "*.7z", "*.rar",
        "*.zst", "*.lz4", "*.lzh", "*.cab", "*.arj", "*.rpm", "*.deb", "*.Z",
        "*.lz", "*.lzo", "*.tar.gz", "*.tar.bz2", "*.tar.xz", "*.tar.zst",
    ]

    @pytest.mark.parametrize("expected", ARCHIVE_PATTERNS)
    def test_contains_archive_pattern(self, gitignore_patterns, expected):
        assert expected in gitignore_patterns

    def test_archive_patterns_have_no_duplicates(self, gitignore_patterns):
        """Regression: guards against accidentally duplicating an archive
        pattern (e.g. copy-paste errors) when this long list was authored."""
        archive_lines = [p for p in gitignore_patterns if p in self.ARCHIVE_PATTERNS]
        assert len(archive_lines) == len(set(archive_lines))

    def test_all_archive_patterns_present_count_matches(self, gitignore_patterns):
        present = [p for p in self.ARCHIVE_PATTERNS if p in gitignore_patterns]
        assert len(present) == len(self.ARCHIVE_PATTERNS)


class TestGitignoreSecretsRegression:
    """Security-focused regression checks.

    The previous version of `.gitignore` (pre-PR) explicitly ignored `.env`,
    `.env.local` and `*.env.*`. The rewritten `.gitignore` shipped in this PR
    drops all of those patterns in favor of only ignoring virtualenv
    directories named `env/`/`ENV/`. As a direct, observable consequence,
    `ERP-BACKEND/.env` (containing what look like credentials/secrets) is now
    tracked in this repository.
    """

    def test_env_file_pattern_is_present(self, gitignore_patterns):
        """This is expected to fail against the .gitignore shipped in this
        PR: no pattern here matches a literal `.env` file, meaning
        environment/secret files are no longer excluded from version control.
        This is flagged as a security regression introduced by the .gitignore
        rewrite in this PR.
        """
        env_patterns = {".env", ".env.*", "*.env", "*.env.*", ".env.local"}
        assert env_patterns & set(gitignore_patterns), (
            "No '.env' ignore pattern found in .gitignore. The previous "
            "version ignored '.env', '.env.local' and '*.env.*'; this "
            "appears to have been dropped, which can lead to committing "
            "secrets (see ERP-BACKEND/.env, which is currently tracked)."
        )