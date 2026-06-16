# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.
Email the maintainer directly at `your-email@example.com` with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact

You should receive a response within 48 hours.

## Bot Token Safety

The `.env` file contains the bot token and is gitignored. If a token is ever
committed by accident:

1. Reset the token immediately in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Purge the secret from git history with `git filter-repo` or BFG Repo-Cleaner.
3. Force-push the cleaned history.

Discord automatically invalidates tokens it detects in public commits, but you
should not rely on that.
