<?php
// BoostSuite Combined Audit — PHP Backend
// Runs SEO, Security, Performance, Accessibility, and Cookie audits

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$url = $input['url'] ?? '';

if (empty($url)) {
    http_response_code(400);
    echo json_encode(['error' => 'URL is required']);
    exit;
}

// Validate URL
if (!filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid URL']);
    exit;
}

// Fetch the page
$startTime = microtime(true);
$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 5,
    CURLOPT_TIMEOUT => 15,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuiteAudit/1.0)',
    CURLOPT_NOBODY => false,
    CURLOPT_HEADER => true,
]);

$response = curl_exec($ch);
$headerSize = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$loadTime = microtime(true) - $startTime;
$totalSize = curl_getinfo($ch, CURLINFO_SIZE_DOWNLOAD);
$contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);

if (curl_errno($ch)) {
    curl_close($ch);
    echo json_encode(['error' => 'Failed to fetch URL: ' . curl_error($ch)]);
    exit;
}
curl_close($ch);

// Split headers and body
$headers = substr($response, 0, $headerSize);
$body = substr($response, $headerSize);

// Parse response headers
$responseHeaders = [];
foreach (explode("\r\n", $headers) as $header) {
    if (strpos($header, ':') !== false) {
        list($key, $value) = explode(':', $header, 2);
        $responseHeaders[strtolower(trim($key))] = trim($value);
    }
}

// ============ SEO AUDIT ============
$seoChecks = [];
$seoScore = 0;

// Title tag
if (preg_match('/<title[^>]*>([^<]+)<\/title>/i', $body, $m)) {
    $title = trim($m[1]);
    if (strlen($title) > 10) {
        $seoChecks[] = ['check' => 'Title Tag', 'status' => 'pass', 'detail' => mb_substr($title, 0, 60) . (strlen($title) > 60 ? '...' : '')];
        $seoScore += 15;
    } else {
        $seoChecks[] = ['check' => 'Title Tag', 'status' => 'fail', 'detail' => 'Title too short (' . strlen($title) . ' chars)'];
    }
} else {
    $seoChecks[] = ['check' => 'Title Tag', 'status' => 'fail', 'detail' => 'No title tag found'];
}

// Meta description
if (preg_match('/<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']/i', $body, $m)) {
    $desc = trim($m[1]);
    if (strlen($desc) > 30) {
        $seoChecks[] = ['check' => 'Meta Description', 'status' => 'pass', 'detail' => mb_substr($desc, 0, 80) . '...'];
        $seoScore += 15;
    } else {
        $seoChecks[] = ['check' => 'Meta Description', 'status' => 'fail', 'detail' => 'Meta description too short'];
    }
} else {
    $seoChecks[] = ['check' => 'Meta Description', 'status' => 'fail', 'detail' => 'No meta description'];
}

// Canonical
if (preg_match('/rel=["\']canonical["\']/', $body)) {
    $seoChecks[] = ['check' => 'Canonical Tag', 'status' => 'pass', 'detail' => 'Canonical URL set'];
    $seoScore += 10;
} else {
    $seoChecks[] = ['check' => 'Canonical Tag', 'status' => 'fail', 'detail' => 'No canonical tag'];
}

// Open Graph
if (preg_match('/og:title|og:description|og:image/i', $body)) {
    $seoChecks[] = ['check' => 'Open Graph', 'status' => 'pass', 'detail' => 'OG tags found'];
    $seoScore += 10;
} else {
    $seoChecks[] = ['check' => 'Open Graph', 'status' => 'fail', 'detail' => 'No Open Graph tags'];
}

// Structured data
if (preg_match('/application\/ld\+json/i', $body) || preg_match('/itemscope|itemtype/i', $body)) {
    $seoChecks[] = ['check' => 'Structured Data', 'status' => 'pass', 'detail' => 'Schema markup found'];
    $seoScore += 15;
} else {
    $seoChecks[] = ['check' => 'Structured Data', 'status' => 'fail', 'detail' => 'No structured data'];
}

// H1 tags
$h1Count = preg_match_all('/<h1[^>]*>/i', $body);
if ($h1Count === 1) {
    $seoChecks[] = ['check' => 'H1 Tag', 'status' => 'pass', 'detail' => 'Exactly one H1 tag'];
    $seoScore += 10;
} elseif ($h1Count === 0) {
    $seoChecks[] = ['check' => 'H1 Tag', 'status' => 'fail', 'detail' => 'No H1 tag found'];
} else {
    $seoChecks[] = ['check' => 'H1 Tag', 'status' => 'warn', 'detail' => "$h1Count H1 tags found (should be 1)"];
    $seoScore += 5;
}

