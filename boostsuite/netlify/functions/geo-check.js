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
                        content: `You are a GEO expert. Analyze this business's AI visibility. Return ONLY valid JSON, no explanation.

{"score": 0-100, "analysis": "2-3 sentences", "platforms": ["list of AI platforms"], "suggestions": ["5 actionable tips"]}

Score: review sites +20, GBP claimed +15, reviews +15, NAP consistency +10, directories +10, social +10, schema +10, blog +10.`
                    },
                    {
                        role: 'user',
                        content: `Business: ${business}\nLocation: ${location}\nNiche: ${niche}\n\nSearch Results Found:\n${searchContext || 'No search results found.'}`
                    }
                ],
                temperature: 0.3,
                max_tokens: 1500,
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
