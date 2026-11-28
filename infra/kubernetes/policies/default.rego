package main

import future.keywords.in

# Default deny-all policy set when no external policies repo is reachable.
# Local default-deny fallback policy. The dedicated external policies
# repository (erp03/policies) has not yet been established.

default allow = false

# Allow the backend healthcheck endpoint pattern
allow {
	input.operation == "http.request"
	input.path == "/api/v1/healthz"
	input.method == "GET"
}

# Allow the backend readiness endpoint pattern
allow {
	input.operation == "http.request"
	input.path == "/api/v1/readyz"
	input.method == "GET"
}
