FROM frappe/erpnext:v15.120.0

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=frappe:frappe docker/erpnext/production-entrypoint.sh /usr/local/bin/erpnext-entrypoint
RUN chmod 0755 /usr/local/bin/erpnext-entrypoint

USER frappe
WORKDIR /home/frappe/frappe-bench
ENTRYPOINT ["/usr/local/bin/erpnext-entrypoint"]
CMD ["start"]
