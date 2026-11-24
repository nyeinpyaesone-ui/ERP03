"""Regression checks for immutable stateful images in the production Compose path."""

from pathlib import Path


def test_compose_stateful_images_are_pinned_to_verified_multi_platform_digests() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    compose = (repository_root / "docker-compose.yml").read_text(encoding="utf-8")

    assert (
        "image: postgres:15.20-alpine3.24@sha256:"
        "e18480a22d6e48f4d816a6696769b1ec09ac73a824c5649e49c7d8b684913f3d"
    ) in compose
    assert (
        "image: redis:7.4.12-alpine3.22@sha256:"
        "7f7d30b7fdd09467bac58198a1f166dd69789d348d4fe859cccb20e0cf287fbe"
    ) in compose

    assert "image: postgres:15.14" not in compose
    assert "image: redis:7-alpine" not in compose
