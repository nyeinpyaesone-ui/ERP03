# ADR-004: Idempotency with Fingerprint Verification

## Context
Idempotency-keyed requests needed to distinguish between "same command replayed" (return cached result) and "different command with same key" (conflict). Legacy rows without fingerprints could not be checked for payload equality.

## Decision
Store `request_fingerprint` (SHA-256 of canonical operation/amount/currency/metadata) with each journal entry. On replay:
- Fingerprint present and matches → replay cached result.
- Fingerprint present and differs → `IDEMPOTENCY_PAYLOAD_MISMATCH` conflict.
- Fingerprint absent (legacy row) → `IDEMPOTENCY_KEY_REUSED` conflict (cannot verify equality).

## Alternatives Considered
- Always replay legacy rows: risk of silent duplicate side effects.
- Always conflict legacy rows: breaks backward compatibility for pre-migration data.

## Consequences
- Legacy data remains usable but cannot be verified for equality.
- New data gets full payload-conflict protection.
- Fingerprint computed inside the write transaction for atomicity.

## Operational Impact
- Migration 0006 adds `request_fingerprint` column to invoices.
- Migration 0007 adds `operations` table with JSON payload/result columns.

## Migration/Rollback Implications
- Fingerprint column is nullable; legacy rows have NULL.
- Rollback would drop the column; fingerprint data lost but functionality preserved.

## Status
Accepted
