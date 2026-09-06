# Bi Plugin

## Overview
Bi plugin for ERP-Core system.

## Features
- TODO: List features

## Configuration
```yaml
plugins:
  enabled:
    - bi
  config:
    bi:
      # Add configuration options here
```

## API Endpoints
- `GET /api/v1/bi/` - List items
- `GET /api/v1/bi/status` - Plugin status

## Development
1. Implement models in `plugin.py`
2. Add routes in `register_routes()`
3. Update configuration options
4. Test with ERP-Core system
