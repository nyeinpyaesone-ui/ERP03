# CI recovery checkpoint — 2026-08-13

This file intentionally records the controlled retry checkpoint after GitHub Actions run 31681872516 ended with `startup_failure` and zero jobs. It contains no credentials and no runtime configuration.

Recovery policy:
- Do not blindly retry failed jobs when GitHub created no jobs.
- Verify GitHub Actions service health before the next trigger.
- Use one controlled trigger after service health is confirmed.
- If startup failure repeats, stop retries and investigate repository/org Actions policy or runner availability rather than modifying application code.
