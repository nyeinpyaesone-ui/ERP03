FROM frappe/erpnext:v15.120.0

USER root
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    OIDC_ENABLED=${OIDC_ENABLED:-false} \
    OIDC_PROVIDER=${OIDC_PROVIDER:-} \
    OIDC_CLIENT_ID=${OIDC_CLIENT_ID:-} \
    OIDC_CLIENT_SECRET=${OIDC_CLIENT_SECRET:-} \
    OIDC_REDIRECT_URI=${OIDC_REDIRECT_URI:-} \
    OIDC_SCOPE=${OIDC_SCOPE:-openid profile email} \
    SECRET_KEY=${SECRET_KEY:-}

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir authlib requests-oauthlib

# Copy OIDC configuration script
COPY --chown=frappe:frappe docker/erpnext/configure-oidc.py /opt/scripts/configure-oidc.py
RUN chmod 0755 /opt/scripts/configure-oidc.py

# Copy production entrypoint
COPY --chown=frappe:frappe docker/erpnext/production-entrypoint.sh /usr/local/bin/erpnext-entrypoint
RUN chmod 0755 /usr/local/bin/erpnext-entrypoint

USER frappe
WORKDIR /home/frappe/frappe-bench
ENTRYPOINT ["/usr/local/bin/erpnext-entrypoint"]
CMD ["start"]
