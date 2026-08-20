# Security Runbook - Protecting Your SaaS Apps

## Overview
Your apps run on Netlify with Claude API backends. This runbook covers the essential security practices to keep your apps, users, and revenue safe.

---

## 1. API Key Security

### **Never commit API keys to Git**
- [ ] Check `.gitignore` includes:
  ```
  .env
  .env.local
  *.pem
  *.key
  secrets/
  ```
- [ ] Use **Netlify Environment Variables** for:
  - Claude API key
  - Gumroad API key (if integrated)
  - Any other sensitive tokens

### **How to set Netlify env vars**:
1. Netlify Dashboard → Site Settings → Environment Variables
2. Add key-value pairs (e.g., `CLAUDE_API_KEY=sk-xxx`)
3. Redeploy site to pick up changes

### **Rotate keys regularly**:
- [ ] Rotate Claude API key every 90 days
- [ ] Rotate Gumroad API key every 90 days
- [ ] Store old keys in a password manager (1Password, Bitwarden) before deleting

---

## 2. Rate Limiting & Abuse Prevention

### **Problem**: Free tier abuse (bots, scrapers)
**Solution**: Implement rate limiting

### **Frontend rate limiting** (quick fix):
- Use `localStorage` to track uses per IP/session
- Block after 3 free uses (redirect to upgrade page)
- Example:
  ```js
  const uses = localStorage.getItem('uses') || 0;
  if (uses >= 3) {
    alert('Free uses exhausted. Upgrade to Pro!');
    return;
  }
  localStorage.setItem('uses', parseInt(uses) + 1);
  ```

### **Backend rate limiting** (more secure):
- Use Netlify Functions with rate limiting middleware
- Track requests by IP (not just localStorage, which can be cleared)
- Tools: `express-rate-limit`, Cloudflare Workers, or Netlify Edge Functions

### **Cloudflare (recommended)**:
- [ ] Add Cloudflare as a CDN in front of Netlify
- [ ] Enable "Rate Limiting" rules (free tier: 10 rules)
- [ ] Block IPs that exceed 10 requests/minute

---

## 3. HTTPS & Domain Security

### **Enforce HTTPS**:
- [ ] All apps should use HTTPS (Netlify does this by default)
- [ ] Check: `https://yourapp.netlify.app` redirects HTTP → HTTPS

### **Custom domains**:
- [ ] Use custom domains (e.g., `seobooster.ai` instead of `seoboosterai.netlify.app`)
- [ ] Add DNSSEC to your domain registrar (prevents DNS hijacking)
- [ ] Enable "Force HTTPS" in Netlify settings

### **SSL certificate renewal**:
- Netlify auto-renews Let's Encrypt certs
- [ ] Check cert expiry: `https://www.ssllabs.com/ssltest/`

---

## 4. User Data & GDPR Compliance

### **Minimize data collection**:
- [ ] Only collect what you need (email for Pro users, no passwords if using Gumroad)
- [ ] Don't log user inputs (audit results, Etsy listings, menu descriptions) unless anonymized

