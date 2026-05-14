// Netlify Function: Combined Audit
// Runs all 5 audit types and returns comprehensive report

const https = require('https');
const http = require('http');
const { URL } = require('url');

// ============= UTILITY FUNCTIONS =============

async function fetchPage(url, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const req = client.get(url, {
            timeout,
            headers: { 'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)' }
        }, (res) => {
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

async function fetchWithHeaders(url, timeout = 15000) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const startTime = Date.now();
        const req = client.get(url, {
            timeout,
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)',
                'Accept-Encoding': 'gzip, deflate, br'
            }
        }, (res) => {
            const loadTime = Date.now() - startTime;
            
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                const redirectUrl = new URL(res.headers.location, url).href;
                return fetchWithHeaders(redirectUrl, timeout).then(resolve).catch(reject);
            }
            
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                resolve({
                    html: data,
                    headers: res.headers,
                    statusCode: res.statusCode,
                    loadTime,
                    size: Buffer.byteLength(data, 'utf8')
                });
            });
        });
        
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    });
}

// ============= AUDIT FUNCTIONS =============

function analyzeSEO(html) {
    const checks = [];
    let score = 0;
    
    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
    if (titleMatch && titleMatch[1].length > 10) {
        checks.push({ check: 'Title Tag', status: 'pass', detail: `${titleMatch[1].substring(0, 50)}...` });
        score += 15;
    } else {
        checks.push({ check: 'Title Tag', status: 'fail', detail: 'Missing or too short' });
    }
    
    const metaDesc = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i);
    if (metaDesc && metaDesc[1].length > 30) {
        checks.push({ check: 'Meta Description', status: 'pass', detail: `${metaDesc[1].substring(0, 60)}...` });
        score += 15;
    } else {
        checks.push({ check: 'Meta Description', status: 'fail', detail: 'Missing or too short' });
    }
    
    if (/rel=["']canonical["']/.test(html)) {
        checks.push({ check: 'Canonical Tag', status: 'pass', detail: 'Canonical URL set' });
        score += 10;
    } else {
        checks.push({ check: 'Canonical Tag', status: 'fail', detail: 'No canonical tag' });
    }
    
    if (/og:title|og:description|og:image/i.test(html)) {
        checks.push({ check: 'Open Graph', status: 'pass', detail: 'OG tags found' });
        score += 10;
    } else {
        checks.push({ check: 'Open Graph', status: 'fail', detail: 'No OG tags' });
    }
    
    if (/application\/ld\+json/.test(html) || /itemscope|itemtype/i.test(html)) {
        checks.push({ check: 'Structured Data', status: 'pass', detail: 'Schema markup found' });
        score += 15;
    } else {
        checks.push({ check: 'Structured Data', status: 'fail', detail: 'No structured data' });
    }
    
    const h1Count = (html.match(/<h1[^>]*>/gi) || []).length;
    if (h1Count === 1) {
        checks.push({ check: 'H1 Tag', status: 'pass', detail: 'Exactly one H1' });
        score += 10;
    } else if (h1Count === 0) {
        checks.push({ check: 'H1 Tag', status: 'fail', detail: 'No H1 tag' });
    } else {
        checks.push({ check: 'H1 Tag', status: 'warn', detail: `${h1Count} H1 tags` });
        score += 5;
    }
    
    const images = html.match(/<img[^>]*>/gi) || [];
    const imagesWithAlt = images.filter(img => /alt=["'][^"']+["']/i.test(img));
    if (images.length > 0) {
        const altPercent = (imagesWithAlt.length / images.length * 100).toFixed(0);
        if (altPercent > 80) {
            checks.push({ check: 'Image Alt Text', status: 'pass', detail: `${altPercent}% have alt text` });
            score += 10;
        } else {
            checks.push({ check: 'Image Alt Text', status: 'warn', detail: `Only ${altPercent}% have alt text` });
            score += 5;
        }
    }
    
    const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
    if (bodyMatch) {
        const text = bodyMatch[1].replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
        const wordCount = text.split(' ').length;
        if (wordCount > 500) {
            checks.push({ check: 'Content Length', status: 'pass', detail: `${wordCount} words` });
            score += 15;
        } else if (wordCount > 200) {
            checks.push({ check: 'Content Length', status: 'warn', detail: `${wordCount} words (thin)` });
            score += 7;
        } else {
            checks.push({ check: 'Content Length', status: 'fail', detail: `${wordCount} words (too thin)` });
        }
    }
    
    return { score: Math.min(100, score), checks };
}

