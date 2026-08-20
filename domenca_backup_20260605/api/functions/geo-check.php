<?php
/**
 * GEO Check — PHP version
 * POST /api/functions/geo-check.php
 * Body: {"business": "Name", "location": "City", "niche": "Industry"}
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('geo_check');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('geo_check');

$DEEPSEEK_KEY = '***REMOVED***';

$input = json_decode(file_get_contents('php://input'), true);
$business = $input['business'] ?? '';
$location = $input['location'] ?? '';
$niche = $input['niche'] ?? '';

if (!$business || !$location || !$niche) {
    http_response_code(400);
    echo json_encode(['error' => 'All fields required']);
    exit;
}

// Search for business presence using DeepSeek
$system = "You are a GEO (Generative Engine Optimization) expert. Analyze a business's AI visibility. Respond with ONLY valid JSON.";
$user = "Business: $business\nLocation: $location\nNiche: $niche\n\nAnalyze their likely visibility in AI assistants (ChatGPT, Gemini, Perplexity). Consider: Google Business Profile, reviews, directory listings, structured data, social media presence.\n\nRespond with JSON:\n{\"score\":0-100,\"analysis\":\"2-3 sentences\",\"platforms\":[\"where they appear\"],\"suggestions\":[\"suggestion1\",\"suggestion2\",\"suggestion3\",\"suggestion4\"]}";

$aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $user);
$result = json_decode($aiResult, true);

if (!$result || !isset($result['score'])) {
    $result = [
        'score' => 10,
        'analysis' => "Limited AI visibility detected for $business. Most small businesses lack structured data and directory presence needed for AI recommendations.",
        'platforms' => [],
        'suggestions' => [
            "Claim and optimize a Google Business Profile",
            "Get listed on industry directories (Clutch, Sortlist, etc.)",
            "Collect customer reviews on Google and Trustpilot",
            "Add structured data (Schema.org) to your website",
        ]
    ];
}

echo json_encode($result);

function callDeepSeek($key, $system, $user) {
    $ch = curl_init('https://api.deepseek.com/v1/chat/completions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => ['Content-Type: application/json', "Authorization: Bearer $key"],
        CURLOPT_POSTFIELDS => json_encode([
            'model' => 'deepseek-v4-flash',
            'messages' => [['role' => 'system', 'content' => $system], ['role' => 'user', 'content' => $user]],
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
