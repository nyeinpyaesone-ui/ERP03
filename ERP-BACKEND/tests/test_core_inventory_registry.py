"""
Unit tests for the module registry and route inventory
(app/core/inventory/registry.py).
"""
from datetime import datetime

import pytest

from app.core.inventory.registry import (
    AuthRequirement,
    Dependency,
    HttpMethod,
    ModuleRegistry,
    RouteInventory,
)


class TestHttpMethod:
    """Tests for the HttpMethod string enum."""

    @pytest.mark.parametrize(
        "member,expected",
        [
            (HttpMethod.GET, "GET"),
            (HttpMethod.POST, "POST"),
            (HttpMethod.PUT, "PUT"),
            (HttpMethod.PATCH, "PATCH"),
            (HttpMethod.DELETE, "DELETE"),
            (HttpMethod.HEAD, "HEAD"),
        ],
    )
    def test_member_values(self, member, expected):
        assert member.value == expected
        assert member == expected

    def test_is_a_str_subclass(self):
        assert isinstance(HttpMethod.GET, str)


class TestAuthRequirement:
    """Tests for the AuthRequirement string enum."""

    @pytest.mark.parametrize(
        "member,expected",
        [
            (AuthRequirement.NONE, "none"),
            (AuthRequirement.AUTHENTICATED, "authenticated"),
            (AuthRequirement.SPECIFIC_ROLE, "specific_role"),
            (AuthRequirement.SPECIFIC_PERMISSION, "specific_permission"),
        ],
    )
    def test_member_values(self, member, expected):
        assert member.value == expected
        assert member == expected


class TestDependency:
    """Tests for the Dependency dataclass and its custom equality/hash."""

    def test_critical_defaults_to_true(self):
        dep = Dependency(type="database", name="invoice")
        assert dep.critical is True

    def test_critical_can_be_set_explicitly(self):
        dep = Dependency(type="database", name="invoice", critical=False)
        assert dep.critical is False

    def test_equality_is_based_only_on_type_and_name(self):
        dep1 = Dependency(type="database", name="invoice", critical=True)
        dep2 = Dependency(type="database", name="invoice", critical=False)
        assert dep1 == dep2

    def test_inequality_for_different_name(self):
        dep1 = Dependency(type="database", name="invoice")
        dep2 = Dependency(type="database", name="payment")
        assert dep1 != dep2

    def test_inequality_for_different_type(self):
        dep1 = Dependency(type="database", name="invoice")
        dep2 = Dependency(type="cache", name="invoice")
        assert dep1 != dep2

    def test_equality_against_non_dependency_object_is_false(self):
        dep = Dependency(type="database", name="invoice")
        assert (dep == "database:invoice") is False
        assert (dep == 42) is False
        assert dep != object()

    def test_hash_is_consistent_with_equality(self):
        dep1 = Dependency(type="database", name="invoice", critical=True)
        dep2 = Dependency(type="database", name="invoice", critical=False)
        assert hash(dep1) == hash(dep2)

    def test_equal_dependencies_deduplicate_in_a_set(self):
        dep1 = Dependency(type="database", name="invoice", critical=True)
        dep2 = Dependency(type="database", name="invoice", critical=False)
        assert len({dep1, dep2}) == 1


