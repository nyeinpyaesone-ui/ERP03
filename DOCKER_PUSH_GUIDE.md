# 🐳 Push Docker Images to Hub — Step by Step

## Step 1: Get a Computer with Docker
You need a computer (Windows/Mac/Linux) with Docker installed.
Download: https://docs.docker.com/get-docker/

## Step 2: Open Terminal/Command Prompt

## Step 3: Run These Commands (Copy & Paste)

```bash
# 1. Download your code
git clone https://github.com/nyeinpyaesone-ui/ERP.git
cd ERP

# 2. Login to Docker Hub (use your username)
docker login -u powerrangeranikg
# When asked for password, paste your ACCESS TOKEN (not your password)

# 3. Build backend image (this takes 2-5 minutes)
docker build -t powerrangeranikg/erp-solution-backend:v1.0.0 ./backend

# 4. Build frontend image (this takes 2-5 minutes)
docker build -t powerrangeranikg/erp-solution-frontend:v1.0.0 ./frontend

# 5. Tag as latest
docker tag powerrangeranikg/erp-solution-backend:v1.0.0 powerrangeranikg/erp-solution-backend:latest
docker tag powerrangeranikg/erp-solution-frontend:v1.0.0 powerrangeranikg/erp-solution-frontend:latest

# 6. Push to Docker Hub (this takes 5-10 minutes)
docker push powerrangeranikg/erp-solution-backend:v1.0.0
docker push powerrangeranikg/erp-solution-frontend:v1.0.0
docker push powerrangeranikg/erp-solution-backend:latest
docker push powerrangeranikg/erp-solution-frontend:latest
```

## Step 4: Check on Your Phone
After pushing, open your browser and go to:
https://hub.docker.com/r/powerrangeranikg/erp-solution-backend

You should see:
- ✅ Image name: erp-solution-backend
- ✅ Tags: v1.0.0, latest
- ✅ Size: ~500MB

## ❓ Where to Get Your Access Token

1. Go to https://hub.docker.com on your computer
2. Login as powerrangeranikg
3. Click your avatar → Account Settings → Security
4. Click "New Access Token"
5. Name it "ERP Push"
6. Copy the token (starts with dckr_pat_...)
7. Use this token when docker login asks for password

## 🆘 If You Get Errors

| Error | Solution |
|-------|----------|
| "Cannot connect to Docker" | Start Docker Desktop app first |
| "Access denied" | Use ACCESS TOKEN, not password |
| "No Dockerfile" | Make sure you're in the ERP folder |
| "Build failed" | Check internet connection |

## ✅ Success Check

After pushing, you should see on Docker Hub:
- ⭐ 1 repository: erp-solution-backend
- ⭐ 1 repository: erp-solution-frontend
- ⭐ Tags: v1.0.0 and latest for both

## 🚀 After Images Are Live

Your docker-compose.prod.yml will work:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

This starts your full ERP system!
