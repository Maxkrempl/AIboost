# Marketing Content — BoostSuite MCP Server (za Smithery publish)

## Smithery Listing

**Name:** BoostSuite
**Description:** Website audit tools for AI agents — SEO, GEO, performance, security, accessibility, GDPR compliance. Pay per call with USDC (x402) or subscribe with API key.

**Tags:** seo, audit, website, accessibility, security, gdpr, performance, ai-agent, x402, crypto

## Short Description (for Smithery card)
> 6 website audit tools for AI agents. SEO audit, GEO check, ad copy generation, listing optimization, combined audit, menu translation. Pay with USDC (x402) — zero fees, instant.

## Long Description (for Smithery page)
> BoostSuite gives AI agents the power to analyze any website. Run SEO audits, check AI search visibility (GEO), generate ad copy, optimize listings, and more — all through the MCP protocol.
>
> **Pay per call with USDC** via x402 protocol — zero protocol fees, no accounts needed, instant payments on Base network. Or subscribe with an API key for monthly plans.
>
> Perfect for: coding agents that need to audit sites, marketing agents optimizing content, research agents analyzing competitors.

## Marketing Posts

### Post 1: Smithery Launch Announcement
🚀 **BoostSuite MCP Server is live!**

6 website audit tools for AI agents:
• SEO Audit — full analysis with score + fixes
• GEO Check — AI search visibility (ChatGPT, Gemini, Perplexity)
• Ad Copy Generator — Google, Facebook, Instagram, LinkedIn, email
• Listing Optimizer — marketplace optimization
• Combined Audit — all-in-one health check
• Menu Translate — 9 languages, appetizing descriptions

💰 **Pay with USDC** via x402 — zero fees, no accounts, instant.
🔑 Or use an API key for monthly plans.

Install: `npx -y @smithery/cli install @hercegdarko/boostsuite-mcp-server`

#MCP #AIAgents #SEO #x402 #USDC

### Post 2: Technical Deep Dive
**How we monetized an MCP server with crypto payments:**

1. Built 6 PHP API endpoints for website audits
2. Wrapped them as MCP tools (Python, FastMCP)
3. Added x402 payment middleware — agent pays 0.02-0.15 USDC per call
4. Hybrid: x402 for agents, Stripe for human subscribers
5. Published on Smithery.ai

The agent flow:
→ Call tool → 402 Payment Required (price + wallet)
→ Pay USDC on Base → retry with tx hash
→ Verified on-chain → get result

No API keys. No accounts. No human needed.

Code: github.com/Maxkrempl/boostsuite-mcp-server

### Post 3: Value Proposition
**Every AI agent needs to audit websites.**

SEO scores. AI visibility. Security checks. Performance. Accessibility. GDPR.

BoostSuite MCP Server gives your agent all 6 tools in one package.

Pricing:
• SEO audit: 0.05 USDC
• GEO check: 0.03 USDC
• Combined audit: 0.15 USDC
• Menu translate: 0.02 USDC

That's cheaper than a coffee per audit. ☕

#AIAgents #MCP #WebDev #Crypto

## GitHub README section (for repo)

### Why BoostSuite MCP?

Most MCP servers are wrappers around existing APIs. BoostSuite is different — we built the API specifically for AI agents:

- **Real audits** — not just scraping, actual analysis with AI-powered insights
- **Micro-payments** — pay exactly what you use, no subscriptions required
- **Agent-native** — designed for autonomous agents, no human in the loop
- **Hybrid payment** — x402 crypto for agents, Stripe for humans
- **9 tools** — SEO, GEO, ads, listings, combined audit, menu translation
