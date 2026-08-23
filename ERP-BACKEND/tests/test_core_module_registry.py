"""
Unit tests for the module registry (app/core/module_registry.py).
"""
import pytest
from unittest.mock import MagicMock

from app.core.module_registry import ModuleDescriptor, ModuleRegistry, registry as global_registry


class TestModuleDescriptor:
    """Tests for the ModuleDescriptor dataclass."""

    def test_depends_on_defaults_to_empty_list(self):
        desc = ModuleDescriptor(name="finance", version="1.0.0", router_factory=lambda: None)
        assert desc.depends_on == []

    def test_depends_on_default_is_independent_per_instance(self):
        desc1 = ModuleDescriptor(name="a", version="1", router_factory=lambda: None)
        desc2 = ModuleDescriptor(name="b", version="1", router_factory=lambda: None)

        desc1.depends_on.append("x")

        assert desc2.depends_on == []

    def test_depends_on_can_be_supplied_explicitly(self):
        desc = ModuleDescriptor(
            name="finance", version="1.0.0", router_factory=lambda: None, depends_on=["core"],
        )
        assert desc.depends_on == ["core"]


class TestModuleRegistryRegister:
    """Tests for ModuleRegistry.register and .get."""

    def test_register_and_get_returns_same_descriptor(self):
        reg = ModuleRegistry()
        desc = ModuleDescriptor(name="finance", version="1.0.0", router_factory=lambda: None)

        reg.register(desc)

        assert reg.get("finance") is desc

    def test_register_duplicate_name_raises_value_error(self):
        reg = ModuleRegistry()
        reg.register(ModuleDescriptor(name="finance", version="1.0.0", router_factory=lambda: None))

        with pytest.raises(ValueError, match="already registered"):
            reg.register(ModuleDescriptor(name="finance", version="2.0.0", router_factory=lambda: None))

    def test_get_missing_module_raises_key_error(self):
        reg = ModuleRegistry()
        with pytest.raises(KeyError):
            reg.get("missing")


class TestModuleRegistryAll:
    """Tests for ModuleRegistry.all."""

    def test_all_returns_empty_list_when_no_modules(self):
        reg = ModuleRegistry()
        assert reg.all() == []

    def test_all_returns_every_registered_descriptor(self):
        reg = ModuleRegistry()
        d1 = ModuleDescriptor(name="a", version="1", router_factory=lambda: None)
        d2 = ModuleDescriptor(name="b", version="1", router_factory=lambda: None)
        reg.register(d1)
        reg.register(d2)

        result = reg.all()

        assert len(result) == 2
        assert d1 in result
        assert d2 in result


class TestModuleRegistryMountAll:
    """Tests for ModuleRegistry.mount_all."""

    def test_mount_all_includes_router_with_prefix_and_tags(self):
        reg = ModuleRegistry()
        fake_router = object()
        factory = MagicMock(return_value=fake_router)
        reg.register(ModuleDescriptor(name="finance", version="1.0.0", router_factory=factory))
        app = MagicMock()

        reg.mount_all(app, prefix="/api/v1")

        factory.assert_called_once()
        app.include_router.assert_called_once_with(fake_router, prefix="/api/v1/finance", tags=["finance"])

    def test_mount_all_default_prefix_is_api_v1(self):
        reg = ModuleRegistry()
        reg.register(ModuleDescriptor(name="hr", version="1.0.0", router_factory=MagicMock(return_value=object())))
        app = MagicMock()

        reg.mount_all(app)

        _, kwargs = app.include_router.call_args
        assert kwargs["prefix"] == "/api/v1/hr"

    def test_mount_all_mounts_every_registered_module(self):
        reg = ModuleRegistry()
        reg.register(ModuleDescriptor(name="a", version="1", router_factory=MagicMock(return_value=object())))
        reg.register(ModuleDescriptor(name="b", version="1", router_factory=MagicMock(return_value=object())))
        app = MagicMock()

        reg.mount_all(app)

        assert app.include_router.call_count == 2

    def test_mount_all_with_no_modules_does_not_call_include_router(self):
        reg = ModuleRegistry()
        app = MagicMock()

        reg.mount_all(app)

        app.include_router.assert_not_called()


class TestGlobalRegistrySingleton:
    """Tests for the module-level registry singleton."""

    def test_global_registry_is_module_registry_instance(self):
        assert isinstance(global_registry, ModuleRegistry)