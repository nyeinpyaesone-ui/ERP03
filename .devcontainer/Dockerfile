# syntax=docker/dockerfile:1.7
# Universal Development Container
# Optimized for FastAPI, React/Vite, PostgreSQL, Redis and GitHub CI/CD.
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Docker/Node/Python runtimes are supplied by Dev Container Features.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates gpg gnupg2 pass jq \
    unzip zip xz-utils build-essential libpq-dev \
    postgresql-client redis-tools \
    && mkdir -p -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
       -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod a+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
       > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=dialog
