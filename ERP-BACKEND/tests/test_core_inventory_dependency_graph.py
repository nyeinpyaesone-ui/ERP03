"""
Unit tests for the dependency graph (app/core/inventory/dependency_graph.py).
"""
from app.core.inventory.dependency_graph import DependencyGraph


class TestAddModuleDependency:
    """Tests for DependencyGraph.add_module_dependency."""

    def test_adds_dependency_for_new_module(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")

        assert graph.get_module_dependencies("sales") == {"inventory"}

    def test_accumulates_multiple_dependencies_for_same_module(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")

        assert graph.get_module_dependencies("sales") == {"inventory", "finance"}

    def test_adding_same_dependency_twice_is_idempotent(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "inventory")

        assert graph.get_module_dependencies("sales") == {"inventory"}


class TestAddServiceDependency:
    """Tests for DependencyGraph.add_service_dependency."""

    def test_adds_service_dependency(self):
        graph = DependencyGraph()
        graph.add_service_dependency("finance", "accounting_system")

        assert graph.service_dependencies["finance"] == {"accounting_system"}

    def test_accumulates_multiple_service_dependencies(self):
        graph = DependencyGraph()
        graph.add_service_dependency("inventory", "redis")
        graph.add_service_dependency("inventory", "barcode_scanner_api")

        assert graph.service_dependencies["inventory"] == {"redis", "barcode_scanner_api"}


class TestGetModuleDependencies:
    """Tests for DependencyGraph.get_module_dependencies."""

    def test_returns_empty_set_for_unknown_module(self):
        graph = DependencyGraph()
        assert graph.get_module_dependencies("unknown") == set()

    def test_does_not_mutate_graph_when_queried(self):
        graph = DependencyGraph()
        graph.get_module_dependencies("unknown")
        assert graph.module_dependencies == {}


class TestGetModuleDependents:
    """Tests for DependencyGraph.get_module_dependents."""

    def test_returns_all_modules_that_depend_on_given_module(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("procurement", "inventory")

        assert graph.get_module_dependents("inventory") == {"sales", "procurement"}

    def test_returns_empty_set_when_nothing_depends_on_module(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")

        assert graph.get_module_dependents("sales") == set()

    def test_returns_empty_set_for_completely_unknown_module(self):
        graph = DependencyGraph()
        assert graph.get_module_dependents("unknown") == set()


class TestHasCircularDependency:
    """Tests for DependencyGraph.has_circular_dependency."""

    def test_false_for_empty_graph(self):
        graph = DependencyGraph()
        assert graph.has_circular_dependency() is False

    def test_false_for_acyclic_graph(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("inventory", "finance")

        assert graph.has_circular_dependency() is False

    def test_true_for_direct_two_node_cycle(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "a")

        assert graph.has_circular_dependency() is True

    def test_true_for_longer_cycle(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "c")
        graph.add_module_dependency("c", "a")

        assert graph.has_circular_dependency() is True

    def test_true_for_self_dependency(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "a")

        assert graph.has_circular_dependency() is True


class TestGetCircularDependencies:
    """Tests for DependencyGraph.get_circular_dependencies."""

    def test_empty_list_for_acyclic_graph(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")

        assert graph.get_circular_dependencies() == []

    def test_returns_cycle_path_for_three_node_cycle(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "c")
        graph.add_module_dependency("c", "a")

        cycles = graph.get_circular_dependencies()

        assert cycles == [["a", "b", "c", "a"]]

    def test_returns_self_loop_cycle(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "a")

        cycles = graph.get_circular_dependencies()

        assert cycles == [["a", "a"]]

    def test_empty_list_for_empty_graph(self):
        graph = DependencyGraph()
        assert graph.get_circular_dependencies() == []


class TestGetCriticalDependencies:
    """Tests for DependencyGraph.get_critical_dependencies."""

    def test_returns_all_non_empty_dependency_names(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")

        assert graph.get_critical_dependencies("sales") == {"inventory", "finance"}

    def test_excludes_falsy_dependency_names(self):
        """The implementation filters dependencies with `if dep_module:`, so
        an (unusual) empty-string dependency name is excluded from the
        critical set."""
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "")
        graph.add_module_dependency("sales", "inventory")

        assert graph.get_critical_dependencies("sales") == {"inventory"}

    def test_empty_set_for_module_with_no_dependencies(self):
        graph = DependencyGraph()
        assert graph.get_critical_dependencies("unknown") == set()


class TestGetDependencyChain:
    """Tests for DependencyGraph.get_dependency_chain."""

    def test_module_with_no_dependencies_returns_leaf_node(self):
        graph = DependencyGraph()
        chain = graph.get_dependency_chain("standalone")

        assert chain == {"module": "standalone", "dependencies": [], "depth": 0}

    def test_builds_nested_chain_sorted_alphabetically(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "zeta")
        graph.add_module_dependency("sales", "alpha")

        chain = graph.get_dependency_chain("sales")

        assert chain["module"] == "sales"
        assert chain["depth"] == 0
        assert [d["module"] for d in chain["dependencies"]] == ["alpha", "zeta"]
        assert all(d["depth"] == 1 for d in chain["dependencies"])

    def test_truncates_when_exceeding_max_depth(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "c")
        graph.add_module_dependency("c", "d")

        chain = graph.get_dependency_chain("a", max_depth=1)

        b_node = chain["dependencies"][0]
        assert b_node["module"] == "b"
        assert b_node["depth"] == 1
        assert "truncated" not in b_node

        c_node = b_node["dependencies"][0]
        assert c_node["module"] == "c"
        assert c_node["depth"] == 2
        assert c_node["truncated"] is True
        assert c_node["dependencies"] == []

    def test_does_not_truncate_within_default_max_depth(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "c")

        chain = graph.get_dependency_chain("a")

        b_node = chain["dependencies"][0]
        c_node = b_node["dependencies"][0]
        assert "truncated" not in c_node


class TestGetImpactAnalysis:
    """Tests for DependencyGraph.get_impact_analysis."""

    def test_structure_reports_direct_dependents_and_dependencies(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "inventory")
        graph.add_module_dependency("sales", "finance")

        analysis = graph.get_impact_analysis("inventory")

        assert analysis["changed_module"] == "inventory"
        assert analysis["direct_dependents"] == ["sales"]
        assert analysis["dependencies"] == []
        assert analysis["external_services"] == []

    def test_dependencies_and_external_services_reported_for_changed_module(self):
        graph = DependencyGraph()
        graph.add_module_dependency("finance", "audit")
        graph.add_service_dependency("finance", "accounting_system")

        analysis = graph.get_impact_analysis("finance")

        assert analysis["dependencies"] == ["audit"]
        assert analysis["external_services"] == ["accounting_system"]

    def test_indirect_dependents_is_always_empty_due_to_implementation_bug(self):
        """Regression test documenting a real bug: `_get_transitive_dependents`
        recurses into each direct dependent's own dependents, but never adds
        the dependent module name itself into the accumulated result set.
        As a consequence `indirect_dependents` is always `[]`, regardless of
        how many levels of transitive dependents actually exist in the
        graph (here: w -> x -> y, so `y` genuinely has an indirect
        dependent `w` that is not being reported).
        """
        graph = DependencyGraph()
        graph.add_module_dependency("w", "x")
        graph.add_module_dependency("x", "y")

        analysis = graph.get_impact_analysis("y")

        assert analysis["direct_dependents"] == ["x"]
        assert analysis["indirect_dependents"] == []

    def test_empty_analysis_for_isolated_module(self):
        graph = DependencyGraph()
        analysis = graph.get_impact_analysis("isolated")

        assert analysis == {
            "changed_module": "isolated",
            "direct_dependents": [],
            "indirect_dependents": [],
            "dependencies": [],
            "external_services": [],
        }


class TestToDict:
    """Tests for DependencyGraph.to_dict."""

    def test_structure_for_empty_graph(self):
        graph = DependencyGraph()
        result = graph.to_dict()

        assert result == {
            "module_dependencies": {},
            "service_dependencies": {},
            "has_circular_dependencies": False,
            "circular_cycles": [],
        }

    def test_sorts_dependency_and_service_lists(self):
        graph = DependencyGraph()
        graph.add_module_dependency("sales", "zeta")
        graph.add_module_dependency("sales", "alpha")
        graph.add_service_dependency("sales", "zeta_service")
        graph.add_service_dependency("sales", "alpha_service")

        result = graph.to_dict()

        assert result["module_dependencies"]["sales"] == ["alpha", "zeta"]
        assert result["service_dependencies"]["sales"] == ["alpha_service", "zeta_service"]

    def test_reports_circular_dependency_flags_and_cycles(self):
        graph = DependencyGraph()
        graph.add_module_dependency("a", "b")
        graph.add_module_dependency("b", "a")

        result = graph.to_dict()

        assert result["has_circular_dependencies"] is True
        assert result["circular_cycles"] == [["a", "b", "a"]]