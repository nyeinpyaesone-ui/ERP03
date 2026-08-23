"""
Unit tests for the module/route inventory registry
(app/core/inventory/registry.py).
"""
import pytest

from app.core.inventory.registry import (
    HttpMethod,
    AuthRequirement,
    Dependency,
    RouteInventory,
    ModuleRegistry,
)


def make_route(path="/api/v1/finance/invoices", method=HttpMethod.GET, module_name="finance", **overrides):
    """Helper to build a RouteInventory with sensible defaults for tests."""
    kwargs = dict(
        path=path,
        method=method,
        module_name=module_name,
        handler_function="list_invoices",
        description="List invoices",
        auth_requirement=AuthRequirement.AUTHENTICATED,
        auth_details="REQUIRES: finance.read",
    )
    kwargs.update(overrides)
    return RouteInventory(**kwargs)


class TestHttpMethod:
    """Tests for the HttpMethod string enum."""

    def test_members_equal_their_string_values(self):
        assert HttpMethod.GET == "GET"
        assert HttpMethod.POST == "POST"
        assert HttpMethod.PUT == "PUT"
        assert HttpMethod.PATCH == "PATCH"
        assert HttpMethod.DELETE == "DELETE"
        assert HttpMethod.HEAD == "HEAD"

    def test_value_attribute(self):
        assert HttpMethod.GET.value == "GET"


class TestAuthRequirement:
    """Tests for the AuthRequirement string enum."""

    def test_members_equal_their_string_values(self):
        assert AuthRequirement.NONE == "none"
        assert AuthRequirement.AUTHENTICATED == "authenticated"
        assert AuthRequirement.SPECIFIC_ROLE == "specific_role"
        assert AuthRequirement.SPECIFIC_PERMISSION == "specific_permission"


class TestDependency:
    """Tests for the Dependency dataclass."""

    def test_critical_defaults_to_true(self):
        dep = Dependency(type="database", name="invoice")
        assert dep.critical is True

    def test_equality_ignores_critical_flag(self):
        d1 = Dependency(type="database", name="invoice", critical=True)
        d2 = Dependency(type="database", name="invoice", critical=False)
        assert d1 == d2

    def test_equality_requires_matching_type_and_name(self):
        d1 = Dependency(type="database", name="invoice")
        d2 = Dependency(type="service", name="invoice")
        d3 = Dependency(type="database", name="payment")
        assert d1 != d2
        assert d1 != d3

    def test_equality_with_non_dependency_returns_false(self):
        dep = Dependency(type="database", name="invoice")
        assert (dep == "invoice") is False
        assert (dep == 42) is False

    def test_hash_matches_for_equal_dependencies(self):
        d1 = Dependency(type="database", name="invoice", critical=True)
        d2 = Dependency(type="database", name="invoice", critical=False)
        assert hash(d1) == hash(d2)

    def test_deduplicates_in_a_set(self):
        d1 = Dependency(type="database", name="invoice", critical=True)
        d2 = Dependency(type="database", name="invoice", critical=False)
        d3 = Dependency(type="service", name="audit")

        deps = {d1, d2, d3}

        assert len(deps) == 2


class TestRouteInventoryDefaults:
    """Tests for RouteInventory default field values."""

    def test_defaults_are_empty_collections(self):
        route = make_route()

        assert route.reads_database_tables == set()
        assert route.writes_database_tables == set()
        assert route.dependencies == set()
        assert route.events_emitted == set()
        assert route.events_consumed == set()

    def test_operational_defaults(self):
        route = make_route()

        assert route.idempotency_required is False
        assert route.requires_saga is False
        assert route.cacheable is False
        assert route.cache_ttl_seconds is None
        assert route.state_machine is None

    def test_mutable_defaults_are_independent_per_instance(self):
        """Regression: default_factory-based sets must not be shared across instances."""
        route1 = make_route(path="/a")
        route2 = make_route(path="/b")

        route1.reads_database_tables.add("invoice")
        route1.dependencies.add(Dependency(type="database", name="invoice"))

        assert route2.reads_database_tables == set()
        assert route2.dependencies == set()


