#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
terraform init -backend=false
terraform validate
terraform fmt -check
echo "Terraform validation passed"
