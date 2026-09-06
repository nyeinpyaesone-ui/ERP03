# Pos Plugin

## Overview
Pos plugin for ERP-Core system.

## Features
- TODO: List features

## Configuration
```yaml
plugins:
  enabled:
    - pos
  config:
    pos:
      # Add configuration options here
```

## API Endpoints
- `GET /api/v1/pos/` - List items
- `GET /api/v1/pos/status` - Plugin status

## Development
1. Implement models in `plugin.py`
2. Add routes in `register_routes()`
3. Update configuration options
4. Test with ERP-Core system
