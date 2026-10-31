# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/devcontainers/universal:2

# Install Python 3.12
RUN apt-get update && apt-get install -y python3.12 python3.12-venv python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for docker-in-docker)
RUN apt-get update && apt-get install -y docker.io \
    && rm -rf /var/lib/apt/lists/*

# Set up workspace
WORKDIR /workspace

# Copy setup scripts
COPY scripts/ /workspace/scripts/
COPY .devcontainer/post-create.sh /workspace/.devcontainer/post-create.sh

# Make scripts executable
RUN chmod +x /workspace/scripts/*.sh /workspace/.devcontainer/post-create.sh

# Pre-install Python dependencies
COPY ERP-BACKEND/requirements.txt ERP-BACKEND/dev-requirements.txt /workspace/ERP-BACKEND/
RUN python3.12 -m pip install --upgrade pip \
    && pip install -r /workspace/ERP-BACKEND/requirements.txt \
    && pip install -r /workspace/ERP-BACKEND/dev-requirements.txt

# Pre-install frontend dependencies
COPY frontend/package.json frontend/package-lock.json /workspace/frontend/
RUN cd /workspace/frontend && npm ci --no-audit --no-fund

USER vscode
