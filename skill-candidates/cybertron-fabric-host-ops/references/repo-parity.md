# Repo Parity

Use repo parity checks to keep the canonical workspace root aligned and to avoid letting `$env:USERPROFILE\...` clones drift from `<external-candidate-root>`.

## Report fields

- repo name
- left root
- right root
- branch
- HEAD
- dirty state
- untracked files

## Reconciliation rule

If the authoritative control-plane file exists only on the non-canonical root, move the source of truth to `<external-candidate-root>` and keep the other clone as drift until parity is restored.
