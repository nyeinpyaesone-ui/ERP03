from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ModuleDescriptor:
    name: str
    version: str
    router_factory: Callable
    depends_on: list[str] = field(default_factory=list)


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleDescriptor] = {}

    def register(self, descriptor: ModuleDescriptor) -> None:
        if descriptor.name in self._modules:
            raise ValueError(f"Module '{descriptor.name}' already registered")
        self._modules[descriptor.name] = descriptor

    def get(self, name: str) -> ModuleDescriptor:
        return self._modules[name]

    def all(self) -> list[ModuleDescriptor]:
        return list(self._modules.values())

    def mount_all(self, app, prefix: str = "/api/v1") -> None:
        for desc in self._modules.values():
            router = desc.router_factory()
            app.include_router(router, prefix=f"{prefix}/{desc.name}", tags=[desc.name])


registry = ModuleRegistry()