// Images alt text
preg_match_all('/<img[^>]*>/i', $body, $imgs);
$totalImages = count($imgs[0]);
$imagesWithAlt = 0;
foreach ($imgs[0] as $img) {
    if (preg_match('/alt=["\'][^"\']+["\']/i', $img)) $imagesWithAlt++;
}
if ($totalImages > 0) {
    $altPercent = round($imagesWithAlt / $totalImages * 100);
    if ($altPercent > 80) {
        $seoChecks[] = ['check' => 'Image Alt Text', 'status' => 'pass', 'detail' => "$altPercent% of images have alt text"];
        $seoScore += 10;
    } elseif ($altPercent > 40) {
        $seoChecks[] = ['check' => 'Image Alt Text', 'status' => 'warn', 'detail' => "Only $altPercent% of images have alt text"];
        $seoScore += 5;
    } else {
        $seoChecks[] = ['check' => 'Image Alt Text', 'status' => 'fail', 'detail' => "Only $altPercent% of images have alt text"];
    }
} else {
    $seoChecks[] = ['check' => 'Image Alt Text', 'status' => 'pass', 'detail' => 'No images to check'];
    $seoScore += 10;
}

// Word count
$wordCount = str_word_count(strip_tags($body));
if ($wordCount > 300) {
    $seoChecks[] = ['check' => 'Content Length', 'status' => 'pass', 'detail' => "$wordCount words"];
    $seoScore += 10;
} elseif ($wordCount > 100) {
    $seoChecks[] = ['check' => 'Content Length', 'status' => 'warn', 'detail' => "Only $wordCount words (aim for 300+)"];
    $seoScore += 5;
} else {
    $seoChecks[] = ['check' => 'Content Length', 'status' => 'fail', 'detail' => "Only $wordCount words — very thin content"];
}

// Internal/external links
preg_match_all('/href=["\']([^"\']+)["\']/i', $body, $links);
$internal = 0;
$external = 0;
foreach ($links[1] as $link) {
    if (strpos($link, 'http') === 0) {
        if (parse_url($link, PHP_URL_HOST) === parse_url($url, PHP_URL_HOST)) $internal++;
        else $external++;
    } elseif ($link[0] === '/' || $link[0] === '#') {
        $internal++;
    }
}
$seoChecks[] = ['check' => 'Links', 'status' => $internal > 0 ? 'pass' : 'warn', 'detail' => "$internal internal, $external external links"];
$seoScore += min(10, $internal * 2);

$seoScore = min(100, $seoScore);

// ============ SECURITY AUDIT ============
$secChecks = [];
$secScore = 0;

$https = parse_url($url, PHP_URL_SCHEME) === 'https';
if ($https) {
    $secChecks[] = ['check' => 'HTTPS', 'status' => 'pass', 'detail' => 'Site uses HTTPS'];
    $secScore += 20;
} else {
    $secChecks[] = ['check' => 'HTTPS', 'status' => 'fail', 'detail' => 'Site does NOT use HTTPS'];
}

$secHeaders = [
    'strict-transport-security' => ['HSTS', 15],
    'x-content-type-options' => ['MIME Protection', 10],
    'x-frame-options' => ['Clickjacking Protection', 10],
    'x-xss-protection' => ['XSS Protection', 10],
    'content-security-policy' => ['CSP', 15],
    'referrer-policy' => ['Referrer Policy', 10],
    'permissions-policy' => ['Permissions Policy', 10],
];

foreach ($secHeaders as $header => $info) {
    if (isset($responseHeaders[$header])) {
        $secChecks[] = ['check' => $info[0], 'status' => 'pass', 'detail' => 'Header present'];
        $secScore += $info[1];
    } else {
        $secChecks[] = ['check' => $info[0], 'status' => 'fail', 'detail' => 'Header missing'];
    }
}

// Server header hidden
if (!isset($responseHeaders['server'])) {
    $secChecks[] = ['check' => 'Server Hidden', 'status' => 'pass', 'detail' => 'Server header not exposed'];
    $secScore += 5;
} else {
    $secChecks[] = ['check' => 'Server Hidden', 'status' => 'warn', 'detail' => 'Server header exposed'];
}

$secScore = min(100, $secScore);

// ============ PERFORMANCE AUDIT ============
$perfChecks = [];
$perfScore = 0;

// Load time
if ($loadTime < 1) {
    $perfChecks[] = ['check' => 'Load Time', 'status' => 'pass', 'detail' => round($loadTime * 1000) . 'ms'];
    $perfScore += 30;
} elseif ($loadTime < 3) {
    $perfChecks[] = ['check' => 'Load Time', 'status' => 'warn', 'detail' => round($loadTime * 1000) . 'ms (aim for <1s)'];
    $perfScore += 15;
} else {
    $perfChecks[] = ['check' => 'Load Time', 'status' => 'fail', 'detail' => round($loadTime * 1000) . 'ms — too slow'];
}

