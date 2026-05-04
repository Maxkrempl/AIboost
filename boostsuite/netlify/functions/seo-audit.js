const fetch = require('node-fetch');
const cheerio = require('cheerio');

// Build a fallback score from raw SEO data when AI parsing fails
function buildFallbackResult(data) {
    let score = 0;

    // Title (20 pts)
    if (data.title && data.title !== 'Missing') {
        score += 15;
        if (data.title.length >= 30 && data.title.length <= 60) score += 5;
    }
    // Meta description (20 pts)
    if (data.metaDescription && data.metaDescription !== 'Missing') {
        score += 15;
        if (data.metaDescription.length >= 120 && data.metaDescription.length <= 160) score += 5;
    }
    // H1 (15 pts)
    if (data.h1Count >= 1) score += 15;
    // Images with alt (15 pts)
    if (data.imageCount > 0) {
        const ratio = data.imagesWithAlt / data.imageCount;
        score += Math.round(ratio * 15);
    }
    // Word count (10 pts)
    if (data.wordCount >= 300) score += 10;
    else if (data.wordCount >= 100) score += 5;
    // Canonical (10 pts)
    if (data.canonical && data.canonical !== 'Missing') score += 10;
    // OG tags (10 pts)
    if (data.ogTitle && data.ogTitle !== 'Missing') score += 5;
    if (data.ogDescription && data.ogDescription !== 'Missing') score += 5;

    return { score: Math.min(score, 100), analysis: buildAnalysis(data), fixes: buildFixes(data) };
}

function buildAnalysis(data) {
    const issues = [];
    const good = [];

    if (!data.title || data.title === 'Missing') issues.push('missing page title');
    else if (data.title.length > 60) issues.push('title is too long');
    else good.push('title tag is present');

    if (!data.metaDescription || data.metaDescription === 'Missing') issues.push('no meta description');
    else good.push('meta description exists');

    if (data.h1Count === 0) issues.push('no H1 heading found');
    else good.push(`${data.h1Count} H1 heading(s)`);

    if (data.imageCount > 0 && data.imagesWithAlt < data.imageCount) {
        issues.push(`${data.imageCount - data.imagesWithAlt} images missing alt text`);
    }

    if (data.wordCount < 300) issues.push('thin content (under 300 words)');

    let text = good.length ? `Strengths: ${good.join(', ')}. ` : '';
    text += issues.length ? `Issues found: ${issues.join(', ')}.` : 'No major issues found.';
    return text;
}

function buildFixes(data) {
    const fixes = [];
    if (!data.title || data.title === 'Missing') fixes.push('Add a descriptive page title (30-60 characters)');
    else if (data.title.length > 60) fixes.push('Shorten the page title to under 60 characters');

    if (!data.metaDescription || data.metaDescription === 'Missing') fixes.push('Add a meta description (120-160 characters)');
    else if (data.metaDescription.length > 160) fixes.push('Shorten meta description to under 160 characters');

    if (data.h1Count === 0) fixes.push('Add a single H1 heading to the page');
    if (data.imageCount > 0 && data.imagesWithAlt < data.imageCount) fixes.push('Add alt text to all images for accessibility and SEO');
    if (data.wordCount < 300) fixes.push('Add more content — aim for at least 300 words');
    if (!data.canonical || data.canonical === 'Missing') fixes.push('Add a canonical URL tag');
    if (!data.ogTitle || data.ogTitle === 'Missing') fixes.push('Add Open Graph title for better social media sharing');

    // Always fill to 5
    while (fixes.length < 5) {
        const defaults = [
            'Add structured data (Schema.org) markup',
            'Create and submit an XML sitemap',
            'Ensure the site uses HTTPS',
            'Improve page load speed',
            'Add internal linking between related pages',
        ];
        const next = defaults.find(d => !fixes.includes(d));
        if (next) fixes.push(next);
        else break;
    }
    return fixes.slice(0, 5);
}

