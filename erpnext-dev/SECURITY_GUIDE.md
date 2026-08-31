# ERPNext Security Guide

## 🔐 Secret Management

### Auto-Generated Secrets
The following secrets have been automatically generated with cryptographically secure random values:

| Secret | Purpose | Location |
|--------|---------|----------|
| `DB_PASSWORD` | MariaDB database password | `secrets/.env.secrets` |
| `ADMIN_PASSWORD` | ERPNext Administrator password | `secrets/.env.secrets` |
| `JWT_SECRET` | JSON Web Token signing key | `secrets/.env.secrets` |
| `SECRET_KEY` | Django/Frappe secret key | `secrets/.env.secrets` |
| `ENCRYPTION_KEY` | Field encryption key | `secrets/.env.secrets` |
| `REDIS_*_PASSWORD` | Redis authentication | `secrets/.env.secrets` |
| `BACKUP_ENCRYPTION_KEY` | Backup encryption | `secrets/.env.secrets` |

### Default Credentials (CHANGE IN PRODUCTION!)
- **Username**: `Administrator`
- **Password**: `0f1c64124374ddb3c99eff7f7827e7da` (auto-generated)

## 📁 Secret Files Structure

```
erpnext-dev/
├── secrets/
│   ├── .env.secrets        # Core auto-generated secrets
│   └── .env.secrets.full   # Complete template with placeholders
├── .env                    # Your active configuration (create from .env.example)
├── .env.example            # Template with documentation
└── .gitignore              # Prevents accidental commits
```

## ⚠️ Critical Security Actions

### 1. Immediate Actions (Before First Run)
```bash
# Copy secrets to your active .env file
cd /workspace/erpnext-dev
cp secrets/.env.secrets .env

# Review and update user-specific values in .env:
# - MAIL_USERNAME and MAIL_PASSWORD
# - Any OAuth credentials if using SSO
```

### 2. Production Deployment Checklist
- [ ] Change all auto-generated passwords
- [ ] Generate new JWT_SECRET and SECRET_KEY
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up external secrets manager (AWS Secrets Manager, HashiCorp Vault)
- [ ] Enable Redis authentication
- [ ] Configure firewall rules
- [ ] Set up backup encryption
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting

### 3. Email Configuration
For email notifications to work:
1. Use Gmail or another SMTP provider
2. Generate an App-Specific Password (not your regular password)
3. Update `.env`:
   ```
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-specific-password
   ```

### 4. OAuth/SSO Setup (Optional)
If enabling Google/GitHub login:
1. Create OAuth credentials in provider console
2. Update `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

## 🔒 File Permissions

Set restrictive permissions on secret files:
```bash
chmod 600 .env
chmod 600 secrets/.env.secrets
chmod 600 secrets/.env.secrets.full
```

## 🚫 Never Commit Secrets

The `.gitignore` file is configured to prevent accidental commits of:
- `.env` files (except `.env.example`)
- `.env.secrets*` files
- Certificate and key files
- Docker volumes containing data

Always verify before committing:
```bash
git status
git diff --cached
```

## 🔄 Rotating Secrets

To rotate secrets periodically:
```bash
cd secrets
# Regenerate all secrets
./regenerate-secrets.sh  # (Create this script for automation)
# Update .env with new values
# Restart all services
docker-compose down && docker-compose up -d
```

## 📊 Security Monitoring

Enable security monitoring:
1. Configure Sentry for error tracking
2. Enable Frappe audit logging
3. Set up log aggregation (ELK Stack, Splunk)
4. Monitor failed login attempts
5. Track API rate limit violations

## 🛡️ Additional Hardening

### Firewall Rules
Only expose necessary ports:
- 8000 (HTTP/Websocket) - Public
- 9000 (Socket.IO) - Internal
- 3306 (MariaDB) - Internal only
- 6379 (Redis) - Internal only

### Database Security
- Use strong passwords (already configured)
- Restrict database user privileges
- Enable SSL for database connections
- Regular backups with encryption

### Network Security
- Use Docker networks for isolation
- Implement network policies in production
- Consider using a WAF (Web Application Firewall)

## 📞 Security Contacts

Report security vulnerabilities to:
- Email: security@yourorganization.com
- Do not disclose publicly until patched

---

**Last Updated**: Auto-generated during setup
**Version**: ERPNext v16.31.1