function checkCookieBanner(html) {
    const checks = [];
    let score = 0;
    
    const bannerPatterns = [
        { name: 'CookieBot', pattern: /cookiebot|cookieconsent|cookie.?consent/i, points: 15 },
        { name: 'OneTrust', pattern: /onetrust|optanon/i, points: 15 },
        { name: 'GDPR Cookie Consent', pattern: /gdpr.?cookie|cookie.?notice|cookie.?policy/i, points: 15 },
        { name: 'CookieYes', pattern: /cookieyes|ckyconsent/i, points: 15 },
        { name: 'Iubenda', pattern: /iubenda/i, points: 15 },
        { name: 'Generic cookie banner', pattern: /cookie.*accept|accept.*cookie|cookie.*agree|we.*use.*cookie/i, points: 10 },
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
    
    const categoryPatterns = [
        { name: 'Necessary cookies', pattern: /necessary|essential|strictly/i },
        { name: 'Analytics cookies', pattern: /analytics|statistics|performance/i },
        { name: 'Marketing cookies', pattern: /marketing|advertising|targeting/i },
    ];
    
    let categoriesFound = 0;
    for (const cat of categoryPatterns) {
        if (cat.pattern.test(html)) categoriesFound++;
    }
    
    if (categoriesFound >= 3) {
        checks.push({ check: 'Cookie Categories', status: 'pass', detail: `${categoriesFound} categories` });
        score += 15;
    } else if (categoriesFound > 0) {
        checks.push({ check: 'Cookie Categories', status: 'warn', detail: `Only ${categoriesFound} categories` });
        score += 7;
    } else {
        checks.push({ check: 'Cookie Categories', status: 'fail', detail: 'No cookie categories' });
    }
    
    if (/privacy.?policy|datenschutz|politica.?privacy/i.test(html)) {
        checks.push({ check: 'Privacy Policy', status: 'pass', detail: 'Privacy policy found' });
        score += 10;
    } else {
        checks.push({ check: 'Privacy Policy', status: 'fail', detail: 'No privacy policy' });
    }
    
    if (/GDPR|DSGVO|RODO|osebni podatki|zaštita podataka/i.test(html)) {
        checks.push({ check: 'GDPR Compliance', status: 'pass', detail: 'GDPR references found' });
        score += 10;
    } else {
        checks.push({ check: 'GDPR Compliance', status: 'fail', detail: 'No GDPR references' });
    }
    
    if (/opt.?out|unsubscribe|manage.?cookie|cookie.?settings/i.test(html)) {
        checks.push({ check: 'Opt-out Mechanism', status: 'pass', detail: 'Cookie management available' });
        score += 10;
    } else {
        checks.push({ check: 'Opt-out Mechanism', status: 'warn', detail: 'No cookie management' });
    }
    
    return { score: Math.min(100, score), checks };
}

async function checkSecurityHeaders(url) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const req = client.request(url, {
            method: 'HEAD',
            timeout: 10000,
            headers: { 'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)' }
        }, (res) => {
            const headers = res.headers;
            const checks = [];
            let score = 0;
            
            if (parsedUrl.protocol === 'https:') {
                checks.push({ check: 'HTTPS', status: 'pass', detail: 'Site uses HTTPS' });
                score += 20;
            } else {
                checks.push({ check: 'HTTPS', status: 'fail', detail: 'No HTTPS!' });
            }
            
            const securityHeaders = [
                { name: 'Strict-Transport-Security', label: 'HSTS', points: 15 },
                { name: 'X-Content-Type-Options', label: 'MIME Protection', points: 10 },
                { name: 'X-Frame-Options', label: 'Clickjacking Protection', points: 10 },
                { name: 'X-XSS-Protection', label: 'XSS Protection', points: 10 },
                { name: 'Content-Security-Policy', label: 'CSP', points: 15 },
                { name: 'Referrer-Policy', label: 'Referrer Policy', points: 5 },
                { name: 'Permissions-Policy', label: 'Permissions Policy', points: 5 },
            ];
            
            for (const sh of securityHeaders) {
                if (headers[sh.name.toLowerCase()]) {
                    checks.push({ check: sh.label, status: 'pass', detail: 'Set' });
                    score += sh.points;
                } else {
                    checks.push({ check: sh.label, status: 'fail', detail: 'Not set' });
                }
            }
            
            if (!headers['server']) {
                checks.push({ check: 'Server Hidden', status: 'pass', detail: 'Server info hidden' });
                score += 5;
            } else {
                checks.push({ check: 'Server Hidden', status: 'warn', detail: `Server: ${headers['server']}` });
            }
            
            if (!headers['x-powered-by']) {
                checks.push({ check: 'Powered-By Hidden', status: 'pass', detail: 'X-Powered-By hidden' });
                score += 5;
            } else {
                checks.push({ check: 'Powered-By Hidden', status: 'warn', detail: `Exposed: ${headers['x-powered-by']}` });
            }
            
            resolve({ score: Math.min(100, score), checks });
        });
        
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
        req.end();
    });
}

