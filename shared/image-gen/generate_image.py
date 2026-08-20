#!/usr/bin/env python3
"""
HTML → PNG Image Generator for HD Webdesign marketing.
Generates professional images from HTML templates.

Usage:
  python3 generate_image.py --template linkedin --title "MCP Server" --subtitle "x402 Payments" --output /tmp/image.png
  python3 generate_image.py --template email-header --title "BoostSuite" --output /tmp/image.png
  python3 generate_image.py --html /path/to/custom.html --output /tmp/image.png

Templates: linkedin, twitter, email-header, menu-mockup, seo-report, hero, banner
"""

import argparse
import os
import sys
import subprocess
import tempfile
import json

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

# Default color schemes per template
COLOR_SCHEMES = {
    "linkedin": {"bg1": "#0a1628", "bg2": "#0d1f3c", "accent1": "#10b981", "accent2": "#3b82f6", "text": "#ffffff"},
    "twitter": {"bg1": "#0c0a1a", "bg2": "#1a1040", "accent1": "#8b5cf6", "accent2": "#06b6d4", "text": "#ffffff"},
    "email-header": {"bg1": "#1a0a00", "bg2": "#2d1400", "accent1": "#d97706", "accent2": "#f59e0b", "text": "#ffffff"},
    "menu-mockup": {"bg1": "#1a0a00", "bg2": "#2d1400", "accent1": "#d97706", "accent2": "#fbbf24", "text": "#ffffff"},
    "seo-report": {"bg1": "#0a1628", "bg2": "#0d1f3c", "accent1": "#10b981", "accent2": "#22d3ee", "text": "#ffffff"},
    "hero": {"bg1": "#0c0a1a", "bg2": "#1a1040", "accent1": "#8b5cf6", "accent2": "#ec4899", "text": "#ffffff"},
    "banner": {"bg1": "#0a1628", "bg2": "#0d1f3c", "accent1": "#3b82f6", "accent2": "#10b981", "text": "#ffffff"},
}

SIZES = {
    "linkedin": (1200, 627),
    "twitter": (1200, 675),
    "email-header": (600, 200),
    "menu-mockup": (600, 800),
    "seo-report": (800, 600),
    "hero": (1920, 1080),
    "banner": (1200, 400),
}


def load_template(template_name):
    """Load HTML template from templates directory."""
    path = os.path.join(TEMPLATES_DIR, f"{template_name}.html")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None


def generate_html(template_name, title, subtitle, features, stats, colors):
    """Generate HTML content from template."""
    template = load_template(template_name)
    if template:
        # Replace placeholders
        html = template.replace("{{TITLE}}", title or "")
        html = html.replace("{{SUBTITLE}}", subtitle or "")
        html = html.replace("{{FEATURES}}", features or "")
        html = html.replace("{{STATS}}", stats or "")
        for key, value in (colors or {}).items():
            html = html.replace(f"{{{{{key}}}}}", value)
        return html
    
    # Fallback: generate generic template
    return generate_generic_html(template_name, title, subtitle, features, stats, colors)


def generate_generic_html(template_name, title, subtitle, features, stats, colors):
    """Generate a generic HTML template."""
    scheme = COLOR_SCHEMES.get(template_name, COLOR_SCHEMES["linkedin"])
    if colors:
        scheme.update(colors)
    
    features_html = ""
    if features:
        for f in features.split(","):
            features_html += f'<div class="feature">{f.strip()}</div>\n'
    
    stats_html = ""
    if stats:
        for s in stats.split(","):
            stats_html += f'<div class="stat">{s.strip()}</div>\n'
    
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ width: 1200px; height: 627px; overflow: hidden; font-family: 'Segoe UI', system-ui, sans-serif; }}
.container {{
  width: 1200px; height: 627px;
  background: linear-gradient(135deg, {scheme['bg1']} 0%, {scheme['bg2']} 100%);
  position: relative; display: flex; align-items: center; padding: 0 80px;
}}
.glow {{ position: absolute; width: 500px; height: 500px; border-radius: 50%; background: radial-gradient(circle, {scheme['accent1']}22 0%, transparent 70%); top: -150px; right: 200px; }}
.text-side {{ position: relative; z-index: 2; max-width: 600px; }}
h1 {{ color: {scheme['text']}; font-size: 48px; font-weight: 800; line-height: 1.1; margin-bottom: 16px; }}
h1 .accent {{ color: {scheme['accent1']}; }}
.subtitle {{ color: rgba(255,255,255,0.55); font-size: 18px; line-height: 1.6; margin-bottom: 28px; }}
.features {{ display: flex; gap: 10px; flex-wrap: wrap; }}
.feature {{
  background: {scheme['accent1']}15; border: 1px solid {scheme['accent1']}33;
  color: rgba(255,255,255,0.8); font-size: 14px; padding: 8px 16px; border-radius: 8px;
}}
.stats {{ position: absolute; right: 80px; top: 50%; transform: translateY(-50%); z-index: 2; }}
.stat {{
  background: rgba(15,23,42,0.8); border: 1px solid {scheme['accent1']}22;
  color: {scheme['accent1']}; font-size: 14px; padding: 12px 20px; border-radius: 8px;
  margin-bottom: 12px; font-weight: 600;
}}
</style>
</head>
<body>
<div class="container">
  <div class="glow"></div>
  <div class="text-side">
    <h1>{title or ''}</h1>
    <p class="subtitle">{subtitle or ''}</p>
    <div class="features">{features_html}</div>
  </div>
  <div class="stats">{stats_html}</div>
