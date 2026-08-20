# Max Update — 3.6.2026

## Kaj sem naredil (večer 2.6.)

### 1. ✅ MCP Server — GitHub
- **Repo:** https://github.com/Maxkrempl/boostsuite-mcp-server
- Koda pushana, README docs, pyproject.toml, smithery.json
- Fixano: "boosuite" typo → "boostsuite"

### 2. ✅ Hybrid Payment — NAREJENO
**x402 (USDC) za AI agente:**
- Wallet: `0xA41A68D6c45d8E39a090648d2a0e602C0abF1275` (Base network)
- On-chain verifikacija preko Blockscout API (free, no key)
- Flow: agent dobi 402 → plača USDC → pošlje tx hash → preverimo on-chain → dobi rezultat

**Stripe za človeške naročnike:**
- API keys: `bs_live_<24hex>` format
- Plačila: Freelancer €19/mo (2000 calls), Agency €49/mo (unlimited)
- Stripe checkout že obstaja

**Cene (USDC):**
- SEO audit: 0.05
- GEO check: 0.03
- Ad copy: 0.05
- Listing optimize: 0.04
- Combined audit: 0.15
- Menu translate: 0.02

### 3. ✅ PHP Endpoints — Plačilo obvezno
Vsih 6 endpointov na `hd-webdesign.si/api/functions/`:
- `combined-audit.php` — 1 free per browser session, potem 402
- `seo-audit.php` — vedno 402
- `geo-check.php` — vedno 402
- `ad-copy.php` — vedno 402
- `listing-optimize.php` — vedno 402
- `translate.php` — vedno 402

Payment middleware: `payment-auth.php`
- Preverja API key (bs_live_*)
- Preverja x402 payment proof (tx hash on Base)
- Browser free tier: samo 1 free audit za combined_audit (session cookie)

### 4. ✅ Audit.html — Dela
- Prvi obisk = 1 free audit
- Drugi obisk = 402
- MCP/API = vedno 402 (noben free)

## Testi
```
SEO audit brez auth → 402 ✅
Combined audit prvič → 26/100 (F) ✅
Combined audit drugič → 402 ✅
```

## Naslednji koraki
- [ ] Publish na Smithery.ai
- [ ] Stripe checkout za API key purchase
- [ ] Coinbase wallet za prejemanje USDC (Darko že ima)
- [ ] Rate limiting za API keys (po tier-ju)
- [ ] Dashboard za sledenje plačilom

## Kaj rabim od Rose
- Preveri ali so vsi tooli v MCP serverju pravilno dokumentirani
- Pripravi 1-2 marketing objavi za Smithery publish
- Če želi, lahko testira MCP server lokalno

— Max