class TestRouteInventory:
    """Tests for the RouteInventory dataclass."""

    def _make_route(self, **overrides):
        defaults = dict(
            path="/api/v1/finance/invoices",
            method=HttpMethod.GET,
            module_name="finance",
            handler_function="list_invoices",
            description="List all invoices",
            auth_requirement=AuthRequirement.AUTHENTICATED,
            auth_details="REQUIRES: finance.read",
        )
        defaults.update(overrides)
        return RouteInventory(**defaults)

    def test_default_collection_and_scalar_fields(self):
        route = self._make_route()

        assert route.reads_database_tables == set()
        assert route.writes_database_tables == set()
        assert route.dependencies == set()
        assert route.idempotency_required is False
        assert route.requires_saga is False
        assert route.cacheable is False
        assert route.cache_ttl_seconds is None
        assert route.state_machine is None
        assert route.events_emitted == set()
        assert route.events_consumed == set()
        assert isinstance(route.created_at, datetime)
        assert isinstance(route.last_modified_at, datetime)

    def test_default_factory_collections_are_independent_per_instance(self):
        """Regression: mutable default containers must not be shared across
        instances (a classic dataclass footgun avoided via field(default_factory=...))."""
        route1 = self._make_route(path="/a")
        route2 = self._make_route(path="/b")

        route1.reads_database_tables.add("invoice")
        route1.events_emitted.add("invoice.created")

        assert route2.reads_database_tables == set()
        assert route2.events_emitted == set()

    @pytest.mark.parametrize(
        "method", [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH, HttpMethod.DELETE]
    )
    def test_is_write_operation_true_for_mutating_methods(self, method):
        route = self._make_route(method=method)
        assert route.is_write_operation is True
        assert route.is_read_operation is False

    @pytest.mark.parametrize("method", [HttpMethod.GET, HttpMethod.HEAD])
    def test_is_read_operation_true_for_safe_methods(self, method):
        route = self._make_route(method=method)
        assert route.is_read_operation is True
        assert route.is_write_operation is False

    def test_equality_is_based_only_on_path_and_method(self):
        route1 = self._make_route(handler_function="handler_a", description="desc a")
        route2 = self._make_route(handler_function="handler_b", description="desc b")
        assert route1 == route2

    def test_inequality_for_different_path(self):
        route1 = self._make_route(path="/a")
        route2 = self._make_route(path="/b")
        assert route1 != route2

    def test_inequality_for_different_method(self):
        route1 = self._make_route(method=HttpMethod.GET)
        route2 = self._make_route(method=HttpMethod.POST)
        assert route1 != route2

    def test_equality_against_non_route_inventory_object_is_false(self):
        route = self._make_route()
        assert (route == "not-a-route") is False

    def test_hash_consistent_with_equality_allows_set_dedup(self):
        route1 = self._make_route(handler_function="a")
        route2 = self._make_route(handler_function="b")
        assert hash(route1) == hash(route2)
        assert len({route1, route2}) == 1

    def test_to_dict_structure_with_default_values(self):
        route = self._make_route()
        result = route.to_dict()

        assert result["path"] == "/api/v1/finance/invoices"
        assert result["method"] == "GET"
        assert result["module"] == "finance"
        assert result["handler"] == "list_invoices"
        assert result["description"] == "List all invoices"
        assert result["auth"] == {
            "requirement": "authenticated",
            "details": "REQUIRES: finance.read",
        }
        assert result["data"] == {"reads": [], "writes": []}
        assert result["dependencies"] == []
        assert result["operational"] == {
            "idempotency_required": False,
            "requires_saga": False,
            "cacheable": False,
            "cache_ttl_seconds": None,
        }
        assert result["workflow"] == {
            "state_machine": None,
            "events_emitted": [],
            "events_consumed": [],
        }

    def test_to_dict_sorts_reads_writes_and_workflow_events(self):
        route = self._make_route(
            reads_database_tables={"zeta", "alpha"},
            writes_database_tables={"gamma", "beta"},
            events_emitted={"z_event", "a_event"},
            events_consumed={"y_event", "b_event"},
        )
        result = route.to_dict()

        assert result["data"]["reads"] == ["alpha", "zeta"]
        assert result["data"]["writes"] == ["beta", "gamma"]
        assert result["workflow"]["events_emitted"] == ["a_event", "z_event"]
        assert result["workflow"]["events_consumed"] == ["b_event", "y_event"]

    def test_to_dict_sorts_dependencies_by_name_and_serializes_fields(self):
        route = self._make_route(
            dependencies={
                Dependency(type="service", name="zeta_service", critical=False),
                Dependency(type="database", name="alpha_table", critical=True),
            }
        )
        result = route.to_dict()

        assert [d["name"] for d in result["dependencies"]] == ["alpha_table", "zeta_service"]
        by_name = {d["name"]: d for d in result["dependencies"]}
        assert by_name["alpha_table"] == {"type": "database", "name": "alpha_table", "critical": True}
        assert by_name["zeta_service"] == {"type": "service", "name": "zeta_service", "critical": False}

    def test_to_dict_reflects_operational_and_workflow_flags(self):
        route = self._make_route(
            idempotency_required=True,
            requires_saga=True,
            cacheable=True,
            cache_ttl_seconds=300,
            state_machine="draft -> pending -> approved",
        )
        result = route.to_dict()

        assert result["operational"] == {
            "idempotency_required": True,
            "requires_saga": True,
            "cacheable": True,
            "cache_ttl_seconds": 300,
        }
        assert result["workflow"]["state_machine"] == "draft -> pending -> approved"


