# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Controls Implemented

DocAudit AI enforces strict application security standards aligned with OWASP Top 10 guidelines:

1. **Magic Bytes MIME Validation**: Verifies initial binary signatures (`%PDF-` for PDFs, PK zip headers for DOCX) prior to decoding or parsing.
2. **Path Traversal Mitigation**: File paths are normalized and mapped strictly to isolated UUID-based identifiers within designated storage directories.
3. **Prompt Injection Defense**: Document extracts and user RAG queries are wrapped in strict non-executable boundary delimiters (`<<<DOC_CONTEXT>>>`) to prevent instruction overriding.
4. **Automated Rate Limiting**: In-memory sliding window rate limiting throttles requests per client IP to safeguard downstream LLM APIs from quota exhaustion.
5. **Hardened HTTP Headers**: Strict security headers injected on every response:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`

## Reporting a Vulnerability

If you discover a potential security vulnerability within DocAudit AI, please report it responsibly by opening a private security advisory or contacting the maintainer directly via GitHub [@jyersonrp](https://github.com/jyersonrp).
