#!/usr/bin/env python3
"""Minimal GitHub repository webhook receiver for host-level ERP03 deployment."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
import hmac
import json
import os
import subprocess

HOST = os.getenv("WEBHOOK_HOST", "127.0.0.1")
PORT = int(os.getenv("WEBHOOK_PORT", "9001"))
SECRET = os.environ["GITHUB_WEBHOOK_SECRET"].encode()
REPOSITORY = os.getenv("GITHUB_REPOSITORY", "nyeinpyaesone-ui/ERP03")
BRANCH = os.getenv("GITHUB_BRANCH", "main")
DEPLOY_SCRIPT = os.getenv("DEPLOY_SCRIPT", "/opt/erp03/deploy-from-github.sh")


def valid_signature(body: bytes, header: str | None) -> bool:
    if not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)


class Handler(BaseHTTPRequestHandler):
    def _respond(self, status: int, message: str) -> None:
        body = message.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/github/webhook":
            self._respond(404, "not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        if not valid_signature(body, self.headers.get("X-Hub-Signature-256")):
            self._respond(401, "invalid signature")
            return

        event = self.headers.get("X-GitHub-Event", "")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, "invalid json")
            return

        if payload.get("repository", {}).get("full_name") != REPOSITORY:
            self._respond(202, "ignored repository")
            return

        deploy = False
        if event == "workflow_run":
            run = payload.get("workflow_run", {})
            deploy = (
                run.get("action") == "completed"
                and run.get("conclusion") == "success"
                and run.get("head_branch") == BRANCH
            )
        elif event == "push" and os.getenv("DEPLOY_ON_PUSH", "false").lower() == "true":
            deploy = payload.get("ref") == f"refs/heads/{BRANCH}"

        if not deploy:
            self._respond(202, "ignored event")
            return

        try:
            subprocess.Popen(
                [DEPLOY_SCRIPT],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            self._respond(500, "deployment start failed")
            return

        self._respond(202, "deployment started")

    def log_message(self, fmt: str, *args) -> None:
        print("github-webhook:", fmt % args, flush=True)


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
