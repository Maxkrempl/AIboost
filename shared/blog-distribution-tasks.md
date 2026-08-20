# Blog Distribution Instructions — June 2026

## For Max (OpenClaw)

Darko wants the new GEO blog posts properly distributed across the website. These are the tasks that need to be done.

---

## 1. Add new blogs to blog index page

The blog index (`/blog/` or the blog listing page) needs to show the 3 new posts at the top:

### New posts to add (in this order, newest first):

**Blog 10:** GEO for Agencies: How to Sell AI Visibility Services to Your Clients
- URL: `/blog/geo-for-agencies.html`
- Date: June 11, 2026
- Category: Agency Guide, GEO
- Description: How digital agencies can use GEO as a new revenue stream. Sell AI visibility audits and Schema.org implementation to your clients.

**Blog 09:** How to Make ChatGPT Recommend Your Business: A Complete GEO Checklist
- URL: `/blog/geo-checklist-chatgpt-recommendations.html`
- Date: June 11, 2026
- Category: GEO Guide, Checklist
- Description: A 10-step GEO checklist to make ChatGPT, Gemini, and Perplexity recommend your business. Actionable steps with code examples.

**Blog 08:** Structured Data, llms.txt & FAQ: Why AI Can't Find Your Website
- URL: `/blog/structured-data-llms-txt-ai-visibility.html`
- Date: June 11, 2026
- Category: GEO Guide, Technical
- Description: Your website might be invisible to ChatGPT, Gemini, and Perplexity. Here's why structured data, llms.txt, and FAQ markup are the technical foundation of AI visibility.

---

## 2. Cross-links to add

### From `/boost-suite/` page:
Add a section or link after the tool descriptions:

```html
<div style="margin-top: 2rem; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3B82F6;">
  <p style="margin: 0 0 0.5rem; font-weight: 600;">📚 Learn more about AI Visibility</p>
  <p style="margin: 0; font-size: 0.95rem;">
    <a href="/blog/geo-for-agencies.html">GEO for Agencies: How to Sell AI Visibility Services →</a><br>
    <a href="/blog/geo-checklist-chatgpt-recommendations.html">GEO Checklist: 10 Steps to AI Visibility →</a><br>
    <a href="/blog/structured-data-llms-txt-ai-visibility.html">Why AI Can't Find Your Website →</a>
  </p>
</div>
```

### From `/menu-boost/` page:
Add links to relevant restaurant/menu blogs:

```html
<div style="margin-top: 2rem; padding: 1.5rem; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #D4980A;">
  <p style="margin: 0 0 0.5rem; font-weight: 600;">📚 Learn more</p>
  <p style="margin: 0; font-size: 0.95rem;">
    <a href="/blog/best-ai-menu-description-generator-2026.html">Best AI Menu Description Generator 2026 →</a><br>
    <a href="/blog/qr-code-vs-physical-menu.html">QR Code Menu vs Physical Menu →</a><br>
    <a href="/blog/how-to-translate-restaurant-menu.html">How to Translate a Restaurant Menu into 6 Languages →</a>
  </p>
</div>
```

### From homepage (`/`):
Add a "Latest from our blog" section before the footer:

```html
<section style="padding: 4rem 2rem; max-width: 1100px; margin: 0 auto;">
  <h2 style="text-align: center; margin-bottom: 2rem;">Latest from our blog</h2>
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
    <a href="/blog/geo-for-agencies.html" style="padding: 1.5rem; border: 1px solid #eee; border-radius: 12px; text-decoration: none; color: inherit;">
      <p style="color: #666; font-size: 0.85rem; margin-bottom: 0.5rem;">Agency Guide · June 11</p>
      <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">GEO for Agencies</h3>
      <p style="color: #666; font-size: 0.9rem;">How to sell AI visibility services to your clients.</p>
    </a>
    <a href="/blog/geo-checklist-chatgpt-recommendations.html" style="padding: 1.5rem; border: 1px solid #eee; border-radius: 12px; text-decoration: none; color: inherit;">
      <p style="color: #666; font-size: 0.85rem; margin-bottom: 0.5rem;">GEO Guide · June 11</p>
      <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">GEO Checklist</h3>
      <p style="color: #666; font-size: 0.9rem;">10 steps to make ChatGPT recommend your business.</p>
    </a>
    <a href="/blog/structured-data-llms-txt-ai-visibility.html" style="padding: 1.5rem; border: 1px solid #eee; border-radius: 12px; text-decoration: none; color: inherit;">
      <p style="color: #666; font-size: 0.85rem; margin-bottom: 0.5rem;">Technical · June 11</p>
      <h3 style="font-size: 1.1rem; margin-bottom: 0.5rem;">Why AI Can't Find Your Website</h3>
      <p style="color: #666; font-size: 0.9rem;">Structured data, llms.txt, and FAQ — the technical foundation.</p>
    </a>
  </div>
</section>
```

---

## 3. Sitemap update

Add the new blog URLs to the sitemap.xml:

```xml
<url>
  <loc>https://hd-webdesign.si/blog/structured-data-llms-txt-ai-visibility.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
<url>
  <loc>https://hd-webdesign.si/blog/podatki-strukturirani-llms-txt-ai-vidljivost.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
<url>
  <loc>https://hd-webdesign.si/blog/strukturierte-daten-llms-txt-ai-sichtbarkeit.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
<url>
  <loc>https://hd-webdesign.si/blog/strukturirani-podaci-llms-txt-ai-vidljivost.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
<url>
  <loc>https://hd-webdesign.si/blog/dati-strutturati-llms-txt-visibilita-ai.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
<url>
  <loc>https://hd-webdesign.si/blog/geo-checklist-chatgpt-recommendations.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
<url>
  <loc>https://hd-webdesign.si/blog/geo-for-agencies.html</loc>
  <lastmod>2026-06-11</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.8</priority>
</url>
```

---

## 4. Images already uploaded

These images are already on the server at `/blog/`:
- `geo-structured-data-header.jpg` (193KB) — for blog 08
- `geo-checklist-header.jpg` (76KB) — for blog 09
- `geo-agency-dashboard.jpg` — for blog 10

---

## Priority

1. **HIGH** — Blog index update (new posts visible)
2. **HIGH** — Cross-links from boost-suite page
3. **MEDIUM** — Homepage "Latest from blog" section
4. **MEDIUM** — Sitemap update

---

*Created by Rose · June 11, 2026*