### **GDPR requirements** (EU users):
- [ ] Add a Privacy Policy page (use a template: [TermsFeed](https://www.termsfeed.com))
- [ ] Add a Cookie Notice if using Google Analytics or similar
- [ ] Allow users to request data deletion (email you at `support@yourapp.com`)

### **Data retention**:
- [ ] Delete logs older than 30 days
- [ ] Don't store API responses long-term (unless user explicitly saves them)

---

## 5. Payment Security (Gumroad)

### **Use Gumroad for payments** (not Stripe directly):
- Gumroad handles PCI compliance, fraud detection, VAT
- You never touch credit card data

### **Verify Gumroad webhooks**:
- [ ] Use Gumroad's webhook signature verification to prevent fake purchases
- [ ] Example:
  ```js
  const crypto = require('crypto');
  const signature = req.headers['x-gumroad-signature'];
  const payload = JSON.stringify(req.body);
  const hash = crypto.createHmac('sha256', process.env.GUMROAD_WEBHOOK_SECRET).update(payload).digest('hex');
  if (hash !== signature) {
    return res.status(401).send('Invalid signature');
  }
  ```

### **Test mode first**:
- [ ] Use Gumroad's test mode before going live
- [ ] Verify refunds work correctly

---

## 6. Dependency Security

### **Keep dependencies updated**:
- [ ] Run `npm audit` weekly
- [ ] Fix high/critical vulnerabilities immediately
- [ ] Update Node.js to latest LTS (currently v24.x)

### **Automate updates**:
- [ ] Use Dependabot (GitHub) or Renovate to auto-create PRs for updates
- [ ] Review and merge weekly

### **Avoid shady packages**:
- [ ] Only use packages with >1K weekly downloads
- [ ] Check package reputation on [Snyk Advisor](https://snyk.io/advisor/)

---

## 7. Backup & Disaster Recovery

### **Git is your backup**:
- [ ] Push code to GitHub/GitLab daily
- [ ] Keep private repos (don't expose .env files)

### **Database backups** (if you add a DB later):
- [ ] Daily automated backups (most DBs have this built-in)
- [ ] Store backups in a different region (e.g., EU + US)

### **Netlify site backups**:
- Netlify keeps deploy history for 90 days
- [ ] Download critical builds manually if needed

---

## 8. Monitoring & Alerts

### **Uptime monitoring**:
- [ ] Use [UptimeRobot](https://uptimerobot.com) (free) to ping your apps every 5 minutes
- [ ] Get email alerts if site goes down

### **Error tracking**:
- [ ] Add [Sentry](https://sentry.io) (free tier) to track JS errors
- [ ] Review errors weekly

### **Log monitoring**:
- [ ] Check Netlify Function logs for unusual activity (500 errors, slow requests)
- [ ] Set up Slack/email alerts for critical errors

---

## 9. Incident Response Plan

### **If API key is leaked**:
1. **Immediately rotate** the key (Claude dashboard → regenerate)
2. **Revoke** the old key
3. **Check logs** for unauthorized usage
4. **Bill spike?** Contact Claude support for refund/dispute

### **If site is hacked**:
1. **Take site offline** (Netlify: "Stop auto-publishing")
2. **Revert to last known good deploy**
3. **Audit Git history** for malicious commits
4. **Change all passwords** (Netlify, GitHub, Gumroad, email)
5. **Enable 2FA** on all accounts

### **If user data is breached**:
1. **Notify affected users** within 72 hours (GDPR requirement)
2. **File a data breach report** (if EU users affected)
3. **Post-mortem**: What went wrong? How to prevent it?

---

## 10. Security Checklist (Monthly Review)

- [ ] API keys rotated (every 90 days)
- [ ] Dependencies updated (`npm audit`)
- [ ] SSL certificates valid (check ssllabs.com)
- [ ] Uptime 99%+ (check UptimeRobot)
- [ ] No critical errors in Sentry
- [ ] Gumroad payments working (test a purchase)
- [ ] Rate limiting working (test 10+ free uses)
- [ ] Privacy Policy + Cookie Notice up to date
- [ ] Backups tested (try restoring a deploy)

---

## Tools Summary

| Task | Tool | Cost |
|------|------|------|
| Env vars | Netlify Dashboard | Free |
| Rate limiting | Cloudflare | Free |
| SSL certs | Let's Encrypt (via Netlify) | Free |
| Uptime monitoring | UptimeRobot | Free |
| Error tracking | Sentry | Free tier |
| Dependency scanning | npm audit | Free |
| Password manager | Bitwarden / 1Password | €3-5/mo |
| 2FA | Authy / Google Authenticator | Free |

---

## Final Notes

- **Security is not a one-time task** — it's ongoing.
- **Automate what you can** (Dependabot, UptimeRobot, Sentry).
- **Don't panic** — most "hacks" are just bots trying common exploits. Rate limiting + HTTPS stops 99% of them.
- **When in doubt, ask** — post in security communities (r/netsec, HackerNews) or hire a freelance security auditor for €100-500.

---

**Stay safe. Build fast. Ship often. 🔒**
