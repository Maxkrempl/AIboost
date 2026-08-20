// Combined Audit Tool - Runs all 4 audits and generates comprehensive report
const { checkCookieBanner } = require('./cookie_audit');
const { checkSecurityHeaders, checkMixedContent } = require('./security_audit');
const { fetchWithHeaders, analyzePerformance } = require('./performance_audit');
const { analyzeAccessibility } = require('./accessibility_audit');

const https = require('https');
const http = require('http');
const { URL } = require('url');

// Import SEO audit (existing)
async function fetchSEOData(url, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const parsedUrl = new URL(url);
        const client = parsedUrl.protocol === 'https:' ? https : http;
        
        const req = client.get(url, {
            timeout,
            headers: { 'User-Agent': 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)' }
        }, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                const redirectUrl = new URL(res.headers.location, url).href;
                return fetchSEOData(redirectUrl, timeout).then(resolve).catch(reject);
            }
            
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        });
        
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    });
}

function analyzeSEO(html) {
    const checks = [];
    let score = 0;
    
    // Title tag
    const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
    if (titleMatch && titleMatch[1].length > 10) {
        checks.push({ check: 'Title Tag', status: 'pass', detail: `${titleMatch[1].substring(0, 50)}...` });
        score += 15;
    } else {
        checks.push({ check: 'Title Tag', status: 'fail', detail: 'Missing or too short' });
    }
    
    // Meta description
    const metaDesc = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i);
    if (metaDesc && metaDesc[1].length > 30) {
        checks.push({ check: 'Meta Description', status: 'pass', detail: `${metaDesc[1].substring(0, 60)}...` });
        score += 15;
    } else {
        checks.push({ check: 'Meta Description', status: 'fail', detail: 'Missing or too short' });
    }
    
    // Canonical
    if (/rel=["']canonical["']/.test(html)) {
        checks.push({ check: 'Canonical Tag', status: 'pass', detail: 'Canonical URL set' });
        score += 10;
    } else {
        checks.push({ check: 'Canonical Tag', status: 'fail', detail: 'No canonical tag' });
    }
    
    // Open Graph
    if (/og:title|og:description|og:image/i.test(html)) {
        checks.push({ check: 'Open Graph', status: 'pass', detail: 'OG tags found' });
        score += 10;
    } else {
        checks.push({ check: 'Open Graph', status: 'fail', detail: 'No OG tags' });
    }
    
    // Structured data
    if (/application\/ld\+json/.test(html) || /itemscope|itemtype/i.test(html)) {
        checks.push({ check: 'Structured Data', status: 'pass', detail: 'Schema markup found' });
        score += 15;
    } else {
        checks.push({ check: 'Structured Data', status: 'fail', detail: 'No structured data' });
    }
    
    // H1 tags
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
    
    // Images with alt text
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
    
    // Word count
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

async function runCombinedAudit(url) {
    const results = {
        url,
        timestamp: new Date().toISOString(),
        audits: {},
        overall: { score: 0, grade: '', summary: '' }
    };
    
    try {
        // Fetch page for HTML-based audits
        const html = await fetchSEOData(url);
        
        // Run all audits
        const seo = analyzeSEO(html);
        const cookie = checkCookieBanner(html);
        const accessibility = analyzeAccessibility(html);
        
        // These need the HTTP response
        const response = await fetchWithHeaders(url);
        const performance = analyzePerformance(url, response);
        const securityHeaders = await checkSecurityHeaders(url);
        const mixedContent = await checkMixedContent(url);
        
        if (mixedContent.hasMixed) {
            securityHeaders.checks.push({ check: 'Mixed Content', status: 'fail', detail: `${mixedContent.count} HTTP resources on HTTPS page` });
            securityHeaders.score = Math.max(0, securityHeaders.score - 20);
        } else {
            securityHeaders.checks.push({ check: 'Mixed Content', status: 'pass', detail: 'No mixed content' });
            securityHeaders.score = Math.min(100, securityHeaders.score + 5);
        }
        
        results.audits = {
            seo: { ...seo, category: '🔍 SEO' },
            security: { ...securityHeaders, category: '🔒 Security' },
            performance: { ...performance, category: '⚡ Performance' },
            accessibility: { ...accessibility, category: '♿ Accessibility' },
            cookies: { ...cookie, category: '🍪 Cookies & Privacy' }
        };
        
        // Calculate overall score
        const scores = [seo.score, securityHeaders.score, performance.score, accessibility.score, cookie.score];
        const overallScore = Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
        
        // Determine grade
        let grade;
        if (overallScore >= 90) grade = 'A';
        else if (overallScore >= 80) grade = 'B';
        else if (overallScore >= 70) grade = 'C';
        else if (overallScore >= 60) grade = 'D';
        else grade = 'F';
        
        results.overall = {
            score: overallScore,
            grade,
            summary: generateSummary(results.audits)
        };
        
    } catch (error) {
        results.error = error.message;
    }
    
    return results;
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
    if (critical.length > 0) {
        summary += `🚨 ${critical.length} critical issues: ${critical.slice(0, 3).join('; ')}`;
    }
    if (warnings.length > 0) {
        summary += `${critical.length > 0 ? '\n' : ''}⚠️ ${warnings.length} warnings: ${warnings.slice(0, 3).join('; ')}`;
    }
    if (!summary) summary = '✅ All audits passed!';
    
    return summary;
}

module.exports = { runCombinedAudit };

// CLI mode
if (require.main === module) {
    const url = process.argv[2];
    if (!url) {
        console.log('Usage: node combined_audit.js <url>');
        process.exit(1);
    }
    
    runCombinedAudit(url).then(result => {
        console.log(JSON.stringify(result, null, 2));
    }).catch(err => {
        console.error(JSON.stringify({ error: err.message }));
        process.exit(1);
    });
}