</div>
</body>
</html>"""


def html_to_png(html_content, output_path, width=1200, height=627):
    """Convert HTML to PNG using headless Chromium."""
    # Write HTML to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        html_path = f.name
    
    try:
        # Method 1: Use Chromium/Chrome headless
        for browser in ["chromium-browser", "chromium", "google-chrome", "google-chrome-stable"]:
            try:
                result = subprocess.run(
                    [browser, "--headless", "--disable-gpu", "--no-sandbox",
                     f"--window-size={width},{height}",
                     f"--screenshot={output_path}",
                     f"file://{html_path}"],
                    capture_output=True, text=True, timeout=30
                )
                if os.path.exists(output_path):
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        # Method 2: Use puppeteer/playwright if available
        try:
            result = subprocess.run(
                ["node", "-e", f"""
const puppeteer = require('puppeteer');
(async () => {{
  const browser = await puppeteer.launch({{headless: true, args: ['--no-sandbox']}});
  const page = await browser.newPage();
  await page.setViewport({{width: {width}, height: {height}}});
  await page.goto('file://{html_path}', {{waitUntil: 'networkidle0'}});
  await page.screenshot({{path: '{output_path}', fullPage: false}});
  await browser.close();
}})();
                """],
                capture_output=True, text=True, timeout=30
            )
            if os.path.exists(output_path):
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Method 3: Use wkhtmltoimage if available
        try:
            result = subprocess.run(
                ["wkhtmltoimage", "--width", str(width), "--height", str(height),
                 html_path, output_path],
                capture_output=True, text=True, timeout=30
            )
            if os.path.exists(output_path):
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        print("ERROR: No HTML-to-image converter found. Install chromium, puppeteer, or wkhtmltoimage.", file=sys.stderr)
        return False
        
    finally:
        os.unlink(html_path)


def main():
    parser = argparse.ArgumentParser(description="Generate marketing images from HTML")
    parser.add_argument("--template", default="linkedin", help="Template name")
    parser.add_argument("--title", help="Main title text")
    parser.add_argument("--subtitle", help="Subtitle text")
    parser.add_argument("--features", help="Comma-separated feature tags")
    parser.add_argument("--stats", help="Comma-separated stat items")
    parser.add_argument("--html", help="Custom HTML file (overrides template)")
    parser.add_argument("--output", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, help="Image width")
    parser.add_argument("--height", type=int, help="Image height")
    parser.add_argument("--colors", help="JSON color overrides")
    
    args = parser.parse_args()
    
    colors = json.loads(args.colors) if args.colors else None
    width = args.width or SIZES.get(args.template, (1200, 627))[0]
    height = args.height or SIZES.get(args.template, (1200, 627))[1]
    
    if args.html:
        with open(args.html, "r") as f:
            html_content = f.read()
    else:
        html_content = generate_html(args.template, args.title, args.subtitle, 
                                     args.features, args.stats, colors)
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    if html_to_png(html_content, args.output, width, height):
        size_kb = os.path.getsize(args.output) / 1024
        print(json.dumps({"status": "success", "file": args.output, "size_kb": round(size_kb)}))
    else:
        print(json.dumps({"status": "error", "message": "Failed to generate image"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
