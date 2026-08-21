# GitHub Actions Secrets Setup

## Required Secrets

Go to **Settings → Secrets and variables → Actions** in your GitHub repository.

### Docker Hub (for CI/CD releases)
| Secret | Value | How to get |
|--------|-------|------------|
| `DOCKER_USERNAME` | Your Docker Hub username | https://hub.docker.com |
| `DOCKER_PASSWORD` | Your Docker Hub password or token | Account Settings → Security |

### Deployment (for Kubernetes)
| Secret | Value | How to get |
|--------|-------|------------|
| `KUBE_CONFIG` | Base64-encoded kubeconfig | `cat ~/.kube/config \| base64` |
| `SSH_PRIVATE_KEY` | Your server SSH key | `cat ~/.ssh/id_rsa` |

### Cloud (optional)
| Secret | Value | How to get |
|--------|-------|------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM key | AWS Console → IAM |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret | AWS Console → IAM |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account JSON | GCP Console → IAM |

### API Keys (for production)
| Secret | Value | How to get |
|--------|-------|------------|
| `OPENAI_API_KEY` | OpenAI API key | https://platform.openai.com |
| `SENTRY_DSN` | Sentry project DSN | https://sentry.io |
| `STRIPE_SECRET_KEY` | Stripe secret key | https://dashboard.stripe.com |

## Setting Up Secrets

```bash
# Using GitHub CLI (if installed)
gh secret set DOCKER_USERNAME --body "your-username"
gh secret set DOCKER_PASSWORD --body "your-password"

# Or manually via GitHub web interface:
# Settings → Secrets and variables → Actions → New repository secret
```

## Verification

After setting secrets, verify with:
```bash
gh secret list
```