async function checkMixedContent(url) {
    try {
        const html = await fetchPage(url);
        const httpResources = html.match(/src=["']http:\/\/[^"']+["']/g) || [];
        const httpLinks = html.match(/href=["']http:\/\/[^"']+["']/g) || [];
        const totalMixed = httpResources.length + httpLinks.length;
        
        return { hasMixed: totalMixed > 0, count: totalMixed };
    } catch {
        return { hasMixed: false, count: 0 };
    }
}

function analyzePerformance(url, response) {
    const checks = [];
    let score = 0;
    const { html, headers, loadTime, size } = response;
    
    if (loadTime < 1000) {
        checks.push({ check: 'Load Time', status: 'pass', detail: `${loadTime}ms - Excellent` });
        score += 20;
    } else if (loadTime < 2000) {
        checks.push({ check: 'Load Time', status: 'pass', detail: `${loadTime}ms - Good` });
        score += 15;
    } else if (loadTime < 3000) {
        checks.push({ check: 'Load Time', status: 'warn', detail: `${loadTime}ms - Needs work` });
        score += 10;
    } else {
        checks.push({ check: 'Load Time', status: 'fail', detail: `${loadTime}ms - Slow` });
        score += 5;
    }
    
    const sizeKB = size / 1024;
    if (sizeKB < 100) {
        checks.push({ check: 'Page Size', status: 'pass', detail: `${sizeKB.toFixed(0)}KB - Lean` });
        score += 15;
    } else if (sizeKB < 500) {
        checks.push({ check: 'Page Size', status: 'pass', detail: `${sizeKB.toFixed(0)}KB - OK` });
        score += 10;
    } else if (sizeKB < 1000) {
        checks.push({ check: 'Page Size', status: 'warn', detail: `${sizeKB.toFixed(0)}KB - Heavy` });
        score += 5;
    } else {
        checks.push({ check: 'Page Size', status: 'fail', detail: `${sizeKB.toFixed(0)}KB - Very heavy` });
    }
    
    const encoding = headers['content-encoding'] || '';
    if (encoding.includes('gzip') || encoding.includes('br') || encoding.includes('deflate')) {
        checks.push({ check: 'Compression', status: 'pass', detail: `${encoding.toUpperCase()} enabled` });
        score += 15;
    } else {
        checks.push({ check: 'Compression', status: 'fail', detail: 'No compression' });
    }
    
    const cacheControl = headers['cache-control'] || '';
    if (cacheControl.includes('max-age') || headers['expires']) {
        checks.push({ check: 'Caching', status: 'pass', detail: 'Cache headers set' });
        score += 10;
    } else {
        checks.push({ check: 'Caching', status: 'fail', detail: 'No cache headers' });
    }
    
    const images = html.match(/<img[^>]+>/gi) || [];
    let lazyLoaded = 0;
    for (const img of images) {
        if (/loading=["']lazy["']/.test(img)) lazyLoaded++;
    }
    
    if (images.length > 0) {
        const lazyPercent = (lazyLoaded / images.length * 100).toFixed(0);
        if (lazyPercent > 50) {
            checks.push({ check: 'Lazy Loading', status: 'pass', detail: `${lazyPercent}% lazy-loaded` });
            score += 10;
        } else if (lazyLoaded > 0) {
            checks.push({ check: 'Lazy Loading', status: 'warn', detail: `Only ${lazyPercent}%` });
            score += 5;
        } else {
            checks.push({ check: 'Lazy Loading', status: 'fail', detail: 'No lazy loading' });
        }
    }
    
    const externalScripts = (html.match(/src=["']https?:\/\/[^"']+\.js/g) || []).length;
    const externalStyles = (html.match(/href=["']https?:\/\/[^"']+\.css/g) || []).length;
    const totalExternal = externalScripts + externalStyles;
    
    if (totalExternal < 5) {
        checks.push({ check: 'External Resources', status: 'pass', detail: `${totalExternal} resources` });
        score += 10;
    } else if (totalExternal < 15) {
        checks.push({ check: 'External Resources', status: 'warn', detail: `${totalExternal} resources` });
        score += 5;
    } else {
        checks.push({ check: 'External Resources', status: 'fail', detail: `${totalExternal} - too many` });
    }
    
    return { score: Math.min(100, score), checks };
}

function analyzeAccessibility(html) {
    const checks = [];
    let score = 0;
    
    if (/<html[^>]*lang=["'][^"']+["']/i.test(html)) {
        checks.push({ check: 'Language Attribute', status: 'pass', detail: 'Set' });
        score += 10;
    } else {
        checks.push({ check: 'Language Attribute', status: 'fail', detail: 'Missing' });
    }
    
    const h1Count = (html.match(/<h1[^>]*>/gi) || []).length;
    if (h1Count === 1) {
        checks.push({ check: 'H1 Tag', status: 'pass', detail: 'Exactly one H1' });
        score += 10;
    } else if (h1Count === 0) {
        checks.push({ check: 'H1 Tag', status: 'fail', detail: 'No H1' });
    } else {
        checks.push({ check: 'H1 Tag', status: 'warn', detail: `${h1Count} H1s` });
        score += 5;
    }
    
    const images = html.match(/<img[^>]*>/gi) || [];
    const imagesWithAlt = images.filter(img => /alt=["'][^"']+["']/i.test(img));
    if (images.length > 0) {
        const altPercent = (imagesWithAlt.length / images.length * 100).toFixed(0);
        if (altPercent > 80) {
            checks.push({ check: 'Image Alt Text', status: 'pass', detail: `${altPercent}%` });
            score += 15;
        } else if (altPercent > 50) {
            checks.push({ check: 'Image Alt Text', status: 'warn', detail: `Only ${altPercent}%` });
            score += 7;
        } else {
            checks.push({ check: 'Image Alt Text', status: 'fail', detail: `${altPercent}%` });
        }
    }
    
    const semanticElements = html.match(/<(header|nav|main|footer|aside|section|article)[^>]*>/gi) || [];
    const ariaRoles = html.match(/role=["'][^"']+["']/gi) || [];
    const totalLandmarks = semanticElements.length + ariaRoles.length;
    
    if (totalLandmarks >= 3) {
        checks.push({ check: 'ARIA Landmarks', status: 'pass', detail: `${totalLandmarks} landmarks` });
        score += 10;
    } else if (totalLandmarks > 0) {
        checks.push({ check: 'ARIA Landmarks', status: 'warn', detail: `Only ${totalLandmarks}` });
        score += 5;
    } else {
        checks.push({ check: 'ARIA Landmarks', status: 'fail', detail: 'None found' });
    }
    
    const inputs = html.match(/<input[^>]*>/gi) || [];
    const labels = html.match(/<label[^>]*>/gi) || [];
    const ariaLabels = html.match(/aria-label=["'][^"']+["']/gi) || [];
    const totalLabels = labels.length + ariaLabels.length;
    
    if (inputs.length > 0) {
        if (totalLabels >= inputs.length) {
            checks.push({ check: 'Form Labels', status: 'pass', detail: 'All inputs labeled' });
            score += 10;
        } else {
            checks.push({ check: 'Form Labels', status: 'warn', detail: `${inputs.length} inputs, ${totalLabels} labels` });
            score += 5;
        }
    }
    
    if (/skip.*nav|jump.*content/i.test(html)) {
        checks.push({ check: 'Skip Navigation', status: 'pass', detail: 'Found' });
        score += 10;
    } else {
        checks.push({ check: 'Skip Navigation', status: 'warn', detail: 'Not found' });
    }
    
    if (/user-scalable\s*=\s*["']?no/i.test(html) || /maximum-scale\s*=\s*1/i.test(html)) {
        checks.push({ check: 'Zoom Allowed', status: 'fail', detail: 'Zoom disabled!' });
    } else {
        checks.push({ check: 'Zoom Allowed', status: 'pass', detail: 'Zoom allowed' });
        score += 5;
    }
    
    return { score: Math.min(100, score), checks };
}

function generateSummary(audits) {
    const critical = [];
    const warnings = [];
    
    for (const [key, audit] of Object.entries(audits)) {
        for (const check of audit.checks) {
            if (check.status === 'fail') critical.push(`${audit.category}: ${check.check}`);
            if (check.status === 'warn') warnings.push(`${audit.category}: ${check.check}`);
        }
    }
    
    let summary = '';
    if (critical.length > 0) summary += `🚨 ${critical.length} critical issues`;
    if (warnings.length > 0) summary += `${critical.length > 0 ? ' | ' : ''}⚠️ ${warnings.length} warnings`;
    if (!summary) summary = '✅ All audits passed!';
    
    return summary;
}

// ============= MAIN HANDLER =============

exports.handler = async (event) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    };
    
    if (event.httpMethod === 'OPTIONS') {
        return { statusCode: 200, headers, body: '' };
    }
    
    try {
        const { url } = JSON.parse(event.body || '{}');
        
        if (!url) {
            return {
                statusCode: 400,
                headers,
                body: JSON.stringify({ error: 'URL is required' })
            };
        }
        
        // Validate URL
        new URL(url);
        
        const startTime = Date.now();
        
        // Fetch page for HTML-based audits
        const html = await fetchPage(url);
        const response = await fetchWithHeaders(url);
        
        // Run all audits
        const seo = analyzeSEO(html);
        const cookies = checkCookieBanner(html);
        const accessibility = analyzeAccessibility(html);
        const performance = analyzePerformance(url, response);
        const securityHeaders = await checkSecurityHeaders(url);
        const mixedContent = await checkMixedContent(url);
        
        // Merge mixed content into security
        if (mixedContent.hasMixed) {
            securityHeaders.checks.push({ check: 'Mixed Content', status: 'fail', detail: `${mixedContent.count} HTTP resources on HTTPS page` });
            securityHeaders.score = Math.max(0, securityHeaders.score - 20);
        } else {
            securityHeaders.checks.push({ check: 'Mixed Content', status: 'pass', detail: 'No mixed content' });
            securityHeaders.score = Math.min(100, securityHeaders.score + 5);
        }
        
        const audits = {
            seo: { ...seo, category: '🔍 SEO' },
            security: { ...securityHeaders, category: '🔒 Security' },
            performance: { ...performance, category: '⚡ Performance' },
            accessibility: { ...accessibility, category: '♿ Accessibility' },
            cookies: { ...cookies, category: '🍪 Cookies & Privacy' }
        };
        
        // Calculate overall score
        const scores = [seo.score, securityHeaders.score, performance.score, accessibility.score, cookies.score];
        const overallScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        
        let grade;
        if (overallScore >= 90) grade = 'A';
        else if (overallScore >= 80) grade = 'B';
        else if (overallScore >= 70) grade = 'C';
        else if (overallScore >= 60) grade = 'D';
        else grade = 'F';
        
        const duration = Date.now() - startTime;
        
        return {
            statusCode: 200,
            headers,
            body: JSON.stringify({
                url,
                timestamp: new Date().toISOString(),
                duration: `${duration}ms`,
                audits,
                overall: {
                    score: overallScore,
                    grade,
                    summary: generateSummary(audits)
                }
            })
        };
        
    } catch (error) {
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({
                error: error.message || 'Audit failed'
            })
        };
    }
};
