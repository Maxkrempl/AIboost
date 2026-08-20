#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "BoostSuite MCP",
  version: "1.0.0",
});

// Helper: fetch URL content
async function fetchUrl(url) {
  const res = await fetch(url, {
    headers: { "User-Agent": "BoostSuite-MCP/1.0" },
  });
  return res.text();
}

// Helper: extract meta tags
function extractMeta(html) {
  const title = html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1] || "";
  const desc = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)?.[1] || "";
  const ogTitle = html.match(/<meta[^>]*property=["']og:title["'][^>]*content=["']([^"']+)["']/i)?.[1] || "";
  const ogDesc = html.match(/<meta[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']/i)?.[1] || "";
  const canonical = html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["']/i)?.[1] || "";
  return { title, desc, ogTitle, ogDesc, canonical };
}

// Helper: extract schema.org JSON-LD
function extractSchema(html) {
  const schemas = [];
  const regex = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  while ((match = regex.exec(html)) !== null) {
    try { schemas.push(JSON.parse(match[1])); } catch {}
  }
  return schemas;
}

// ========== TOOL 1: SEO Audit ==========
server.tool(
  "seo-audit",
  "Run SEO audit on a URL — returns title, meta, schema, headers analysis",
  { url: z.string().url() },
  async ({ url }) => {
    try {
      const html = await fetchUrl(url);
      const meta = extractMeta(html);
      const schemas = extractSchema(html);
      const wordCount = html.replace(/<[^>]+>/g, "").split(/\s+/).length;
      const score = [
        meta.title ? 1 : 0, meta.desc ? 1 : 0, meta.ogTitle ? 1 : 0,
        meta.ogDesc ? 1 : 0, meta.canonical ? 1 : 0, schemas.length > 0 ? 1 : 0,
        /<meta[^>]*name=["']viewport["']/i.test(html) ? 1 : 0,
        /<html[^>]*lang=["']/i.test(html) ? 1 : 0,
      ].reduce((a, b) => a + b, 0);
      return {
        content: [{ type: "text", text: JSON.stringify({
          url, score: `${score}/8`,
          title: meta.title || "❌ MISSING", description: meta.desc || "❌ MISSING",
          ogTitle: meta.ogTitle || "❌ MISSING", ogDesc: meta.ogDesc || "❌ MISSING",
          canonical: meta.canonical || "❌ MISSING",
          schemaTypes: schemas.map(s => s["@type"] || "unknown"),
          schemaCount: schemas.length, wordCount,
        }, null, 2) }],
      };
    } catch (e) { return { content: [{ type: "text", text: `Error: ${e.message}` }] }; }
  }
);

// ========== TOOL 2: GEO Check ==========
server.tool(
  "geo-check",
  "Check GEO (Generative Engine Optimization) readiness",
  { url: z.string().url() },
  async ({ url }) => {
    try {
      const html = await fetchUrl(url);
      const schemas = extractSchema(html);
      const meta = extractMeta(html);
      const checks = {
        hasStructuredData: schemas.length > 0,
        hasOrganization: schemas.some(s => s["@type"] === "Organization"),
        hasLocalBusiness: schemas.some(s => s["@type"] === "LocalBusiness"),
        hasFAQ: schemas.some(s => s["@type"] === "FAQPage"),
        hasBreadcrumb: schemas.some(s => s["@type"] === "BreadcrumbList"),
        hasOpenGraph: !!(meta.ogTitle && meta.ogDesc),
        hasCanonical: !!meta.canonical,
        descriptionLength: meta.desc.length,
      };
      const passed = Object.values(checks).filter(v => v === true).length;
      const total = Object.keys(checks).length;
      const recs = [];
      if (!checks.hasStructuredData) recs.push("Add JSON-LD structured data");
      if (!checks.hasOrganization) recs.push("Add Organization schema");
      if (!checks.hasLocalBusiness) recs.push("Add LocalBusiness schema");
      if (!checks.hasFAQ) recs.push("Add FAQ schema");
      if (!checks.hasOpenGraph) recs.push("Add Open Graph meta tags");
      if (!checks.hasCanonical) recs.push("Add canonical URL");
      return {
        content: [{ type: "text", text: JSON.stringify({
          url, geoScore: `${passed}/${total}`, checks, recommendations: recs,
          aiReadiness: passed >= 6 ? "🟢 GOOD" : passed >= 4 ? "🟡 NEEDS WORK" : "🔴 POOR",
        }, null, 2) }],
      };
    } catch (e) { return { content: [{ type: "text", text: `Error: ${e.message}` }] }; }
  }
);

// ========== TOOL 3: Schema Generator ==========
server.tool(
  "schema-generate",
  "Generate JSON-LD schema markup for a business",
  {
    type: z.enum(["Organization", "LocalBusiness", "FAQPage", "Product", "Service"]),
    name: z.string(), url: z.string().url(),
    description: z.string().optional(), phone: z.string().optional(), address: z.string().optional(),
  },
  async ({ type, name, url, description, phone, address }) => {
    let schema = { "@context": "https://schema.org", "@type": type, name, url };
    if (description) schema.description = description;
    if (phone) schema.telephone = phone;
    if (address) schema.address = { "@type": "PostalAddress", streetAddress: address };
    return { content: [{ type: "text", text: `Add this to your page as <script type="application/ld+json">\n\n${JSON.stringify(schema, null, 2)}` }] };
  }
);

// ========== TOOL 4: Ad Copy ==========
server.tool(
  "ad-copy",
  "Generate ad copy for Google/Meta ads",
  { product: z.string(), audience: z.string().optional(), platform: z.enum(["google", "meta", "both"]).default("both") },
  async ({ product, audience, platform }) => {
    const headlines = [`${product} — Hitro in Zanesljivo`, `Najboljša Ponudba za ${product}`, `${product} po Meri`, `Zaupajte Strokovnjakom — ${product}`, `${product} že Od €19/mesec`];
    const descriptions = [`Odkrijte ${product}${audience ? ` za ${audience}` : ""}. Brezplačna preskusna verzija.`, `Z ${product}${audience ? ` za ${audience}` : ""} prihranite čas in denar.`, `${product} — AI-podprto orodje ki deluje.`];
    return { content: [{ type: "text", text: JSON.stringify({ platform, headlines, descriptions, cta: "Preizvusite Brezplačno" }, null, 2) }] };
  }
);

// ========== TOOL 5: NAP Checker ==========
server.tool(
  "nap-check",
  "Check NAP consistency across directories",
  { businessName: z.string(), phone: z.string(), address: z.string(), website: z.string().url() },
  async ({ businessName, phone, address, website }) => {
    const dirs = ["Google Business Profile", "Yelp", "Facebook", "Apple Maps", "Bing Places", "TripAdvisor"];
    return { content: [{ type: "text", text: JSON.stringify({
      business: businessName, nap: { name: businessName, address, phone, website },
      directories: dirs.map(d => ({ name: d, status: "needs_manual_check" })),
      recommendation: "Ensure identical NAP across all directories for local SEO.",
    }, null, 2) }] };
  }
);

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("BoostSuite MCP server running on stdio");