class TestRouteInventoryEqualityAndHash:
    """Tests for RouteInventory equality/hash based on (path, method)."""

    def test_equal_when_path_and_method_match(self):
        route1 = make_route(path="/api/v1/x", method=HttpMethod.GET, module_name="a", description="first")
        route2 = make_route(path="/api/v1/x", method=HttpMethod.GET, module_name="b", description="second")

        assert route1 == route2
        assert hash(route1) == hash(route2)

    def test_not_equal_when_method_differs(self):
        route1 = make_route(path="/api/v1/x", method=HttpMethod.GET)
        route2 = make_route(path="/api/v1/x", method=HttpMethod.POST)

        assert route1 != route2

    def test_not_equal_when_path_differs(self):
        route1 = make_route(path="/api/v1/x", method=HttpMethod.GET)
        route2 = make_route(path="/api/v1/y", method=HttpMethod.GET)

        assert route1 != route2

    def test_equality_with_non_route_inventory_returns_false(self):
        route = make_route()
        assert (route == "not a route") is False


class TestRouteInventoryOperationTypeProperties:
    """Tests for is_write_operation / is_read_operation."""

    @pytest.mark.parametrize("method", [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH, HttpMethod.DELETE])
    def test_is_write_operation_true_for_mutating_methods(self, method):
        route = make_route(method=method)
        assert route.is_write_operation is True
        assert route.is_read_operation is False

    @pytest.mark.parametrize("method", [HttpMethod.GET, HttpMethod.HEAD])
    def test_is_read_operation_true_for_safe_methods(self, method):
        route = make_route(method=method)
        assert route.is_read_operation is True
        assert route.is_write_operation is False


class TestRouteInventoryToDict:
    """Tests for RouteInventory.to_dict()."""

    def test_to_dict_basic_fields(self):
        route = make_route(
            path="/api/v1/finance/invoices/{id}/approve",
            method=HttpMethod.POST,
            module_name="finance",
            handler_function="approve_invoice",
            description="Approve invoice",
            auth_requirement=AuthRequirement.SPECIFIC_PERMISSION,
            auth_details="REQUIRES: finance.approve",
            idempotency_required=True,
            requires_saga=False,
            cacheable=True,
            cache_ttl_seconds=300,
            state_machine="draft -> pending -> approved",
        )

        result = route.to_dict()

        assert result["path"] == "/api/v1/finance/invoices/{id}/approve"
        assert result["method"] == "POST"
        assert result["module"] == "finance"
        assert result["handler"] == "approve_invoice"
        assert result["description"] == "Approve invoice"
        assert result["auth"] == {
            "requirement": "specific_permission",
            "details": "REQUIRES: finance.approve",
        }
        assert result["operational"] == {
            "idempotency_required": True,
            "requires_saga": False,
            "cacheable": True,
            "cache_ttl_seconds": 300,
        }
        assert result["workflow"]["state_machine"] == "draft -> pending -> approved"

    def test_to_dict_sorts_reads_and_writes(self):
        route = make_route(
            reads_database_tables={"invoice", "customer"},
            writes_database_tables={"invoice_line_items", "audit_log"},
        )

        result = route.to_dict()

        assert result["data"]["reads"] == ["customer", "invoice"]
        assert result["data"]["writes"] == ["audit_log", "invoice_line_items"]

    def test_to_dict_sorts_dependencies_by_name(self):
        route = make_route(
            dependencies={
                Dependency(type="service", name="notifications", critical=False),
                Dependency(type="database", name="invoice"),
                Dependency(type="external", name="accounting_system"),
            }
        )

        result = route.to_dict()

        names = [d["name"] for d in result["dependencies"]]
        assert names == ["accounting_system", "invoice", "notifications"]
        assert {"type": "database", "name": "invoice", "critical": True} in result["dependencies"]
        assert {"type": "service", "name": "notifications", "critical": False} in result["dependencies"]

    def test_to_dict_sorts_events(self):
        route = make_route(
            events_emitted={"invoice.approved", "invoice.created"},
            events_consumed={"payment.received"},
        )

        result = route.to_dict()

        assert result["workflow"]["events_emitted"] == ["invoice.approved", "invoice.created"]
        assert result["workflow"]["events_consumed"] == ["payment.received"]


class TestModuleRegistryRegisterModuleAndRoute:
    """Tests for ModuleRegistry.register_module / register_route."""

    def test_register_module_stores_description(self):
        registry = ModuleRegistry()
        registry.register_module("finance", "Financial transactions")

        assert registry.modules["finance"] == "Financial transactions"

    def test_register_route_requires_module_to_be_registered(self):
        registry = ModuleRegistry()
        route = make_route(module_name="finance")

        with pytest.raises(ValueError, match="not registered"):
            registry.register_route(route)

    def test_register_route_succeeds_after_module_registered(self):
        registry = ModuleRegistry()
        registry.register_module("finance", "Financial transactions")
        route = make_route(module_name="finance")

        registry.register_route(route)

        assert route in registry.routes

    def test_register_route_duplicate_path_and_method_does_not_replace_original(self):
        """Sets don't overwrite an already-"equal" element, so re-registering a
        route with the same (path, method) keeps the first one that was added."""
        registry = ModuleRegistry()
        registry.register_module("finance", "Financial transactions")
        original = make_route(module_name="finance", description="original")
        duplicate = make_route(module_name="finance", description="duplicate")

        registry.register_route(original)
        registry.register_route(duplicate)

        assert len(registry.routes) == 1
        (stored_route,) = registry.routes
        assert stored_route.description == "original"