class TestModuleRegistry:
    """Tests for the ModuleRegistry dataclass."""

    def _route(self, path, method, module_name, **overrides):
        defaults = dict(
            path=path,
            method=method,
            module_name=module_name,
            handler_function="handler",
            description="desc",
            auth_requirement=AuthRequirement.AUTHENTICATED,
            auth_details="",
        )
        defaults.update(overrides)
        return RouteInventory(**defaults)

    def test_register_module_stores_description(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "Financial transaction management")
        assert reg.modules == {"finance": "Financial transaction management"}

    def test_register_module_overwrites_existing_entry(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "v1 description")
        reg.register_module("finance", "v2 description")
        assert reg.modules["finance"] == "v2 description"

    def test_register_route_raises_when_module_not_registered(self):
        reg = ModuleRegistry()
        route = self._route("/api/v1/x", HttpMethod.GET, "finance")

        with pytest.raises(ValueError, match="not registered"):
            reg.register_route(route)

    def test_register_route_succeeds_for_registered_module(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        route = self._route("/api/v1/x", HttpMethod.GET, "finance")

        reg.register_route(route)

        assert route in reg.routes
        assert len(reg.routes) == 1

    def test_register_route_is_idempotent_for_duplicate_path_and_method(self):
        """Regression: registering a route with the same (path, method) twice
        must not create duplicate entries, since RouteInventory equality/hash
        is defined on (path, method) alone."""
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        route1 = self._route("/api/v1/x", HttpMethod.GET, "finance", handler_function="h1")
        route2 = self._route("/api/v1/x", HttpMethod.GET, "finance", handler_function="h2")

        reg.register_route(route1)
        reg.register_route(route2)

        assert len(reg.routes) == 1

    def test_get_module_routes_filters_by_module_and_sorts_by_path_and_method(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        reg.register_module("inventory", "desc")
        r_b = self._route("/api/v1/b", HttpMethod.GET, "finance")
        r_a = self._route("/api/v1/a", HttpMethod.GET, "finance")
        r_other_module = self._route("/api/v1/c", HttpMethod.GET, "inventory")
        for r in (r_b, r_a, r_other_module):
            reg.register_route(r)

        finance_routes = reg.get_module_routes("finance")

        assert [r.path for r in finance_routes] == ["/api/v1/a", "/api/v1/b"]

    def test_get_module_routes_returns_empty_list_for_unknown_module(self):
        reg = ModuleRegistry()
        assert reg.get_module_routes("does-not-exist") == []

    def test_get_routes_by_table_matches_reads_and_writes(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        r_read = self._route("/a", HttpMethod.GET, "finance", reads_database_tables={"invoice"})
        r_write = self._route("/b", HttpMethod.POST, "finance", writes_database_tables={"invoice"})
        r_unrelated = self._route("/c", HttpMethod.GET, "finance", reads_database_tables={"payment"})
        for r in (r_read, r_write, r_unrelated):
            reg.register_route(r)

        matched_paths = {r.path for r in reg.get_routes_by_table("invoice")}

        assert matched_paths == {"/a", "/b"}

    def test_get_routes_by_table_returns_empty_when_no_match(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        reg.register_route(self._route("/a", HttpMethod.GET, "finance", reads_database_tables={"payment"}))

        assert reg.get_routes_by_table("invoice") == []

    def test_get_write_routes_returns_only_mutating_routes(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        r_get = self._route("/a", HttpMethod.GET, "finance")
        r_post = self._route("/b", HttpMethod.POST, "finance")
        reg.register_route(r_get)
        reg.register_route(r_post)

        assert reg.get_write_routes() == [r_post]

    def test_get_routes_requiring_idempotency(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        r_idempotent = self._route("/a", HttpMethod.POST, "finance", idempotency_required=True)
        r_plain = self._route("/b", HttpMethod.POST, "finance", idempotency_required=False)
        reg.register_route(r_idempotent)
        reg.register_route(r_plain)

        assert reg.get_routes_requiring_idempotency() == [r_idempotent]

    def test_get_routes_with_saga(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "desc")
        r_saga = self._route("/a", HttpMethod.POST, "finance", requires_saga=True)
        r_plain = self._route("/b", HttpMethod.POST, "finance", requires_saga=False)
        reg.register_route(r_saga)
        reg.register_route(r_plain)

        assert reg.get_routes_with_saga() == [r_saga]

    def test_to_dict_structure_and_counts(self):
        reg = ModuleRegistry()
        reg.register_module("finance", "Financial transaction management")
        r_read = self._route("/a", HttpMethod.GET, "finance")
        r_write = self._route(
            "/b", HttpMethod.POST, "finance", idempotency_required=True, requires_saga=True
        )
        reg.register_route(r_read)
        reg.register_route(r_write)

        result = reg.to_dict()

        assert result["modules"] == {"finance": "Financial transaction management"}
        assert result["routes_count"] == 2
        assert result["write_routes_count"] == 1
        assert result["idempotency_required_count"] == 1
        assert result["saga_routes_count"] == 1
        assert [r["path"] for r in result["routes"]] == ["/a", "/b"]

    def test_to_dict_with_no_routes_or_modules(self):
        reg = ModuleRegistry()
        result = reg.to_dict()

        assert result["modules"] == {}
        assert result["routes_count"] == 0
        assert result["write_routes_count"] == 0
        assert result["idempotency_required_count"] == 0
        assert result["saga_routes_count"] == 0
        assert result["routes"] == []

    def test_to_dict_routes_sorted_by_module_then_path(self):
        reg = ModuleRegistry()
        reg.register_module("sales", "desc")
        reg.register_module("finance", "desc")
        reg.register_route(self._route("/b", HttpMethod.GET, "sales"))
        reg.register_route(self._route("/a", HttpMethod.GET, "finance"))

        result = reg.to_dict()

        assert [(r["module"], r["path"]) for r in result["routes"]] == [
            ("finance", "/a"),
            ("sales", "/b"),
        ]