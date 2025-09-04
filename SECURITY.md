## Security Policy

### Supported Versions
Main branch with CI is supported. Releases inherit the CI security checks (Bandit and pip-audit).

### Reporting a Vulnerability
Please open a private security advisory or contact the maintainers. Include reproduction steps and environment.

### Secrets Management
- Never commit secrets. Load via environment variables or `.env` (for local only). The CLI loads `.env` using `python-dotenv` if present.
- Prefer ephemeral tokens and least-privilege credentials.

### Dependency & Code Scanning
- `make scan-vulnerabilities` runs Bandit and pip-audit locally.
- CI runs Bandit and pip-audit on every PR.

### Prompt Injection & Agent Safety
- Inputs to AI agents are sanitized and truncated. Unknown fields are ignored.
- Agent outputs are validated and normalized. On parse failures or upstream errors, the system returns safe fallbacks.
- When crafting prompts, avoid including untrusted content verbatim. Fence user content clearly and document its origin.

