exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
    };

    if (event.httpMethod === 'OPTIONS') return { statusCode: 200, headers, body: '' };
    if (event.httpMethod !== 'POST') return { statusCode: 405, headers, body: JSON.stringify({ error: 'Method not allowed' }) };

    try {
        const { price_id, email } = JSON.parse(event.body);
        if (!price_id) return { statusCode: 400, headers, body: JSON.stringify({ error: 'Missing price_id' }) };

        const stripeKey = process.env.STRIPE_SECRET_KEY || '***REMOVED***';
        if (!stripeKey) return { statusCode: 500, headers, body: JSON.stringify({ error: 'Stripe key not configured' }) };

        const params = new URLSearchParams();
        params.append('mode', 'subscription');
        params.append('payment_method_types[]', 'card');
        params.append('line_items[0][price]', price_id);
        params.append('line_items[0][quantity]', '1');
        params.append('success_url', 'https://menuboostai.netlify.app/success.html?session_id={CHECKOUT_SESSION_ID}');
        params.append('cancel_url', 'https://menuboostai.netlify.app/');
        params.append('metadata[product]', 'MenuBoost');
        params.append('metadata[source]', 'menuboostai.netlify.app');
        params.append('subscription_data[metadata][product]', 'MenuBoost');
        params.append('subscription_data[metadata][source]', 'menuboostai.netlify.app');

        if (email) params.append('customer_email', email);

        const response = await fetch('https://api.stripe.com/v1/checkout/sessions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${stripeKey}`,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params.toString(),
        });

        const data = await response.json();

        if (response.ok && data.url) {
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({ checkout_url: data.url }),
            };
        } else {
            return {
                statusCode: 500,
                headers,
                body: JSON.stringify({ error: data.error?.message || 'Failed to create checkout session' }),
            };
        }
    } catch (error) {
        return { statusCode: 500, headers, body: JSON.stringify({ error: error.message }) };
    }
};
