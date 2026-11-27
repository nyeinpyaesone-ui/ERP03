# syntax=docker/dockerfile:1
# Python 3.12 Bookworm supports linux/amd64 and linux/arm64.
FROM mcr.microsoft.com/devcontainers/python:3-3.12-bookworm

USER root

# Remove an inherited stale Yarn APT source before apt-get update.
RUN set -eux; \
    for source in /etc/apt/sources.list /etc/apt/sources.list.d/*.list /etc/apt/sources.list.d/*.sources; do \
      [ -f "$source" ] || continue; \
      if grep -q 'dl.yarnpkg.com/debian' "$source"; then rm -f "$source"; fi; \
    done; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*

# Node 22 satisfies the repository's Vite 8 toolchain.
RUN set -eux; \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -; \
    apt-get update; \
    apt-get install -y --no-install-recommends nodejs; \
    rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/erp03-venv
ENV VENV_DIR=/opt/erp03-venv
ENV PATH="/opt/erp03-venv/bin:${PATH}"

WORKDIR /workspace

COPY scripts/ /workspace/scripts/
COPY .devcontainer/post-create.sh /workspace/.devcontainer/post-create.sh
RUN chmod +x /workspace/scripts/*.sh /workspace/.devcontainer/post-create.sh

COPY ERP-BACKEND/requirements.txt ERP-BACKEND/dev-requirements.txt /workspace/ERP-BACKEND/
RUN python -m venv "$VIRTUAL_ENV" \
    && python -m pip install --upgrade pip \
    && pip install -r /workspace/ERP-BACKEND/requirements.txt \
    && pip install -r /workspace/ERP-BACKEND/dev-requirements.txt \
    && chown -R vscode:vscode "$VIRTUAL_ENV"

COPY frontend/package.json frontend/package-lock.json /workspace/frontend/
RUN cd /workspace/frontend && npm ci --no-audit --no-fund --include=optional

USER vscode
