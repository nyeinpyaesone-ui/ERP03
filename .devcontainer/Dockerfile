# syntax=docker/dockerfile:1
# Python 3.12 Bookworm is published for linux/amd64 and linux/arm64.
# The previous universal image is x86-64-only and cannot be used for ARM64 builds.
FROM mcr.microsoft.com/devcontainers/python:3-3.12-bookworm

USER root

# Remove an inherited stale Yarn APT source before apt-get update. ERP03 uses npm;
# keeping an unused third-party Yarn source can make a valid base image fail
# when that repository's signing key changes.
RUN set -eux; \
    for source in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do \
      [ -f "$source" ] || continue; \
      if grep -q 'dl.yarnpkg.com/debian' "$source"; then \
        rm -f "$source"; \
      fi; \
    done; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl docker.io; \
    rm -rf /var/lib/apt/lists/*

# Install Node.js 22 from the official NodeSource repository.
RUN set -eux; \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -; \
    apt-get update; \
    apt-get install -y --no-install-recommends nodejs; \
    rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/erp03-venv
ENV PATH="/opt/erp03-venv/bin:${PATH}"

WORKDIR /workspace

COPY scripts/ /workspace/scripts/
COPY .devcontainer/post-create.sh /workspace/.devcontainer/post-create.sh
RUN chmod +x /workspace/scripts/*.sh /workspace/.devcontainer/post-create.sh

COPY ERP-BACKEND/requirements.txt ERP-BACKEND/dev-requirements.txt /workspace/ERP-BACKEND/
RUN python -m venv "$VIRTUAL_ENV" \
    && python -m pip install --upgrade pip \
    && pip install -r /workspace/ERP-BACKEND/requirements.txt \
    && pip install -r /workspace/ERP-BACKEND/dev-requirements.txt

COPY frontend/package.json frontend/package-lock.json /workspace/frontend/
RUN cd /workspace/frontend && npm ci --no-audit --no-fund

USER vscode
