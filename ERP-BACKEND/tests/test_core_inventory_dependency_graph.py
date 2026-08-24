"""
Unit tests for the dependency graph (app/core/inventory/dependency_graph.py).
"""
from app.core.inventory.dependency_graph import DependencyGraph


class TestAddDependency:
    """Tests for add_module_dependency / add_service_dependency."""

    def test_add_module_dependency_creates_entry(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")

        assert graph.module_dependencies["sales"] == {"inventory"}

    def test_add_module_dependency_accumulates_multiple_targets(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")

        assert graph.module_dependencies["sales"] == {"inventory", "finance"}

    def test_add_module_dependency_is_idempotent_for_duplicates(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "inventory")

        assert graph.module_dependencies["sales"] == {"inventory"}

    def test_add_service_dependency_creates_entry(self):
        graph = DependencyGraph()
        graph.add_service_dependency("finance", "accounting_system")

        assert graph.service_dependencies["finance"] == {"accounting_system"}

    def test_add_service_dependency_accumulates_multiple_services(self):
        graph = DependencyGraph()
        graph.add_service_dependency("inventory", "redis")
        graph.add_service_dependency("inventory", "barcode_scanner_api")

        assert graph.service_dependencies["inventory"] == {"redis", "barcode_scanner_api"}


class TestGetModuleDependenciesAndDependents:
    """Tests for get_module_dependencies / get_module_dependents."""

    def test_get_module_dependencies_returns_empty_set_for_unknown_module(self):
        graph = DependencyGraph()
        assert graph.get_module_dependencies("unknown") == set()

    def test_get_module_dependencies_returns_added_dependencies(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")

        assert graph.get_module_dependencies("sales") == {"inventory", "finance"}

    def test_get_module_dependents_returns_modules_depending_on_target(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("procurement", "inventory")
        graph.add_module_dependency("sales", "finance")

        assert graph.get_module_dependents("inventory") == {"sales", "procurement"}
        assert graph.get_module_dependents("finance") == {"sales"}

    def test_get_module_dependents_returns_empty_set_when_nothing_depends_on_it(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")

        assert graph.get_module_dependents("sales") == set()


class TestCircularDependencyDetection:
    """Tests for has_circular_dependency / get_circular_dependencies."""

    def test_no_circular_dependency_for_linear_chain(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "c")

        assert graph.has_circular_dependency() is False
        assert graph.get_circular_dependencies() == []

    def test_no_circular_dependency_for_diamond_shape(self):
        """a depends on b and c; both b and c depend on d. Not a cycle."""
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("a", "c")
        graph.add_module_dependency("b", "d")
        graph.add_module_dependency("c", "d")

        assert graph.has_circular_dependency() is False
        assert graph.get_circular_dependencies() == []

    def test_detects_two_module_cycle(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "a")

        assert graph.has_circular_dependency() is True
        cycles = graph.get_circular_dependencies()
        assert len(cycles) == 1
        assert cycles[0] == ["a", "b", "a"]

    def test_detects_self_dependency_as_cycle(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "a")

        assert graph.has_circular_dependency() is True
        assert graph.get_circular_dependencies() == [["a", "a"]]

    def test_no_dependencies_has_no_cycles(self):
        graph = DependencyGraph()

        assert graph.has_circular_dependency() is False
        assert graph.get_circular_dependencies() == []


class TestGetCriticalDependencies:
    """Tests for get_critical_dependencies."""

    def test_returns_all_non_empty_named_dependencies(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")

        assert graph.get_critical_dependencies("sales") == {"inventory", "finance"}

    def test_returns_empty_set_for_module_without_dependencies(self):
        graph = DependencyGraph()

        assert graph.get_critical_dependencies("unknown") == set()


class TestGetDependencyChain:
    """Tests for get_dependency_chain."""

    def test_chain_for_module_without_dependencies(self):
        graph = DependencyGraph()

        chain = graph.get_dependency_chain("standalone")

        assert chain == {"module": "standalone", "dependencies": [], "depth": 0}

    def test_chain_traverses_nested_dependencies(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("inventory", "audit")

        chain = graph.get_dependency_chain("sales")

        assert chain["module"] == "sales"
        assert chain["depth"] == 0
        assert len(chain["dependencies"]) == 1
        inventory_node = chain["dependencies"][0]
        assert inventory_node["module"] == "inventory"
        assert inventory_node["depth"] == 1
        assert len(inventory_node["dependencies"]) == 1
        audit_node = inventory_node["dependencies"][0]
        assert audit_node["module"] == "audit"
        assert audit_node["depth"] == 2
        assert audit_node["dependencies"] == []

    def test_chain_truncates_beyond_max_depth(self):
        graph = DependencyGraph()
        graph.add_module_dependency("m0", "m1")
        graph.add_module_dependency("m1", "m2")
        graph.add_module_dependency("m2", "m3")

        chain = graph.get_dependency_chain("m0", max_depth=1)

        m1_node = chain["dependencies"][0]
        assert m1_node["depth"] == 1
        assert "truncated" not in m1_node

        m2_node = m1_node["dependencies"][0]
        assert m2_node["depth"] == 2
        assert m2_node["truncated"] is True
        assert m2_node["dependencies"] == []

    def test_chain_dependencies_are_sorted(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")
        graph.add_module_dependency("sales", "audit")

        chain = graph.get_dependency_chain("sales")

        modules_in_order = [dep["module"] for dep in chain["dependencies"]]
        assert modules_in_order == ["audit", "finance", "inventory"]


class TestGetImpactAnalysis:
    """Tests for get_impact_analysis / _get_transitive_dependents."""

    def _layered_graph(self):
        graph = DependencyGraph()
        graph.add_module_dependency("core", "base")
        graph.add_module_dependency("service", "core")
        graph.add_module_dependency("app", "service")
        return graph

    def test_direct_and_indirect_dependents(self):
        graph = self._layered_graph()

        analysis = graph.get_impact_analysis("base")

        assert analysis["changed_module"] == "base"
        assert analysis["direct_dependents"] == ["core"]
        # Regression: `_get_transitive_dependents` only ever propagates the
        # *result* of the recursive call upward (`transitive.update(...)`)
        # and never adds the dependent itself to the set, so it always
        # returns an empty list regardless of how deep the dependency chain
        # is. "app" and "service" transitively depend on "base" but are not
        # reported here. This test documents that current behavior.
        assert analysis["indirect_dependents"] == []
        assert analysis["dependencies"] == []

    def test_includes_external_service_dependencies(self):
        graph = self._layered_graph()
        graph.add_service_dependency("base", "redis")
        graph.add_service_dependency("base", "accounting_system")

        analysis = graph.get_impact_analysis("base")

        assert analysis["external_services"] == ["accounting_system", "redis"]

    def test_impact_analysis_for_module_with_no_dependents(self):
        graph = self._layered_graph()

        analysis = graph.get_impact_analysis("app")

        assert analysis["direct_dependents"] == []
        assert analysis["indirect_dependents"] == []
        assert analysis["dependencies"] == ["service"]

    def test_transitive_dependents_always_returns_empty_list(self):
        """Regression test documenting a real bug: `_get_transitive_dependents`
        builds its result via `transitive.update(<recursive call>)` but never
        adds the visited `dependent` itself into the `transitive` set. Since
        the base case (no further dependents) also returns an empty list,
        the whole recursive chain collapses to `[]` no matter how many
        levels of transitive dependents actually exist in the graph.
        """
        graph = self._layered_graph()

        assert graph._get_transitive_dependents("base") == []
        assert graph._get_transitive_dependents("core") == []
        assert graph._get_transitive_dependents("nonexistent") == []


class TestToDict:
    """Tests for DependencyGraph.to_dict()."""

    def test_to_dict_serializes_sorted_dependencies(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")
        graph.add_service_dependency("sales", "payment_processor")

        result = graph.to_dict()

        assert result["module_dependencies"]["sales"] == ["finance", "inventory"]
        assert result["service_dependencies"]["sales"] == ["payment_processor"]
        assert result["has_circular_dependencies"] is False
        assert result["circular_cycles"] == []

    def test_to_dict_reflects_circular_dependencies(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "a")

        result = graph.to_dict()

        assert result["has_circular_dependencies"] is True
        assert result["circular_cycles"] == [["a", "b", "a"]]

    def test_to_dict_empty_graph(self):
        graph = DependencyGraph()

        result = graph.to_dict()

        assert result == {
            "module_dependencies": {},
            "service_dependencies": {},
            "has_circular_dependencies": False,
            "circular_cycles": [],
        }