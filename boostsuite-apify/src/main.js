/**
 * BoostSuite MCP Server — Apify Actor
 * Wraps the BoostSuite HTTP MCP endpoint as an Apify Actor.
 * Agents connect via MCP protocol, Apify handles hosting + billing.
 */

import { Actor } from 'apify';

const MCP_URL = 'https://hd-webdesign.si/api/mcp/';

const TOOLS = [
  { name: 'seo_audit', description: 'Full SEO audit with score and recommendations', price_usd: 0.05 },
  { name: 'geo_check', description: 'AI search visibility check (ChatGPT, Gemini, Perplexity)', price_usd: 0.03 },
  { name: 'ad_copy_generator', description: 'Generate ad copy for Google, Facebook, Instagram, LinkedIn, email', price_usd: 0.05 },
  { name: 'listing_optimizer', description: 'Optimize product/service listings for marketplaces', price_usd: 0.04 },
  { name: 'combined_audit', description: 'All-in-one website audit (SEO + security + performance + accessibility + GDPR)', price_usd: 0.15 },
  { name: 'menu_translate', description: 'Multilingual menu item descriptions (9 languages)', price_usd: 0.02 },
];

async function callMCP(method, params = {}) {
  const response = await fetch(MCP_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: Date.now(),
      method,
      params,
    }),
  });

  const text = await response.text();
  // Parse SSE response
  const lines = text.split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      try {
        return JSON.parse(line.slice(6));
      } catch {}
    }
  }
  throw new Error('Invalid MCP response');
}

Actor.main(async () => {
  const input = await Actor.getInput() || {};
  const { tool, arguments: args = {} } = input;

  if (!tool) {
    // Return tool list
    await Actor.pushData({
      tools: TOOLS.map(t => ({
        name: t.name,
        description: t.description,
        price_usd: t.price_usd,
      })),
    });
    return;
  }

  // Charge per event
  const toolInfo = TOOLS.find(t => t.name === tool);
  if (toolInfo) {
    await Actor.charge('tool_call', 1);
  }

  // Call the MCP server
  const result = await callMCP('tools/call', { name: tool, arguments: args });

  await Actor.pushData({
    tool,
    arguments: args,
    result: result.result || result,
  });
});
