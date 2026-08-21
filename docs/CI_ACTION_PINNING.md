# GitHub Actions Pinning

ERP03 requires third-party GitHub Actions to be pinned to immutable full-length commit SHAs.

Check locally:

```bash
python scripts/pin-github-actions.py --check
```

Resolve and update mutable refs:

```bash
GITHUB_TOKEN=... python scripts/pin-github-actions.py --fix
```

Dependabot updates GitHub Actions weekly. The pinning workflow prevents mutable refs from reaching `main`.
