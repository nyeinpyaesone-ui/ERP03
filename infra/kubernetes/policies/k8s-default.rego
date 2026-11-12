package kubernetes

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  container.securityContext.runAsNonRoot == false
  msg := sprintf("Deployment %q container %q must not set runAsNonRoot to false", [input.metadata.name, container.name])
}

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.securityContext.runAsNonRoot == true
  not input.spec.template.spec.securityContext.runAsNonRoot == true
  msg := sprintf("Deployment %q container %q must enforce runAsNonRoot", [input.metadata.name, container.name])
}

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.cpu
  msg := sprintf("Deployment %q container %q must define a CPU limit", [input.metadata.name, container.name])
}

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.memory
  msg := sprintf("Deployment %q container %q must define a memory limit", [input.metadata.name, container.name])
}

deny[msg] {
  input.kind == "Deployment"
  input.metadata.name == "erp03-backend"
  container := input.spec.template.spec.containers[_]
  not container.readinessProbe
  msg := sprintf("Backend container %q must define a readiness probe", [container.name])
}
