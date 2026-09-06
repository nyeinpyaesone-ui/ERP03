# Quality Plugin

## Overview
Quality plugin for ERP-Core system.

## Features
- TODO: List features

## Configuration
```yaml
plugins:
  enabled:
    - quality
  config:
    quality:
      # Add configuration options here
```

## API Endpoints
- `GET /api/v1/quality/` - List items
- `GET /api/v1/quality/status` - Plugin status

## Development
1. Implement models in `plugin.py`
2. Add routes in `register_routes()`
3. Update configuration options
4. Test with ERP-Core system