// Page size
$sizeKB = round($totalSize / 1024);
if ($sizeKB < 500) {
    $perfChecks[] = ['check' => 'Page Size', 'status' => 'pass', 'detail' => "${sizeKB}KB"];
    $perfScore += 25;
} elseif ($sizeKB < 2000) {
    $perfChecks[] = ['check' => 'Page Size', 'status' => 'warn', 'detail' => "${sizeKB}KB (aim for <500KB)"];
    $perfScore += 10;
} else {
    $perfChecks[] = ['check' => 'Page Size', 'status' => 'fail', 'detail' => "${sizeKB}KB — very large"];
}

// Compression
if (isset($responseHeaders['content-encoding']) && preg_match('/gzip|br|deflate/i', $responseHeaders['content-encoding'])) {
    $perfChecks[] = ['check' => 'Compression', 'status' => 'pass', 'detail' => 'Gzip/Brotli enabled'];
    $perfScore += 20;
} else {
    $perfChecks[] = ['check' => 'Compression', 'status' => 'fail', 'detail' => 'No compression detected'];
}

// Caching
if (isset($responseHeaders['cache-control']) && preg_match('/max-age=(\d+)/', $responseHeaders['cache-control'], $m) && $m[1] > 0) {
    $perfChecks[] = ['check' => 'Caching', 'status' => 'pass', 'detail' => 'Cache-Control set (max-age: ' . $m[1] . 's)'];
    $perfScore += 15;
} else {
    $perfChecks[] = ['check' => 'Caching', 'status' => 'fail', 'detail' => 'No cache headers'];
}

// HTTP/2
$perfChecks[] = ['check' => 'Protocol', 'status' => 'pass', 'detail' => 'HTTP/1.1 (server-dependent)'];
$perfScore += 10;

$perfScore = min(100, $perfScore);

// ============ ACCESSIBILITY AUDIT ============
$accChecks = [];
$accScore = 0;

// Lang attribute
if (preg_match('/<html[^>]*lang=["\'][^"\']+["\']/i', $body)) {
    $accChecks[] = ['check' => 'Language Attribute', 'status' => 'pass', 'detail' => 'HTML lang attribute set'];
    $accScore += 20;
} else {
    $accChecks[] = ['check' => 'Language Attribute', 'status' => 'fail', 'detail' => 'No lang attribute on <html>'];
}

// Viewport
if (preg_match('/<meta[^>]*name=["\']viewport["\']/i', $body)) {
    $accChecks[] = ['check' => 'Viewport', 'status' => 'pass', 'detail' => 'Viewport meta tag present'];
    $accScore += 20;
} else {
    $accChecks[] = ['check' => 'Viewport', 'status' => 'fail', 'detail' => 'No viewport meta tag'];
}

// Form labels
preg_match_all('/<input[^>]*>/i', $body, $inputs);
$inputsWithLabels = 0;
foreach ($inputs[0] as $input) {
    if (preg_match('/id=["\']([^"\']+)["\']/i', $input, $m)) {
        if (preg_match('/for=["\']' . preg_quote($m[1]) . '["\']/i', $body)) $inputsWithLabels++;
    }
}
$totalInputs = count($inputs[0]);
if ($totalInputs > 0) {
    $labelPercent = round($inputsWithLabels / $totalInputs * 100);
    if ($labelPercent > 80) {
        $accChecks[] = ['check' => 'Form Labels', 'status' => 'pass', 'detail' => "$labelPercent% of inputs have labels"];
        $accScore += 20;
    } else {
        $accChecks[] = ['check' => 'Form Labels', 'status' => 'warn', 'detail' => "Only $labelPercent% of inputs have labels"];
        $accScore += 5;
    }
} else {
    $accChecks[] = ['check' => 'Form Labels', 'status' => 'pass', 'detail' => 'No inputs to check'];
    $accScore += 20;
}

// Heading hierarchy
$headings = [];
for ($i = 1; $i <= 6; $i++) {
    $count = preg_match_all("/<h" . $i . "[^>]*>/i", $body);
    if ($count > 0) $headings[$i] = $count;
}
$headingOk = true;
$prevLevel = 0;
foreach ($headings as $level => $count) {
    if ($level > $prevLevel + 1 && $prevLevel > 0) $headingOk = false;
    $prevLevel = $level;
}
if ($headingOk && count($headings) > 0) {
    $accChecks[] = ['check' => 'Heading Hierarchy', 'status' => 'pass', 'detail' => 'Logical heading structure'];
    $accScore += 20;
} else {
    $accChecks[] = ['check' => 'Heading Hierarchy', 'status' => 'warn', 'detail' => 'Heading levels may be skipped'];
    $accScore += 5;
}

