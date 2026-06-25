# Troubleshooting Guide

## Common Issues

### Backend won't start
```bash
# Check PostgreSQL is running
docker-compose ps
# Check logs
docker-compose logs backend
# Verify environment variables
cat backend/.env
```

### Frontend build fails
```bash
# Clear node_modules
cd frontend && rm -rf node_modules && npm install
# Check Node version
node --version  # Should be 20+
```

### Mobile app won't load
```bash
# Clear Expo cache
cd mobile && npx expo start --clear
# Check Metro bundler
npx react-native start --reset-cache
```

### Database connection errors
```bash
# Check PostgreSQL is accessible
psql -h localhost -U erp -d erp_solution
# Verify connection string in .env
# Check firewall rules
```

### Git push rejected
```bash
# Pull latest changes first
git pull origin main --rebase
# Or force push (careful!)
git push origin main --force
```

## Getting Help
1. Check [docs/](docs/) for specific guides
2. Search [GitHub Issues](https://github.com/nyeinpyaesone-ui/ERP/issues)
3. Run `./scripts/gh-manager.sh verify` for diagnostics
4. Contact: nyeinpyaesone273@gmail.com
