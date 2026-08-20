<?php
/**
 * SEO Audit — PHP version
 * POST /api/functions/seo-audit.php
 * Body: {"url": "https://example.com"}
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Payment-Proof');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('seo_audit');

$DEEPSEEK_KEY = '***REMOVED***';

$input = json_decode(file_get_contents('php://input'), true);
$url = isset($input['url']) ? $input['url'] : '';
if (!$url) { http_response_code(400); echo json_encode(['error' => 'URL is required']); exit; }

// Fetch URL — use localhost for our own domain (Domenca blocks external automated requests)
$fetchUrl = $url;
if (strpos($url, 'hd-webdesign.si') !== false) {
    $fetchUrl = str_replace('https://hd-webdesign.si', 'http://127.0.0.1', $url);
    $fetchUrl = str_replace('http://127.0.0.1/', 'http://127.0.0.1/', $fetchUrl);
}
$ch = curl_init($fetchUrl);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_TIMEOUT => 15,
    CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuiteSEO/1.0)',
    CURLOPT_SSL_VERIFYPEER => true,
]);
$html = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if (!$html || $httpCode >= 400) {
    http_response_code(502);
    echo json_encode(['error' => "Failed to fetch URL: HTTP $httpCode"]);
    exit;
}

// Parse HTML
$dom = new DOMDocument();
@$dom->loadHTML($html, LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD | LIBXML_NOERROR);
$xp = new DOMXPath($dom);

// Title
$titleNode = $xp->query('//title')->item(0);
$title = $titleNode ? trim($titleNode->textContent) : '';

// Meta description
$metaNode = $xp->query('//meta[@name="description"]')->item(0);
$metaDesc = $metaNode ? $metaNode->getAttribute('content') : '';

// Headings
$h1Count = $xp->query('//h1')->length;
$h2Count = $xp->query('//h2')->length;
$h3Count = $xp->query('//h3')->length;

// Images
$images = $xp->query('//img');
$imageCount = $images->length;
$imagesWithAlt = 0;
for ($i = 0; $i < $images->length; $i++) {
    $img = $images->item($i);
    if ($img->hasAttribute('alt') && trim($img->getAttribute('alt'))) {
        $imagesWithAlt++;
    }
}

// Links
$links = $xp->query('//a[@href]');
$wordCount = str_word_count(strip_tags($html));

// Canonical
$canNode = $xp->query('//link[@rel="canonical"]')->item(0);
$canonical = $canNode ? $canNode->getAttribute('href') : '';

// OG tags
$ogNode = $xp->query('//meta[@property="og:title"]')->item(0);
$ogTitle = $ogNode ? $ogNode->getAttribute('content') : '';

$ogDescNode = $xp->query('//meta[@property="og:description"]')->item(0);
$ogDescription = $ogDescNode ? $ogDescNode->getAttribute('content') : '';

// Robots
$robotsNode = $xp->query('//meta[@name="robots"]')->item(0);
$metaRobots = $robotsNode ? $robotsNode->getAttribute('content') : '';

$seoData = array(
    'url' => $url,
    'title' => $title,
    'metaDescription' => $metaDesc,
    'h1Count' => $h1Count,
    'h2Count' => $h2Count,
    'h3Count' => $h3Count,
    'imageCount' => $imageCount,
    'imagesWithAlt' => $imagesWithAlt,
    'wordCount' => $wordCount,
    'canonical' => $canonical,
    'ogTitle' => $ogTitle,
    'ogDescription' => $ogDescription,
    'metaRobots' => $metaRobots,
);

// Call DeepSeek
$prompt = "Analyze this SEO data and respond with ONLY valid JSON:\n" . json_encode($seoData, JSON_PRETTY_PRINT);
$system = 'You are an expert SEO auditor. Respond with ONLY valid JSON: {"score":0-100,"analysis":"2-3 sentences","fixes":["fix1","fix2","fix3","fix4","fix5"]}';
$aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $prompt);

$result = json_decode($aiResult, true);
if (!$result || !isset($result['score'])) {
    // Fallback scoring
    $score = 0;
    if ($title) $score += 15;
    if (strlen($title) >= 30 && strlen($title) <= 60) $score += 5;
    if ($metaDesc) $score += 15;
    if (strlen($metaDesc) >= 120 && strlen($metaDesc) <= 160) $score += 5;
    if ($h1Count >= 1) $score += 15;
    if ($imageCount > 0) $score += round(($imagesWithAlt / $imageCount) * 15);
    if ($wordCount >= 300) $score += 10;
    elseif ($wordCount >= 100) $score += 5;
    if ($canonical) $score += 10;
    if ($ogTitle) $score += 5;
    if ($ogDescription) $score += 5;
    $result = array('score' => min($score, 100), 'analysis' => 'Analysis based on raw SEO data.', 'fixes' => buildFixes($seoData));
}

$result['rawData'] = $seoData;
echo json_encode($result);

function callDeepSeek($key, $system, $user) {
    $ch = curl_init('https://api.deepseek.com/v1/chat/completions');
    curl_setopt_array($ch, array(
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => array('Content-Type: application/json', 'Authorization: Bearer ' . $key),
        CURLOPT_POSTFIELDS => json_encode(array(
            'model' => 'deepseek-v4-flash',
            'messages' => array(
                array('role' => 'system', 'content' => $system),
                array('role' => 'user', 'content' => $user),
            ),
            'temperature' => 0.2,
            'max_tokens' => 600,
        )),
        CURLOPT_TIMEOUT => 30,
    ));
    $resp = curl_exec($ch);
    curl_close($ch);
    $data = json_decode($resp, true);
    if (isset($data['choices'][0]['message']['content'])) {
        return $data['choices'][0]['message']['content'];
    }
    return '';
}

function buildFixes($d) {
    $f = array();
    if (!$d['title']) $f[] = 'Add a descriptive page title (30-60 chars)';
    if (!$d['metaDescription']) $f[] = 'Add a meta description (120-160 chars)';
    if ($d['h1Count'] === 0) $f[] = 'Add a single H1 heading';
    if ($d['imageCount'] > 0 && $d['imagesWithAlt'] < $d['imageCount']) $f[] = 'Add alt text to all images';
    if ($d['wordCount'] < 300) $f[] = 'Add more content (aim for 300+ words)';
    $defaults = array('Add structured data (Schema.org)', 'Create an XML sitemap', 'Add internal linking');
    foreach ($defaults as $df) {
        if (count($f) >= 5) break;
        if (!in_array($df, $f)) $f[] = $df;
    }
    return array_slice($f, 0, 5);
}
