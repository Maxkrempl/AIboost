#!/usr/bin/env python3
"""BoostSuite MCP Server — SEO/GEO Tools for AI Agents"""
import json
import re
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# MCP Tool definitions
TOOLS = [
    {
        "name": "seo-audit",
        "description": "Run SEO audit on a URL — returns title, meta, schema, headers analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "geo-check",
        "description": "Check GEO (Generative Engine Optimization) readiness — how well does a URL serve AI agents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "format": "uri"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "schema-generate",
        "description": "Generate JSON-LD schema markup for a business",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["Organization", "LocalBusiness", "FAQPage", "Product", "Service"]},
                "name": {"type": "string"},
                "url": {"type": "string", "format": "uri"},
                "description": {"type": "string"},
                "phone": {"type": "string"},
                "address": {"type": "string"}
            },
            "required": ["type", "name", "url"]
        }
    },
    {
        "name": "ad-copy",
        "description": "Generate ad copy for Google/Meta ads",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
                "audience": {"type": "string"},
                "platform": {"type": "string", "enum": ["google", "meta", "both"], "default": "both"}
            },
            "required": ["product"]
        }
    },
    {
        "name": "nap-check",
        "description": "Check NAP (Name, Address, Phone) consistency across directories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "businessName": {"type": "string"},
                "phone": {"type": "string"},
                "address": {"type": "string"},
                "website": {"type": "string", "format": "uri"}
            },
            "required": ["businessName", "phone", "address", "website"]
        }
    }
]

def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BoostSuite-MCP/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def extract_meta(html):
    title = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    desc = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
    og_title = re.search(r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
    og_desc = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', html, re.I)
    canonical = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.I)
    return {
        "title": title.group(1) if title else "",
        "desc": desc.group(1) if desc else "",
        "ogTitle": og_title.group(1) if og_title else "",
        "ogDesc": og_desc.group(1) if og_desc else "",
        "canonical": canonical.group(1) if canonical else ""
    }

def extract_schema(html):
    schemas = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.I | re.S):
        try:
            schemas.append(json.loads(m.group(1)))
        except:
            pass
    return schemas

def tool_seo_audit(url):
    html = fetch_url(url)
    meta = extract_meta(html)
    schemas = extract_schema(html)
    word_count = len(re.sub(r'<[^>]+>', '', html).split())
    score = sum([
        1 if meta["title"] else 0,
        1 if meta["desc"] else 0,
        1 if meta["ogTitle"] else 0,
        1 if meta["ogDesc"] else 0,
        1 if meta["canonical"] else 0,
        1 if schemas else 0,
        1 if re.search(r'<meta[^>]*name=["\']viewport["\']', html, re.I) else 0,
        1 if re.search(r'<html[^>]*lang=["\']', html, re.I) else 0,
    ])
    return {
        "url": url,
        "score": f"{score}/8",
        "title": meta["title"] or "❌ MISSING",
        "description": meta["desc"] or "❌ MISSING",
        "ogTitle": meta["ogTitle"] or "❌ MISSING",
        "ogDesc": meta["ogDesc"] or "❌ MISSING",
        "canonical": meta["canonical"] or "❌ MISSING",
        "schemaTypes": [s.get("@type", "unknown") for s in schemas],
        "schemaCount": len(schemas),
        "wordCount": word_count
    }

