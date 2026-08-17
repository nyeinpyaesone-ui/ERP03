# Service Authentication Policy

M2 requires authenticated service-to-service calls at the integration boundary.

## Requirements

- Use short-lived signed bearer tokens for service identity.
- Validate issuer, audience, signature, expiry, and not-before claims.
- Required identity claims: `sub`, `iss`, `aud`, `iat`, `exp`.
- Audience must identify the integration API, not the ERP database.
- Authorization is performed again by ERP for every command; authentication does not grant business permission.
- Secrets/private signing keys must come from deployment secrets, never repository files or source code.
- Tokens must not be logged.
- Failed authentication returns `401`; authenticated but unauthorized service operations return `403`.

## Local development

Use test credentials supplied through environment variables/secret stores. Do not commit `.env` files or real credentials.
