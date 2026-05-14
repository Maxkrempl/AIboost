// Performance Audit Tool for BoostSuite
// Checks: page size, resource count, compression, caching, image optimization

const https = require('https');
const http = require('http');
const { URL } = require('url');

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
            
            // Follow redirects
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

function analyzePerformance(url, response) {
    const checks = [];
    let score = 0;
    const { html, headers, loadTime, size } = response;
    
    // Page load time
    if (loadTime < 1000) {
        checks.push({ check: 'Load Time', status: 'pass', detail: `${loadTime}ms - Excellent` });
        score += 20;
    } else if (loadTime < 2000) {
        checks.push({ check: 'Load Time', status: 'pass', detail: `${loadTime}ms - Good` });
        score += 15;
    } else if (loadTime < 3000) {
        checks.push({ check: 'Load Time', status: 'warn', detail: `${loadTime}ms - Needs improvement` });
        score += 10;
    } else {
        checks.push({ check: 'Load Time', status: 'fail', detail: `${loadTime}ms - Slow` });
        score += 5;
    }
    
    // Page size
    const sizeKB = size / 1024;
    if (sizeKB < 100) {
        checks.push({ check: 'Page Size', status: 'pass', detail: `${sizeKB.toFixed(0)}KB - Lean` });
        score += 15;
    } else if (sizeKB < 500) {
        checks.push({ check: 'Page Size', status: 'pass', detail: `${sizeKB.toFixed(0)}KB - Acceptable` });
        score += 10;
    } else if (sizeKB < 1000) {
        checks.push({ check: 'Page Size', status: 'warn', detail: `${sizeKB.toFixed(0)}KB - Heavy` });
        score += 5;
    } else {
        checks.push({ check: 'Page Size', status: 'fail', detail: `${sizeKB.toFixed(0)}KB - Very heavy` });
    }
    
    // Gzip compression
    const encoding = headers['content-encoding'] || '';
    if (encoding.includes('gzip') || encoding.includes('br') || encoding.includes('deflate')) {
        checks.push({ check: 'Compression', status: 'pass', detail: `${encoding.toUpperCase()} compression enabled` });
        score += 15;
    } else {
        checks.push({ check: 'Compression', status: 'fail', detail: 'No compression detected' });
    }
    
    // Caching headers
    const cacheControl = headers['cache-control'] || '';
    const expires = headers['expires'] || '';
    
    if (cacheControl.includes('max-age') || expires) {
        checks.push({ check: 'Browser Caching', status: 'pass', detail: 'Cache headers set' });
        score += 10;
    } else {
        checks.push({ check: 'Browser Caching', status: 'fail', detail: 'No cache headers' });
    }
    
    // Image analysis
    const images = html.match(/<img[^>]+>/gi) || [];
    const totalImages = images.length;
    
    let lazyLoaded = 0;
    let missingAlt = 0;
    let largeImages = 0;
    
    for (const img of images) {
        if (/loading=["']lazy["']/.test(img)) lazyLoaded++;
        if (!/alt=["'][^"']+["']/.test(img)) missingAlt++;
        // Check for large image dimensions in attributes
        const width = img.match(/width=["'](\d+)["']/);
        const height = img.match(/height=["'](\d+)["']/);
        if (width && parseInt(width[1]) > 1920) largeImages++;
        if (height && parseInt(height[1]) > 1080) largeImages++;
    }
    
    if (totalImages > 0) {
        const lazyPercent = (lazyLoaded / totalImages * 100).toFixed(0);
        if (lazyPercent > 50) {
            checks.push({ check: 'Lazy Loading', status: 'pass', detail: `${lazyPercent}% images lazy-loaded` });
            score += 10;
        } else if (lazyLoaded > 0) {
            checks.push({ check: 'Lazy Loading', status: 'warn', detail: `Only ${lazyPercent}% lazy-loaded` });
            score += 5;
        } else {
            checks.push({ check: 'Lazy Loading', status: 'fail', detail: 'No lazy loading' });
        }
        
        if (missingAlt > 0) {
            checks.push({ check: 'Image Alt Text', status: 'warn', detail: `${missingAlt}/${totalImages} images missing alt` });
        } else {
            checks.push({ check: 'Image Alt Text', status: 'pass', detail: 'All images have alt text' });
            score += 5;
        }
    }
    
    // External resources analysis
    const externalScripts = (html.match(/src=["']https?:\/\/[^"']+\.js/g) || []).length;
    const externalStyles = (html.match(/href=["']https?:\/\/[^"']+\.css/g) || []).length;
    const totalExternal = externalScripts + externalStyles;
    
    if (totalExternal < 5) {
        checks.push({ check: 'External Resources', status: 'pass', detail: `${totalExternal} external resources` });
        score += 10;
    } else if (totalExternal < 15) {
        checks.push({ check: 'External Resources', status: 'warn', detail: `${totalExternal} external resources` });
        score += 5;
    } else {
        checks.push({ check: 'External Resources', status: 'fail', detail: `${totalExternal} external resources - too many` });
    }
    
    // Preconnect/preload hints
    if (/rel=["']preconnect["']/.test(html) || /rel=["']preload["']/.test(html)) {
        checks.push({ check: 'Resource Hints', status: 'pass', detail: 'Preconnect/preload hints found' });
        score += 5;
    } else {
        checks.push({ check: 'Resource Hints', status: 'warn', detail: 'No preconnect/preload hints' });
    }
    
    // Viewport meta
    if (/viewport/.test(html)) {
        checks.push({ check: 'Viewport Meta', status: 'pass', detail: 'Viewport configured' });
        score += 5;
    } else {
        checks.push({ check: 'Viewport Meta', status: 'fail', detail: 'No viewport meta tag' });
    }
    
    return { score: Math.min(100, score), checks };
}

module.exports = { fetchWithHeaders, analyzePerformance };

// CLI mode
if (require.main === module) {
    const url = process.argv[2];
    if (!url) {
        console.log('Usage: node performance_audit.js <url>');
        process.exit(1);
    }
    
    fetchWithHeaders(url)
        .then(response => {
            const result = analyzePerformance(url, response);
            console.log(JSON.stringify(result, null, 2));
        })
        .catch(err => {
            console.error(JSON.stringify({ error: err.message }));
            process.exit(1);
        });
}