def tool_geo_check(url):
    html = fetch_url(url)
    schemas = extract_schema(html)
    meta = extract_meta(html)
    checks = {
        "hasStructuredData": len(schemas) > 0,
        "hasOrganization": any(s.get("@type") == "Organization" for s in schemas),
        "hasLocalBusiness": any(s.get("@type") == "LocalBusiness" for s in schemas),
        "hasFAQ": any(s.get("@type") == "FAQPage" for s in schemas),
        "hasBreadcrumb": any(s.get("@type") == "BreadcrumbList" for s in schemas),
        "hasOpenGraph": bool(meta["ogTitle"] and meta["ogDesc"]),
        "hasCanonical": bool(meta["canonical"]),
        "descriptionLong": len(meta["desc"]) >= 120,
    }
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    recs = []
    if not checks["hasStructuredData"]: recs.append("Add JSON-LD structured data")
    if not checks["hasOrganization"]: recs.append("Add Organization schema")
    if not checks["hasLocalBusiness"]: recs.append("Add LocalBusiness schema (if applicable)")
    if not checks["hasFAQ"]: recs.append("Add FAQ schema for AI-friendly Q&A")
    if not checks["hasOpenGraph"]: recs.append("Add Open Graph meta tags")
    if not checks["hasCanonical"]: recs.append("Add canonical URL")
    return {
        "url": url,
        "geoScore": f"{passed}/{total}",
        "checks": checks,
        "recommendations": recs,
        "aiReadiness": "🟢 GOOD" if passed >= 6 else "🟡 NEEDS WORK" if passed >= 4 else "🔴 POOR"
    }

def tool_schema_generate(type_, name, url, description="", phone="", address=""):
    schema = {"@context": "https://schema.org", "@type": type_, "name": name, "url": url}
    if description: schema["description"] = description
    if phone: schema["telephone"] = phone
    if address: schema["address"] = {"@type": "PostalAddress", "streetAddress": address}
    return {"instructions": "Add this to your page as <script type=\"application/ld+json\">", "schema": schema}

def tool_ad_copy(product, audience="", platform="both"):
    headlines = [
        f"{product} — Hitro in Zanesljivo",
        f"Najboljša Ponudba za {product}",
        f"{product} po Meri",
        f"Zaupajte Strokovnjakom — {product}",
        f"{product} že Od €19/mesec",
    ]
    descriptions = [
        f"Odkrijte {product}{' za ' + audience if audience else ''}. Brezplačna preskusna verzija, takojšnji rezultati.",
        f"Z {product}{' za ' + audience if audience else ''} prihranite čas in denar. Začnite danes.",
        f"{product} — AI-podprto orodje ki deluje. 5 minut nastavitve.",
    ]
    return {"platform": platform, "headlines": headlines, "descriptions": descriptions, "cta": "Preizvusite Brezplačno"}

def tool_nap_check(business_name, phone, address, website):
    dirs = ["Google Business Profile", "Yelp", "Facebook", "Apple Maps", "Bing Places", "TripAdvisor"]
    return {
        "business": business_name,
        "nap": {"name": business_name, "address": address, "phone": phone, "website": website},
        "directories": [{"name": d, "status": "needs_manual_check"} for d in dirs],
        "recommendation": "Ensure identical NAP across all directories for local SEO."
    }

def handle_tool(name, args):
    if name == "seo-audit": return tool_seo_audit(args["url"])
    if name == "geo-check": return tool_geo_check(args["url"])
    if name == "schema-generate": return tool_schema_generate(args["type"], args["name"], args["url"], args.get("description",""), args.get("phone",""), args.get("address",""))
    if name == "ad-copy": return tool_ad_copy(args["product"], args.get("audience",""), args.get("platform","both"))
    if name == "nap-check": return tool_nap_check(args["businessName"], args["phone"], args["address"], args["website"])
    return {"error": f"Unknown tool: {name}"}

class MCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        method = body.get("method")
        req_id = body.get("id")

        if method == "initialize":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "BoostSuite MCP", "version": "1.0.0"}
            }}
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
        elif method == "tools/call":
            args = body.get("params", {})
            tool_name = args.get("name")
            tool_args = args.get("arguments", {})
            try:
                result = handle_tool(tool_name, tool_args)
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]
                }}
            except Exception as e:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -1, "message": str(e)}}
        else:
            resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(resp).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # Silence logs

if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", 8787))
    server = HTTPServer(("127.0.0.1", port), MCPHandler)
    print(f"BoostSuite MCP running on port {port}")
    server.serve_forever()
