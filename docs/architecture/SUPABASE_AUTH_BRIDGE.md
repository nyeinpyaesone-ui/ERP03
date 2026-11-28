# ERP03 Supabase Auth bridge

## Architecture

ERP03 remains the system of record for users, businesses, branches, roles, permissions and business data. The existing ERP credential/JWT flow remains available. Supabase Auth is an optional second identity provider, not a replacement for ERP authorization.

A Supabase identity is linked only after:
1. The user is authenticated with an active ERP03 account.
2. Supabase Auth validates the submitted access token through the project's `/auth/v1/user` endpoint.
3. Supabase reports a verified email.
4. The verified Supabase email matches the current ERP user's email.
5. The Supabase subject is not already linked to another ERP user, and the ERP user has no conflicting link.

The backend stores only the Supabase Auth user UUID on `users.supabase_user_id`. Business and branch claims are always loaded from the ERP database; Supabase metadata and JWT custom claims never grant ERP roles or tenant access.

## Configuration

Backend runtime (both values required):
- `SUPABASE_URL`: HTTPS project URL.
- `SUPABASE_PUBLISHABLE_KEY`: publishable key, never a service-role or secret API key.

Frontend build:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_PUBLISHABLE_KEY`

The Vite configuration also maps the existing Vercel `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` variables to those public build-time names. No `SUPABASE_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, or `SUPABASE_JWT_SECRET` is exposed to the browser.

For the Vercel Vite project, set the public URL and publishable key for Preview and Production (and Development if used). The backend deployment must separately receive the same two settings in its private runtime environment. Do not put backend-only credentials in Vercel frontend variables.

## User flow

1. Sign in with the existing ERP03 credentials.
2. Open Settings → Authentication.
3. Sign in with the Supabase user whose email is already verified and matches the ERP account.
4. ERP03 links the Supabase UUID to the current ERP user.
5. Later sessions may sign in through Supabase; the backend verifies the access token with Supabase and resolves the mapped ERP user before authorizing any API operation.

Unlinked Supabase users are denied. No automatic email-based account linking occurs. Existing ERP login and registration remain supported.

## Operations and safety

- Apply Alembic revision `0011_supabase_identity_link` after `0010_txn_journal` through the normal reviewed ERP03 database migration process.
- Do not apply this migration to the connected Supabase project: the column belongs to ERP03's existing application database.
- Keep Supabase Auth redirect/site URLs restricted to approved ERP03 origins in the Supabase dashboard.
- Enable email confirmation and configure SMTP before enabling production Supabase sign-in.
- The frontend keeps its session in tab-scoped `sessionStorage`; refresh tokens are rotated through Supabase Auth.
- Auth verification depends on the Supabase Auth API; temporary provider outages fail closed with HTTP 503.
- Unlinking, account deletion, and identity reassignment require a separately reviewed administrative workflow.

## Validation status

The migration and feature are present on the draft ERP03 feature branch. CI, staging Auth-flow tests, and migration rollback validation must pass before production activation.
