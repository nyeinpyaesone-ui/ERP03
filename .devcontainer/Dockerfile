# ERPNext Development Container
FROM frappe/erpnext:v15.120.0

# Switch to root for installations
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    curl \
    wget \
    build-essential \
    python3-dev \
    python3-pip \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    fonts-font-awesome \
    locales \
    && rm -rf /var/lib/apt/lists/*

# Set locale
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

# Install Python development packages
RUN pip3 install --no-cache-dir \
    ipython \
    ipdb \
    black \
    flake8 \
    pylint \
    pytest \
    pytest-cov \
    pre-commit \
    authlib \
    requests-oauthlib

# Create development user
RUN groupadd -r devuser && useradd -r -g devuser -m devuser

# Set up workspace
WORKDIR /workspace

# Copy OIDC configuration script
COPY docker/erpnext/configure-oidc.py /usr/local/bin/configure-oidc.py
RUN chmod +x /usr/local/bin/configure-oidc.py

# Environment variables for development
ENV SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-in-production}
ENV OIDC_ENABLED=${OIDC_ENABLED:-false}
ENV DEVELOPMENT_MODE=true
ENV HOME=/home/devuser

# Set proper permissions
RUN chown -R devuser:devuser /workspace

# Switch to non-root user
USER devuser

# Default command
CMD ["/bin/bash"]
