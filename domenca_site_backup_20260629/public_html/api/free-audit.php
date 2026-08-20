<?php
/**
 * Free SEO/GEO Audit Widget
 * GET /api/free-audit.php?url=https://example.com
 * Returns basic SEO score + GEO visibility teaser (no auth required)
 * Limits: 1 free audit per IP per hour
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://hd-webdesign.si');

// Rate limit: 1 per IP per hour
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$limitFile = sys_get_temp_dir() . '/audit_limits.json';
$limits = file_exists($limitFile) ? json_decode(file_get_contents($limitFile), true) : [];
$hourKey = date('Y-m-d-H') . '_' . $ip;

if (isset($limits[$hourKey]) && $limits[$hourKey] >= 1) {
    http_response_code(429);
    echo json_encode(['error' => 'Rate limit: 1 free audit per hour. Upgrade for unlimited.']);
    exit;
}

$url = $_GET['url'] ?? '';
if (!$url || !filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Valid URL required']);
    exit;
}

// Basic SEO check (no external API needed)
$html = @file_get_contents($url, false, stream_context_create([
    'http' => ['timeout' => 10, 'user_agent' => 'Mozilla/5.0 (compatible; BoostSuiteBot/1.0)']
]));

// Fallback to curl if file_get_contents fails
if (!$html) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuiteBot/1.0)',
    ]);
    $html = curl_exec($ch);
    curl_close($ch);
}

if (!$html) {
    http_response_code(422);
    echo json_encode(['error' => 'Could not fetch URL']);
    exit;
}

// Calculate basic SEO score
$score = 50; // base
$issues = [];
$strengths = [];

// Title tag
if (preg_match('/<title[^>]*>(.*?)<\/title>/is', $html, $m)) {
    $title = trim(strip_tags($m[1]));
    $len = strlen($title);
    if ($len >= 30 && $len <= 60) { $score += 10; $strengths[] = "Good title tag ($len chars)"; }
    elseif ($len > 0) { $score += 5; $issues[] = "Title tag should be 30-60 chars (yours: $len)"; }
    else { $issues[] = "Missing title tag"; }
} else {
    $issues[] = "Missing title tag";
}

// Meta description
if (preg_match('/<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']/is', $html, $m) ||
    preg_match('/<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']/is', $html, $m)) {
    $desc = trim(strip_tags($m[1]));
    $len = strlen($desc);
    if ($len >= 120 && $len <= 160) { $score += 10; $strengths[] = "Good meta description ($len chars)"; }
    elseif ($len > 0) { $score += 5; $issues[] = "Meta description should be 120-160 chars (yours: $len)"; }
    else { $issues[] = "Missing meta description"; }
} else {
    $issues[] = "Missing meta description";
}

// H1 tags
$h1Count = preg_match_all('/<h1[^>]*>/i', $html);
if ($h1Count === 1) { $score += 10; $strengths[] = "Good H1 structure"; }
elseif ($h1Count === 0) { $issues[] = "No H1 tag found"; }
else { $score += 5; $issues[] = "Multiple H1 tags ($h1Count found, should be 1)"; }

// Images without alt
$totalImages = preg_match_all('/<img[^>]*>/i', $html);
$imagesWithoutAlt = preg_match_all('/<img(?![^>]*\balt\b)[^>]*>/i', $html);
if ($totalImages > 0) {
    $altRatio = ($totalImages - $imagesWithoutAlt) / $totalImages;
    if ($altRatio >= 0.9) { $score += 10; $strengths[] = "Good image alt text coverage"; }
    else { $score += 5; $issues[] = "$imagesWithoutAlt of $totalImages images missing alt text"; }
} else {
    $score += 5;
}

// HTTPS
if (strpos($url, 'https://') === 0) { $score += 5; $strengths[] = "HTTPS enabled"; }
else { $issues[] = "Not using HTTPS"; }

// Structured data
if (strpos($html, 'application/ld+json') !== false) { $score += 5; $strengths[] = "Has structured data (JSON-LD)"; }
else { $issues[] = "No structured data (JSON-LD) found"; }

// Clamp score
$score = max(0, min(100, $score));

// Record usage
$limits[$hourKey] = 1;
// Cleanup old entries (keep last 24h)
$cleanutoff = date('Y-m-d-H', strtotime('-24 hours'));
$limits = array_filter($limits, fn($k) => substr($k, 0, 13) >= $cleanutoff, ARRAY_FILTER_USE_KEY);
file_put_contents($limitFile, json_encode($limits));

echo json_encode([
    'score' => $score,
    'grade' => $score >= 80 ? 'A' : ($score >= 60 ? 'B' : ($score >= 40 ? 'C' : 'F')),
    'url' => $url,
    'strengths' => $strengths,
    'issues' => array_slice($issues, 0, 5),
    'message' => $score >= 80
        ? 'Your site looks good! Get the full report with AI-powered recommendations.'
        : 'There\'s room for improvement. Get the full audit with actionable fixes.',
    'cta' => '/boost-suite/'
]);
