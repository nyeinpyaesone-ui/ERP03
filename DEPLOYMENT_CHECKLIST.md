# Production Deployment Checklist for ERP03

## Prerequisites
- [x] Docker & Docker Compose installed
- [x] Secrets directory created with proper permissions (600)
- [x] `.env.production` configured

## Security Verification
- [ ] Replace default secrets in `secrets/` with cryptographically random values
- [ ] Ensure `docker-compose.yml` is not committed to public repositories
- [ ] Verify firewall rules allow only ports 80 (HTTP) and 443 (HTTPS)
- [ ] Enable SSL/TLS termination (see Nginx SSL configuration below)

## Deployment Steps
1. **Build and Start Services**
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```

2. **Verify Health Checks**
   ```bash
   docker compose ps
   # All services should show "healthy" status after 1 minute
   ```

3. **Check Logs**
   ```bash
   docker compose logs -f api
   docker compose logs -f db
   docker compose logs -f redis
   ```

4. **Run Database Migrations**
   (Handled automatically in docker-compose command, but verify)
   ```bash
   docker compose exec api alembic current
   ```

5. **Create Initial Admin User**
   ```bash
   docker compose exec api python -m app.utils.create_admin
   # Or use the API endpoint if implemented
   ```

## Post-Deployment Validation
- [ ] Access `http://<your-domain>/` (Frontend loads)
- [ ] Access `http://<your-domain>/api/v1/health` (Returns 200 OK)
- [ ] Login with admin credentials
- [ ] Verify database connectivity (create/read test inventory item)
- [ ] Check Redis caching (monitor hit/miss rates)

## Monitoring & Maintenance
- [ ] Set up log aggregation (ELK Stack, Loki, etc.)
- [ ] Configure alerts for service health checks
- [ ] Schedule regular database backups
- [ ] Plan for certificate renewal (if using Let's Encrypt)

## SSL/TLS Configuration (Optional but Recommended)
Add to `frontend/nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # ... rest of config
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

Mount certificates in `docker-compose.yml`:
```yaml
volumes:
  - ./ssl:/etc/nginx/ssl:ro
```

## Rollback Plan
If issues occur:
```bash
# Stop new version
docker compose down

# Revert code to previous commit
git checkout <previous-commit>

# Rebuild and start
docker compose up -d --build
```

## Performance Tuning (Post-Launch)
- Monitor `top` inside containers for CPU/Memory usage
- Adjust `deploy.resources` in `docker-compose.yml` based on metrics
- Tune PostgreSQL `shared_buffers` and `work_mem` if needed
- Configure Redis `maxmemory-policy` based on usage patterns
