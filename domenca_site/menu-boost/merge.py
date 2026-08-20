#!/usr/bin/env python3
"""Merge landing.html and app.html into a single index.html"""
import re

# Read both files
with open('/home/darko/.openclaw/workspace/domenca_site/menu-boost/landing.html') as f:
    landing = f.read()

with open('/home/darko/.openclaw/workspace/domenca_site/menu-boost/app.html') as f:
    app = f.read()

# Extract landing page CSS
landing_css_match = re.search(r'<style>(.*?)</style>', landing, re.DOTALL)
landing_css = landing_css_match.group(1) if landing_css_match else ''

# Extract landing page body content
landing_body_match = re.search(r'<body>(.*?)</body>', landing, re.DOTALL)
landing_body = landing_body_match.group(1).strip() if landing_body_match else ''

# Extract app CSS
app_css_match = re.search(r'<style>(.*?)</style>', app, re.DOTALL)
app_css = app_css_match.group(1) if app_css_match else ''

# Extract app body content (everything between <body> and <script>)
app_body_match = re.search(r'<body>(.*?)<script>', app, re.DOTALL)
app_body = app_body_match.group(1).strip() if app_body_match else ''

# Extract app scripts
app_scripts_match = re.search(r'<script>(.*?)</script>\s*</body>', app, re.DOTALL)
app_scripts = app_scripts_match.group(1).strip() if app_scripts_match else ''

# Prefix app CSS selectors with #appOverlay (handle comments properly)
def prefix_css(css, prefix):
    """Prefix all CSS selectors with a given prefix, skipping comments"""
    result = []
    i = 0
    while i < len(css):
        # Skip comments
        if css[i:i+2] == '/*':
            end = css.find('*/', i)
            if end == -1:
                result.append(css[i:])
                break
            result.append(css[i:end+2])
            i = end + 2
            continue
        
        # Skip whitespace
        if css[i] in ' \t\n\r':
            result.append(css[i])
            i += 1
            continue
        
        # Find the next rule (selector { properties })
        # Find the opening brace
        brace_start = css.find('{', i)
        if brace_start == -1:
            # No more rules, append remaining
            result.append(css[i:])
            break
        
        selector = css[i:brace_start].strip()
        
        # Skip if it's a @keyframes or @media rule (handle the inner content)
        if selector.startswith('@keyframes') or selector.startswith('@media'):
            # Find matching closing brace
            depth = 1
            j = brace_start + 1
            while j < len(css) and depth > 0:
                if css[j] == '{':
                    depth += 1
                elif css[j] == '}':
                    depth -= 1
                j += 1
            result.append(css[i:j])
            i = j
            continue
        
        # Find matching closing brace
        depth = 1
        j = brace_start + 1
        while j < len(css) and depth > 0:
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
            j += 1
        
        properties = css[brace_start:j]
        
        # Prefix the selector
        selectors = [s.strip() for s in selector.split(',')]
        prefixed_selectors = [f'{prefix} {s}' for s in selectors]
        result.append(', '.join(prefixed_selectors) + ' ' + properties)
        i = j
    
    return ''.join(result)

prefixed_app_css = prefix_css(app_css, '#appOverlay')

# Fix the header back button to go to landing
app_body = app_body.replace(
    """<button class="header-btn" id="btnPrefsBack">← Nazaj</button>""",
    """<button class="header-btn" id="btnPrefsBack" onclick="closeApp()">← Nazaj</button>"""
)

# Modify app scripts
app_scripts_modified = app_scripts.replace(
    "function showScreen(name) {",
    """function closeApp() {
    document.getElementById('appOverlay').style.display = 'none';
    document.getElementById('landingView').style.display = 'block';
    if (state && state.stream) { state.stream.getTracks().forEach(t => t.stop()); state.stream = null; }
    document.body.style.overflow = '';
  }
  function openApp() {
    document.getElementById('appOverlay').style.display = 'block';
    document.getElementById('landingView').style.display = 'none';
    document.body.style.overflow = 'hidden';
    showScreen('welcome');
  }
  function showScreen(name) {"""
)

# Fix camera close to go back to landing
app_scripts_modified = app_scripts_modified.replace(
    "$('btnCameraClose').onclick = () => { stopCamera(); showScreen('welcome'); };",
    "$('btnCameraClose').onclick = () => { stopCamera(); closeApp(); };"
)

# Build the merged file
merged = f'''<!DOCTYPE html>
<html lang="sl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>MenuBoost — AI Menu Descriptions for Restaurants | 10 Languages</title>
<meta name="description" content="MenuBoost uses AI to generate appetizing menu descriptions in 10 languages. Photograph your menu, get descriptions in seconds. Free to try.">
<meta name="keywords" content="AI menu, restaurant menu, menu description, menu translation, AI for restaurants, menu generator">
<meta property="og:title" content="MenuBoost — AI Menu Descriptions for Restaurants">
<meta property="og:description" content="Photograph menus, translate instantly, generate AI descriptions in 10 languages.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://hd-webdesign.si/menu-boost/">
<meta property="og:image" content="https://hd-webdesign.si/menu-boost/images/menuboost-icon-512.png">
<link rel="canonical" href="https://hd-webdesign.si/menu-boost/">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "MenuBoost",
  "description": "AI-powered menu description generator for restaurants.",
  "url": "https://hd-webdesign.si/menu-boost/",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web",
  "offers": {{"@type": "Offer", "price": "19", "priceCurrency": "EUR"}},
  "featureList": "Menu translation, AI descriptions, 10 languages, 6 writing styles, photo scanning"
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {{"@type": "Question", "name": "What is MenuBoost?", "acceptedAnswer": {{"@type": "Answer", "text": "MenuBoost is an AI tool that generates professional menu descriptions for restaurants in 10 languages."}}}},
    {{"@type": "Question", "name": "How much does MenuBoost cost?", "acceptedAnswer": {{"@type": "Answer", "text": "3 free dishes. Pro: €19/month for unlimited dishes, all languages and styles."}}}},
    {{"@type": "Question", "name": "What languages does MenuBoost support?", "acceptedAnswer": {{"@type": "Answer", "text": "Slovenian, English, German, Italian, Croatian, Serbian, French, Spanish, Turkish, and Greek."}}}}
  ]
}}
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-DJER0DNGTF"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-DJER0DNGTF');
</script>
<meta name="theme-color" content="#F4F1EA">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="manifest" href="manifest.json">
<link rel="icon" type="image/svg+xml" href="images/menuboost-favicon.svg">
<link rel="apple-touch-icon" href="images/menuboost-icon-180.png">
<style>
{landing_css}

/* === APP OVERLAY === */
#appOverlay {{
  display:none;position:fixed;inset:0;z-index:1000;
  background:#FAF7F2;overflow-y:auto;-webkit-overflow-scrolling:touch;
}}
#appOverlay .app {{
  height:auto;min-height:100dvh;display:flex;flex-direction:column;
}}
</style>
<style>
{prefixed_app_css}
</style>
</head>
<body>

<!-- LANDING VIEW -->
{landing_body}

<!-- APP OVERLAY (hidden by default) -->
<div id="appOverlay">
{app_body}
</div>

<script src="i18n-app.js"></script>
<script>
{app_scripts_modified}
</script>

</body>
</html>'''

with open('/home/darko/.openclaw/workspace/domenca_site/menu-boost/index.html', 'w') as f:
    f.write(merged)

print(f"Written {len(merged)} bytes to index.html")
