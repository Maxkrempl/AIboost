# Image Generation Toolkit for Rose

## Overview
Generate professional marketing images for HD Webdesign products using HTML→PNG pipeline.

## How It Works
1. Rose creates HTML with product-specific content
2. Screenshots HTML in headless browser
3. Delivers PNG to Telegram/email

## Templates Available
- `linkedin` — 1200×627, professional dark tech aesthetic
- `twitter` — 1200×675, code snippets + gradient
- `email-header` — 600×200, warm gold accents
- `seo-report` — 800×600, BoostSuite audit visualization
- `menu-mockup` — 600×800, restaurant menu preview
- `hero` — 1920×1080, website hero sections
- `banner` — 1200×400, promotional banners

## Usage

### Quick Generation
```python
# From CLI
python3 ~/.openclaw/workspace/shared/image-gen/generate_image.py \
  --template linkedin \
  --title "MCP Server + x402 Payments" \
  --subtitle "AI agents that pay for themselves" \
  --output ~/Pictures/my-image.png
```

### Custom HTML
```python
# Create custom HTML, screenshot it
1. Write HTML to /tmp/custom.html
2. Use headless Chrome: chromium-browser --headless --screenshot=output.png file:///tmp/custom.html
```

### For Email Outreach
```python
# Personalized demo for restaurant
1. Take their website screenshot
2. Create HTML with their name + BoostSuite audit scores
3. Screenshot → attach to email
```

## Workflow for Rose

### LinkedIn Posts
```
1. Pick topic (MCP, x402, BoostSuite, MenuBoost)
2. Create HTML with compelling headline + stats
3. Screenshot at 1200×627
4. Post with text caption
```

### Email Attachments
```
1. Research target restaurant/agency
2. Create personalized mockup (menu preview, SEO report)
3. Screenshot → attach to outreach email
4. "Here's what your site could look like..."
```

### Social Media
```
1. Create HTML with product highlights
2. Screenshot at platform-appropriate size
3. Schedule post
```

## File Locations
- Templates: `~/.openclaw/workspace/shared/image-gen/templates/`
- Script: `~/.openclaw/workspace/shared/image-gen/generate_image.py`
- Output: `~/Pictures/` or `/tmp/`

## Tips
- Keep text minimal — visual impact > word count
- Use contrast — dark bg + bright accents
- Add mockup elements — browser windows, code blocks, charts
- Personalize for recipients — their name, their website
