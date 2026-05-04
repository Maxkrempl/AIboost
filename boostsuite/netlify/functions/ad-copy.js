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
        const { product, audience, tone, cta, platform } = JSON.parse(event.body);
        if (!product || !audience || !cta) {
            return { statusCode: 400, headers, body: JSON.stringify({ error: 'Product, audience, and CTA required' }) };
        }

        const platformPrompts = {
            google: `Generate 3 Google Ads variations. Each must have:
- Headline (max 30 characters)
- Description (max 90 characters)
Format each as: "Headline: ...\nDescription: ..."`,
            facebook: `Generate 3 Facebook/Instagram ad variations. Each must have:
- Primary text (125 characters max for feed)
- Headline (40 characters max)
- Description (30 characters max)
Format each as: "Primary: ...\nHeadline: ...\nDescription: ..."`,
            linkedin: `Generate 3 LinkedIn ad variations. Each must have:
- Introductory text (150 characters)
- Headline (70 characters)
- Description (100 characters)
Format each as: "Intro: ...\nHeadline: ...\nDescription: ..."`,
            x: `Generate 3 X (Twitter) post variations. Each must be under 280 characters and include a CTA.`,
            email: `Generate 3 email subject line + preview text variations. Each must have:
- Subject line (50 characters max)
- Preview text (90 characters max)
Format each as: "Subject: ...\nPreview: ..."`,
        };

        const platformPrompt = platformPrompts[platform] || platformPrompts.google;

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
                        content: `You are an expert copywriter specializing in ${platform} ads. Generate compelling, conversion-focused ad copy.

${platformPrompt}

Tone: ${tone}
Call to Action: ${cta}

Respond with a JSON object: { "variations": ["variation 1 text", "variation 2 text", "variation 3 text"] }

Each variation should be a complete, ready-to-use text block. Be creative and varied — each should take a different angle.`
                    },
                    {
                        role: 'user',
                        content: `Product/Service: ${product}\nTarget Audience: ${audience}`
                    }
                ],
                temperature: 0.7,
                max_tokens: 800,
            }),
        });

        if (!deepseekResponse.ok) throw new Error(`DeepSeek API error: ${deepseekResponse.status}`);

        const deepseekData = await deepseekResponse.json();
        const aiContent = deepseekData.choices[0].message.content;

        let result;
        try {
            result = JSON.parse(aiContent);
        } catch (e) {
            // Split by numbered patterns or ---
            const parts = aiContent.split(/\n---\n|\n\n(?=\d\.)/).filter(Boolean);
            result = { variations: parts.length ? parts : [aiContent] };
        }

        return { statusCode: 200, headers, body: JSON.stringify(result) };
    } catch (error) {
        console.error('Ad copy error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
