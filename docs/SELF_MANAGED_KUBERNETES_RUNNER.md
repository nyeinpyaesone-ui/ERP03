# Self-managed Kubernetes GitHub Actions runner

## Purpose

ERP03 uses a self-managed Kubernetes cluster. This setup provides a **read-only preflight** from a dedicated runner inside the cluster network. It is deliberately separate from deployment: it does not apply manifests, run migrations, restart workloads, read Secret values, or change cluster state.

## Runner requirements

Register a dedicated GitHub Actions self-hosted runner with these labels:

- `self-hosted`
- `linux`
- `erp03-k8s`

Place it on a controlled management host that can reach the Kubernetes API. Do not reuse a production workload node unless that is already the approved runner-host design. Prefer an ephemeral runner; do not execute untrusted pull-request code on this runner.

Install and maintain:

- a supported `kubectl` client compatible with the cluster version;
- a Kustomize binary;
- a kubeconfig for a dedicated, read-only Kubernetes identity.

The kubeconfig must be provisioned on the runner host, not stored in the repository or printed in workflow logs. Restrict its file permissions to the runner account. Do not grant this preflight identity create, update, patch, delete, exec, port-forward, or Secret-read permissions.

### Minimum read-only RBAC

The identity needs only:
- **Cluster scope:** `get` on `namespaces`, solely to confirm the requested namespace exists.
- **Target namespace scope:** `list` on `deployments`, `pods`, `persistentvolumeclaims`, `services`, and `ingresses`, for the inventory output.

Do not bind `view` if that role grants more access than needed in your cluster version; use a dedicated ClusterRole plus a namespace Role/RoleBinding with the exact verbs and resources above. The identity must not read Kubernetes Secret objects.

## GitHub configuration

Create a GitHub Environment named `kubernetes-preflight` and set this environment variable:

| Variable | Value |
|---|---|
| `ERP03_KUBE_CONTEXT` | Exact context name returned by `kubectl config current-context` on the runner |

Do not add kubeconfig contents, certificates, tokens, or database credentials as workflow variables.

## Run

1. Confirm the dedicated runner is online with all three labels.
2. Open Actions → **ERP03 Kubernetes Preflight**.
3. Select `erp03-staging` or `erp03`.
4. Run only from `main`.
5. Review the output for context match, read-only RBAC, namespace inventory, overlay rendering, and target-environment image policy.

All three overlays are rendered on every preflight. A staging inspection reports unresolved base-image digest placeholders as a warning and does not block read-only cluster inspection. A production inspection fails closed while any digest placeholder remains or any production image is not digest-pinned. Replace placeholders only with digests verified from the exact published OCI artifacts. Do not substitute a tag or guessed digest.

## Security boundary

The workflow uses only read operations. It is not a deployment workflow and cannot be treated as proof of production readiness. A later deployment workflow must use a separate environment, a separately scoped identity, an independent approval gate, controlled migration execution, rollout health checks, and a tested rollback path.
