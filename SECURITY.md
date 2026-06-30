# Security Policy

## Supported Versions

| Version | Supported |
|---|:---:|
| 1.x | ✅ |

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability, please report it responsibly:

1. **Email**: Send details to the repository owner via GitHub's private security advisory feature.
2. **Go to**: [Security Advisories](https://github.com/Azziz14/Rag_Placement_Copilot-/security/advisories/new)
3. **Include**:
   - A description of the vulnerability
   - Steps to reproduce it
   - Potential impact
   - Suggested fix (if any)

We will acknowledge your report within **48 hours** and aim to release a fix within **7 days** for critical issues.

## Security Best Practices for Self-Hosting

- Never commit `.env` files — use `.env.example` as a template.
- Rotate your `SUPABASE_JWT_SECRET` and `GEMINI_API_KEY` regularly.
- In production, restrict `BACKEND_CORS_ORIGINS` to your exact frontend domain.
- Use PostgreSQL with SSL in production — do not use SQLite.
- Run the Docker container as a non-root user.
