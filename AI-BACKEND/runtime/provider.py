from __future__ import annotations

from typing import Protocol


class ModelProvider(Protocol):
    async def generate(self, prompt: str) -> str: ...


class DeterministicProvider:
    """Safe MVP provider used for routing tests; no external model dependency."""

    async def generate(self, prompt: str) -> str:
        return prompt