exports.handler = async (event, context) => {
    // CORS headers
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json',
    };

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };
    }

    try {
        const { url } = JSON.parse(event.body);
        if (!url) {
            return { statusCode: 400, headers, body: JSON.stringify({ error: 'URL is required' }) };
        }

        // Fetch the URL
        const response = await fetch(url, {
            headers: { 'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteSEO/1.0)' },
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const html = await response.text();
        const $ = cheerio.load(html);

        // Extract SEO elements
        const title = $('title').text().trim() || 'Missing';
        const metaDescription = $('meta[name="description"]').attr('content') || 'Missing';
        const h1 = $('h1').map((i, el) => $(el).text().trim()).get();
        const h2 = $('h2').map((i, el) => $(el).text().trim()).get();
        const h3 = $('h3').map((i, el) => $(el).text().trim()).get();
        const images = $('img');
        const imageCount = images.length;
        const imagesWithAlt = images.filter((i, el) => $(el).attr('alt')).length;
        const links = $('a[href]');
        const internalLinks = links.filter((i, el) => $(el).attr('href').startsWith('/') || $(el).attr('href').includes(url)).length;
        const externalLinks = links.length - internalLinks;
        const wordCount = $('body').text().split(/\s+/).filter(w => w.length > 0).length;
        const metaRobots = $('meta[name="robots"]').attr('content') || 'Not set';
        const canonical = $('link[rel="canonical"]').attr('href') || 'Missing';
        const ogTitle = $('meta[property="og:title"]').attr('content') || 'Missing';
        const ogDescription = $('meta[property="og:description"]').attr('content') || 'Missing';

        // Prepare data for AI analysis
        const seoData = {
            url,
            title,
            metaDescription,
            h1Count: h1.length,
            h2Count: h2.length,
            h3Count: h3.length,
            imageCount,
            imagesWithAlt,
            internalLinks,
            externalLinks,
            wordCount,
            metaRobots,
            canonical,
            ogTitle,
            ogDescription,
        };

        // Call DeepSeek API for analysis
        const deepseekResponse = await fetch('https://api.deepseek.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
            },
            body: JSON.stringify({
                model: 'deepseek-chat',
                messages: [
                    {
                        role: 'system',
                        content: `You are an expert SEO auditor. Analyze the provided SEO data and respond with ONLY a valid JSON object. No markdown, no code fences, no explanation outside the JSON.

The JSON must have exactly these keys:
- "score": integer 0-100
- "analysis": string (2-3 sentences about strengths and weaknesses)
- "fixes": array of exactly 5 short actionable strings

Example:
{"score":72,"analysis":"Good title tag but missing meta description. H1 structure is solid but images lack alt text.","fixes":["Add a meta description under 160 characters","Add alt text to all images","Improve page load speed","Add structured data markup","Create an XML sitemap"]}`
                    },
                    {
                        role: 'user',
                        content: JSON.stringify(seoData, null, 2)
                    }
                ],
                temperature: 0.2,
                max_tokens: 600,
            }),
        });

        if (!deepseekResponse.ok) {
            throw new Error(`DeepSeek API error: ${deepseekResponse.status}`);
        }

        const deepseekData = await deepseekResponse.json();
        const aiContent = deepseekData.choices[0].message.content;
        let result;
        try {
            // Strip markdown code fences if present
            let cleaned = aiContent.replace(/```(?:json)?\s*/gi, '').replace(/```\s*/g, '').trim();
            result = JSON.parse(cleaned);
        } catch (e) {
            // fallback: try to find JSON object in the text
            try {
                const jsonMatch = aiContent.match(/\{[\s\S]*\}/);
                if (jsonMatch) result = JSON.parse(jsonMatch[0]);
            } catch (e2) {}
        }
        // If still no valid result, build one from raw data
        if (!result || typeof result.score !== 'number') {
            result = buildFallbackResult(seoData);
        }
        // Ensure analysis and fixes always exist
        if (!result.analysis || result.analysis.length < 20) {
            result.analysis = buildAnalysis(seoData);
        }
        if (!result.fixes || !result.fixes.length) {
            result.fixes = buildFixes(seoData);
        }

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                score: result.score,
                analysis: result.analysis,
                fixes: result.fixes,
                rawData: seoData,
            }),
        };
    } catch (error) {
        console.error('SEO audit error:', error);
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({ error: error.message }),
        };
    }
};