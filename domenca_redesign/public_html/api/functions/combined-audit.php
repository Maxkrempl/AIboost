<?php
ob_start();
/**
 * BoostSuite — Combined Website Audit (PHP port)
 * Runs SEO, Security, Performance, Accessibility, and Cookie/GDPR audits
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    ob_clean();
echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Payment check — require API key or x402 payment
session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('combined_audit');

$input = json_decode(file_get_contents('php://input'), true);
$url = $input['url'] ?? '';

if (!$url) {
    http_response_code(400);
    ob_clean();
echo json_encode(['error' => 'URL is required']);
    exit;
}

// Validate URL
if (!filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    ob_clean();
echo json_encode(['error' => 'Invalid URL']);
    exit;
}

$startTime = microtime(true);

// ============= UTILITY FUNCTIONS =============

function fetchPage($url, $timeout = 10) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 5,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)',
        CURLOPT_ENCODING => '',
    ]);
    $html = curl_exec($ch);
    curl_close($ch);
    return $html ?: '';
}

function fetchWithHeaders($url, $timeout = 15) {
    $ch = curl_init($url);
    $startTime = microtime(true);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 5,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)',
        CURLOPT_ENCODING => 'gzip, deflate, br',
        CURLOPT_HEADER => true,
    ]);
    $response = curl_exec($ch);
    $loadTime = round((microtime(true) - $startTime) * 1000);
    $headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
    curl_close($ch);

    $headersStr = substr($response, 0, $headerSize);
    $html = substr($response, $headerSize);

    $headers = [];
    foreach (explode("\r\n", $headersStr) as $line) {
        if (strpos($line, ':') !== false) {
            [$key, $val] = explode(':', $line, 2);
            $headers[strtolower(trim($key))] = trim($val);
        }
    }

    return [
        'html' => $html,
        'headers' => $headers,
        'loadTime' => $loadTime,
        'size' => strlen($html),
    ];
}

// ============= AUDIT FUNCTIONS =============

function analyzeSEO($html) {
    $checks = [];
    $score = 0;

    // Title Tag
    if (preg_match('/<title[^>]*>([^<]+)<\/title>/i', $html, $m) && strlen($m[1]) > 10) {
        $checks[] = ['check' => 'Title Tag', 'status' => 'pass', 'detail' => substr($m[1], 0, 50) . '...'];
        $score += 15;
    } else {
        $checks[] = ['check' => 'Title Tag', 'status' => 'fail', 'detail' => 'Missing or too short'];
    }

    // Meta Description
    if (preg_match('/<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m) && strlen($m[1]) > 30) {
        $checks[] = ['check' => 'Meta Description', 'status' => 'pass', 'detail' => substr($m[1], 0, 60) . '...'];
        $score += 15;
    } else {
        $checks[] = ['check' => 'Meta Description', 'status' => 'fail', 'detail' => 'Missing or too short'];
    }

    // Canonical
    if (preg_match('/rel=["\']canonical["\']/', $html)) {
        $checks[] = ['check' => 'Canonical Tag', 'status' => 'pass', 'detail' => 'Canonical URL set'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Canonical Tag', 'status' => 'fail', 'detail' => 'No canonical tag'];
    }

    // Open Graph
    if (preg_match('/og:title|og:description|og:image/i', $html)) {
        $checks[] = ['check' => 'Open Graph', 'status' => 'pass', 'detail' => 'OG tags found'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Open Graph', 'status' => 'fail', 'detail' => 'No OG tags'];
    }

    // Structured Data
    if (preg_match('/application\/ld\+json/', $html) || preg_match('/itemscope|itemtype/i', $html)) {
        $checks[] = ['check' => 'Structured Data', 'status' => 'pass', 'detail' => 'Schema markup found'];
        $score += 15;
    } else {
        $checks[] = ['check' => 'Structured Data', 'status' => 'fail', 'detail' => 'No structured data'];
    }

    // H1 Tag
    preg_match_all('/<h1[^>]*>/i', $html, $h1s);
    $h1Count = count($h1s[0]);
    if ($h1Count === 1) {
        $checks[] = ['check' => 'H1 Tag', 'status' => 'pass', 'detail' => 'Exactly one H1'];
        $score += 10;
    } elseif ($h1Count === 0) {
        $checks[] = ['check' => 'H1 Tag', 'status' => 'fail', 'detail' => 'No H1 tag'];
    } else {
        $checks[] = ['check' => 'H1 Tag', 'status' => 'warn', 'detail' => "$h1Count H1 tags"];
        $score += 5;
    }

    // Image Alt Text
    preg_match_all('/<img[^>]*>/i', $html, $imgs);
    $imgsWithAlt = 0;
    foreach ($imgs[0] as $img) {
        if (preg_match('/alt=["\'][^"\']+["\']/i', $img)) $imgsWithAlt++;
    }
    if (count($imgs[0]) > 0) {
        $pct = round($imgsWithAlt / count($imgs[0]) * 100);
        if ($pct > 80) {
            $checks[] = ['check' => 'Image Alt Text', 'status' => 'pass', 'detail' => "$pct% have alt text"];
            $score += 10;
        } else {
            $checks[] = ['check' => 'Image Alt Text', 'status' => 'warn', 'detail' => "Only $pct% have alt text"];
            $score += 5;
        }
    }

    // Content Length
    if (preg_match('/<body[^>]*>([\s\S]*)<\/body>/i', $html, $body)) {
        $text = preg_replace('/<[^>]+>/', ' ', $body[1]);
        $text = preg_replace('/\s+/', ' ', trim($text));
        $wordCount = str_word_count($text);
        if ($wordCount > 500) {
            $checks[] = ['check' => 'Content Length', 'status' => 'pass', 'detail' => "$wordCount words"];
            $score += 15;
        } elseif ($wordCount > 200) {
            $checks[] = ['check' => 'Content Length', 'status' => 'warn', 'detail' => "$wordCount words (thin)"];
            $score += 7;
        } else {
            $checks[] = ['check' => 'Content Length', 'status' => 'fail', 'detail' => "$wordCount words (too thin)"];
        }
    }

    return ['score' => min(100, $score), 'checks' => $checks];
}

function checkSecurityHeaders($url) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_NOBODY => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 5,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)',
        CURLOPT_HEADER => true,
    ]);
    curl_exec($ch);
    $headers = [];
    $headerStr = curl_getinfo($ch, CURLINFO_HEADER_OUT);
    $allHeaders = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
    $response = curl_exec($ch);

    // Parse response headers
    $headerLines = explode("\r\n", substr($response, 0, $allHeaders));
    foreach ($headerLines as $line) {
        if (strpos($line, ':') !== false) {
            [$key, $val] = explode(':', $line, 2);
            $headers[strtolower(trim($key))] = trim($val);
        }
    }
    curl_close($ch);

    $checks = [];
    $score = 0;

    // HTTPS
    if (strpos($url, 'https://') === 0) {
        $checks[] = ['check' => 'HTTPS', 'status' => 'pass', 'detail' => 'Site uses HTTPS'];
        $score += 20;
    } else {
        $checks[] = ['check' => 'HTTPS', 'status' => 'fail', 'detail' => 'No HTTPS!'];
    }

    // Security headers
    $secHeaders = [
        'strict-transport-security' => ['label' => 'HSTS', 'points' => 15],
        'x-content-type-options' => ['label' => 'MIME Protection', 'points' => 10],
        'x-frame-options' => ['label' => 'Clickjacking Protection', 'points' => 10],
        'x-xss-protection' => ['label' => 'XSS Protection', 'points' => 10],
        'content-security-policy' => ['label' => 'CSP', 'points' => 15],
        'referrer-policy' => ['label' => 'Referrer Policy', 'points' => 5],
        'permissions-policy' => ['label' => 'Permissions Policy', 'points' => 5],
    ];

    foreach ($secHeaders as $name => $info) {
        if (isset($headers[$name])) {
            $checks[] = ['check' => $info['label'], 'status' => 'pass', 'detail' => 'Set'];
            $score += $info['points'];
        } else {
            $checks[] = ['check' => $info['label'], 'status' => 'fail', 'detail' => 'Not set'];
        }
    }

    // Server hidden
    if (!isset($headers['server'])) {
        $checks[] = ['check' => 'Server Hidden', 'status' => 'pass', 'detail' => 'Server info hidden'];
        $score += 5;
    } else {
        $checks[] = ['check' => 'Server Hidden', 'status' => 'warn', 'detail' => "Server: {$headers['server']}"];
    }

    // Powered-By hidden
    if (!isset($headers['x-powered-by'])) {
        $checks[] = ['check' => 'Powered-By Hidden', 'status' => 'pass', 'detail' => 'X-Powered-By hidden'];
        $score += 5;
    } else {
        $checks[] = ['check' => 'Powered-By Hidden', 'status' => 'warn', 'detail' => "Exposed: {$headers['x-powered-by']}"];
    }

    return ['score' => min(100, $score), 'checks' => $checks, '_headers' => $headers];
}

function analyzePerformance($url, $response) {
    $checks = [];
    $score = 0;
    $html = $response['html'];
    $headers = $response['headers'];
    $loadTime = $response['loadTime'];
    $size = $response['size'];

    // Load Time
    if ($loadTime < 1000) {
        $checks[] = ['check' => 'Load Time', 'status' => 'pass', 'detail' => "{$loadTime}ms - Excellent"];
        $score += 20;
    } elseif ($loadTime < 2000) {
        $checks[] = ['check' => 'Load Time', 'status' => 'pass', 'detail' => "{$loadTime}ms - Good"];
        $score += 15;
    } elseif ($loadTime < 3000) {
        $checks[] = ['check' => 'Load Time', 'status' => 'warn', 'detail' => "{$loadTime}ms - Needs work"];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Load Time', 'status' => 'fail', 'detail' => "{$loadTime}ms - Slow"];
        $score += 5;
    }

    // Page Size
    $sizeKB = $size / 1024;
    if ($sizeKB < 100) {
        $checks[] = ['check' => 'Page Size', 'status' => 'pass', 'detail' => round($sizeKB) . 'KB - Lean'];
        $score += 15;
    } elseif ($sizeKB < 500) {
        $checks[] = ['check' => 'Page Size', 'status' => 'pass', 'detail' => round($sizeKB) . 'KB - OK'];
        $score += 10;
    } elseif ($sizeKB < 1000) {
        $checks[] = ['check' => 'Page Size', 'status' => 'warn', 'detail' => round($sizeKB) . 'KB - Heavy'];
        $score += 5;
    } else {
        $checks[] = ['check' => 'Page Size', 'status' => 'fail', 'detail' => round($sizeKB) . 'KB - Very heavy'];
    }

    // Compression
    $encoding = $headers['content-encoding'] ?? '';
    if (strpos($encoding, 'gzip') !== false || strpos($encoding, 'br') !== false || strpos($encoding, 'deflate') !== false) {
        $checks[] = ['check' => 'Compression', 'status' => 'pass', 'detail' => strtoupper($encoding) . ' enabled'];
        $score += 15;
    } else {
        $checks[] = ['check' => 'Compression', 'status' => 'fail', 'detail' => 'No compression'];
    }

    // Caching
    $cacheControl = $headers['cache-control'] ?? '';
    if (strpos($cacheControl, 'max-age') !== false || isset($headers['expires'])) {
        $checks[] = ['check' => 'Caching', 'status' => 'pass', 'detail' => 'Cache headers set'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Caching', 'status' => 'fail', 'detail' => 'No cache headers'];
    }

    // Lazy Loading
    preg_match_all('/<img[^>]+>/i', $html, $imgs);
    $lazyLoaded = 0;
    foreach ($imgs[0] as $img) {
        if (preg_match('/loading=["\']lazy["\']/i', $img)) $lazyLoaded++;
    }
    if (count($imgs[0]) > 0) {
        $pct = round($lazyLoaded / count($imgs[0]) * 100);
        if ($pct > 50) {
            $checks[] = ['check' => 'Lazy Loading', 'status' => 'pass', 'detail' => "$pct% lazy-loaded"];
            $score += 10;
        } elseif ($lazyLoaded > 0) {
            $checks[] = ['check' => 'Lazy Loading', 'status' => 'warn', 'detail' => "Only $pct%"];
            $score += 5;
        } else {
            $checks[] = ['check' => 'Lazy Loading', 'status' => 'fail', 'detail' => 'No lazy loading'];
        }
    }

    // External Resources
    preg_match_all('/src=["\']https?:\/\/[^"\']+\.js/', $html, $scripts);
    preg_match_all('/href=["\']https?:\/\/[^"\']+\.css/', $html, $styles);
    $totalExternal = count($scripts[0]) + count($styles[0]);
    if ($totalExternal < 5) {
        $checks[] = ['check' => 'External Resources', 'status' => 'pass', 'detail' => "$totalExternal resources"];
        $score += 10;
    } elseif ($totalExternal < 15) {
        $checks[] = ['check' => 'External Resources', 'status' => 'warn', 'detail' => "$totalExternal resources"];
        $score += 5;
    } else {
        $checks[] = ['check' => 'External Resources', 'status' => 'fail', 'detail' => "$totalExternal - too many"];
    }

    return ['score' => min(100, $score), 'checks' => $checks];
}

function analyzeAccessibility($html) {
    $checks = [];
    $score = 0;

    // Language Attribute
    if (preg_match('/<html[^>]*lang=["\'][^"\']+["\']/i', $html)) {
        $checks[] = ['check' => 'Language Attribute', 'status' => 'pass', 'detail' => 'Set'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Language Attribute', 'status' => 'fail', 'detail' => 'Missing'];
    }

    // H1 Tag
    preg_match_all('/<h1[^>]*>/i', $html, $h1s);
    $h1Count = count($h1s[0]);
    if ($h1Count === 1) {
        $checks[] = ['check' => 'H1 Tag', 'status' => 'pass', 'detail' => 'Exactly one H1'];
        $score += 10;
    } elseif ($h1Count === 0) {
        $checks[] = ['check' => 'H1 Tag', 'status' => 'fail', 'detail' => 'No H1'];
    } else {
        $checks[] = ['check' => 'H1 Tag', 'status' => 'warn', 'detail' => "$h1Count H1s"];
        $score += 5;
    }

    // Image Alt Text
    preg_match_all('/<img[^>]*>/i', $html, $imgs);
    $imgsWithAlt = 0;
    foreach ($imgs[0] as $img) {
        if (preg_match('/alt=["\'][^"\']+["\']/i', $img)) $imgsWithAlt++;
    }
    if (count($imgs[0]) > 0) {
        $pct = round($imgsWithAlt / count($imgs[0]) * 100);
        if ($pct > 80) {
            $checks[] = ['check' => 'Image Alt Text', 'status' => 'pass', 'detail' => "$pct%"];
            $score += 15;
        } elseif ($pct > 50) {
            $checks[] = ['check' => 'Image Alt Text', 'status' => 'warn', 'detail' => "Only $pct%"];
            $score += 7;
        } else {
            $checks[] = ['check' => 'Image Alt Text', 'status' => 'fail', 'detail' => "$pct%"];
        }
    }

    // ARIA Landmarks
    preg_match_all('/<(header|nav|main|footer|aside|section|article)[^>]*>/i', $html, $semantic);
    preg_match_all('/role=["\'][^"\']+["\']/i', $html, $aria);
    $totalLandmarks = count($semantic[0]) + count($aria[0]);
    if ($totalLandmarks >= 3) {
        $checks[] = ['check' => 'ARIA Landmarks', 'status' => 'pass', 'detail' => "$totalLandmarks landmarks"];
        $score += 10;
    } elseif ($totalLandmarks > 0) {
        $checks[] = ['check' => 'ARIA Landmarks', 'status' => 'warn', 'detail' => "Only $totalLandmarks"];
        $score += 5;
    } else {
        $checks[] = ['check' => 'ARIA Landmarks', 'status' => 'fail', 'detail' => 'None found'];
    }

    // Form Labels
    preg_match_all('/<input[^>]*>/i', $html, $inputs);
    preg_match_all('/<label[^>]*>/i', $html, $labels);
    preg_match_all('/aria-label=["\'][^"\']+["\']/i', $html, $ariaLabels);
    $totalLabels = count($labels[0]) + count($ariaLabels[0]);
    if (count($inputs[0]) > 0) {
        if ($totalLabels >= count($inputs[0])) {
            $checks[] = ['check' => 'Form Labels', 'status' => 'pass', 'detail' => 'All inputs labeled'];
            $score += 10;
        } else {
            $checks[] = ['check' => 'Form Labels', 'status' => 'warn', 'detail' => count($inputs[0]) . " inputs, $totalLabels labels"];
            $score += 5;
        }
    }

    // Skip Navigation
    if (preg_match('/skip.*nav|jump.*content/i', $html)) {
        $checks[] = ['check' => 'Skip Navigation', 'status' => 'pass', 'detail' => 'Found'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Skip Navigation', 'status' => 'warn', 'detail' => 'Not found'];
    }

    // Zoom
    if (preg_match('/user-scalable\s*=\s*["\']?no/i', $html) || preg_match('/maximum-scale\s*=\s*1/i', $html)) {
        $checks[] = ['check' => 'Zoom Allowed', 'status' => 'fail', 'detail' => 'Zoom disabled!'];
    } else {
        $checks[] = ['check' => 'Zoom Allowed', 'status' => 'pass', 'detail' => 'Zoom allowed'];
        $score += 5;
    }

    return ['score' => min(100, $score), 'checks' => $checks];
}

function checkCookieBanner($html) {
    $checks = [];
    $score = 0;

    $bannerPatterns = [
        ['name' => 'CookieBot', 'pattern' => '/cookiebot|cookieconsent|cookie.?consent/i', 'points' => 15],
        ['name' => 'OneTrust', 'pattern' => '/onetrust|optanon/i', 'points' => 15],
        ['name' => 'GDPR Cookie Consent', 'pattern' => '/gdpr.?cookie|cookie.?notice|cookie.?policy/i', 'points' => 15],
        ['name' => 'CookieYes', 'pattern' => '/cookieyes|ckyconsent/i', 'points' => 15],
        ['name' => 'Iubenda', 'pattern' => '/iubenda/i', 'points' => 15],
        ['name' => 'Generic cookie banner', 'pattern' => '/cookie.*accept|accept.*cookie|cookie.*agree|we.*use.*cookie/i', 'points' => 10],
    ];

    $bannerFound = false;
    foreach ($bannerPatterns as $bp) {
        if (preg_match($bp['pattern'], $html)) {
            $checks[] = ['check' => $bp['name'], 'status' => 'pass', 'detail' => "{$bp['name']} detected"];
            $score += $bp['points'];
            $bannerFound = true;
            break;
        }
    }

    if (!$bannerFound) {
        $checks[] = ['check' => 'Cookie Banner', 'status' => 'fail', 'detail' => 'No cookie consent banner detected'];
    }

    // Cookie Categories
    $catPatterns = [
        '/necessary|essential|strictly/i',
        '/analytics|statistics|performance/i',
        '/marketing|advertising|targeting/i',
    ];
    $categoriesFound = 0;
    foreach ($catPatterns as $pat) {
        if (preg_match($pat, $html)) $categoriesFound++;
    }
    if ($categoriesFound >= 3) {
        $checks[] = ['check' => 'Cookie Categories', 'status' => 'pass', 'detail' => "$categoriesFound categories"];
        $score += 15;
    } elseif ($categoriesFound > 0) {
        $checks[] = ['check' => 'Cookie Categories', 'status' => 'warn', 'detail' => "Only $categoriesFound categories"];
        $score += 7;
    } else {
        $checks[] = ['check' => 'Cookie Categories', 'status' => 'fail', 'detail' => 'No cookie categories'];
    }

    // Privacy Policy
    if (preg_match('/privacy.?policy|datenschutz|politica.?privacy/i', $html)) {
        $checks[] = ['check' => 'Privacy Policy', 'status' => 'pass', 'detail' => 'Privacy policy found'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Privacy Policy', 'status' => 'fail', 'detail' => 'No privacy policy'];
    }

    // GDPR
    if (preg_match('/GDPR|DSGVO|RODO|osebni podatki|zaštita podataka/i', $html)) {
        $checks[] = ['check' => 'GDPR Compliance', 'status' => 'pass', 'detail' => 'GDPR references found'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'GDPR Compliance', 'status' => 'fail', 'detail' => 'No GDPR references'];
    }

    // Opt-out
    if (preg_match('/opt.?out|unsubscribe|manage.?cookie|cookie.?settings/i', $html)) {
        $checks[] = ['check' => 'Opt-out Mechanism', 'status' => 'pass', 'detail' => 'Cookie management available'];
        $score += 10;
    } else {
        $checks[] = ['check' => 'Opt-out Mechanism', 'status' => 'warn', 'detail' => 'No cookie management'];
    }

    return ['score' => min(100, $score), 'checks' => $checks];
}

function checkMixedContent($url) {
    $html = fetchPage($url);
    preg_match_all('/src=["\']http:\/\/[^"\']+["\']/', $html, $httpSrc);
    preg_match_all('/href=["\']http:\/\/[^"\']+["\']/', $html, $httpHref);
    $total = count($httpSrc[0]) + count($httpHref[0]);
    return ['hasMixed' => $total > 0, 'count' => $total];
}

function generateSummary($audits) {
    $critical = [];
    $warnings = [];
    foreach ($audits as $audit) {
        foreach ($audit['checks'] as $check) {
            if ($check['status'] === 'fail') $critical[] = "{$audit['category']}: {$check['check']}";
            if ($check['status'] === 'warn') $warnings[] = "{$audit['category']}: {$check['check']}";
        }
    }
    $summary = '';
    if ($critical) $summary .= '🚨 ' . count($critical) . ' critical issues';
    if ($warnings) $summary .= ($critical ? ' | ' : '') . '⚠️ ' . count($warnings) . ' warnings';
    if (!$summary) $summary = '✅ All audits passed!';
    return $summary;
}

// ============= MAIN =============

try {
    $html = fetchPage($url);
    $response = fetchWithHeaders($url);

    $seo = analyzeSEO($html);
    $cookies = checkCookieBanner($html);
    $accessibility = analyzeAccessibility($html);
    $performance = analyzePerformance($url, $response);
    $secResult = checkSecurityHeaders($url);
    $securityHeaders = ['score' => $secResult['score'], 'checks' => $secResult['checks']];
    $mixedContent = checkMixedContent($url);

    // Merge mixed content into security
    if ($mixedContent['hasMixed']) {
        $securityHeaders['checks'][] = ['check' => 'Mixed Content', 'status' => 'fail', 'detail' => "{$mixedContent['count']} HTTP resources on HTTPS page"];
        $securityHeaders['score'] = max(0, $securityHeaders['score'] - 20);
    } else {
        $securityHeaders['checks'][] = ['check' => 'Mixed Content', 'status' => 'pass', 'detail' => 'No mixed content'];
        $securityHeaders['score'] = min(100, $securityHeaders['score'] + 5);
    }

    $audits = [
        'seo' => ['score' => $seo['score'], 'checks' => $seo['checks'], 'category' => '🔍 SEO'],
        'security' => ['score' => $securityHeaders['score'], 'checks' => $securityHeaders['checks'], 'category' => '🔒 Security'],
        'performance' => ['score' => $performance['score'], 'checks' => $performance['checks'], 'category' => '⚡ Performance'],
        'accessibility' => ['score' => $accessibility['score'], 'checks' => $accessibility['checks'], 'category' => '♿ Accessibility'],
        'cookies' => ['score' => $cookies['score'], 'checks' => $cookies['checks'], 'category' => '🍪 Cookies & Privacy'],
    ];

    $scores = array_column($audits, 'score');
    $overallScore = round(array_sum($scores) / count($scores));

    if ($overallScore >= 90) $grade = 'A';
    elseif ($overallScore >= 80) $grade = 'B';
    elseif ($overallScore >= 70) $grade = 'C';
    elseif ($overallScore >= 60) $grade = 'D';
    else $grade = 'F';

    $duration = round((microtime(true) - $startTime) * 1000);

    ob_clean();
    echo json_encode([
        'url' => $url,
        'timestamp' => date('c'),
        'duration' => "{$duration}ms",
        'audits' => $audits,
        'overall' => [
            'score' => $overallScore,
            'grade' => $grade,
            'summary' => generateSummary($audits),
        ],
    ], JSON_UNESCAPED_UNICODE | JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_AMP);

} catch (Exception $e) {
    http_response_code(500);
    ob_clean();
echo json_encode(['error' => $e->getMessage() ?: 'Audit failed']);
}
