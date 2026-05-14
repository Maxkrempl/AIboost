const fetch = require('node-fetch');
const { verifyApiKey, trackUsage, corsHeaders } = require('./auth');

exports.handler = async (event, context) => {
    const headers = corsHeaders();

    if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
    if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

    // Optional API key auth
    let authUser = null;
    const authHeader = event.headers?.authorization || event.headers?.Authorization || '';
    if (authHeader.startsWith('Bearer ')) {
        authUser = await verifyApiKey(event);
        if (authUser.error) {
            return { statusCode: 401, headers, body: JSON.stringify({ error: authUser.error }) };
        }
        trackUsage(authHeader.slice(7).trim());
    }

    try {
        const { product, category, features, target, platform } = JSON.parse(event.body);
        if (!product || !category || !features) {
            return { statusCode: 400, headers, body: JSON.stringify({ error: 'Product, category, and features required' }) };
        }

        const platformPrompts = {
            etsy: `Generate an optimized Etsy listing with:
- "title": SEO title under 140 characters. Include main keyword first, then descriptive words, then use case.
- "description": Product description 200-280 words. Start with a hook, describe benefits (not just features), include materials, dimensions, care instructions. Use natural language with keywords woven in.
- "tags": Array of exactly 13 Etsy tags (each under 20 characters). Mix broad and specific keywords.`,
            amazon: `Generate an optimized Amazon listing with:
- "title": Product title under 200 characters. Follow Amazon format: Brand + Model + Product Type + Key Features + Size/Color.
- "bullet_points": Array of 5 bullet points (each under 500 chars). Start each with a BENEFIT in caps, then explain the feature.
- "description": Product description 150-250 words. Focus on use cases and differentiators.
- "keywords": Array of 7 backend search terms (no duplicates from title).`,
            google: `Generate an optimized Google Business Profile with:
- "title": Business name + category (under 75 chars)
- "description": Business description 750-1000 characters. Include services, location keywords, unique selling points. Write for customers, not algorithms.
- "categories": Array of 5 relevant Google Business categories
- "attributes": Array of 5 key attributes to highlight`,
        };

        const platformPrompt = platformPrompts[platform] || platformPrompts.etsy;

        const deepseekResponse = await fetch('https://api.deepseek.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
            },
            body: JSON.stringify({
                model: 'deepseek-v4-flash',
                messages: [
                    {
                        role: 'system',
                        content: `You are an expert ${platform} SEO specialist. Generate optimized product listings that rank higher and convert better.

${platformPrompt}

Respond with a JSON object with the fields specified above. Be specific, persuasive, and keyword-rich without being spammy.`
                    },
                    {
                        role: 'user',
                        content: `Product: ${product}\nCategory: ${category}\nFeatures/Materials: ${features}\nTarget Buyer: ${target || 'General consumers'}`
                    }
                ],
                temperature: 0.5,
                max_tokens: 1000,
            }),
        });

        if (!deepseekResponse.ok) throw new Error(`DeepSeek API error: ${deepseekResponse.status}`);

        const deepseekData = await deepseekResponse.json();
        const msg = deepseekData.choices[0].message;
        const aiContent = msg.content || msg.reasoning_content || '';

        let result;
        try {
            result = JSON.parse(aiContent);
        } catch (e) {
            // Fallback for Etsy format
            result = {
                title: product + ' - ' + features.split(',')[0],
                description: aiContent.substring(0, 500),
                tags: features.split(',').map(f => f.trim().toLowerCase()).slice(0, 13),
            };
        }

        return { statusCode: 200, headers, body: JSON.stringify(result) };
    } catch (error) {
        console.error('Listing optimize error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
