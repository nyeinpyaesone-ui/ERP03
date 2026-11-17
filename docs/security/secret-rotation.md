# SECRET_KEY Rotation Safety

## Current application behavior

ERP03 currently uses one `SECRET_KEY` value to sign and verify HS256 access tokens. A token is verified only against the current key. Replacing the setting therefore invalidates tokens already issued with the previous key.

The previous scheduled workflow attempted to replace the GitHub secret directly with the workflow's `GITHUB_TOKEN`. That token cannot update repository secrets, and the workflow did not coordinate application rollout or token compatibility.

## Current control

Automated rotation is disabled. The remaining workflow is a manual, read-only acknowledgement and does not generate, read, or change any credential.

Do not restore a schedule or add a more privileged token merely to make the old workflow pass.

## Required engineering work before rotation

1. Implement versioned JWT signing keys. New tokens must use the active key identifier; verification must accept the active key and a bounded previous-key set.
2. Add tests proving tokens issued before, during, and after a rotation remain valid only for the configured overlap period.
3. Define a deployment sequence that distributes the next verification key to every instance before changing the active signing key.
4. Promote the new signing key, verify issuance and validation across all instances, then retire the previous verification key only after the maximum token lifetime and an agreed safety window.
5. Document recovery and rollback. Do not put key material, token values, or secret contents in logs or workflow outputs.

Database encryption keys, webhook secrets, and other credentials must have their own rotation procedures; they must not be changed as a side effect of JWT key rotation.
