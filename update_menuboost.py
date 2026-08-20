import re

with open("menuboost/index.html", "r") as f:
    content = f.read()

# Extract the style block inside head (including <style>...</style>)
style_pattern = r"(<style>.*?</style>)"
style_match = re.search(style_pattern, content, re.DOTALL)
style_block = style_match.group(1) if style_match else ""

# Define new meta tags
new_head = '''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="AI‑powered multilingual menu descriptions for restaurants. Generate poetic, compelling food descriptions in 6 languages in seconds.">
    <link rel="canonical" href="https://hd-webdesign.si/menuboost/" />
    
    <!-- Open Graph -->
    <meta property="og:title" content="MenuBoost — AI Menu Description Generator for Restaurants" />
    <meta property="og:description" content="AI‑powered multilingual menu descriptions for restaurants. Generate poetic, compelling food descriptions in 6 languages in seconds." />
    <meta property="og:image" content="https://hd-webdesign.si/images/og-image.jpg" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://hd-webdesign.si/menuboost/" />
    <meta property="og:site_name" content="MenuBoost" />
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:creator" content="@herceg23" />
    <meta name="twitter:title" content="MenuBoost — AI Menu Description Generator for Restaurants" />
    <meta name="twitter:description" content="AI‑powered multilingual menu descriptions for restaurants. Generate poetic, compelling food descriptions in 6 languages in seconds." />
    <meta name="twitter:image" content="https://hd-webdesign.si/images/og-image.jpg" />
    
    <title>MenuBoost — AI Menu Description Generator for Restaurants</title>
    <link rel="stylesheet" href="/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🍽️</text></svg>">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "MenuBoost",
        "description": "AI‑powered multilingual menu description generator for restaurants. Generates poetic, compelling food descriptions in 6 languages.",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "url": "https://hd-webdesign.si/menuboost/",
        "offers": {
            "@type": "Offer",
            "price": "19",
            "priceCurrency": "EUR"
        },
        "author": {
            "@type": "Person",
            "name": "Darko Herceg",
            "url": "https://hd-webdesign.si/"
        }
    }
    </script>
    ''' + style_block + '''
</head>'''

# Replace the entire head section
pattern = r"<head>.*?</head>"
new_content = re.sub(pattern, new_head, content, flags=re.DOTALL)

with open("menuboost/index.html", "w") as f:
    f.write(new_content)
print("Updated menuboost/index.html")