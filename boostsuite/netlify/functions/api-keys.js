/**
 * POST /api-keys
 *   { action: "create", email: "...", plan: "starter"|"agency" }
 *   { action: "list" }
 *   { action: "revoke", key: "bs_live_..." }
 *
 * Admin-protected: requires x-admin-token header matching ADMIN_TOKEN env var.
 */

const { corsHeaders, registerKey, getkeyMeta, keyFingerprint } = require('./auth');

exports.handler = async (event) => {
    const headers = corsHeaders();

    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }

    // Admin auth
    const adminToken = event.headers?.['x-admin-token'] || event.headers?.['X-Admin-Token'];
    if (!adminToken || adminToken !== process.env.ADMIN_TOKEN) {
        return {
            statusCode: 403,
            headers,
            body: JSON.stringify({ error: 'Forbidden – invalid admin token' }),
        };
    }

    try {
        const body = JSON.parse(event.body || '{}');
        const { action } = body;

        // ── CREATE ────────────────────────────────────────────────────
        if (action === 'create') {
            const { email, plan = 'starter' } = body;
            if (!email || !email.includes('@')) {
                return { statusCode: 400, headers, body: JSON.stringify({ error: 'Valid email required' }) };
            }
            if (!['starter', 'agency'].includes(plan)) {
                return { statusCode: 400, headers, body: JSON.stringify({ error: 'Plan must be starter or agency' }) };
            }

            const apiKey = registerKey(email, plan);
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    success: true,
                    apiKey,
                    plan,
                    email: email.toLowerCase().trim(),
                    message: 'Store this key securely – it cannot be retrieved later.',
                }),
            };
        }

        // ── LIST ──────────────────────────────────────────────────────
        if (action === 'list') {
            const keys = [];
            for (const [fp, meta] of keyStore.entries()) {
                keys.push({ fingerprint: fp, ...meta });
            }
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({ keys, total: keys.length }),
            };
        }

        // ── REVOKE ────────────────────────────────────────────────────
        if (action === 'revoke') {
            const { fingerprint } = body;
            if (!fingerprint) {
                return { statusCode: 400, headers, body: JSON.stringify({ error: 'Fingerprint required' }) };
            }
            // We can't directly import keyStore from auth module (separate instances)
            // This is a limitation of in-memory storage on Netlify
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    success: true,
                    message: 'Key revocation requires database storage. For now, rotate the API_MASTER_SECRET to invalidate all keys.',
                }),
            };
        }

        return { statusCode: 400, headers, body: JSON.stringify({ error: 'Unknown action. Use: create, list, revoke' }) };
    } catch (e) {
        return { statusCode: 500, headers, body: JSON.stringify({ error: e.message }) };
    }
};
