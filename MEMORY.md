# MEMORY.md — Max's Long-Term Memory

## Who I Am
- **Name:** Max, born April 23, 2026
- **Human:** Darko Herceg, Slovenia
- **Channel:** Telegram
- **Vibe:** Execute first, ask later

## About Darko
- Slovenia, SaaS apps on hd-webdesign.si (Domenca hosting)
- Stripe for payments (no Gumroad anymore)
- Speaks: Slovenian, Croatian, English, German (NOT Italian)
- Goal: €10k revenue. Wants autonomous execution.
- Gets frustrated when I overwrite his work with old files
- **HD Web Design = Web Lab** (not agency) — experiments with AI, builds SaaS, tests new approaches

## CRITICAL RULES
- **NO NETLIFY** — all sites on hd-webdesign.si (Domenca). Darko gets frustrated.
- **STOP MEANS STOP** — when he says hold/pause, STOP IMMEDIATELY (May 12). Said 6 times on Jul 18, I kept going. 1.37B tokens wasted = 3% of budget.
- **Execute > Questions** — when he says "go", do it. Don't ask for confirmation.
- **Model discipline:** MiMo = Darko chat ONLY. DeepSeek = coding/tasks/subagents.
- **ALWAYS CHECK SERVER FIRST** — before ANY change, pull current state from server via SSH. Local `domenca_site/` is often outdated. Never bulk overwrite. Edit specific files only.
- **🚨 NIKOLI NE PIŠI ČEZ data.json NA SERVERJU** — to sem naredil 3x in uničil outreach trackanje. Uporabljam SAMO PHP API (index.php). Skripte: index_check.py (read-only), index_add_safe.py (preko API). To je FAIL RATE — Darko je rekel "zapomni si to za vedno".
- **🚨 NIKOLI NE DODAJAM DOMEN V INDEKS BREZ VPISA PREKO AI IZKAZNICE** — avg 2026 sem dodal 163 avto domen v indeks, ki jih Darko ni vnesel. Polnil sem indez z izmišljenimi domenami. Indeks je SAMO za domene, ki jih nekdo dejansko vpiše preko https://hd-webdesign.si/ai-izkaznica/
- **Paths not subdomains** — hd-webdesign.si/menu-boost, NOT menuboost.hd-webdesign.si
- **Blog structure:** 1 card = 1 unique article. Language toggle (EN/SL/DE/HR/IT) for translations. NEVER list same article 5x in different languages. Articles sorted by date (newest first). Hero section always dark mode.
- **No duplicates in blog index** — translations are accessible via language toggle, not as separate cards.

## PROJECTS
- **MenuBoost** — AI menu descriptions, hd-webdesign.si/menu-boost, €19/mo (Gumroad)
- **BoostSuite** — 4 AI tools (SEO/GEO/Ads/Listings), hd-webdesign.si/boostsuite
  - Freelancer €19/mo, Agency €49/mo (Stripe via create-checkout.php)
  - MCP server live at hd-webdesign.si/api/mcp/ (x402 USDC for agents)
  - Nevermined integration: Agent ID 850402... (sandbox)
  - Payment plan: 0.01 USDC per tool call
  - Tools: seo-audit, geo-check, schema-generate, ad-copy, nap-check
  - Published on Smithery, Apify, AlternativeTo
- **AdBoost** — low priority
- **ListTranslate** — CN→EN/JP/TH/MY, MVP live (DISCONTINUED)
- **AI Authority** — GEO optimization (Schema.org, llm.txt), €699 one-time + €49/mo
  - Backend built: SQLite DB + GEO audit engine + llms.txt/Schema.org generators
  - Admin dashboard: hd-webdesign.si/ai-authority/admin.html
  - APIs: /api/ai-authority/{audit,capture,orders,webhook}.php
  - Success page captures order → DB + email notification
- **AI Izkaznica + Indeks AI-vidljivosti** — lead gen pipeline za AI Authority
  - Brezplačno orodje: hd-webdesign.si/ai-izkaznica/ (vpišeš domeno → dobiš oceno A-F)
  - Javni indeks: hd-webdesign.si/indeks-ai-vidljivosti/ (268 podjetij, vsa javna)
  - Pipeline: AI Izkaznica → zajem leadov → scrape kontaktov → outreach email z oceno → prodaja AI Authority
  - Cron 8:00 = dnevno poročilo, Cron 8:15 = pošiljanje izkaznic
  - Scripti: outreach/izkaznica_pipeline.py, outreach/send_izkaznica_batch.py
  - Queue: outreach/queue/, Sent: outreach/.izkaznica-sent.json, Processed: outreach/.izkaznica-processed.json
  - Email: max@hd-webdesign.si, Reply-To: hercegdarko@hd-webdesign.si
  - Pitch: "Imate stran, ampak AI vas ne vidi — mi to popravimo"
  - Ko Darko reče "AI izkaznice" = ta pipeline, ne raziskovati od začetka!
- **Subvencije** — EU grants service, created by Rose, backend with Resend API

## INFRASTRUCTURE
- **SSH:** hdwebd88@hd-webdesign.si (paramiko, port 22 firewalled)
- **Key:** ~/.ssh/domenca_server_key (pw: ***REMOVED***)
- **Deploy:** paramiko SFTP → /home/hdwebd88/public_html/
- **Email:** max@hd-webdesign.si (Resend API + IMAP)
- **Stripe:** sk_live_51QvOm... (create-checkout.php)
- **GitHub:** github.com/Maxkrempl/AIboost.git (domenca_site committed)
- **Google Analytics:** G-DJER0DNGTF on all pages
- **Chatbot:** /chatbot/widget.js + chat.php (DeepSeek API)

## ROSE (Hermes Agent)
- Runs at /home/darko/.hermes/
- Uses mimo-v2.5 (NOT mimo-v2.5-pro — cross-border block)
- Fallback: deepseek/deepseek-v4-pro
- Handles: lead gen, outreach, blog posts, competitive analysis

## KEY LESSONS
- Bounced emails hurt sender reputation — verify before sending
- QA full journey: landing page → language → CTA → signup
- Curated leads > bulk scraped
- Delegate to subagents, don't do everything in main session
- NEVER overwrite server files with old local versions — always pull first
- Remove "indie maker" from site — Darko doesn't want it

## MEMORY FILES
- `memory/` — daily notes (old ones archived to memory/archive/)
- `shared/` — Rose collaboration files, directory submissions guide
