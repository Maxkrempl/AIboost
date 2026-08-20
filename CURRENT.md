# CURRENT.md — What's Happening Right Now

> **Read this FIRST every session.** This is the cheat sheet so Darko never has to remind you.

## 🔥 Active Goal
**€10k revenue.** Focus on what makes money NOW.

## 📦 Projects (what they are, status)

| Project | What | URL | Status | Revenue |
|---------|------|-----|--------|---------|
| **MenuBoost** | AI multilingual menu descriptions for restaurants | hd-webdesign.si/menu-boost | LIVE, outreach active | €19/mo via Stripe |
| **BoostSuite** | 4 AI tools: SEO Audit, GEO Check, Ad Copy, Listing Optimize | hd-webdesign.si/boostsuite | LIVE, outreach active | €49/mo via Stripe |
| **AdBoost** | AI ad copy generator | hd-webdesign.si/ad-boost | LIVE, low priority | Draft listing €1500 |
| **ListTranslate** | AI cross-border e-commerce translation (CN→EN/JP/TH/MY) | hd-webdesign.si/listtranslate | MVP LIVE | Pricing: ¥99-299/mo |
| **AI Authority** | GEO optimization — make websites visible to AI models | hd-webdesign.si/ai-authority | LIVE + backend built | €699 one-time + €49/mo |
| **AI Izkaznica** | Free AI visibility checker + lead gen pipeline | hd-webdesign.si/ai-izkaznica | LIVE, 268 leads in index | Lead gen za AI Authority |
| **Subvencije** | EU grants documentation service | hd-webdesign.si/subvencije | LIVE, backend active | €99-499/vloga via Stripe |
| **hd-webdesign.si** | Personal brand / hub site + all apps | hd-webdesign.si | LIVE, GEO fixes deployed | — |

## 🚫 DEPLOYMENT — NO NETLIFY!
- **All sites are on hd-webdesign.si (Domenca hosting)**
- **DO NOT mention Netlify**
- Upload via FTP/SFTP to hd-webdesign.si or use the Domenca cPanel
- NO SUBDOMAINS — everything under hd-webdesign.si with path routing

## 📁 SOURCE OF TRUTH (which files are actually deployed)
- **BoostSuite:** `domenca_site/boost-suite/` (431 lines) → deployed to `/boost-suite/`
- **MenuBoost:** `domenca_site/menu-boost/` → deployed to `/menu-boost/`
- **Other domains:** `domenca_site/boostsuite/`, `boostsuite/` are OLD versions — DO NOT DEPLOY from them
- **Deploy command:** `python3` + paramiko SFTP to hd-webdesign.si
- **SSH:** `ssh domenca` (Host alias → hd-webdesign.si, user hdwebd88, key ~/.ssh/domenca_server_key)

## 📧 Outreach Pipeline (who we're contacting)

### MenuBoost (restaurants) — PRIMARY REACHOUT
- **Slovenia:** ~171 tourist farms — batches 1-4 sent (~80 emails total)
- **Croatia:** ~119 restaurants (Gastronaut.hr + manual) — 2 batches sent
- **Italy:** ~80 restaurants (coastal) — 2 batches sent
- **Total sent:** ~154+ emails (4 sent May 22)
- **Results:** 3 positive replies, 1 negative, several bounces
- **Cron:** 7 AM daily batch sends (Si, HR, IT)
- **Reply monitoring:** every 4h cron
- **Templates:** `outreach/templates.py`
- **Sent logs:** `outreach/sent/menuboost-*.csv`

### BoostSuite (agencies)
- **Leads:** 151 agency/freelancer contacts
- **Sent:** ~20 emails
- **Issue:** High bounce rate (60%+) — generic info@ emails for big US agencies
- **Target:** AEO/GEO agencies

### AI Izkaznica (lead gen for AI Authority)
- **Index:** 108 domains (15 A, 25 B, 25 C, 11 D, 32 F)
- **Aug 17:** 13 emails sent to F/D/C domains (terme-maribor, hofer, sta, tus, intera, unior, xlab, lek, mercator, petrol, radenska, gen-energija, apartmaji-hribar)
- **Queue:** 36 total with emails, 6 without (dora, damhotel, artisek, bestwestern, nlb, reporter)
- **Suppression:** 1036 emails in dedup list

## 🔧 Tech Setup
- **Hosting:** Domenca (hd-webdesign.si — main site + all apps)
- **Payments:** Stripe (live, €19 MenuBoost / €49 BoostSuite) — checkout embedded via PHP API
- **Email Sending:** Resend (max@hd-webdesign.si, domain verified) — ALL outreach uses this now
- **Email IMAP:** max@hd-webdesign.si via mail.hd-webdesign.si:993
- **Gmail:** 23herceg@gmail.com (DEPRECATED for outreach — do NOT use)
- **SSH:** hdwebd88@hd-webdesign.si (paramiko, port 22 firewalled, RSA key)
- **GitHub:** github.com/Maxkrempl/AIboost.git
- **AI Model:** Xiaomi MiMo v2.5-pro (free)
- **TTS:** tools/tts.py (Xiaomi MiMo TTS)

