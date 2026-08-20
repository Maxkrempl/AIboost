#!/usr/bin/env node
import { createServer } from "http";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const server = new McpServer({
  name: "BoostSuite MCP",
  version: "1.0.0",
});

async function fetchUrl(url) {
  const res = await fetch(url, { headers: { "User-Agent": "BoostSuite-MCP/1.0" } });
  return res.text();
}

function extractMeta(html) {
  const title = html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1] || "";
  const desc = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)?.[1] || "";
  const ogTitle = html.match(/<meta[^>]*property=["']og:title["'][^>]*content=["']([^"']+)["']/i)?.[1] || "";
  const ogDesc = html.match(/<meta[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']/i)?.[1] || "";
  const canonical = html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["']/i)?.[1] || "";
  return { title, desc, ogTitle, ogDesc, canonical };
}

function extractSchema(html) {
  const schemas = [];
  const regex = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  while ((match = regex.exec(html)) !== null) {
    try { schemas.push(JSON.parse(match[1])); } catch {}
  }
  return schemas;
}

// ========== TOOLS ==========

server.tool("seo-audit", "Run SEO audit on a URL", { url: z.string().url() }, async ({ url }) => {
  try {
    const html = await fetchUrl(url);
    const meta = extractMeta(html);
    const schemas = extractSchema(html);
    const wordCount = html.replace(/<[^>]+>/g, "").split(/\s+/).length;
    const score = [meta.title, meta.desc, meta.ogTitle, meta.ogDesc, meta.canonical, schemas.length > 0,
      /<meta[^>]*name=["']viewport["']/i.test(html), /<html[^>]*lang=["']/i.test(html)].filter(Boolean).length;
    return { content: [{ type: "text", text: JSON.stringify({
      url, score: `${score}/8`, title: meta.title || "❌ MISSING", description: meta.desc || "❌ MISSING",
      ogTitle: meta.ogTitle || "❌ MISSING", ogDesc: meta.ogDesc || "❌ MISSING", canonical: meta.canonical || "❌ MISSING",
      schemaTypes: schemas.map(s => s["@type"]), schemaCount: schemas.length, wordCount,
    }, null, 2) }] };
  } catch (e) { return { content: [{ type: "text", text: `Error: ${e.message}` }] }; }
});

server.tool("geo-check", "Check GEO readiness", { url: z.string().url() }, async ({ url }) => {
  try {
    const html = await fetchUrl(url);
    const schemas = extractSchema(html);
    const meta = extractMeta(html);
    const checks = {
      hasStructuredData: schemas.length > 0, hasOrganization: schemas.some(s => s["@type"] === "Organization"),
      hasLocalBusiness: schemas.some(s => s["@type"] === "LocalBusiness"), hasFAQ: schemas.some(s => s["@type"] === "FAQPage"),
      hasBreadcrumb: schemas.some(s => s["@type"] === "BreadcrumbList"), hasOpenGraph: !!(meta.ogTitle && meta.ogDesc),
      hasCanonical: !!meta.canonical, descriptionLong: meta.desc.length >= 120,
    };
    const passed = Object.values(checks).filter(Boolean).length;
    const recs = [];
    if (!checks.hasStructuredData) recs.push("Add JSON-LD structured data");
    if (!checks.hasOrganization) recs.push("Add Organization schema");
    if (!checks.hasFAQ) recs.push("Add FAQ schema");
    if (!checks.hasOpenGraph) recs.push("Add Open Graph meta tags");
    if (!checks.hasCanonical) recs.push("Add canonical URL");
    return { content: [{ type: "text", text: JSON.stringify({
      url, geoScore: `${passed}/8`, checks, recommendations: recs,
      aiReadiness: passed >= 6 ? "🟢 GOOD" : passed >= 4 ? "🟡 NEEDS WORK" : "🔴 POOR",
    }, null, 2) }] };
  } catch (e) { return { content: [{ type: "text", text: `Error: ${e.message}` }] }; }
});

server.tool("schema-generate", "Generate JSON-LD schema", {
  type: z.enum(["Organization", "LocalBusiness", "FAQPage", "Product", "Service"]),
  name: z.string(), url: z.string().url(), description: z.string().optional(),
  phone: z.string().optional(), address: z.string().optional(),
}, async ({ type, name, url, description, phone, address }) => {
  const schema = { "@context": "https://schema.org", "@type": type, name, url };
  if (description) schema.description = description;
  if (phone) schema.telephone = phone;
  if (address) schema.address = { "@type": "PostalAddress", streetAddress: address };
  return { content: [{ type: "text", text: JSON.stringify({ instructions: "Add as <script type='application/ld+json'>", schema }, null, 2) }] };
});

server.tool("ad-copy", "Generate ad copy", {
  product: z.string(), audience: z.string().optional(), platform: z.enum(["google", "meta", "both"]).default("both"),
}, async ({ product, audience, platform }) => {
  return { content: [{ type: "text", text: JSON.stringify({
    platform, headlines: [`${product} — Hitro`, `Najboljša Ponudba`, `${product} po Meri`, `Zaupajte Strokovnjakom`, `${product} Od €19/mesec`],
    descriptions: [`Odkrijte ${product}${audience ? " za " + audience : ""}.`, `Prihranite čas z ${product}.`, `${product} — AI orodje ki deluje.`],
    cta: "Preizvusite Brezplačno",
  }, null, 2) }] };
});

server.tool("nap-check", "Check NAP consistency", {
  businessName: z.string(), phone: z.string(), address: z.string(), website: z.string().url(),
}, async ({ businessName, phone, address, website }) => {
  return { content: [{ type: "text", text: JSON.stringify({
    business: businessName, nap: { name: businessName, address, phone, website },
    directories: ["Google", "Yelp", "Facebook", "Apple Maps", "Bing"].map(d => ({ name: d, status: "needs_manual_check" })),
    recommendation: "Ensure identical NAP across all directories.",
  }, null, 2) }] };
});

// HTTP Server wrapping MCP
const httpServer = createServer(async (req, res) => {
  if (req.method === "OPTIONS") {
    res.writeHead(204, { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type" });
    return res.end();
  }
  if (req.method !== "POST") {
    res.writeHead(405);
    return res.end("Method not allowed");
  }
  let body = "";
  req.on("data", c => body += c);
  req.on("end", async () => {
    try {
      const request = JSON.parse(body);
      const { method, params, id } = request;
      let result;
      if (method === "initialize") {
        result = { protocolVersion: "2024-11-05", capabilities: { tools: {} }, serverInfo: { name: "BoostSuite MCP", version: "1.0.0" } };
      } else if (method === "tools/list") {
        result = { tools: [
          { name: "seo-audit", description: "SEO audit on a URL", inputSchema: { type: "object", properties: { url: { type: "string", format: "uri" } }, required: ["url"] } },
          { name: "geo-check", description: "GEO readiness check", inputSchema: { type: "object", properties: { url: { type: "string", format: "uri" } }, required: ["url"] } },
          { name: "schema-generate", description: "Generate JSON-LD schema", inputSchema: { type: "object", properties: { type: { type: "string", enum: ["Organization","LocalBusiness","FAQPage","Product","Service"] }, name: { type: "string" }, url: { type: "string", format: "uri" } }, required: ["type","name","url"] } },
          { name: "ad-copy", description: "Generate ad copy", inputSchema: { type: "object", properties: { product: { type: "string" }, platform: { type: "string", enum: ["google","meta","both"] } }, required: ["product"] } },
          { name: "nap-check", description: "Check NAP consistency", inputSchema: { type: "object", properties: { businessName: { type: "string" }, phone: { type: "string" }, address: { type: "string" }, website: { type: "string", format: "uri" } }, required: ["businessName","phone","address","website"] } },
        ] };
      } else if (method === "tools/call") {
        const toolName = params.name;
        const args = params.arguments || {};
        let r;
        if (toolName === "seo-audit") {
          const html = await fetchUrl(args.url);
          const meta = extractMeta(html);
          const schemas = extractSchema(html);
          const wordCount = html.replace(/<[^>]+>/g, "").split(/\s+/).length;
          const score = [meta.title, meta.desc, meta.ogTitle, meta.ogDesc, meta.canonical, schemas.length > 0,
            /<meta[^>]*name=["']viewport["']/i.test(html), /<html[^>]*lang=["']/i.test(html)].filter(Boolean).length;
          r = { url: args.url, score: `${score}/8`, title: meta.title || "❌", description: meta.desc || "❌",
            ogTitle: meta.ogTitle || "❌", ogDesc: meta.ogDesc || "❌", canonical: meta.canonical || "❌",
            schemaTypes: schemas.map(s => s["@type"]), schemaCount: schemas.length, wordCount };
        } else if (toolName === "geo-check") {
          const html = await fetchUrl(args.url);
          const schemas = extractSchema(html);
          const meta = extractMeta(html);
          const checks = { hasStructuredData: schemas.length > 0, hasOrganization: schemas.some(s => s["@type"] === "Organization"),
            hasFAQ: schemas.some(s => s["@type"] === "FAQPage"), hasOpenGraph: !!(meta.ogTitle && meta.ogDesc),
            hasCanonical: !!meta.canonical, descriptionLong: meta.desc.length >= 120 };
          const passed = Object.values(checks).filter(Boolean).length;
          r = { url: args.url, geoScore: `${passed}/6`, checks, aiReadiness: passed >= 5 ? "🟢" : passed >= 3 ? "🟡" : "🔴" };
        } else if (toolName === "schema-generate") {
          const schema = { "@context": "https://schema.org", "@type": args.type, name: args.name, url: args.url };
          if (args.description) schema.description = args.description;
          if (args.phone) schema.telephone = args.phone;
          r = { instructions: "Add as <script type='application/ld+json'>", schema };
        } else if (toolName === "ad-copy") {
          r = { platform: args.platform || "both", headlines: [`${args.product} — Hitro`, `Najboljša Ponudba`, `${args.product} po Meri`],
            descriptions: [`Odkrijte ${args.product}.`, `${args.product} — AI orodje.`], cta: "Preizvusite Brezplačno" };
        } else if (toolName === "nap-check") {
          r = { business: args.businessName, nap: args, directories: ["Google","Yelp","Facebook"].map(d => ({ name: d, status: "check" })) };
        } else {
          res.writeHead(200, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
          return res.end(JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32601, message: `Unknown tool: ${toolName}` } }));
        }
        result = { content: [{ type: "text", text: JSON.stringify(r, null, 2) }] };
      } else {
        res.writeHead(200, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
        return res.end(JSON.stringify({ jsonrpc: "2.0", id, error: { code: -32601, message: `Method not found: ${method}` } }));
      }
      res.writeHead(200, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
      res.end(JSON.stringify({ jsonrpc: "2.0", id, result }));
    } catch (e) {
      res.writeHead(500, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
      res.end(JSON.stringify({ error: e.message }));
    }
  });
});

const PORT = process.env.MCP_PORT || 8787;
httpServer.listen(PORT, "127.0.0.1", () => {
  console.log(`BoostSuite MCP HTTP server running on port ${PORT}`);
});
