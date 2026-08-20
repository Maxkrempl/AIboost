#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { config } from "dotenv";
import { Payments } from "@nevermined-io/payments";

config();

// Initialize Nevermined Payments
const payments = Payments.getInstance({
  nvmApiKey: process.env.NVM_API_KEY!,
  environment: (process.env.NVM_ENVIRONMENT as any) || "sandbox",
});

const server = new McpServer({
  name: "BoostSuite MCP",
  version: "1.0.0",
});

// Helper: fetch URL content
async function fetchUrl(url: string): Promise<string> {
  const res = await fetch(url, {
    headers: { "User-Agent": "BoostSuite-MCP/1.0" },
  });
  return res.text();
}

// Helper: extract meta tags
function extractMeta(html: string) {
  const title = html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1] || "";
  const desc =
    html
      .match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)
      ?.[1] || "";
  const ogTitle =
    html
      .match(/<meta[^>]*property=["']og:title["'][^>]*content=["']([^"']+)["']/i)
      ?.[1] || "";
  const ogDesc =
    html
      .match(
        /<meta[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']/i
      )
      ?.[1] || "";
  const canonical =
    html.match(/<link[^>]*rel=["']canonical["'][^>]*href=["']([^"']+)["']/i)
      ?.[1] || "";
  return { title, desc, ogTitle, ogDesc, canonical };
}

// Helper: extract schema.org JSON-LD
function extractSchema(html: string): any[] {
  const schemas: any[] = [];
  const regex = /<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi;
  let match;
  while ((match = regex.exec(html)) !== null) {
    try {
      schemas.push(JSON.parse(match[1]));
    } catch {}
  }
  return schemas;
}

// Helper: check headers
function checkHeaders(html: string) {
  return {
    hasViewport: /<meta[^>]*name=["']viewport["']/i.test(html),
    hasCharset: /<meta[^>]*charset/i.test(html),
    hasLang: /<html[^>]*lang=["']/i.test(html),
    hasHttps: true, // assume HTTPS
  };
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
      const headers = checkHeaders(html);
      const wordCount = html.replace(/<[^>]+>/g, "").split(/\s+/).length;

      const score = [
        meta.title ? 1 : 0,
        meta.desc ? 1 : 0,
        meta.ogTitle ? 1 : 0,
        meta.ogDesc ? 1 : 0,
        meta.canonical ? 1 : 0,
        schemas.length > 0 ? 1 : 0,
        headers.hasViewport ? 1 : 0,
        headers.hasLang ? 1 : 0,
      ].reduce((a, b) => a + b, 0);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                url,
                score: `${score}/8`,
                title: meta.title || "❌ MISSING",
                description: meta.desc || "❌ MISSING",
                ogTitle: meta.ogTitle || "❌ MISSING",
                ogDesc: meta.ogDesc || "❌ MISSING",
                canonical: meta.canonical || "❌ MISSING",
                schemaTypes: schemas.map((s) => s["@type"] || "unknown"),
                schemaCount: schemas.length,
                headers,
                wordCount,
              },
              null,
              2
            ),
          },
        ],
      };
    } catch (e: any) {
      return { content: [{ type: "text", text: `Error: ${e.message}` }] };
    }
  }
);

// ========== TOOL 2: GEO Check ==========
server.tool(
  "geo-check",
  "Check GEO (Generative Engine Optimization) readiness — how well does a URL serve AI agents",
  { url: z.string().url() },
  async ({ url }) => {
    try {
      const html = await fetchUrl(url);
      const schemas = extractSchema(html);
      const meta = extractMeta(html);

      const checks = {
        hasStructuredData: schemas.length > 0,
        hasOrganization: schemas.some((s) => s["@type"] === "Organization"),
        hasLocalBusiness: schemas.some((s) => s["@type"] === "LocalBusiness"),
        hasFAQ: schemas.some((s) => s["@type"] === "FAQPage"),
        hasBreadcrumb: schemas.some(
          (s) => s["@type"] === "BreadcrumbList"
        ),
        hasOpenGraph: !!(meta.ogTitle && meta.ogDesc),
        hasCanonical: !!meta.canonical,
        descriptionLength: meta.desc.length,
        titleLength: meta.title.length,
      };

      const passed = Object.values(checks).filter(
        (v) => v === true
      ).length;
      const total = Object.keys(checks).length;

      const recommendations: string[] = [];
      if (!checks.hasStructuredData)
        recommendations.push("Add JSON-LD structured data");
      if (!checks.hasOrganization)
        recommendations.push("Add Organization schema");
      if (!checks.hasLocalBusiness)
        recommendations.push("Add LocalBusiness schema (if applicable)");
      if (!checks.hasFAQ)
        recommendations.push("Add FAQ schema for AI-friendly Q&A");
      if (!checks.hasOpenGraph)
        recommendations.push("Add Open Graph meta tags");
      if (!checks.hasCanonical)
        recommendations.push("Add canonical URL");
      if (meta.desc.length < 120)
        recommendations.push(
          `Description too short (${meta.desc.length}/120+ chars)`
        );

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                url,
                geoScore: `${passed}/${total}`,
                checks,
                recommendations,
                aiReadiness:
                  passed >= 6
                    ? "🟢 GOOD"
                    : passed >= 4
                    ? "🟡 NEEDS WORK"
                    : "🔴 POOR",
              },
              null,
              2
            ),
          },
        ],
      };
    } catch (e: any) {
      return { content: [{ type: "text", text: `Error: ${e.message}` }] };
    }
  }
);

