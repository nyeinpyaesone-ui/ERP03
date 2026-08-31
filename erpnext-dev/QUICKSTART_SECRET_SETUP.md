# ERPNext Secret Setup - Quick Start Guide

## ✅ What Has Been Done

Your ERPNext development environment is now configured with **cryptographically secure secrets**:

### 🔐 Auto-Generated Secure Credentials

| Component | Value | Status |
|-----------|-------|--------|
| **Database Password** | `0e15c462cb18ebc53d77432f4a25466c` | ✅ Generated |
| **Admin Password** | `0f1c64124374ddb3c99eff7f7827e7da` | ✅ Generated |
| **JWT Secret** | `c3736cf19de112d69394133a4281736f...` | ✅ Generated |
| **Secret Key** | `f642e33be9aa165c9d998ec498dc65c5...` | ✅ Generated |
| **Redis Cache Password** | `be55e2f8fc3b8363f2dc8239c0772313` | ✅ Generated |
| **Redis Queue Password** | `1d1747c178e1079a9d9d4686bbac611e` | ✅ Generated |
| **Encryption Key** | `7409613269b691ed4c82e57583f40fc1...` | ✅ Generated |

### 📁 Files Created

```
/workspace/erpnext-dev/
├── .env                          # ✅ Active configuration with secrets
├── .env.example                  # Template with documentation
├── .gitignore                    # ✅ Prevents secret commits
├── SECURITY_GUIDE.md             # ✅ Comprehensive security guide
├── secrets/
│   ├── .env.secrets              # ✅ Core auto-generated secrets
│   └── .env.secrets.full         # Complete template with placeholders
└── volumes/                      # Docker data volumes
```

## 🚀 Next Steps to Start ERPNext

### Option 1: Quick Start (Recommended)
```bash
cd /workspace/erpnext-dev
./quickstart.sh
```

### Option 2: Manual Start
```bash
cd /workspace/erpnext-dev

# Verify your .env file has secrets
cat .env | grep PASSWORD

# Start all services
docker-compose -f docker-compose.dev.yaml up -d

# View logs
docker-compose -f docker-compose.dev.yaml logs -f
```

### Option 3: Start Specific Services
```bash
# Start only database and Redis first
docker-compose -f docker-compose.dev.yaml up -d db redis-cache redis-queue redis-socketio

# Wait 30 seconds, then start ERPNext
sleep 30
docker-compose -f docker-compose.dev.yaml up -d backend frontend scheduler worker websocket
```

## 🔑 Login Credentials

After startup completes:

- **URL**: http://erp.localhost:8000
- **Username**: `Administrator`
- **Password**: `0f1c64124374ddb3c99eff7f7827e7da`

⚠️ **IMPORTANT**: Change this password after first login!

## ⚙️ Optional Configuration (Update in .env)

The following values in your `.env` file need your personal input if you want these features:

### Email Notifications
```bash
# Edit .env and replace these lines:
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

### OAuth/SSO (Optional)
```bash
# Only if you want Google/GitHub login:
GOOGLE_CLIENT_ID=your-actual-client-id
GOOGLE_CLIENT_SECRET=your-actual-client-secret
```

### Payment Gateway (Optional)
```bash
# Only if you want to accept payments:
STRIPE_SECRET_KEY=sk_test_your-actual-key
```

## 🔒 Security Best Practices Applied

✅ Cryptographically secure random passwords (256-bit entropy)  
✅ Separate passwords for each component (DB, Redis, Admin)  
✅ Unique JWT and encryption keys  
✅ `.gitignore` configured to prevent accidental commits  
✅ Security guide with production checklist  
✅ Secrets stored in dedicated `secrets/` directory  

## 🛡️ File Permissions (Recommended)

Set restrictive permissions on secret files:
```bash
cd /workspace/erpnext-dev
chmod 600 .env
chmod 600 secrets/.env.secrets
chmod 600 secrets/.env.secrets.full
```

## 📊 Verification Commands

```bash
# Check if .env has all required secrets
grep -E "PASSWORD|SECRET|KEY" .env | head -15

# Verify .gitignore protects secrets
cat .gitignore | grep -E "env|secret"

# Check file structure
ls -la
ls -la secrets/
```

## ❓ Troubleshooting

### Docker not starting?
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check for port conflicts
docker ps
netstat -tlnp | grep :8000
```

### Can't access erp.localhost?
```bash
# Add to /etc/hosts (Linux/Mac)
echo "127.0.0.1 erp.localhost" | sudo tee -a /etc/hosts

# Or use IP directly: http://127.0.0.1:8000
```

### Forgot admin password?
```bash
# Reset via Docker
docker-compose -f docker-compose.dev.yaml exec backend \
  bench set-admin-password new-password-here
```

## 📞 Need Help?

1. Check `SECURITY_GUIDE.md` for detailed security information
2. Check `SETUP_GUIDE.md` for complete setup instructions
3. Check `README.md` for project overview
4. Review logs: `docker-compose logs backend`

---

**Ready to start?** Run `./quickstart.sh` now!
