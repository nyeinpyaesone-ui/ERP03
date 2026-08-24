"""
Change Data Capture (CDC) Handler
Captures database changes for event-driven architecture
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json

class OperationType(Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class CDCEvent:
    """Represents a captured database change"""
    
    def __init__(self, table: str, operation: OperationType, 
                 before: Optional[Dict[str, Any]], after: Optional[Dict[str, Any]],
                 timestamp: datetime = None):
        self.table = table
        self.operation = operation
        self.before = before
        self.after = after
        self.timestamp = timestamp or datetime.utcnow()
        self.id = f"{table}_{operation.value}_{int(self.timestamp.timestamp())}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'table': self.table,
            'operation': self.operation.value,
            'before': self.before,
            'after': self.after,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

class CDCHandler:
    """Process and route CDC events"""
    
    def __init__(self):
        self.event_queue: List[CDCEvent] = []
        self.subscribers: Dict[str, List[callable]] = {}
    
    def capture_change(self, table: str, operation: OperationType,
                      before: Optional[Dict[str, Any]], 
                      after: Optional[Dict[str, Any]]) -> CDCEvent:
        """Capture a database change event"""
        event = CDCEvent(table, operation, before, after)
        self.event_queue.append(event)
        self._notify_subscribers(table, event)
        return event
    
    def subscribe(self, table: str, callback: callable):
        """Subscribe to changes on a specific table"""
        if table not in self.subscribers:
            self.subscribers[table] = []
        self.subscribers[table].append(callback)
    
    def _notify_subscribers(self, table: str, event: CDCEvent):
        """Notify all subscribers of a table change"""
        if table in self.subscribers:
            for callback in self.subscribers[table]:
                try:
                    callback(event)
                except Exception as e:
                    # Log error but don't fail the whole process
                    print(f"CDC subscriber error: {e}")
    
    def get_events_since(self, timestamp: datetime) -> List[CDCEvent]:
        """Get all events since a given timestamp"""
        return [e for e in self.event_queue if e.timestamp >= timestamp]
    
    def clear_old_events(self, max_age_hours: int = 24):
        """Clear events older than specified hours"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        self.event_queue = [e for e in self.event_queue if e.timestamp >= cutoff]

# Example usage for PostgreSQL logical replication integration
class PostgreSQLCDCListener:
    """Listens to PostgreSQL WAL for CDC events"""
    
    def __init__(self, connection_string: str, cdc_handler: CDCHandler):
        self.conn_string = connection_string
        self.cdc_handler = cdc_handler
        self.active = False
    
    async def start_listening(self, tables: List[str]):
        """Start listening to WAL changes for specified tables"""
        # Implementation would use pg_logical or similar
        # This is a placeholder for the actual PostgreSQL CDC integration
        print(f"Starting CDC listener for tables: {tables}")
        self.active = True
        
        # In production: Connect to PostgreSQL replication slot
        # Parse WAL entries using pgoutput plugin
        # Convert to CDCEvent and pass to cdc_handler.capture_change()
        
    def stop_listening(self):
        """Stop the CDC listener"""
        self.active = False
