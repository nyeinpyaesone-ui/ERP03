# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main (latest) | ✅ |
| Release tags (v1.x) | ✅ |
| Older releases | ❌ |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a vulnerability, please use one of the following channels:

1. **GitHub Security Advisories**: Use the [Security tab](https://github.com/nyeinpyaesone-ui/ERP03/security/advisories/new) to submit a private report.
2. **Email**: Contact the repository maintainer directly.

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Potential impact assessment
- Suggested fix (if any)

### Response Timeline

- **Acknowledgement**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix or mitigation**: Within 30 days for critical issues

## Security Controls

This project implements the following security controls:

- **Authentication**: JWT with configurable expiry (`jwt_expiry_minutes`)
- **Authorization**: Tenant-scoped queries via verified token claims
- **Rate Limiting**: Redis-backed sliding window (configurable via `rate_limit_*` settings)
- **Metrics**: `/metrics` endpoint protected by bearer token auth
- **Secrets**: `Settings` uses `extra="forbid"`; production rejects SQLite, requires HTTPS CORS
- **Non-root containers**: Backend and frontend run as `app` user
- **Dependency scanning**: pip-audit + CodeQL in CI (security.yml)

## Known Security Considerations

- TypeSafe integration is optional and degrades gracefully when disabled
- Idempotency fingerprints use SHA-256 canonical JSON
- Transaction IDs use `secrets.token_hex(16)` for unguessable identifiers
- Branch-row locks serialize invoice number generation to prevent races