// ========== TOOL 3: Schema Generator ==========
server.tool(
  "schema-generate",
  "Generate JSON-LD schema markup for a business",
  {
    type: z.enum([
      "Organization",
      "LocalBusiness",
      "FAQPage",
      "Product",
      "Service",
    ]),
    name: z.string(),
    url: z.string().url(),
    description: z.string().optional(),
    phone: z.string().optional(),
    address: z.string().optional(),
  },
  async ({ type, name, url, description, phone, address }) => {
    let schema: any = {
      "@context": "https://schema.org",
      "@type": type,
      name,
      url,
    };
    if (description) schema.description = description;
    if (phone) schema.telephone = phone;
    if (address) {
      schema.address = {
        "@type": "PostalAddress",
        streetAddress: address,
      };
    }

    return {
      content: [
        {
          type: "text",
          text: `Add this to your page as <script type="application/ld+json">\n\n${JSON.stringify(
            schema,
            null,
            2
          )}`,
        },
      ],
    };
  }
);

// ========== TOOL 4: Ad Copy Generator ==========
server.tool(
  "ad-copy",
  "Generate ad copy for Google/Meta ads",
  {
    product: z.string(),
    audience: z.string().optional(),
    platform: z.enum(["google", "meta", "both"]).default("both"),
  },
  async ({ product, audience, platform }) => {
    const headlines = [
      `${product} — Hitro in Zanesljivo`,
      `Najboljša Ponudba za ${product}`,
      `${product} po Meri`,
      `Zaupajte Strokovnjakom — ${product}`,
      `${product} že Od €19/mesec`,
    ];

    const descriptions = [
      `Odkrijte ${product}${
        audience ? ` za ${audience}` : ""
      }. Brezplačna preskusna verzija, takojšnji rezultati.`,
      `Z ${product}${
        audience ? ` za ${audience}` : ""
      } prihranite čas in denar. Začnite danes.`,
      `${product} — AI-podprto orodje ki deluje. 5 minut nastavitve.`,
    ];

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              platform,
              headlines,
              descriptions,
              cta: "Preizvusite Brezplačno",
            },
            null,
            2
          ),
        },
      ],
    };
  }
);

// ========== TOOL 5: NAP Checker ==========
server.tool(
  "nap-check",
  "Check NAP (Name, Address, Phone) consistency across directories",
  {
    businessName: z.string(),
    phone: z.string(),
    address: z.string(),
    website: z.string().url(),
  },
  async ({ businessName, phone, address, website }) => {
    // In production, this would check Google, Yelp, Facebook, etc.
    // For now, return a template check
    const directories = [
      "Google Business Profile",
      "Yelp",
      "Facebook",
      "Apple Maps",
      "Bing Places",
      "TripAdvisor",
    ];

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              business: businessName,
             nap: { name: businessName, address, phone, website },
              directories: directories.map((d) => ({
                name: d,
                status: "needs_manual_check",
                note: "Automated checking coming soon — verify manually",
              })),
              recommendation:
                "Ensure identical NAP across all directories for local SEO.",
            },
            null,
            2
          ),
        },
      ],
    };
  }
);

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("BoostSuite MCP server running on stdio");
}

main().catch(console.error);
