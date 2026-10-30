package kubernetes

# Default deny-all policy set used by the Policy Enforcement workflow when the
# external erp03/policies repository is unavailable.

deny[msg] {
	# Block deployments without resource limits
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources
}

deny[msg] {
	# Block containers running as root
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  container.securityContext.runAsUser == 0
}

deny[msg] {
	# Block missing readiness probes on backend
  input.kind == "Deployment"
  input.metadata.name == "erp03-backend"
  not input.spec.template.spec.containers[0].readinessProbe
}
