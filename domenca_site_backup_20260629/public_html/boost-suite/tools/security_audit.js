// Security Audit Tool for BoostSuite
// Checks: HTTPS, security headers, mixed content, SSL grade

const https = require('https');
const http = require('http');
const { URL } = require('url');

async function checkSecurityHeaders(url) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const req = client.request(url, {
            method: 'HEAD',
            timeout: 10000,
            headers: {
                'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)'
            }
        }, (res) => {
            const headers = res.headers;
            const checks = [];
            let score = 0;
            
            // HTTPS check
            if (parsedUrl.protocol === 'https:') {
                checks.push({ check: 'HTTPS', status: 'pass', detail: 'Site uses HTTPS' });
                score += 20;
            } else {
                checks.push({ check: 'HTTPS', status: 'fail', detail: 'Site does NOT use HTTPS!' });
            }
            
            // Security headers
            const securityHeaders = [
                { 
                    name: 'Strict-Transport-Security', 
                    label: 'HSTS',
                    pattern: /max-age/i,
                    points: 15 
                },
                { 
                    name: 'X-Content-Type-Options', 
                    label: 'MIME Type Protection',
                    pattern: /nosniff/i,
                    points: 10 
                },
                { 
                    name: 'X-Frame-Options', 
                    label: 'Clickjacking Protection',
                    pattern: /deny|sameorigin/i,
                    points: 10 
                },
                { 
                    name: 'X-XSS-Protection', 
                    label: 'XSS Protection',
                    pattern: /1|block/i,
                    points: 10 
                },
                { 
                    name: 'Content-Security-Policy', 
                    label: 'Content Security Policy',
                    pattern: /.+/,
                    points: 15 
                },
                { 
                    name: 'Referrer-Policy', 
                    label: 'Referrer Policy',
                    pattern: /.+/,
                    points: 5 
                },
                { 
                    name: 'Permissions-Policy', 
                    label: 'Permissions Policy',
                    pattern: /.+/,
                    points: 5 
                },
                { 
                    name: 'X-Permitted-Cross-Domain-Policies', 
                    label: 'Cross-Domain Policy',
                    pattern: /none/i,
                    points: 5 
                },
            ];
            
            let headersFound = 0;
            for (const sh of securityHeaders) {
                if (headers[sh.name.toLowerCase()]) {
                    if (sh.pattern.test(headers[sh.name])) {
                        checks.push({ check: sh.label, status: 'pass', detail: `${sh.name}: ${headers[sh.name.toLowerCase()]}` });
                        score += sh.points;
                        headersFound++;
                    } else {
                        checks.push({ check: sh.label, status: 'warn', detail: `${sh.name} present but may be misconfigured` });
                        score += sh.points / 2;
                    }
                } else {
                    checks.push({ check: sh.label, status: 'fail', detail: `${sh.name} not set` });
                }
            }
            
            // Server info exposure
            if (headers['server']) {
                checks.push({ check: 'Server Info', status: 'warn', detail: `Server exposed: ${headers['server']}` });
            } else {
                checks.push({ check: 'Server Info', status: 'pass', detail: 'Server info hidden' });
                score += 5;
            }
            
            // X-Powered-By
            if (headers['x-powered-by']) {
                checks.push({ check: 'Powered-By', status: 'warn', detail: `X-Powered-By exposed: ${headers['x-powered-by']}` });
            } else {
                checks.push({ check: 'Powered-By', status: 'pass', detail: 'X-Powered-By hidden' });
                score += 5;
            }
            
            // CORS
            if (headers['access-control-allow-origin']) {
                if (headers['access-control-allow-origin'] === '*') {
                    checks.push({ check: 'CORS', status: 'warn', detail: 'CORS allows all origins (*)' });
                } else {
                    checks.push({ check: 'CORS', status: 'pass', detail: 'CORS configured properly' });
                    score += 5;
                }
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
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        return new Promise((resolve, reject) => {
            const req = client.get(url, {
                timeout: 10000,
                headers: { 'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)' }
            }, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    // Check for mixed content (HTTP resources on HTTPS page)
                    const httpResources = data.match(/src=["']http:\/\/[^"']+["']/g) || [];
                    const httpLinks = data.match(/href=["']http:\/\/[^"']+["']/g) || [];
                    
                    const totalMixed = httpResources.length + httpLinks.length;
                    
                    if (totalMixed === 0) {
                        resolve({ hasMixed: false, count: 0 });
                    } else {
                        resolve({ hasMixed: true, count: totalMixed, examples: [...httpResources.slice(0, 3), ...httpLinks.slice(0, 3)] });
                    }
                });
            });
            req.on('error', () => resolve({ hasMixed: false, count: 0, error: true }));
            req.on('timeout', () => { req.destroy(); resolve({ hasMixed: false, count: 0, error: true }); });
            req.end();
        });
    } catch {
        return { hasMixed: false, count: 0, error: true };
    }
}

module.exports = { checkSecurityHeaders, checkMixedContent };

// CLI mode
if (require.main === module) {
    const url = process.argv[2];
    if (!url) {
        console.log('Usage: node security_audit.js <url>');
        process.exit(1);
    }
    
    Promise.all([
        checkSecurityHeaders(url),
        checkMixedContent(url)
    ]).then(([headers, mixed]) => {
        if (mixed.hasMixed) {
            headers.checks.push({ check: 'Mixed Content', status: 'fail', detail: `${mixed.count} HTTP resources on HTTPS page` });
            headers.score = Math.max(0, headers.score - 20);
        } else {
            headers.checks.push({ check: 'Mixed Content', status: 'pass', detail: 'No mixed content' });
            headers.score = Math.min(100, headers.score + 5);
        }
        console.log(JSON.stringify(headers, null, 2));
    }).catch(err => {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    });
}
