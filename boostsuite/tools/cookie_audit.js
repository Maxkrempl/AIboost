// Cookie & GDPR Audit Tool for BoostSuite
// Checks: consent banner, cookie categories, GDPR compliance, privacy policy

const https = require('https');
const http = require('http');
const { URL } = require('url');

async function fetchPage(url, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const req = client.get(url, {
            timeout,
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)'
            }
        }, (res) => {
            // Follow redirects
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                const redirectUrl = new URL(res.headers.location, url).href;
                return fetchPage(redirectUrl, timeout).then(resolve).catch(reject);
            }
            
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    });
}

function checkCookieBanner(html) {
    const checks = [];
    let score = 0;
    
    // Check for cookie consent banner/library
    const bannerPatterns = [
        { name: 'CookieBot', pattern: /cookiebot|cookieconsent|cookie.?consent/i, points: 15 },
        { name: 'OneTrust', pattern: /onetrust|optanon/i, points: 15 },
        { name: 'GDPR Cookie Consent', pattern: /gdpr.?cookie|cookie.?notice|cookie.?policy/i, points: 15 },
        { name: 'CookieYes', pattern: /cookieyes|ckyconsent/i, points: 15 },
        { name: 'Iubenda', pattern: /iubenda/i, points: 15 },
        { name: 'Complianz', pattern: /complianz/i, points: 15 },
        { name: 'Quantcast', pattern: /quantcast|qconsent/i, points: 15 },
        { name: 'Generic cookie banner', pattern: /cookie.*accept|accept.*cookie|cookie.*agree|agree.*cookie|we.*use.*cookie|this.*site.*use.*cookie/i, points: 10 },
    ];
    
    let bannerFound = false;
    for (const bp of bannerPatterns) {
        if (bp.pattern.test(html)) {
            checks.push({ check: bp.name, status: 'pass', detail: `${bp.name} detected` });
            score += bp.points;
            bannerFound = true;
            break;
        }
    }
    
    if (!bannerFound) {
        checks.push({ check: 'Cookie Banner', status: 'fail', detail: 'No cookie consent banner detected' });
    }
    
    // Check for cookie categories
    const categoryPatterns = [
        { name: 'Necessary cookies', pattern: /necessary|essential|strictly/i },
        { name: 'Analytics cookies', pattern: /analytics|statistics|performance/i },
        { name: 'Marketing cookies', pattern: /marketing|advertising|targeting/i },
        { name: 'Preference cookies', pattern: /preferences|functional/i },
    ];
    
    let categoriesFound = 0;
    for (const cat of categoryPatterns) {
        if (cat.pattern.test(html)) {
            categoriesFound++;
        }
    }
    
    if (categoriesFound >= 3) {
        checks.push({ check: 'Cookie Categories', status: 'pass', detail: `${categoriesFound} cookie categories found` });
        score += 15;
    } else if (categoriesFound > 0) {
        checks.push({ check: 'Cookie Categories', status: 'warn', detail: `Only ${categoriesFound} cookie categories found` });
        score += 7;
    } else {
        checks.push({ check: 'Cookie Categories', status: 'fail', detail: 'No cookie categories detected' });
    }
    
    // Check for privacy policy link
    const privacyPatterns = /privacy.?policy|datenschutz|politica.?privacy|pravila.?privatnosti/i;
    if (privacyPatterns.test(html)) {
        checks.push({ check: 'Privacy Policy', status: 'pass', detail: 'Privacy policy link found' });
        score += 10;
    } else {
        checks.push({ check: 'Privacy Policy', status: 'fail', detail: 'No privacy policy link' });
    }
    
    // Check for GDPR keywords
    const gdprKeywords = ['GDPR', 'DSGVO', 'RODO', 'privacy', 'personal data', 'data protection', 'osebni podatki', 'zaštita podataka'];
    const gdprFound = gdprKeywords.filter(k => html.toLowerCase().includes(k.toLowerCase()));
    
    if (gdprFound.length >= 2) {
        checks.push({ check: 'GDPR Compliance', status: 'pass', detail: `GDPR keywords: ${gdprFound.join(', ')}` });
        score += 10;
    } else if (gdprFound.length === 1) {
        checks.push({ check: 'GDPR Compliance', status: 'warn', detail: `Partial GDPR: ${gdprFound[0]}` });
        score += 5;
    } else {
        checks.push({ check: 'GDPR Compliance', status: 'fail', detail: 'No GDPR references found' });
    }
    
    // Check for cookie policy page
    const cookiePolicyPattern = /cookie.?policy|politica.?cookie|pravila.?kolačić/i;
    if (cookiePolicyPattern.test(html)) {
        checks.push({ check: 'Cookie Policy', status: 'pass', detail: 'Cookie policy found' });
        score += 10;
    } else {
        checks.push({ check: 'Cookie Policy', status: 'warn', detail: 'No dedicated cookie policy' });
    }
    
    // Check for opt-out mechanism
    const optOutPattern = /opt.?out|unsubscribe|manage.?cookie|cookie.?settings|cookie.?prefer/i;
    if (optOutPattern.test(html)) {
        checks.push({ check: 'Opt-out Mechanism', status: 'pass', detail: 'Cookie management available' });
        score += 10;
    } else {
        checks.push({ check: 'Opt-out Mechanism', status: 'warn', detail: 'No cookie management found' });
    }
    
    return { score: Math.min(100, score), checks };
}

module.exports = { checkCookieBanner };

// CLI mode
if (require.main === module) {
    const url = process.argv[2];
    if (!url) {
        console.log('Usage: node cookie_audit.js <url>');
        process.exit(1);
    }
    
    fetchPage(url)
        .then(html => {
            const result = checkCookieBanner(html);
            console.log(JSON.stringify(result, null, 2));
        })
        .catch(err => {
            console.error(JSON.stringify({ error: err.message }));
            process.exit(1);
        });
}