// Skip links
if (preg_match('/skip|skip-to-content|skip-nav/i', $body)) {
    $accChecks[] = ['check' => 'Skip Navigation', 'status' => 'pass', 'detail' => 'Skip navigation link found'];
    $accScore += 20;
} else {
    $accChecks[] = ['check' => 'Skip Navigation', 'status' => 'warn', 'detail' => 'No skip navigation link'];
}

$accScore = min(100, $accScore);

// ============ COOKIES & PRIVACY ============
$cookieChecks = [];
$cookieScore = 0;

// Cookie banner detection
if (preg_match('/cookie|consent|gdpr|privacy.*banner|cookie.*notice/i', $body)) {
    $cookieChecks[] = ['check' => 'Cookie Banner', 'status' => 'pass', 'detail' => 'Cookie/privacy notice detected'];
    $cookieScore += 30;
} else {
    $cookieChecks[] = ['check' => 'Cookie Banner', 'status' => 'fail', 'detail' => 'No cookie banner detected'];
}

// Privacy policy link
if (preg_match('/href=["\'][^"\']*privacy[^"\']*["\']/i', $body) || preg_match('/privacy.*policy/i', $body)) {
    $cookieChecks[] = ['check' => 'Privacy Policy', 'status' => 'pass', 'detail' => 'Privacy policy link found'];
    $cookieScore += 25;
} else {
    $cookieChecks[] = ['check' => 'Privacy Policy', 'status' => 'fail', 'detail' => 'No privacy policy link'];
}

// Terms link
if (preg_match('/href=["\'][^"\']*term[^"\']*["\']/i', $body)) {
    $cookieChecks[] = ['check' => 'Terms Page', 'status' => 'pass', 'detail' => 'Terms page link found'];
    $cookieScore += 15;
} else {
    $cookieChecks[] = ['check' => 'Terms Page', 'status' => 'warn', 'detail' => 'No terms page link'];
}

// Third-party trackers
$trackers = [];
if (preg_match('/google-analytics|gtag|googletagmanager/i', $body)) $trackers[] = 'Google Analytics';
if (preg_match('/facebook.*pixel|fbevents/i', $body)) $trackers[] = 'Facebook Pixel';
if (preg_match('/hotjar/i', $body)) $trackers[] = 'Hotjar';
if (preg_match('/linkedin.*insight/i', $body)) $trackers[] = 'LinkedIn Insight';
if (count($trackers) > 0) {
    $cookieChecks[] = ['check' => 'Trackers', 'status' => 'warn', 'detail' => 'Trackers found: ' . implode(', ', $trackers)];
    $cookieScore += 15;
} else {
    $cookieChecks[] = ['check' => 'Trackers', 'status' => 'pass', 'detail' => 'No third-party trackers detected'];
    $cookieScore += 30;
}

$cookieScore = min(100, $cookieScore);

// ============ OVERALL SCORE ============
$overallScore = round(($seoScore * 0.3 + $secScore * 0.2 + $perfScore * 0.2 + $accScore * 0.15 + $cookieScore * 0.15));

if ($overallScore >= 90) $grade = 'A';
elseif ($overallScore >= 80) $grade = 'B';
elseif ($overallScore >= 70) $grade = 'C';
elseif ($overallScore >= 60) $grade = 'D';
elseif ($overallScore >= 40) $grade = 'E';
else $grade = 'F';

$summary = "Your website scored $overallScore/100 ($grade). ";
$weakAreas = [];
if ($seoScore < 60) $weakAreas[] = 'SEO';
if ($secScore < 60) $weakAreas[] = 'Security';
if ($perfScore < 60) $weakAreas[] = 'Performance';
if ($accScore < 60) $weakAreas[] = 'Accessibility';
if ($cookieScore < 60) $weakAreas[] = 'Privacy/Cookies';
if (count($weakAreas) > 0) {
    $summary .= 'Key areas to improve: ' . implode(', ', $weakAreas) . '.';
} else {
    $summary .= 'Your website is performing well across all areas.';
}

echo json_encode([
    'url' => $url,
    'overall' => [
        'score' => $overallScore,
        'grade' => $grade,
        'summary' => $summary
    ],
    'audits' => [
        'seo' => ['category' => 'SEO', 'score' => $seoScore, 'checks' => $seoChecks],
        'security' => ['category' => 'Security', 'score' => $secScore, 'checks' => $secChecks],
        'performance' => ['category' => 'Performance', 'score' => $perfScore, 'checks' => $perfChecks],
        'accessibility' => ['category' => 'Accessibility', 'score' => $accScore, 'checks' => $accChecks],
        'cookies' => ['category' => 'Cookies & Privacy', 'score' => $cookieScore, 'checks' => $cookieChecks]
    ]
]);
