# Security Policy

Automax is pre-release software. Security-sensitive defaults must be explicit and
reviewed before public release.

## Reporting vulnerabilities

Do not publish sensitive exploit details in public issues. Open a private security
advisory when available, or contact the maintainer with a minimal description and
reproduction details.

## Security design notes

- SSH host key verification defaults should remain strict.
- Secrets are loaded from external providers, not embedded in job files.
- Logs and state files must not expose secret values.
- Unsafe options must be visible in YAML or CLI parameters.
