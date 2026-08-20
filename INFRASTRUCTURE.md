# INFRASTRUCTURE.md — Server & Service Access

> **This is the single source of truth for all infrastructure Max manages.**
> Keep this updated when anything changes.

---

## 🖥️ Domenca Server (hd-webdesign.si)

### SSH Access
- **Host:** hd-webdesign.si
- **User:** hdwebd88
- **Port 22 is firewalled from outside**
- **MUST use paramiko** (Python SSH library) — regular `ssh` command won't work
- **Key:** `~/Downloads/adboost-fixed/id_rsa` (encrypted)
- **Passphrase:** same as cPanel password
- **cPanel password:** `gRwu.&#^gaB?HxA{`

### Quick Connect
```python
import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('hd-webdesign.si', username='hdwebd88',
            key_filename='/home/darko/Downloads/adboost-fixed/id_rsa',
            password='gRwu.&#^gaB?HxA{', timeout=10)
```

### Available UAPI Commands
- `DNS::parse_zone` — read zone records (need SOA serial)
- `DNS::mass_edit_zone` — add/remove DNS records (requires serial)
- `DNS::list_zones` — list all zones
- `SubDomain::addsubdomain` — create subdomains
- `Email::*` — email management

### DNS Zone
- **Domain:** hd-webdesign.si
- **Nameservers:** cdns1.controlpanel.si, cdns2.controlpanel.si
- **DNS is managed via UAPI from SSH** (not cPanel web UI)

---

## 📧 Email

### Accounts
| Account | Password | Use |
|---------|----------|-----|
| max@hd-webdesign.si | ***REMOVED*** | Outreach & campaigns |
| darko@hd-webdesign.si | — | Business email |
| hercegdarko@hd-webdesign.si | — | Personal email |

### SMTP/IMAP Settings
- **IMAP:** mail.hd-webdesign.si:993 (SSL)
- **SMTP:** mail.hd-webdesign.si:465 (SSL)
- **Note:** SSL cert has hostname mismatch (common on shared hosting) — use `ssl.CERT_NONE` in Python

---

## 🌐 Hosting

### Active Sites (Domenca — hd-webdesign.si)
| Site | URL |
|------|-----|
| MenuBoost | hd-webdesign.si/menu-boost |
| BoostSuite | hd-webdesign.si/boostsuite |
| AdBoost | hd-webdesign.si/ad-boost |
| Blog | hd-webdesign.si/blog |

**All sites are hosted on Domenca (hd-webdesign.si). No Netlify.**

---

## 🌍 DNS Records (hd-webdesign.si)

### Active Records
| Name | Type | Value |
|------|------|-------|
| @ | A | 212.44.101.121 |
| menuboost | CNAME | menuboostai.netlify.app |
| boostsuite | CNAME | boostsuite.netlify.app |
| adboost | CNAME | adboost-mvp.netlify.app |

### Adding New DNS Records
```python
import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('hd-webdesign.si', username='hdwebd88',
            key_filename='/home/darko/Downloads/adboost-fixed/id_rsa',
            password='gRwu.&#^gaB?HxA{', timeout=10)

# Get current serial
stdin, stdout, stderr = ssh.exec_command('uapi DNS parse_zone zone=hd-webdesign.si 2>&1')
# Find SOA record → serial number

# Add CNAME
record = json.dumps({"dname": "sub.hd-webdesign.si.", "record_type": "CNAME",
                      "ttl": 3600, "data": ["target.netlify.app."]})
cmd = f"uapi DNS mass_edit_zone zone=hd-webdesign.si serial={serial} add='{record}' 2>&1"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
```

---

## 📝 Blog (hd-webdesign.si/blog)

- **Location on server:** `/public_html/blog/`
- **Managed by:** Max (create, edit, publish posts)
- **Current posts:**
  1. Why AI Menu Translations Beat Google Translate
  2. GEO: The New SEO
  3. Building SaaS from Slovenia

---

## 📊 Outreach Infrastructure

### Sender
- **Email:** max@hd-webdesign.si
- **SMTP:** mail.hd-webdesign.si:465 (SSL)
- **Scripts:** `outreach/send_direct.py` (reusable), campaign-specific scripts in `outreach/`
- **Sent logs:** `outreach/sent/*.csv`
- **Suppression:** `outreach/suppression.txt`
- **Reply monitoring:** `outreach/check_replies.py` (IMAP check)

### Lead Storage
- **MenuBoost:** `lead-gen/menuBoost/`
- **BoostSuite:** `lead-gen/boostsuite/`

---

_Last updated: 2026-05-13 by Max_
