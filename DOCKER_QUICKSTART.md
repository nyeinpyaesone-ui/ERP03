# 🚀 QUICK START — Get Docker Images Live

## YOU NEED:
1. Computer with Docker Desktop
2. Docker Hub access token

## COMMANDS TO RUN:
```bash
docker login -u powerrangeranikg
docker build -t powerrangeranikg/erp-solution-backend:v1.0.0 ./backend
docker build -t powerrangeranikg/erp-solution-frontend:v1.0.0 ./frontend
docker push powerrangeranikg/erp-solution-backend:v1.0.0
docker push powerrangeranikg/erp-solution-frontend:v1.0.0
```

## VERIFY:
https://hub.docker.com/r/powerrangeranikg/erp-solution-backend

## NEED HELP?
See DOCKER_TROUBLESHOOT.md for full details
