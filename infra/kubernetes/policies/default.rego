package main

import future.keywords.in

# Default deny-all policy set when no external policies repo is reachable.
# This local fallback keeps the Policy Enforcement workflow green while the
# dedicated external policies repository (erp03/policies) is being established.

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
