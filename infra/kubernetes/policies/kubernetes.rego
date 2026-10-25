# ERP03 Kubernetes admission / policy rules (conftest)
# These validate that deployed manifests meet baseline production standards.

deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.spec.containers[_].resources.limits
    msg := sprintf("Deployment %s is missing resource limits", [input.metadata.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.image
    msg := sprintf("Deployment %s container has no image", [input.metadata.name])
}

deny[msg] {
    input.kind == "Service"
    not input.spec.selector
    msg := sprintf("Service %s is missing a selector", [input.metadata.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    contains(container.image, ":latest")
    msg := sprintf("Deployment %s uses the 'latest' image tag (not allowed)", [input.metadata.name])
}

# Require health probes on deployments
deny[msg] {
    input.kind == "Deployment"
    not input.spec.template.spec.containers[_].readinessProbe
    msg := sprintf("Deployment %s is missing a readiness probe", [input.metadata.name])
}

# Require non-root where possible (best effort)
warn[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    container.securityContext
    not container.securityContext.runAsNonRoot
    msg := sprintf("Deployment %s container does not enforce non-root user", [input.metadata.name])
}
