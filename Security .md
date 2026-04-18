# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | ✅ Active support |
| 1.x     | ⚠️ Security fixes only |
| < 1.0   | ❌ No support |

---

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

If you discover a security vulnerability, please report it privately:

1. **Email:** [your-email@example.com] with subject `[SECURITY] Score Impact Analyzer`
2. **Include:** A description of the vulnerability, steps to reproduce, and potential impact
3. **Response time:** We aim to acknowledge within 48 hours and provide a fix timeline within 7 days

We appreciate responsible disclosure and will credit reporters in the changelog (unless you prefer anonymity).

---

## Security Design Principles

### 1. No Hardcoded Credentials
All database URIs, passwords, and API keys are loaded exclusively from environment variables. The `.env` file is listed in `.gitignore` and must never be committed to version control.

```python
# ✅ Correct — from config.py
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# ❌ Never do this
client = MongoClient("mongodb://admin:password@myserver:27017/")
```

### 2. Student Data Privacy
- Real student attempt files (`.json`) are **gitignored** — they must never be committed
- Student IDs are **masked** in all log output (first and last character only, e.g. `s***1`)
- No student PII is stored in application logs
- The `data/` directory is excluded from version control

### 3. Input Validation
All JSON files loaded from disk are schema-validated before database insertion. Malformed data raises a descriptive exception rather than being silently ingested.

### 4. MongoDB Hardening Checklist
Before deploying to production, ensure:

- [ ] MongoDB is **not** exposed on a public IP without authentication
- [ ] Create a **dedicated database user** with least-privilege access (read/write to `sat_analysis` only)
- [ ] Enable [MongoDB authentication](https://docs.mongodb.com/manual/security/)
- [ ] Use TLS for MongoDB connections in production (`tls=true` in the URI)
- [ ] Disable the MongoDB HTTP interface if enabled
- [ ] Rotate the `MONGO_URI` credentials periodically

```bash
# Example: create a restricted MongoDB user
use sat_analysis
db.createUser({
  user: "sat_app",
  pwd: "<strong-random-password>",
  roles: [{ role: "readWrite", db: "sat_analysis" }]
})
```

### 5. Dependency Security
- Dependencies are pinned to exact versions in `requirements.txt`
- Run `pip audit` or `safety check` regularly to scan for known CVEs
- Automated dependency updates are recommended (Dependabot or Renovate)

```bash
pip install pip-audit
pip-audit
```

### 6. Logging
- Logs are structured JSON — never interpolate raw user-supplied values into log messages
- Log files are excluded from version control via `.gitignore`
- Production deployments should ship logs to a centralised SIEM, not to local disk

---

## Known Limitations

- This tool is designed for **local/trusted-network use**. It does not implement authentication for the analysis pipeline itself — access control is delegated to MongoDB and OS-level permissions.
- The tool does not currently support encrypted storage of student data at rest. If deploying on a shared server, use MongoDB's [Encrypted Storage Engine](https://www.mongodb.com/docs/manual/core/security-encryption-at-rest/).

---

## Acknowledgements

Thanks to all responsible reporters who help keep this project secure.
