#!/usr/bin/env python3
"""ERP03 AI DevOps control plane.

Provider-agnostic and fail-safe: local Ollama is preferred; Gemini can be enabled
explicitly with GEMINI_API_KEY. The tool never sends repository secrets by itself.
It produces a deterministic baseline report when no AI provider is available.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MAX_DIFF_CHARS = 80_000
DEFAULT_MODEL = "qwen2.5:3b"


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()


def git_diff(base: str | None, head: str) -> str:
    if base:
        return run(["git", "diff", "--no-ext-diff", "--unified=2", base, head])[:MAX_DIFF_CHARS]
    try:
        parent = run(["git", "rev-parse", f"{head}^"])
        return run(["git", "diff", "--no-ext-diff", "--unified=2", parent, head])[:MAX_DIFF_CHARS]
    except subprocess.CalledProcessError:
        return run(["git", "show", "--format=", "--no-ext-diff", head])[:MAX_DIFF_CHARS]


def changed_files(base: str | None, head: str) -> list[str]:
    if base:
        output = run(["git", "diff", "--name-only", base, head])
    else:
        try:
            parent = run(["git", "rev-parse", f"{head}^"])
            output = run(["git", "diff", "--name-only", parent, head])
        except subprocess.CalledProcessError:
            output = run(["git", "show", "--format=", "--name-only", head])
    return [line for line in output.splitlines() if line]


def safe_prompt(files: list[str], diff: str) -> str:
    return f"""You are the ERP03 release engineering reviewer. Analyze only the supplied change.

Repository rules:
- correctness before performance
- modular monolith boundaries; no speculative microservices
- no secrets or credentials in source
- migrations must be explicit and deterministic
- CI must fail on real qualification failures
- deployments require verification before promotion

Return strict JSON with keys: summary, risks, required_actions, validation.
Each of risks/required_actions/validation must be an array of concise strings.
Do not invent files, tests, vulnerabilities, or infrastructure that are not evidenced.

Changed files:
{json.dumps(files, indent=2)}

Diff:
{diff}
"""


def call_ollama(prompt: str) -> str | None:
    base_url = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
    if not base_url:
        return None
    model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json"}).encode()
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode())
        return body.get("response")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def call_gemini(prompt: str) -> str | None:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    request = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode())
        return body["candidates"][0]["content"]["parts"][0]["text"]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError, OSError):
        return None


def deterministic_report(files: list[str], diff: str) -> dict[str, object]:
    lower = diff.lower()
    risks: list[str] = []
    actions: list[str] = []
    validation = ["Run the existing ERP03 qualification workflow before promotion."]
    secret_markers = ("password=", "secret=", "api_key=", "private_key", "authorization: bearer")
    if any(marker in lower for marker in secret_markers):
        risks.append("Potential credential-like content is present in the diff; review before merge.")
        actions.append("Remove credentials from source and use the repository/environment secret store.")
    if any(path.endswith((".yml", ".yaml")) and ".github/workflows/" in path for path in files):
        validation.append("Validate workflow YAML and confirm least-privilege permissions.")
    if any("alembic" in path.lower() or "migration" in path.lower() for path in files):
        validation.append("Apply migrations from a clean database and verify upgrade succeeds.")
    if any(path.startswith("ERP-BACKEND/") for path in files):
        validation.append("Run backend compilation and pytest qualification.")
    if any(path.startswith("frontend/") for path in files):
        validation.append("Run frontend lint and production build.")
    return {
        "summary": f"Reviewed {len(files)} changed file(s) with the deterministic ERP03 control plane.",
        "risks": risks,
        "required_actions": actions,
        "validation": validation,
    }


def parse_result(raw: str, fallback: dict[str, object]) -> dict[str, object]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return fallback


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=None)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--output", default="ai-devops-report.json")
    args = parser.parse_args()

    files = changed_files(args.base, args.head)
    diff = git_diff(args.base, args.head)
    fallback = deterministic_report(files, diff)
    prompt = safe_prompt(files, diff)

    provider = "deterministic"
    raw = call_ollama(prompt)
    if raw:
        provider = "ollama"
    elif os.getenv("GEMINI_API_KEY"):
        raw = call_gemini(prompt)
        if raw:
            provider = "gemini"

    report = parse_result(raw, fallback) if raw else fallback
    report["provider"] = provider
    report["changed_files"] = files

    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
