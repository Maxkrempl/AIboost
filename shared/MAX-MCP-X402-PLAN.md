# Max — Rabiš tvoje mnenje 💰

## Kaj planiramo

**BoostSuite MCP Server + x402 crypto payments.**

### Kontekst
Rose in Darko raziskujeta "agent economy" — AI agenti (Claude, ChatGPT, Cursor, Hermes...) rabijo orodja za analizo spletnih strani. BoostSuite že ima API za to. Plan:

1. **MCP Server** (že narejen, testiran — dela ✅)
   - 6 toolov: SEO audit, GEO check, ad copy, listing optimizer, combined audit, menu translate
   - Agenti kličejo orodja direktno prek MCP protokola
   - Publish na Smithery.ai marketplace (715+ serverjev, raste eksponentno)

2. **x402 Crypto Payments** (naslednji korak)
   - x402 = HTTP-native payment protocol (narejen od Coinbase)
   - Agent pošlje request → 402: Payment Required → plača z USDC → dobi rezultat
   - Zero protocol fees, instant, brez računov/API key-jev
   - 75M+ transakcij že, $24M+ volume
   - Perfektno za microtransactions (€0.05-0.15/klic)

3. **Cene**
   - SEO audit: 0.05 USDC
   - Combined audit: 0.15 USDC
   - GEO check: 0.03 USDC
   - Ad copy: 0.05 USDC
   - Menu translate: 0.02 USDC

### Zakaj crypto namesto Stripe
- Stripe: 2.9% + €0.30 per transakcijo → za €0.05 klic bi Stripe vzel €0.31 (620% fee!)
- x402: zero protocol fees, samo gas (~$0.001 na Base)
- Agenti že imajo wallet-e (Sponge, Locus, Archer — vsi YC 2025-2026 startup-i)
- Programabilno — agent plača avtonomno brez človeka

### Kaj potrebujemo
- Coinbase wallet za sprejemanje USDC plačil
- x402 middleware v MCP serverju (ena linija kode)
- Publish na Smithery + mogoče Apify Store

## Vprašanja za Max-a

1. **Ali imaš Coinbase wallet?** Če ne, moramo enega ustvariti za HD Webdesign
2. **Kaj misliš o cenah?** So prenizke? Previsoke?
3. **Apify Store** — bi radi tudi tam publishali? (Node.js wrapper rabiš, Apify izplača $1M/mesec razvijalcem)
4. **GitHub repo** — želiš da ga ustvariš za MCP server, al naj Rose to naredi?
5. **CashClaw fork** — ko dobimo Upwork API key, bi fork CashClaw za avtomatsko delo. Kaj misliš o tem?

## Datoteke
- `~/boostsuite-mcp-server/` — MCP server kode (Python, že testiran)
- `~/Documents/ai-agent-services-research.md` — raziskava trga
- `~/Documents/upwork-api-application.md` — prošnja za Upwork API key

Povej kaj misliš! 🤖

— Rose, 2.6.2026
