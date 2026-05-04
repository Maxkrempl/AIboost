const fetch = require('node-fetch');

exports.handler = async (event, context) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json',
    };

    if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
    if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

    try {
        const { business, location, niche } = JSON.parse(event.body);
        if (!business || !location || !niche) {
            return { statusCode: 400, headers, body: JSON.stringify({ error: 'All fields required' }) };
        }

        // Use Tavily to search for the business
        const tavilyKey = process.env.TAVILY_API_KEY;
        let searchResults = [];

        if (tavilyKey) {
            const queries = [
                `${business} ${location} reviews`,
                `${business} ${niche} ${location}`,
                `"${business}" site:yelp.com OR site:tripadvisor.com OR site:google.com/maps`,
            ];

            for (const query of queries) {
                try {
                    const resp = await fetch('https://api.tavily.com/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            api_key: tavilyKey,
                            query,
                            max_results: 5,
                            include_answer: true,
                        }),
                    });
                    if (resp.ok) {
                        const data = await resp.json();
                        searchResults.push(...(data.results || []));
                    }
                } catch (e) { /* continue */ }
            }
        }

        // Deduplicate by URL
        const seen = new Set();
        searchResults = searchResults.filter(r => {
            if (seen.has(r.url)) return false;
            seen.add(r.url);
            return true;
        });

        // Build context for AI
        const searchContext = searchResults.map(r => `- ${r.title}: ${r.url}\n  ${r.content?.substring(0, 200) || ''}`).join('\n');

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
                        content: `You are an expert in Generative Engine Optimization (GEO). Analyze a business's AI visibility based on search results.

Respond with a JSON object containing:
- "score": number 0-100 (how likely AI assistants are to recommend this business)
- "analysis": 2-3 sentence analysis of their AI visibility
- "platforms": array of AI assistants/platforms likely to recommend them (e.g., "Google Assistant", "ChatGPT", "Alexa", "Perplexity")
- "suggestions": array of 5 actionable improvement suggestions

Scoring criteria:
- Presence on review sites (Yelp, TripAdvisor, Google) = +20
- Google Business Profile claimed = +15
- Multiple positive reviews = +15
- Consistent NAP (name/address/phone) across sites = +10
- Industry directory listings = +10
- Social media presence = +10
- Structured data / schema markup = +10
- Recent content / blog = +10`
                    },
                    {
                        role: 'user',
                        content: `Business: ${business}\nLocation: ${location}\nNiche: ${niche}\n\nSearch Results Found:\n${searchContext || 'No search results found.'}`
                    }
                ],
                temperature: 0.3,
                max_tokens: 600,
            }),
        });

        if (!deepseekResponse.ok) throw new Error(`DeepSeek API error: ${deepseekResponse.status}`);

        const deepseekData = await deepseekResponse.json();
        const aiContent = deepseekData.choices[0].message.content;

        let result;
        try {
            result = JSON.parse(aiContent);
        } catch (e) {
            const scoreMatch = aiContent.match(/\b(\d{1,3})\b/);
            result = {
                score: scoreMatch ? parseInt(scoreMatch[1]) : 50,
                analysis: aiContent.substring(0, 200),
                platforms: ['Google Assistant'],
                suggestions: ['Claim your Google Business Profile', 'Get more reviews', 'List on industry directories'],
            };
        }

        return { statusCode: 200, headers, body: JSON.stringify(result) };
    } catch (error) {
        console.error('GEO check error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
