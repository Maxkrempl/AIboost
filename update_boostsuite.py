import re

with open("boostsuite/index.html", "r") as f:
    content = f.read()

# Extract the style block inside head (including <style>...</style>)
style_pattern = r"(<style>.*?</style>)"
style_match = re.search(style_pattern, content, re.DOTALL)
style_block = style_match.group(1) if style_match else ""

# Define new meta tags
new_head = '''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="AI marketing toolkit for agencies: SEO Audit, GEO Check, Ad Copy Generator, and Listing Optimizer. Scale your agency without hiring more people.">
    <link rel="canonical" href="https://hd-webdesign.si/boostsuite/" />
    
    <!-- Open Graph -->
    <meta property="og:title" content="BoostSuite — AI Marketing Toolkit for Agencies" />
    <meta property="og:description" content="AI marketing toolkit for agencies: SEO Audit, GEO Check, Ad Copy Generator, and Listing Optimizer. Scale your agency without hiring more people." />
    <meta property="og:image" content="https://hd-webdesign.si/images/og-image.jpg" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://hd-webdesign.si/boostsuite/" />
    <meta property="og:site_name" content="BoostSuite" />
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:creator" content="@herceg23" />
    <meta name="twitter:title" content="BoostSuite — AI Marketing Toolkit for Agencies" />
    <meta name="twitter:description" content="AI marketing toolkit for agencies: SEO Audit, GEO Check, Ad Copy Generator, and Listing Optimizer. Scale your agency without hiring more people." />
    <meta name="twitter:image" content="https://hd-webdesign.si/images/og-image.jpg" />
    
    <title>BoostSuite — AI Marketing Toolkit for Agencies</title>
    <link rel="stylesheet" href="/css/style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🚀</text></svg>">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "BoostSuite",
        "description": "AI marketing toolkit for agencies: SEO Audit, GEO Check, Ad Copy Generator, and Listing Optimizer.",
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Web",
        "url": "https://hd-webdesign.si/boostsuite/",
        "offers": [
            {
                "@type": "Offer",
                "price": "19",
                "priceCurrency": "EUR",
                "name": "Freelancer"
            },
            {
                "@type": "Offer",
                "price": "49",
                "priceCurrency": "EUR",
                "name": "Agency"
            }
        ],
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

with open("boostsuite/index.html", "w") as f:
    f.write(new_content)
print("Updated boostsuite/index.html")