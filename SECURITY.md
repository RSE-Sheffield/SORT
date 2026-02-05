# Security Policy

This document outlines security procedures and policies for the SORT (Self-Assessment of Organisational Readiness Tool) project.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| v0.x.x  | :white_check_mark: |

Only the latest release receives security patches. We recommend always running the most recent version.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in SORT, please report it responsibly by emailing:

**info-security@sheffield.ac.uk**

Include the following information in your report:

- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Location of the affected source code (file path, line number if known)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if available)
- Potential impact of the vulnerability
- Any suggested remediation

### What to Expect

- **Acknowledgement**: We will acknowledge receipt of your report within 3 working days
- **Initial Assessment**: We will provide an initial assessment within 10 working days
- **Resolution Timeline**: Critical vulnerabilities will be addressed as a priority; others will be scheduled based on severity
- **Disclosure**: We will coordinate with you on public disclosure timing after a fix is available

We are committed to working with security researchers and will not take legal action against individuals who:

- Report vulnerabilities in good faith
- Avoid accessing or modifying data belonging to others
- Do not exploit vulnerabilities beyond what is necessary to demonstrate the issue
- Allow reasonable time for remediation before disclosure

## Security Measures

### Authentication & Authorisation

- **Custom User Model**: Email-based authentication with mandatory email verification
- **Role-Based Access Control**: ADMIN and PROJECT_MANAGER roles with permission inheritance
- **Session Management**:
  - Sessions expire on browser close
  - 30-minute inactivity timeout
  - Secure, HTTP-only session cookies in production
- **Password Policy**: Django's built-in validators (minimum length, common password check, user similarity check)

### Data Protection

- **CSRF Protection**: Enabled on all state-changing operations
- **Clickjacking Protection**: X-Frame-Options set to SAMEORIGIN
- **Secure Cookies**: SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE enabled in production
- **File Upload Validation**: Restricted to specific file types with size limits
- **Database Security**: Principle of least privilege for database user permissions

### Transport Security

- **TLS 1.3**: Exclusive use of TLS 1.3 (no legacy protocol support)
- **HSTS**: HTTP Strict Transport Security enabled with 2-year max-age
- **Modern Cipher Suites**: X25519, prime256v1, secp384r1 curves only
- **No Compression**: Disabled to mitigate BREACH attacks

### Infrastructure Security

- **Non-root Execution**: Application runs under dedicated service accounts
- **systemd Hardening**: Process isolation with ProtectSystem, NoNewPrivileges, MemoryDenyWriteExecute
- **Reverse Proxy**: Nginx handles TLS termination and static file serving
- **Environment Isolation**: Sensitive configuration via environment variables with restricted file permissions

### Code Security

- **CodeQL Analysis**: Weekly automated security scanning
- **Dependency Updates**: Regular patching of Python and JavaScript dependencies
- **Linting**: Automated code quality checks on all pull requests
- **Code Review**: All changes require review before merging to main branch

## Security Best Practices for Deployment

When deploying SORT, ensure the following:

1. **Environment Variables**
   - Set `DJANGO_DEBUG=False` in production
   - Generate a strong `DJANGO_SECRET_KEY` using `python -c "import secrets; print(secrets.token_urlsafe(37))"`
   - Restrict `.env` file permissions to `600`

2. **Database**
   - Use a dedicated database user with minimal required privileges
   - Enable SSL connections to the database server
   - Use strong, unique database credentials

3. **Web Server**
   - Configure TLS with certificates from a trusted CA
   - Enable HSTS and other security headers
   - Disable directory listing and server version disclosure

4. **Monitoring**
   - Enable access and error logging
   - Monitor for suspicious activity patterns
   - Set up alerts for authentication failures

See [docs/deployment.md](docs/deployment.md) for detailed deployment instructions.

## Security Updates

Security updates are released as patch versions (e.g., 3.12.1 → 3.12.2). Subscribe to repository releases to receive notifications:

1. Go to [github.com/RSE-Sheffield/SORT](https://github.com/RSE-Sheffield/SORT)
2. Click "Watch" → "Custom" → Select "Releases"

## Acknowledgements

We thank the security researchers who have responsibly disclosed vulnerabilities to help keep SORT secure.

## Contact

For other concerns, contact: **rse@sheffield.ac.uk**

For general questions or issues, use [GitHub Issues](https://github.com/RSE-Sheffield/SORT/issues).