class TestModuleRegistryQueries:
    """Tests for ModuleRegistry query helper methods."""

    def _build_registry(self):
        registry = ModuleRegistry()
        registry.register_module("finance", "Financial transactions")
        registry.register_module("inventory", "Stock tracking")

        list_route = make_route(
            path="/api/v1/finance/invoices",
            method=HttpMethod.GET,
            module_name="finance",
            reads_database_tables={"invoice"},
        )
        create_route = make_route(
            path="/api/v1/finance/invoices",
            method=HttpMethod.POST,
            module_name="finance",
            writes_database_tables={"invoice"},
            idempotency_required=True,
        )
        adjust_route = make_route(
            path="/api/v1/inventory/stock/{sku}/adjust",
            method=HttpMethod.POST,
            module_name="inventory",
            writes_database_tables={"stock_levels"},
            idempotency_required=True,
            requires_saga=True,
        )
        registry.register_route(list_route)
        registry.register_route(create_route)
        registry.register_route(adjust_route)
        return registry, list_route, create_route, adjust_route

    def test_get_module_routes_filters_and_sorts(self):
        registry, list_route, create_route, _adjust_route = self._build_registry()

        finance_routes = registry.get_module_routes("finance")

        assert finance_routes == [list_route, create_route]

    def test_get_module_routes_returns_empty_for_unknown_module(self):
        registry, *_ = self._build_registry()

        assert registry.get_module_routes("does-not-exist") == []

    def test_get_routes_by_table_matches_reads_or_writes(self):
        registry, list_route, create_route, _adjust_route = self._build_registry()

        routes = registry.get_routes_by_table("invoice")

        assert set(routes) == {list_route, create_route}

    def test_get_routes_by_table_returns_empty_when_no_match(self):
        registry, *_ = self._build_registry()

        assert registry.get_routes_by_table("nonexistent_table") == []

    def test_get_write_routes(self):
        registry, list_route, create_route, adjust_route = self._build_registry()

        write_routes = registry.get_write_routes()

        assert set(write_routes) == {create_route, adjust_route}
        assert list_route not in write_routes

    def test_get_routes_requiring_idempotency(self):
        registry, list_route, create_route, adjust_route = self._build_registry()

        routes = registry.get_routes_requiring_idempotency()

        assert set(routes) == {create_route, adjust_route}
        assert list_route not in routes

    def test_get_routes_with_saga(self):
        registry, list_route, create_route, adjust_route = self._build_registry()

        routes = registry.get_routes_with_saga()

        assert routes == [adjust_route]


class TestModuleRegistryToDict:
    """Tests for ModuleRegistry.to_dict()."""

    def test_to_dict_empty_registry(self):
        registry = ModuleRegistry()

        result = registry.to_dict()

        assert result["modules"] == {}
        assert result["routes_count"] == 0
        assert result["write_routes_count"] == 0
        assert result["idempotency_required_count"] == 0
        assert result["saga_routes_count"] == 0
        assert result["routes"] == []

    def test_to_dict_counts_and_route_serialization(self):
        registry = ModuleRegistry()
        registry.register_module("finance", "Financial transactions")
        registry.register_module("inventory", "Stock tracking")

        list_route = make_route(path="/z", method=HttpMethod.GET, module_name="finance")
        write_route = make_route(
            path="/a", method=HttpMethod.POST, module_name="inventory", idempotency_required=True, requires_saga=True
        )
        registry.register_route(list_route)
        registry.register_route(write_route)

        result = registry.to_dict()

        assert result["routes_count"] == 2
        assert result["write_routes_count"] == 1
        assert result["idempotency_required_count"] == 1
        assert result["saga_routes_count"] == 1
        # Sorted by (module_name, path): "finance" before "inventory"
        assert [r["module"] for r in result["routes"]] == ["finance", "inventory"]
        assert result["routes"][0]["path"] == "/z"
        assert result["routes"][1]["path"] == "/a"