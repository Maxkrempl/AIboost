// Accessibility Audit Tool for BoostSuite
// Checks: WCAG compliance, ARIA, contrast, keyboard navigation, screen reader support

const https = require('https');
const http = require('http');
const { URL } = require('url');

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

function analyzeAccessibility(html) {
    const checks = [];
    let score = 0;
    
    // Language attribute
    const langMatch = html.match(/<html[^>]*lang=["']([^"']+)["']/i);
    if (langMatch) {
        checks.push({ check: 'Language Attribute', status: 'pass', detail: `lang="${langMatch[1]}"` });
        score += 10;
    } else {
        checks.push({ check: 'Language Attribute', status: 'fail', detail: 'No lang attribute on <html>' });
    }
    
    // Heading hierarchy
    const headings = html.match(/<h[1-6][^>]*>/gi) || [];
    const h1Count = (html.match(/<h1[^>]*>/gi) || []).length;
    
    if (h1Count === 1) {
        checks.push({ check: 'H1 Tag', status: 'pass', detail: 'Exactly one H1 tag' });
        score += 10;
    } else if (h1Count === 0) {
        checks.push({ check: 'H1 Tag', status: 'fail', detail: 'No H1 tag found' });
    } else {
        checks.push({ check: 'H1 Tag', status: 'warn', detail: `${h1Count} H1 tags (should be 1)` });
        score += 5;
    }
    
    if (headings.length > 0) {
        // Check for skipped levels
        const levels = headings.map(h => parseInt(h.match(/<h(\d)/)[1]));
        let skippedLevels = 0;
        for (let i = 1; i < levels.length; i++) {
            if (levels[i] > levels[i-1] + 1) skippedLevels++;
        }
        
        if (skippedLevels === 0) {
            checks.push({ check: 'Heading Hierarchy', status: 'pass', detail: `${headings.length} headings, no skipped levels` });
            score += 10;
        } else {
            checks.push({ check: 'Heading Hierarchy', status: 'warn', detail: `${skippedLevels} skipped heading levels` });
            score += 5;
        }
    } else {
        checks.push({ check: 'Heading Hierarchy', status: 'fail', detail: 'No headings found' });
    }
    
    // Images with alt text
    const images = html.match(/<img[^>]*>/gi) || [];
    const imagesWithAlt = images.filter(img => /alt=["'][^"']+["']/i.test(img));
    const totalImages = images.length;
    
    if (totalImages > 0) {
        const altPercent = (imagesWithAlt.length / totalImages * 100).toFixed(0);
        if (altPercent > 90) {
            checks.push({ check: 'Image Alt Text', status: 'pass', detail: `${altPercent}% images have alt text` });
            score += 15;
        } else if (altPercent > 50) {
            checks.push({ check: 'Image Alt Text', status: 'warn', detail: `Only ${altPercent}% images have alt text` });
            score += 7;
        } else {
            checks.push({ check: 'Image Alt Text', status: 'fail', detail: `${altPercent}% images have alt text` });
        }
    } else {
        checks.push({ check: 'Image Alt Text', status: 'pass', detail: 'No images to check' });
        score += 15;
    }
    
    // ARIA landmarks
    const ariaLandmarks = html.match(/role=["'](banner|navigation|main|contentinfo|complementary|search|form|region)["']/gi) || [];
    const semanticLandmarks = html.match(/<(header|nav|main|footer|aside|section|article)[^>]*>/gi) || [];
    const totalLandmarks = ariaLandmarks.length + semanticLandmarks.length;
    
    if (totalLandmarks >= 3) {
        checks.push({ check: 'ARIA Landmarks', status: 'pass', detail: `${totalLandmarks} landmarks found` });
        score += 10;
    } else if (totalLandmarks > 0) {
        checks.push({ check: 'ARIA Landmarks', status: 'warn', detail: `Only ${totalLandmarks} landmarks` });
        score += 5;
    } else {
        checks.push({ check: 'ARIA Landmarks', status: 'fail', detail: 'No ARIA landmarks' });
    }
    
    // Form labels
    const inputs = html.match(/<input[^>]*>/gi) || [];
    const labels = html.match(/<label[^>]*>/gi) || [];
    const ariaLabels = html.match(/aria-label=["'][^"']+["']/gi) || [];
    const ariaLabelledby = html.match(/aria-labelledby=["'][^"']+["']/gi) || [];
    
    const totalInputs = inputs.length;
    const totalLabels = labels.length + ariaLabels.length + ariaLabelledby.length;
    
    if (totalInputs > 0) {
        if (totalLabels >= totalInputs) {
            checks.push({ check: 'Form Labels', status: 'pass', detail: 'All form inputs have labels' });
            score += 10;
        } else {
            checks.push({ check: 'Form Labels', status: 'warn', detail: `${totalInputs} inputs, ${totalLabels} labels` });
            score += 5;
        }
    } else {
        checks.push({ check: 'Form Labels', status: 'pass', detail: 'No forms to check' });
        score += 10;
    }
    
    // Skip navigation link
    if (/skip.*nav|jump.*content|skip.*main/i.test(html)) {
        checks.push({ check: 'Skip Navigation', status: 'pass', detail: 'Skip navigation link found' });
        score += 10;
    } else {
        checks.push({ check: 'Skip Navigation', status: 'warn', detail: 'No skip navigation link' });
    }
    
    // Focus indicators
    if (/outline.*none|outline.*0/i.test(html)) {
        checks.push({ check: 'Focus Indicators', status: 'warn', detail: 'Outline may be disabled' });
    } else {
        checks.push({ check: 'Focus Indicators', status: 'pass', detail: 'Focus indicators not disabled' });
        score += 5;
    }
    
    // Color contrast (basic check - look for inline colors)
    const inlineColors = html.match(/color:\s*#[0-9a-f]{3,6}/gi) || [];
    const bgColors = html.match(/background(?:-color)?:\s*#[0-9a-f]{3,6}/gi) || [];
    
    if (inlineColors.length > 0 && bgColors.length > 0) {
        checks.push({ check: 'Color Usage', status: 'warn', detail: 'Inline colors found - verify contrast manually' });
    } else {
        checks.push({ check: 'Color Usage', status: 'pass', detail: 'CSS-based color management' });
        score += 5;
    }
    
    // Tables
    const tables = html.match(/<table[^>]*>/gi) || [];
    const thElements = html.match(/<th[^>]*>/gi) || [];
    const captionElements = html.match(/<caption[^>]*>/gi) || [];
    
    if (tables.length > 0) {
        if (thElements.length > 0 || captionElements.length > 0) {
            checks.push({ check: 'Data Tables', status: 'pass', detail: 'Tables have headers/captions' });
            score += 5;
        } else {
            checks.push({ check: 'Data Tables', status: 'warn', detail: 'Tables missing headers' });
        }
    }
    
    // Viewport
    if (/user-scalable\s*=\s*["']?no/i.test(html) || /maximum-scale\s*=\s*1/i.test(html)) {
        checks.push({ check: 'Zoom Allowed', status: 'fail', detail: 'Zoom is disabled!' });
    } else {
        checks.push({ check: 'Zoom Allowed', status: 'pass', detail: 'Zoom is allowed' });
        score += 5;
    }
    
    return { score: Math.min(100, score), checks };
}

module.exports = { analyzeAccessibility };

// CLI mode
if (require.main === module) {
    const url = process.argv[2];
    if (!url) {
        console.log('Usage: node accessibility_audit.js <url>');
        process.exit(1);
    }
    
    fetchPage(url)
        .then(html => {
            const result = analyzeAccessibility(html);
            console.log(JSON.stringify(result, null, 2));
        })
        .catch(err => {
            console.error(JSON.stringify({ error: err.message }));
            process.exit(1);
        });
}
