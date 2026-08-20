<?php
/**
 * GEO Check v2 — URL-based AI Visibility Analysis
 * POST /api/functions/geo-check.php
 * Body: {"url": "https://example.com"}
 *
 * 1. Fetches & scrapes the website
 * 2. Extracts business name, location, niche automatically
 * 3. Technical AI readiness analysis (structured data, llms.txt, robots.txt, etc.)
 * 4. GEO visibility score via DeepSeek
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

// Payment check
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('geo_check');

$DEEPSEEK_KEY = '***REMOVED***';

$input = json_decode(file_get_contents('php://input'), true);
$url = trim($input['url'] ?? '');

if (!$url) {
    http_response_code(400);
    echo json_encode(['error' => 'URL is required']);
    exit;
}

// Add protocol if missing
if (!preg_match('#^https?://#i', $url)) {
    $url = 'https://' . $url;
}

if (!filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid URL']);
    exit;
}

// ============ FETCH WEBSITE ============
$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_MAXREDIRS => 5,
    CURLOPT_TIMEOUT => 15,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_SSL_VERIFYPEER => true,
    CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; BoostSuite/2.0)',
]);
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
$sizeDownload = curl_getinfo($ch, CURLINFO_SIZE_DOWNLOAD);
curl_close($ch);

if (curl_errno($ch) || !$response) {
    http_response_code(422);
    echo json_encode(['error' => 'Could not fetch URL']);
    exit;
}

// ============ EXTRACT BUSINESS INFO ============
$business = extractBusinessInfo($response, $url);
$technical = analyzeTechnicalAI($response, $url);
$baseUrl = preg_replace('#/[^/]*$#', '/', $url);

// Check llms.txt and robots.txt
$technical['llms_txt'] = checkTxtFile($baseUrl, 'llms.txt');
$technical['ai_txt'] = checkTxtFile($baseUrl, 'ai.txt');
$technical['robots_txt'] = checkTxtFile($baseUrl, 'robots.txt');

// ============ EXTRACT CLEAN TEXT FOR AI READING ============
$cleanText = extractCleanText($response);

// ============ GEO ANALYSIS VIA DEEPSEEK ============
$system = "You are a GEO (Generative Engine Optimization) expert. Analyze a website's AI visibility. Respond with ONLY valid JSON.";

$businessInfo = "Extracted from website:\n";
$businessInfo .= "- Business name: {$business['name']}\n";
$businessInfo .= "- Location: {$business['location']}\n";
$businessInfo .= "- Niche/Industry: {$business['niche']}\n";
$businessInfo .= "- Description: {$business['description']}\n";

$techInfo = "\nTechnical AI readiness:\n";
$techInfo .= "- Has structured data (Schema.org): " . ($technical['has_structured_data'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Schema types: " . implode(', ', $technical['schema_types']) . "\n";
$techInfo .= "- Has llms.txt: " . ($technical['llms_txt']['exists'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Has ai.txt: " . ($technical['ai_txt']['exists'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Robots.txt AI bots allowed: " . ($technical['robots_txt_ai_allowed'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Open Graph tags: " . ($technical['has_og_tags'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Meta description: " . ($technical['has_meta_description'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- HTTPS: " . ($technical['is_https'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Word count: {$technical['word_count']}\n";
$techInfo .= "- Has FAQ section: " . ($technical['has_faq'] ? 'YES' : 'NO') . "\n";
$techInfo .= "- Has contact page signals: " . ($technical['has_contact_signals'] ? 'YES' : 'NO') . "\n";

$user = $businessInfo . $techInfo . "\n\nAnalyze their visibility in AI assistants (ChatGPT, Gemini, Perplexity, Claude). Consider: structured data quality, content authority, directory presence, review signals, social proof, and technical AI readiness.\n\nRespond with JSON:\n{\"score\":0-100,\"analysis\":\"2-3 sentences about their AI visibility\",\"platforms\":[\"where they likely appear\"],\"suggestions\":[\"suggestion1\",\"suggestion2\",\"suggestion3\",\"suggestion4\",\"suggestion5\"]}";

$aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $user);
$geoResult = json_decode($aiResult, true);

// ============ AI READING — what would AI actually say about this business ============
$aiReadingSystem = "You are an AI assistant like ChatGPT or Gemini. A user asks: 'What can you tell me about this business?' Based on the website content below, answer as if you ARE the AI assistant. Be honest about what you can and cannot find. Be concise (3-5 sentences).";
$aiReadingUser = "Website content:\n\n" . $cleanText;
$aiReading = callDeepSeek($DEEPSEEK_KEY, $aiReadingSystem, $aiReadingUser);

if (!$geoResult || !isset($geoResult['score'])) {
    $geoResult = [
        'score' => 15,
        'analysis' => "Limited AI visibility detected. The website lacks key signals that AI assistants use to recommend businesses.",
        'platforms' => [],
        'suggestions' => [
            "Add structured data (Schema.org) to your website",
            "Create an llms.txt file describing your business for AI",
            "Claim and optimize your Google Business Profile",
            "Get listed on industry directories",
            "Collect customer reviews on Google and Trustpilot",
        ]
    ];
}

// ============ COMBINE RESULTS ============
$techScore = calculateTechScore($technical);

echo json_encode([
    'url' => $url,
    'business' => $business,
    'technical' => $technical,
    'tech_score' => $techScore,
    'geo' => $geoResult,
    'ai_reading' => $aiReading ?: '',
]);

// ============ HELPER FUNCTIONS ============

function extractBusinessInfo($html, $url) {
    $name = '';
    $location = '';
    $niche = '';
    $description = '';

    // Business name — try multiple sources
    // 1. Schema.org Organization
    if (preg_match('/"@type"\s*:\s*"Organization"[^}]*"name"\s*:\s*"([^"]+)"/i', $html, $m)) {
        $name = $m[1];
    }
    // 2. og:site_name
    elseif (preg_match('/property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m)) {
        $name = $m[1];
    }
    // 3. <title> tag — strip site name suffix
    elseif (preg_match('/<title[^>]*>([^<]+)<\/title>/i', $html, $m)) {
        $title = trim($m[1]);
        // Remove common suffixes like " | Sitename" or " - Sitename"
        $name = preg_split('/\s*[|\-–]\s*/', $title)[0];
    }
    // 4. meta author
    elseif (preg_match('/<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m)) {
        $name = $m[1];
    }

    // Location — try schema.org PostalAddress, then look for address patterns
    if (preg_match('/"@type"\s*:\s*"PostalAddress"[^}]*"addressLocality"\s*:\s*"([^"]+)"/i', $html, $m)) {
        $location = $m[1];
        if (preg_match('/"addressCountry"\s*:\s*"([^"]+)"/i', $html, $cm)) {
            $location .= ', ' . $cm[1];
        }
    } elseif (preg_match('/"@type"\s*:\s*"LocalBusiness"[^}]*"address"[^}]*"addressLocality"\s*:\s*"([^"]+)"/i', $html, $m)) {
        $location = $m[1];
    }
    // Fallback: look for common address patterns in text
    elseif (preg_match('/(?:street|address|naslov|ulica)[^<>]{5,60}/i', $html, $m)) {
        $location = trim(strip_tags($m[0]));
    }

    // Niche — from Schema.org, meta keywords, or content
    if (preg_match('/"@type"\s*:\s*"(LocalBusiness|Restaurant|Store|ProfessionalService|SoftwareApplication)[^"]*"/i', $html, $m)) {
        $niche = $m[1];
        if ($niche === 'LocalBusiness' && preg_match('/"category"\s*:\s*"([^"]+)"/i', $html, $cm)) {
            $niche = $cm[1];
        }
    } elseif (preg_match('/<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m)) {
        $keywords = explode(',', $m[1]);
        $niche = trim($keywords[0]);
    } elseif (preg_match('/<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m)) {
        // Use first few words of description as niche hint
        $words = explode(' ', $m[1]);
        $niche = implode(' ', array_slice($words, 0, 4));
    }

    // Description
    if (preg_match('/property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m)) {
        $description = $m[1];
    } elseif (preg_match('/<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']/i', $html, $m)) {
        $description = $m[1];
    }

    return [
        'name' => $name ?: 'Unknown',
        'location' => $location ?: 'Unknown',
        'niche' => $niche ?: 'Unknown',
        'description' => mb_substr($description, 0, 300),
    ];
}

function analyzeTechnicalAI($html, $url) {
    $result = [];

    // Structured data
    $result['has_structured_data'] = (bool) preg_match('/application\/ld\+json/i', $html);
    $result['schema_types'] = [];
    if ($result['has_structured_data']) {
        preg_match_all('/"@type"\s*:\s*"([^"]+)"/i', $html, $m);
        $result['schema_types'] = array_unique($m[1]);
    }

    // Open Graph
    $result['has_og_tags'] = (bool) preg_match('/og:(title|description|image|type)/i', $html);

    // Meta description
    $result['has_meta_description'] = (bool) preg_match('/<meta[^>]*name=["\']description["\']/i', $html);

    // HTTPS
    $result['is_https'] = (parse_url($url, PHP_URL_SCHEME) === 'https');

    // Word count
    $result['word_count'] = str_word_count(strip_tags($html));

    // FAQ section
    $result['has_faq'] = (bool) preg_match('/"@type"\s*:\s*"FAQPage"/i', $html) ||
                          (bool) preg_match('/faq|frequently.asked|pogosta.vprasanja/i', $html);

    // Contact signals
    $result['has_contact_signals'] = (bool) preg_match('/"@type"\s*:\s*"ContactPage"/i', $html) ||
                                      (bool) preg_match('/mailto:|tel:|phone|telefon|kontakt/i', $html);

    // Hreflang (multi-language)
    $result['has_hreflang'] = (bool) preg_match('/hreflang/i', $html);

    // Canonical
    $result['has_canonical'] = (bool) preg_match('/rel=["\']canonical["\']/i', $html);

    // Twitter card
    $result['has_twitter_card'] = (bool) preg_match('/twitter:card/i', $html);

    // Images with alt text
    preg_match_all('/<img[^>]*>/i', $html, $imgs);
    $totalImages = count($imgs[0]);
    $withAlt = 0;
    foreach ($imgs[0] as $img) {
        if (preg_match('/alt=["\'][^"\']+["\']/i', $img)) $withAlt++;
    }
    $result['images_total'] = $totalImages;
    $result['images_with_alt'] = $withAlt;

    return $result;
}

function checkTxtFile($baseUrl, $filename) {
    $url = rtrim($baseUrl, '/') . '/' . $filename;
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 5,
        CURLOPT_CONNECTTIMEOUT => 3,
        CURLOPT_USERAGENT => 'BoostSuite/2.0',
    ]);
    $content = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return [
        'exists' => ($httpCode === 200 && strlen($content) > 10),
        'content' => ($httpCode === 200) ? mb_substr($content, 0, 1000) : '',
    ];
}

function extractCleanText($html) {
    // Remove scripts, styles, nav, footer, header
    $text = preg_replace('/<script[^>]*>[\s\S]*?<\/script>/i', '', $html);
    $text = preg_replace('/<style[^>]*>[\s\S]*?<\/style>/i', '', $text);
    $text = preg_replace('/<nav[^>]*>[\s\S]*?<\/nav>/i', '', $text);
    $text = preg_replace('/<footer[^>]*>[\s\S]*?<\/footer>/i', '', $text);
    $text = preg_replace('/<header[^>]*>[\s\S]*?<\/header>/i', '', $text);
    $text = preg_replace('/<!--[^>]*-->/', '', $text);
    // Remove HTML tags
    $text = strip_tags($text, '<p><h1><h2><h3><li><strong><em>');
    // Remove remaining tags
    $text = strip_tags($text);
    // Clean whitespace
    $text = preg_replace('/\s+/', ' ', $text);
    $text = trim($text);
    // Limit to ~3000 chars to save tokens
    return mb_substr($text, 0, 3000);
}

function calculateTechScore($tech) {
    $score = 0;

    // Core checks (max 100)
    if ($tech['has_structured_data']) $score += 20;
    if ($tech['has_og_tags']) $score += 10;
    if ($tech['has_meta_description']) $score += 10;
    if ($tech['is_https']) $score += 10;
    if ($tech['has_canonical']) $score += 5;
    if ($tech['has_hreflang']) $score += 5;
    if ($tech['has_twitter_card']) $score += 5;
    if ($tech['has_faq']) $score += 10;
    if ($tech['has_contact_signals']) $score += 5;

    // Content quality
    if ($tech['word_count'] > 500) $score += 10;
    elseif ($tech['word_count'] > 200) $score += 5;

    // Images
    if ($tech['images_total'] > 0) {
        $altPercent = $tech['images_with_alt'] / $tech['images_total'];
        if ($altPercent > 0.8) $score += 5;
    }

    // AI-specific files
    if (checkTxtFileFromTech($tech, 'llms_txt')) $score += 5;

    return min(100, $score);
}

function checkTxtFileFromTech($tech, $key) {
    // This is a simplified check — the actual check was done earlier
    return isset($tech[$key]['exists']) && $tech[$key]['exists'];
}

function callDeepSeek($key, $system, $user) {
    $ch = curl_init('https://api.deepseek.com/v1/chat/completions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', "Authorization: Bearer $key"],
        CURLOPT_POSTFIELDS => json_encode([
            'model' => 'deepseek-v4-flash',
            'messages' => [
                ['role' => 'system', 'content' => $system],
                ['role' => 'user', 'content' => $user],
            ],
            'temperature' => 0.3,
            'max_tokens' => 800,
        ]),
        CURLOPT_TIMEOUT => 30,
    ]);
    $resp = curl_exec($ch);
    curl_close($ch);
    $data = json_decode($resp, true);
    $content = $data['choices'][0]['message']['content'] ?? '';
    $reasoning = $data['choices'][0]['message']['reasoning_content'] ?? '';
    return $content ?: $reasoning;
}
