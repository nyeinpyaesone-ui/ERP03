# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within ERP SOLUTION, please send an email
to nyeinpyaesone273@gmail.com. All security vulnerabilities will be promptly addressed.

Please do NOT open public issues for security vulnerabilities.

## Security Measures

- JWT-based authentication with configurable expiration
- Role-based access control (RBAC)
- Row-level security (RLS) for multi-tenancy
- Input validation and sanitization on all endpoints
- CORS protection
- Rate limiting
- Secrets management via environment variables
- Regular dependency updates via Dependabot

## Best Practices

- Never commit `.env` files or secrets to version control
- Use strong, unique passwords for database and services
- Enable 2FA for all admin accounts
- Regularly rotate API keys and tokens
- Keep Docker images and dependencies updated
