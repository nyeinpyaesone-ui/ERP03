# Mrp Plugin

## Overview
Mrp plugin for ERP-Core system.

## Features
- TODO: List features

## Configuration
```yaml
plugins:
  enabled:
    - mrp
  config:
    mrp:
      # Add configuration options here
```

## API Endpoints
- `GET /api/v1/mrp/` - List items
- `GET /api/v1/mrp/status` - Plugin status

## Development
1. Implement models in `plugin.py`
2. Add routes in `register_routes()`
3. Update configuration options
4. Test with ERP-Core system
