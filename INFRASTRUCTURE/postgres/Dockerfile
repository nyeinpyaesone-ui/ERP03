# ERP03 Custom PostgreSQL Image
FROM postgres:15-alpine
RUN apk add --no-cache     postgresql15-contrib     pg_cron
COPY init/ /docker-entrypoint-initdb.d/
COPY postgresql.conf /etc/postgresql/postgresql.conf
COPY pg_hba.conf /etc/postgresql/pg_hba.conf
HEALTHCHECK --interval=10s --timeout=5s --retries=5     CMD pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} || exit 1
EXPOSE 5432
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
