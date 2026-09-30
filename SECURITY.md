# Security

## Security Principles

- **API Keys**: Must remain server-side. The Next.js frontend NEVER talks to CoinMarketCap directly.
- **Secrets**: Must not be committed. The `.env` file is included in `.gitignore`.
- **Environment**: Only use `.env.example` to document required variables.

## Handling Vulnerabilities

If you discover a security vulnerability, please do not publicly disclose it. Reach out to the repository maintainers via private channels.

## Credentials

If a `CMC_PRO_API_KEY` is accidentally exposed in a commit, rotate it immediately via the CoinMarketCap Developer Portal.