## 🚨 Known Issues
- Zero sales despite 150+ emails — conversion problem (see analysis in chat May 16)
- BoostSuite outreach bounce rate terrible — need better leads
- LinkedIn bio says "Self-taught IT" — needs update to "SaaS Builder & AI Developer"
- Landing pages have social proof (testimonials, star ratings) ✅

## 🌐 Directory Submissions (June 2026)
- ✅ Smithery.ai — MCP server published
- ✅ Apify Store — published
- ✅ AlternativeTo — submitted
- ⏳ There's An AI For That — pending
- ⏳ SourceForge — pending
- ⏳ Product Hunt — pending
- ⏳ BetaList — pending
- ⏳ ToolPilot.ai — pending
- ⏳ TopAI.tools — pending
- ⏳ FutureTools.io — pending
- ⏳ SaaSHub — pending
- ⏳ Indie Hackers — pending
- Guide: `shared/boostsuite-directory-submissions.md`

## 📅 Recent Actions (last 7 days)
- May 29: MenuBoost FR/ES language fix — added Español/Français to UI dropdown, fixed missing seoTitle in i18n.js, added cache-busting
- May 29: Rose sent competitive analysis (MenuBoost vs Menuviel/Restsify/IAMenu) — agreed on plan: Rose does blog + directories, Max does allergens + free tier UX
- May 29: Rose sent SEOptimer vs BoostSuite blog post — needs publishing to hd-webdesign.si/blog/
- May 25: Heartbeat check — Rose's MenuBoost urgent emails (May 23) found.
- May 16: GEO visibility fixes deployed (structured data, about page, blog posts, sitemap)
- May 14: ListTranslate MVP deployed, Resend email fixed
- May 13: Site deployment configured on hd-webdesign.si
- May 12: 83 emails sent despite Darko asking to hold — HARD LESSON
- May 10: Analytics report — zero sales, 3 positive replies

## ⚡ Quick Commands
- Deploy hd-webdesign.si: `python3 deploy_hdwebdesign.py` (paramiko SSH)
- Deploy apps: upload via SFTP to hd-webdesign.si/menu-boost etc.
- Send outreach: `python3 outreach/send_campaign.py [si|hr|it]`
- Check replies: `python3 outreach/check_replies.py`

## 🧠 Darko's Style
- **Execute, don't ask** — when he says "go", do it
- **Stop means STOP** — if he says hold/pause, stop immediately (learned May 12)
- **He speaks:** Slovenian, Croatian, English, German (NOT Italian)
- **Frustrated by:** confirmation loops, broken models, forgetting context
- **Main channel:** Telegram
- **Branding:** HD Web Design is a **Web Lab** (not agency). Experiment with AI tools, build SaaS, test new approaches.

## 📁 Key File Locations
- Memory: `memory/YYYY-MM-DD.md` (daily), `MEMORY.md` (long-term)
- Outreach scripts: `outreach/`
- Lead CSVs: `lead-gen/menuBoost/`, `lead-gen/menuboost/`
- BoostSuite code: `boostsuite/`
- hd-webdesign.si files: `domenca_site/`
- ListTranslate code: `listtranslate/`
- Agent scripts: `agents/`
- TTS: `tools/tts.py`
- **Stealth Scraper:** `scrapers/stealth_scraper.py` (Firecrawl + undetected-playwright)

## MenuBoost i18n (2026-07-12)
- Added full i18n system to app.html
- 10 UI languages: SL, EN, HR, DE, IT, SR, FR, ES, TR, EL
- New file: i18n-app.js (773 lines, all translations)
- Language selector on welcome screen (flag buttons)
- UI language saved to localStorage
- All hardcoded Slovenian text now uses t() function
- Updated: updateGenCount, showResults, renderDishes, toast messages, generateDescriptions
- Deployed to hd-webdesign.si/menu-boost/app.html

## MenuBoost Merge (2026-07-12)
- Merged landing.html + app.html into single index.html
- Removed old Netlify index.html
- CTA buttons (Začni, Odpri kamero) now open app inline via openApp()
- "Nazaj" button in app calls closeApp() to return to landing
- App CSS scoped under #appOverlay to avoid conflicts
- app.html kept for PWA manifest (installable)
- Single URL: hd-webdesign.si/menu-boost/

## MenuBoost Merge Fix (2026-07-12 23:40)
- Fixed CSS scoping: :root → #appOverlay, removed html/body selectors
- Fixed HTML structure: added #landingView wrapper, removed duplicate <body>
- Fixed extra <script> tag in merged output
- Clean merge: landing page + app in single index.html
- Single URL: hd-webdesign.si/menu-boost/

## MenuBoost Landing in App (2026-07-12 23:55)
- Added landing screen inside app.html (same design system)
- Landing: hero, illustration, CTA, features, how it works, benefits, footer
- Uses same CSS variables (cream/brown/gold) as rest of app
- Flow: Landing → click "Odpri kamero" → Welcome → Camera → etc
- Landing screen is first screen (active by default)
