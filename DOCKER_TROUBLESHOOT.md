# 🐳 Docker Push — Complete Troubleshooting Guide

## 🔴 Problem: "Empty Repository" on Docker Hub

This means images were NEVER pushed. Here's how to fix:

---

## ✅ METHOD 1: Command Line (Recommended)

### Step 1: Install Docker
- **Windows**: https://docs.docker.com/desktop/install/windows-install/
- **Mac**: https://docs.docker.com/desktop/install/mac-install/
- **Linux**: `curl -fsSL https://get.docker.com | sh`

### Step 2: Get Your Access Token
1. Go to https://hub.docker.com
2. Login as **powerrangeranikg**
3. Click your name (top right) → **Account Settings**
4. Click **Security** (left sidebar)
5. Click **New Access Token**
6. Name: `ERP Push`
7. Click **Generate**
8. **COPY THE TOKEN** (starts with `dckr_pat_...`)

### Step 3: Open Terminal
- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac**: Press `Cmd + Space`, type `Terminal`, press Enter
- **Linux**: Press `Ctrl + Alt + T`

### Step 4: Run Commands
```bash
# 1. Go to your home folder
cd ~

# 2. Download your code
git clone https://github.com/nyeinpyaesone-ui/ERP.git

# 3. Enter the folder
cd ERP

# 4. Login to Docker Hub
docker login -u powerrangeranikg
# When it asks for password, PASTE YOUR ACCESS TOKEN
# (Right-click → Paste, or Ctrl+V)
# You should see: "Login Succeeded"

# 5. Build backend (takes 3-5 minutes)
docker build -t powerrangeranikg/erp-solution-backend:v1.0.0 ./backend

# 6. Build frontend (takes 3-5 minutes)
docker build -t powerrangeranikg/erp-solution-frontend:v1.0.0 ./frontend

# 7. Tag as latest
docker tag powerrangeranikg/erp-solution-backend:v1.0.0 powerrangeranikg/erp-solution-backend:latest
docker tag powerrangeranikg/erp-solution-frontend:v1.0.0 powerrangeranikg/erp-solution-frontend:latest

# 8. Push backend (takes 5-10 minutes)
docker push powerrangeranikg/erp-solution-backend:v1.0.0
docker push powerrangeranikg/erp-solution-backend:latest

# 9. Push frontend (takes 5-10 minutes)
docker push powerrangeranikg/erp-solution-frontend:v1.0.0
docker push powerrangeranikg/erp-solution-frontend:latest
```

### Step 5: Verify
Open your phone browser and go to:
https://hub.docker.com/r/powerrangeranikg/erp-solution-backend

You should see:
- ✅ Image name
- ✅ Tag: v1.0.0
- ✅ Tag: latest
- ✅ Size

---

## ✅ METHOD 2: GitHub Actions (Automatic)

If you don't want to use command line, set up GitHub Actions:

### Step 1: Add Secrets to GitHub
1. Go to https://github.com/nyeinpyaesone-ui/ERP/settings/secrets/actions
2. Click **New repository secret**
3. Add:
   - Name: `DOCKER_USERNAME`
   - Value: `powerrangeranikg`
4. Click **Add secret**
5. Add another:
   - Name: `DOCKER_PASSWORD`
   - Value: (Your access token from Method 1)
6. Click **Add secret**

### Step 2: Trigger Build
1. Go to https://github.com/nyeinpyaesone-ui/ERP/releases
2. Click **Draft a new release**
3. Tag version: `v1.0.0`
4. Release title: `ERP SOLUTION v1.0.0`
5. Click **Publish release**

GitHub will automatically build and push your images!

---

## ❌ COMMON ERRORS & FIXES

### Error: "Cannot connect to the Docker daemon"
**Fix**: Start Docker Desktop app first

### Error: "Access denied"
**Fix**: Use ACCESS TOKEN, not your Docker Hub password

### Error: "No such file or directory: Dockerfile"
**Fix**: Make sure you're in the ERP folder (`cd ERP`)

### Error: "denied: requested access to the resource is denied"
**Fix**: Run `docker login` again with correct token

### Error: "Build failed"
**Fix**: Check internet connection, try again

---

## 📞 Need Help?

| Contact | Details |
|---------|---------|
| Email | nyeinpyaesone273@gmail.com |
| LinkedIn | linkedin.com/in/nyein-pyae-sone-3250501ba |
| GitHub | github.com/nyeinpyaesone-ui/ERP |
| Phone | +959699795380 |

---

## ✅ SUCCESS CHECKLIST

After pushing, verify:
- [ ] https://hub.docker.com/r/powerrangeranikg/erp-solution-backend shows image
- [ ] https://hub.docker.com/r/powerrangeranikg/erp-solution-frontend shows image
- [ ] Both have tags: v1.0.0 and latest
- [ ] No "Empty repository" message
