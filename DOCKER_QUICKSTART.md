# 🚀 QUICK START — Get Docker Images Live

## YOU NEED:
1. Computer with Docker Desktop
2. Docker Hub access token

## COMMANDS TO RUN:
```bash
docker login -u <docker-hub-username>
docker build -t <docker-hub-username>/erp-solution-backend:v1.0.0 ./backend
docker build -t <docker-hub-username>/erp-solution-frontend:v1.0.0 ./frontend
docker push <docker-hub-username>/erp-solution-backend:v1.0.0
docker push <docker-hub-username>/erp-solution-frontend:v1.0.0
```

## VERIFY:
https://hub.docker.com/r/<docker-hub-username>/erp-solution-backend

## NEED HELP?
See DOCKER_TROUBLESHOOT.md for full details
