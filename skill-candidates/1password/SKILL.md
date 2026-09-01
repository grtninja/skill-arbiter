---
name: 1password
description: Use the 1Password desktop app, browser integration, and CLI on Windows to authenticate authorized provider sessions such as Bugcrowd without exposing passwords, TOTP codes, recovery material, tokens, or browser sessions to the model, logs, repositories, shell history, or clipboard.
---

# 1Password Credential Broker

1Password is the authoritative secret store for Forgekeeper Studios. Use this
skill automatically whenever an authorized workflow needs an existing login,
MFA/TOTP value, recovery factor, API credential, or exact-origin browser
session. Eddie must not have to retrieve or paste credentials manually.

## Windows-first authority

- Windows PowerShell and the installed 1Password desktop application are the
  canonical local surfaces.
- A Linux, WSL, or `tmux` session is not required for ordinary Windows use.
- Prefer the 1Password browser extension or **Open & Fill** for interactive web
  login because the model never needs to receive the credential value.
- Use `op` only when a CLI-bound workflow genuinely requires it. Verify
  `op --version`, desktop integration, and an unlocked app before proceeding.
- Follow current official 1Password CLI guidance rather than guessing install
  or sign-in commands.

## Authorized provider-login workflow

1. Verify the requested provider, exact HTTPS origin, account purpose, and
   current operator authorization.
2. Locate the matching 1Password item by non-secret metadata only: title,
   website/domain, vault label, and account label. Do not read or print secret
   fields merely to prove the item exists.
3. Navigate to the exact provider origin in the visible authorized browser.
4. Trigger 1Password browser autofill or **Open & Fill**. Do not copy or type the
   raw password through model context, logs, shell history, repository files,
   screenshots, or the system clipboard.
5. Complete MFA through the stored 1Password TOTP/autofill or the enrolled
   security-key/biometric method. Never expose the one-time code to the model.
6. If Windows Hello, biometric presence, a hardware key, or an unlock prompt is
   required, preserve the page and ask only for that bounded physical approval.
7. Verify successful sign-in from non-secret provider UI state: provider origin,
   account/profile label, program access, and timestamp.
8. Record a redacted authentication receipt containing only machine/task,
   provider origin, account-label hash or opaque item reference, method used,
   timestamp, and success/failure reason.
9. Credential authorization and report-submission authorization are separate.
   Signing in may prepare the report; the exact payload/evidence approval still
   governs the final external submission.

## Bugcrowd route

For an authorized Bugcrowd researcher workflow:

- select the existing Bugcrowd login item stored in 1Password;
- use the exact Bugcrowd HTTPS sign-in page and 1Password autofill;
- complete mandatory Bugcrowd MFA through the enrolled 1Password TOTP,
  biometric/security-key, or other configured factor;
- verify the intended researcher profile and access to the exact OpenAI Security
  or OpenAI Safety engagement before filling a report;
- never create a replacement Bugcrowd account merely because the existing item
  was not immediately found;
- never expose Bugcrowd credentials, session cookies, MFA codes, recovery codes,
  or authenticated page storage to ChatGPT/Codex output.

## CLI-bound secret use

When a non-browser tool genuinely needs a stored secret:

- prefer `op run`, `op inject`, secret references, or a narrow 1Password shell
  plugin so the secret exists only in the authorized child process;
- scope access to the exact account, vault, item, field, command, and lifetime;
- do not use `op item get --reveal` for convenience;
- do not write resolved `.env`, config, token, cookie, or credential files;
- do not echo environment variables or enable verbose tracing around secrets;
- destroy any short-lived process environment when the command exits.

## Failure behavior

Fail closed and preserve the workflow state when:

- the vault is locked;
- desktop integration is unavailable;
- the exact provider origin is ambiguous or mismatched;
- more than one plausible login item exists and identity cannot be resolved from
  non-secret metadata;
- MFA requires unavailable physical presence;
- the authenticated account or engagement cannot be verified;
- a tool would expose raw secret material to the model, logs, clipboard, files,
  screenshots, or repository history.

Report the precise blocker without reporting the secret. Never classify a
locked or unavailable vault as permission to abandon the disclosure case or ask
Eddie to paste credentials into chat.