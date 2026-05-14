/**
 * BoostSuite API Auth Module
 * 
 * API key format: bs_live_<24hex>
 * Keys are derived from email + master secret using HMAC-SHA256.
 * 
 * Usage in functions:
 *   const { verifyApiKey, corsHeaders } = require('./auth');
 *   const auth = await verifyApiKey(event);
 *   if (auth.error) return { statusCode: 401, headers: corsHeaders(), body: JSON.stringify({ error: auth.error }) };
 */

const crypto = require('crypto');

// ── CORS ──────────────────────────────────────────────────────────────────
function corsHeaders(origin = '*') {
    return {
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Content-Type': 'application/json',
    };
}

// ── Key derivation ────────────────────────────────────────────────────────
function deriveKey(email, secret) {
    const hash = crypto.createHmac('sha256', secret).update(email.toLowerCase().trim()).digest('hex');
    return `bs_live_${hash.slice(0, 24)}`;
}

function keyFingerprint(apiKey) {
    // We store fingerprint → metadata mapping
    return crypto.createHash('sha256').update(apiKey).digest('hex').slice(0, 16);
}

// ── In-memory key store (warm starts only) ────────────────────────────────
// In production, swap this for Supabase / Redis / KV
const keyStore = new Map();

function registerKey(email, plan = 'starter') {
    const secret = process.env.API_MASTER_SECRET || 'boostsuite-dev-secret';
    const apiKey = deriveKey(email, secret);
    const fp = keyFingerprint(apiKey);
    keyStore.set(fp, {
        email: email.toLowerCase().trim(),
        plan,
        createdAt: new Date().toISOString(),
        active: true,
    });
    return apiKey;
}

function getkeyMeta(apiKey) {
    const fp = keyFingerprint(apiKey);
    return keyStore.get(fp) || null;
}

// ── Verify ────────────────────────────────────────────────────────────────
async function verifyApiKey(event) {
    const authHeader =
        event.headers?.authorization ||
        event.headers?.Authorization ||
        '';

    if (!authHeader.startsWith('Bearer ')) {
        return { error: 'Missing or invalid Authorization header. Expected: Bearer <api_key>' };
    }

    const apiKey = authHeader.slice(7).trim();
    if (!apiKey.startsWith('bs_live_')) {
        return { error: 'Invalid API key format' };
    }

    const meta = getkeyMeta(apiKey);
    if (!meta) {
        return { error: 'Unknown API key' };
    }
    if (!meta.active) {
        return { error: 'API key is deactivated' };
    }

    return { email: meta.email, plan: meta.plan };
}

// ── Usage tracking (simple in-memory counter) ─────────────────────────────
const usage = new Map(); // fp → { date: count }

function trackUsage(apiKey) {
    const fp = keyFingerprint(apiKey);
    const today = new Date().toISOString().slice(0, 10);
    const dayData = usage.get(fp) || {};
    dayData[today] = (dayData[today] || 0) + 1;
    usage.set(fp, dayData);
    return dayData[today];
}

function getUsageCount(apiKey) {
    const fp = keyFingerprint(apiKey);
    const today = new Date().toISOString().slice(0, 10);
    const dayData = usage.get(fp) || {};
    return dayData[today] || 0;
}

module.exports = {
    corsHeaders,
    deriveKey,
    keyFingerprint,
    registerKey,
    getkeyMeta,
    verifyApiKey,
    trackUsage,
    getUsageCount,
};
