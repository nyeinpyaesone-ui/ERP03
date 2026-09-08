# Code Agent for ERP03

This agent scans the repository for TODO/FIXME comments, runs pytest if tests exist, and can optionally open GitHub issues for discovered TODOs.

Usage:
- Locally: python agent.py --report report.json
- With GitHub: set GITHUB_TOKEN and run with --create-issues

See config.yaml.example for configuration options.
