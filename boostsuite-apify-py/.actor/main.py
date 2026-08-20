import json
from urllib.request import Request, urlopen
from apify import Actor

MCP_URL = "https://hd-webdesign.si/api/mcp/"

TOOLS = [
    {"name": "seo_audit", "description": "Full SEO audit with score and recommendations", "price_usd": 0.05},
    {"name": "geo_check", "description": "AI search visibility check (ChatGPT, Gemini, Perplexity)", "price_usd": 0.03},
    {"name": "ad_copy_generator", "description": "Generate ad copy for Google, Facebook, Instagram, LinkedIn, email", "price_usd": 0.05},
    {"name": "listing_optimizer", "description": "Optimize product/service listings for marketplaces", "price_usd": 0.04},
    {"name": "combined_audit", "description": "All-in-one website audit (SEO + security + performance + accessibility + GDPR)", "price_usd": 0.15},
    {"name": "menu_translate", "description": "Multilingual menu item descriptions (9 languages)", "price_usd": 0.02},
]

async def call_mcp(method, params=None):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = Request(MCP_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=60) as resp:
        text = resp.read().decode()
    for line in text.split("\n"):
        if line.startswith("data: "):
            try:
                return json.loads(line[6:])
            except json.JSONDecodeError:
                continue
    raise Exception("Invalid MCP response")

async def main():
    async with Actor:
        actor_input = await Actor.get_input() or {}
        tool = actor_input.get("tool", "")
        args = actor_input.get("arguments", {})

        if not tool:
            await Actor.push_data({"tools": TOOLS})
            return

        # Charge per event
        await Actor.charge("tool_call", 1)

        result = await call_mcp("tools/call", {"name": tool, "arguments": args})
        await Actor.push_data({"tool": tool, "arguments": args, "result": result.get("result", result)})

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
