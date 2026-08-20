exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
    };

    if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
    if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

    try {
        const { prompt } = JSON.parse(event.body);
        if (!prompt) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Prompt required' }) };

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
                        content: 'You are a professional food writer and translator. Write appetizing, evocative menu descriptions that make diners want to order. Never start with the dish name. Use sensory language. Keep descriptions concise (2-4 sentences, max 80 words per language).'
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                temperature: 0.7,
                max_tokens: 2000,
            }),
        });

        if (!deepseekResponse.ok) {
            const err = await deepseekResponse.text();
            console.error('DeepSeek error:', err);
            return { statusCode: 502, headers, body: JSON.stringify({ error: `AI service error: ${deepseekResponse.status}` }) };
        }

        const deepseekData = await deepseekResponse.json();
        const msg = deepseekData.choices[0].message;
        const content = msg.content || msg.reasoning_content || '';

        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({ content: [{ text: content }] }),
        };
    } catch (error) {
        console.error('Generate error:', error);
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
