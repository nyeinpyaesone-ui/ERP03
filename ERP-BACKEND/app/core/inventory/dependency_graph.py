"""Dependency graph management for module and route dependencies."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple
from .registry import RouteInventory, Dependency


@dataclass
class DependencyGraph:
    """Graph structure for tracking module and service dependencies."""
    
    # Module-level dependencies
    module_dependencies: Dict[str, Set[str]] = field(default_factory=dict)  # module -> modules it depends on
    service_dependencies: Dict[str, Set[str]] = field(default_factory=dict)  # module -> external services
    
    # Route-level dependencies
    route_dependencies: Dict[Tuple[str, str], Set[Dependency]] = field(default_factory=dict)  # (path, method) -> dependencies
    
    def add_module_dependency(self, module_name: str, depends_on: str) -> None:
        """Add a module-level dependency."""
        if module_name not in self.module_dependencies:
            self.module_dependencies[module_name] = set()
        self.module_dependencies[module_name].add(depends_on)
    
    def add_service_dependency(self, module_name: str, service_name: str) -> None:
        """Add an external service dependency."""
        if module_name not in self.service_dependencies:
            self.service_dependencies[module_name] = set()
        self.service_dependencies[module_name].add(service_name)
    
    def get_module_dependencies(self, module_name: str) -> Set[str]:
        """Get all modules that a module depends on."""
        return self.module_dependencies.get(module_name, set())
    
    def get_module_dependents(self, module_name: str) -> Set[str]:
        """Get all modules that depend on this module."""
        dependents = set()
        for module, deps in self.module_dependencies.items():
            if module_name in deps:
                dependents.add(module)
        return dependents
    
    def has_circular_dependency(self) -> bool:
        """Check if there are any circular dependencies."""
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.get_module_dependencies(node):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for module in self.module_dependencies:
            if module not in visited:
                if has_cycle(module):
                    return True
        
        return False
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """Get all circular dependency cycles."""
        cycles = []
        visited = set()
        rec_stack = []

        def find_cycles(node: str, path: List[str]) -> None:
            visited.add(node)
            path.append(node)

            for neighbor in self.get_module_dependencies(node):
                if neighbor not in visited:
                    find_cycles(neighbor, path.copy())
                elif neighbor in path:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    if cycle not in cycles:
                        cycles.append(cycle)

        for module in self.module_dependencies:
            if module not in visited:
                find_cycles(module, [])

        return cycles

    def get_critical_dependencies(self, module_name: str) -> Set[str]:
        """Get critical (non-fallback) dependencies."""
        critical = set()
        for dep_module in self.get_module_dependencies(module_name):
            if dep_module:  # Non-optional
                critical.add(dep_module)
        return critical
    
    def get_dependency_chain(self, module_name: str, max_depth: int = 5) -> Dict:
        """Get full dependency chain with depth limit."""
        chain = {
            "module": module_name,
            "dependencies": [],
            "depth": 0,
        }
        
        def traverse(mod: str, depth: int) -> Dict:
            if depth > max_depth:
                return {"module": mod, "dependencies": [], "depth": depth, "truncated": True}
            
            deps = self.get_module_dependencies(mod)
            return {
                "module": mod,
                "dependencies": [traverse(d, depth + 1) for d in sorted(deps)],
                "depth": depth,
            }
        
        return traverse(module_name, 0)
    
    def get_impact_analysis(self, module_name: str) -> Dict:
        """Analyze impact of changes to a module."""
        return {
            "changed_module": module_name,
            "direct_dependents": sorted(list(self.get_module_dependents(module_name))),
            "indirect_dependents": self._get_transitive_dependents(module_name),
            "dependencies": sorted(list(self.get_module_dependencies(module_name))),
            "external_services": sorted(list(self.service_dependencies.get(module_name, set()))),
        }
    
    def _get_transitive_dependents(self, module_name: str, visited: Set[str] = None) -> List[str]:
        """Get all transitive dependents (modules that indirectly depend on this module)."""
        if visited is None:
            visited = set()
        
        direct = self.get_module_dependents(module_name)
        transitive = set()
        
        for dependent in direct:
            if dependent not in visited:
                visited.add(dependent)
                transitive.update(self._get_transitive_dependents(dependent, visited))
        
        return sorted(list(transitive))
    
    def to_dict(self) -> dict:
        """Convert graph to dictionary for serialization."""
        return {
            "module_dependencies": {
                mod: sorted(list(deps))
                for mod, deps in self.module_dependencies.items()
            },
            "service_dependencies": {
                mod: sorted(list(services))
                for mod, services in self.service_dependencies.items()
            },
            "has_circular_dependencies": self.has_circular_dependency(),
            "circular_cycles": self.get_circular_dependencies(),
        }
