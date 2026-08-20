import { Actor } from 'apify';
import { load } from 'cheerio';

await Actor.init();

const input = await Actor.getInput();
const { url } = input;

console.log(`Running GEO check for: ${url}`);

const response = await fetch(url, {
  headers: { 'User-Agent': 'BoostSuite-GEO-Check/1.0' }
});
const html = await response.text();
const $ = load(html);

// Extract structured data
const schemas = [];
$('script[type="application/ld+json"]').each((_, el) => {
  try { schemas.push(JSON.parse($(el).html())); } catch {}
});

// Extract meta
const meta = {
  title: $('title').text().trim(),
  description: $('meta[name="description"]').attr('content') || '',
  ogTitle: $('meta[property="og:title"]').attr('content') || '',
  ogDesc: $('meta[property="og:description"]').attr('content') || '',
  ogImage: $('meta[property="og:image"]').attr('content') || '',
  canonical: $('link[rel="canonical"]').attr('href') || '',
  lang: $('html').attr('lang') || '',
};

// GEO checks for AI visibility
const checks = {
  // Schema.org checks
  hasStructuredData: { passed: schemas.length > 0, detail: `${schemas.length} schemas found` },
  hasOrganization: { passed: schemas.some(s => s['@type'] === 'Organization'), detail: 'Organization schema' },
  hasLocalBusiness: { passed: schemas.some(s => s['@type'] === 'LocalBusiness'), detail: 'LocalBusiness schema' },
  hasFAQ: { passed: schemas.some(s => s['@type'] === 'FAQPage'), detail: 'FAQ schema for AI Q&A' },
  hasBreadcrumb: { passed: schemas.some(s => s['@type'] === 'BreadcrumbList'), detail: 'Breadcrumb navigation' },
  hasWebSite: { passed: schemas.some(s => s['@type'] === 'WebSite'), detail: 'WebSite schema' },
  
  // Content checks
  hasTitle: { passed: !!meta.title, detail: meta.title ? 'Title present' : 'No title' },
  hasDescription: { passed: !!meta.description, detail: meta.description ? 'Description present' : 'No description' },
  descriptionLength: { passed: meta.description.length >= 120, detail: `${meta.description.length} chars (min 120)` },
  
  // Open Graph (AI assistants read OG tags)
  hasOpenGraph: { passed: !!(meta.ogTitle && meta.ogDesc), detail: 'OG tags present' },
  hasOgImage: { passed: !!meta.ogImage, detail: meta.ogImage ? 'OG image present' : 'No OG image' },
  
  // Technical
  hasCanonical: { passed: !!meta.canonical, detail: meta.canonical ? 'Canonical URL set' : 'No canonical' },
  hasLang: { passed: !!meta.lang, detail: meta.lang ? `Language: ${meta.lang}` : 'No lang attribute' },
  
  // Heading structure (AI reads headings)
  hasH1: { passed: $('h1').length > 0, detail: `${$('h1').length} H1 tags` },
  hasH2: { passed: $('h2').length > 0, detail: `${$('h2').length} H2 tags` },
  
  // Content quality signals
  wordCount: { passed: $('body').text().split(/\s+/).length >= 300, detail: `${$('body').text().split(/\\s+/).length} words` },
};

// Calculate score
const passed = Object.values(checks).filter(c => c.passed).length;
const total = Object.keys(checks).length;
const score = Math.round((passed / total) * 100);

// AI readiness level
let aiReadiness;
if (score >= 80) aiReadiness = '🟢 EXCELLENT — Highly visible to AI';
else if (score >= 60) aiReadiness = '🟢 GOOD — Visible to AI with minor gaps';
else if (score >= 40) aiReadiness = '🟡 NEEDS WORK — Partially visible to AI';
else aiReadiness = '🔴 POOR — Poorly visible to AI';

// Recommendations
const recommendations = Object.entries(checks)
  .filter(([_, c]) => !c.passed)
  .map(([name, c]) => ({
    issue: name,
    detail: c.detail,
    fix: getFix(name),
  }));

function getFix(checkName) {
  const fixes = {
    hasStructuredData: 'Add JSON-LD structured data for your business',
    hasOrganization: 'Add Organization schema with name, url, logo',
    hasLocalBusiness: 'Add LocalBusiness schema with address, phone, geo',
    hasFAQ: 'Add FAQPage schema with common questions',
    hasBreadcrumb: 'Add BreadcrumbList schema for navigation',
    hasWebSite: 'Add WebSite schema with SearchAction',
    hasTitle: 'Add a descriptive title tag',
    hasDescription: 'Add a meta description (120-160 chars)',
    descriptionLength: 'Expand description to 120+ characters',
    hasOpenGraph: 'Add og:title and og:description meta tags',
    hasOgImage: 'Add og:image meta tag',
    hasCanonical: 'Add canonical URL link tag',
    hasLang: 'Add lang attribute to HTML tag',
    hasH1: 'Add at least one H1 heading',
    hasH2: 'Add H2 headings for content structure',
    wordCount: 'Add more content (min 300 words)',
  };
  return fixes[checkName] || 'Review and fix';
}

const result = {
  url,
  score: `${score}%`,
  passed: `${passed}/${total}`,
  aiReadiness,
  checks: Object.entries(checks).map(([name, c]) => ({
    name,
    passed: c.passed,
    detail: c.detail,
  })),
  schemas: schemas.map(s => ({
    type: s['@type'] || 'Unknown',
    name: s.name || '',
  })),
  meta,
  recommendations,
};

console.log(`GEO Score: ${score}% — ${aiReadiness}`);
await Actor.pushData(result);
await Actor.exit();
