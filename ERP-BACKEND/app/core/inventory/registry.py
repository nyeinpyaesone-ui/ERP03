"""Module registry and route inventory tracking."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime


class HttpMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"


class AuthRequirement(str, Enum):
    """Authentication and authorization requirements."""
    NONE = "none"
    AUTHENTICATED = "authenticated"
    SPECIFIC_ROLE = "specific_role"
    SPECIFIC_PERMISSION = "specific_permission"


@dataclass
class Dependency:
    """Represents a dependency of a route."""
    type: str  # 'database', 'service', 'external', 'cache'
    name: str  # Name of the dependency
    critical: bool = True  # True if service fails without this
    
    def __hash__(self):
        return hash((self.type, self.name))
    
    def __eq__(self, other):
        if isinstance(other, Dependency):
            return self.type == other.type and self.name == other.name
        return False


@dataclass
class RouteInventory:
    """Inventory of a single API route."""
    path: str
    method: HttpMethod
    module_name: str
    handler_function: str
    description: str
    auth_requirement: AuthRequirement
    auth_details: str  # e.g., "REQUIRES: finance.read"
    
    # Data characteristics
    reads_database_tables: Set[str] = field(default_factory=set)
    writes_database_tables: Set[str] = field(default_factory=set)
    dependencies: Set[Dependency] = field(default_factory=set)
    
    # Operational characteristics
    idempotency_required: bool = False
    requires_saga: bool = False
    cacheable: bool = False
    cache_ttl_seconds: Optional[int] = None
    
    # Workflow characteristics
    state_machine: Optional[str] = None  # e.g., "draft -> pending -> approved"
    events_emitted: Set[str] = field(default_factory=set)
    events_consumed: Set[str] = field(default_factory=set)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_modified_at: datetime = field(default_factory=datetime.utcnow)
    
    def __hash__(self):
        return hash((self.path, self.method))
    
    def __eq__(self, other):
        if isinstance(other, RouteInventory):
            return self.path == other.path and self.method == other.method
        return False
    
    @property
    def is_write_operation(self) -> bool:
        """Check if this is a write operation."""
        return self.method in (HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH, HttpMethod.DELETE)
    
    @property
    def is_read_operation(self) -> bool:
        """Check if this is a read operation."""
        return self.method in (HttpMethod.GET, HttpMethod.HEAD)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "path": self.path,
            "method": self.method.value,
            "module": self.module_name,
            "handler": self.handler_function,
            "description": self.description,
            "auth": {
                "requirement": self.auth_requirement.value,
                "details": self.auth_details,
            },
            "data": {
                "reads": sorted(list(self.reads_database_tables)),
                "writes": sorted(list(self.writes_database_tables)),
            },
            "dependencies": [
                {"type": d.type, "name": d.name, "critical": d.critical}
                for d in sorted(self.dependencies, key=lambda x: x.name)
            ],
            "operational": {
                "idempotency_required": self.idempotency_required,
                "requires_saga": self.requires_saga,
                "cacheable": self.cacheable,
                "cache_ttl_seconds": self.cache_ttl_seconds,
            },
            "workflow": {
                "state_machine": self.state_machine,
                "events_emitted": sorted(list(self.events_emitted)),
                "events_consumed": sorted(list(self.events_consumed)),
            },
        }


@dataclass
class ModuleRegistry:
    """Registry of all ERP modules and their routes."""
    modules: Dict[str, str] = field(default_factory=dict)  # module_name -> description
    routes: Set[RouteInventory] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def register_module(self, module_name: str, description: str) -> None:
        """Register a new module."""
        self.modules[module_name] = description
    
    def register_route(self, route: RouteInventory) -> None:
        """Register a new route."""
        if route.module_name not in self.modules:
            raise ValueError(f"Module '{route.module_name}' not registered")
        self.routes.add(route)
    
    def get_module_routes(self, module_name: str) -> List[RouteInventory]:
        """Get all routes for a module."""
        return sorted(
            [r for r in self.routes if r.module_name == module_name],
            key=lambda r: (r.path, r.method.value)
        )
    
    def get_routes_by_table(self, table_name: str) -> List[RouteInventory]:
        """Get all routes that access a specific database table."""
        return [
            r for r in self.routes
            if table_name in r.reads_database_tables or table_name in r.writes_database_tables
        ]
    
    def get_write_routes(self) -> List[RouteInventory]:
        """Get all routes that perform writes."""
        return [r for r in self.routes if r.is_write_operation]
    
    def get_routes_requiring_idempotency(self) -> List[RouteInventory]:
        """Get all routes that require idempotency."""
        return [r for r in self.routes if r.idempotency_required]
    
    def get_routes_with_saga(self) -> List[RouteInventory]:
        """Get all routes that require saga pattern."""
        return [r for r in self.routes if r.requires_saga]
    
    def to_dict(self) -> dict:
        """
        Serialize the registry and its route metrics to a dictionary.
        
        Returns:
            dict: Module descriptions, route counts, and sorted serialized route records.
        """
        return {
            "modules": self.modules,
            "routes_count": len(self.routes),
            "write_routes_count": len(self.get_write_routes()),
            "idempotency_required_count": len(self.get_routes_requiring_idempotency()),
            "saga_routes_count": len(self.get_routes_with_saga()),
            "routes": [
                r.to_dict() for r in sorted(self.routes, key=lambda x: (x.module_name, x.path))
            ],
        }
