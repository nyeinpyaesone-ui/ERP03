# Supply_Chain Plugin

## Overview
Supply_Chain plugin for ERP-Core system.

## Features
- TODO: List features

## Configuration
```yaml
plugins:
  enabled:
    - supply_chain
  config:
    supply_chain:
      # Add configuration options here
```

## API Endpoints
- `GET /api/v1/supply_chain/` - List items
- `GET /api/v1/supply_chain/status` - Plugin status

## Development
1. Implement models in `plugin.py`
2. Add routes in `register_routes()`
3. Update configuration options
4. Test with ERP-Core system
