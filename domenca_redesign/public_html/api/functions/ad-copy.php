<?php
/**
 * Ad Copy Generator — PHP version
 * POST /api/functions/ad-copy.php
 * Body: {"product":"...", "audience":"...", "tone":"...", "cta":"...", "platform":"..."}
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('ad_copy_generator');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('ad_copy_generator');

$DEEPSEEK_KEY = '***REMOVED***';

$input = json_decode(file_get_contents('php://input'), true);
$product = $input['product'] ?? '';
$audience = $input['audience'] ?? '';
$tone = $input['tone'] ?? 'professional';
$cta = $input['cta'] ?? 'Learn more';
$platform = $input['platform'] ?? 'google';

if (!$product || !$audience) {
    http_response_code(400);
    echo json_encode(['error' => 'Product and audience are required']);
    exit;
}

$platformLimits = [
    'google' => ['headline_max' => 30, 'desc_max' => 90, 'count' => 3],
    'facebook' => ['headline_max' => 40, 'desc_max' => 125, 'count' => 3],
    'instagram' => ['headline_max' => 40, 'desc_max' => 125, 'count' => 3],
    'linkedin' => ['headline_max' => 70, 'desc_max' => 150, 'count' => 3],
    'email' => ['headline_max' => 60, 'desc_max' => 200, 'count' => 3],
];
$limits = $platformLimits[$platform] ?? $platformLimits['google'];

$system = "You are an expert ad copywriter. Generate ad variations. Respond with ONLY valid JSON.";
$user = "Generate {$limits['count']} {$platform} ad variations for:\nProduct: $product\nAudience: $audience\nTone: $tone\nCTA: $cta\nHeadline max: {$limits['headline_max']} chars\nDescription max: {$limits['desc_max']} chars\n\nRespond with JSON:\n{\"variations\":[\"Headline: ...\\nDescription: ...\",\"Headline: ...\\nDescription: ...\",\"Headline: ...\\nDescription: ...\"]}";

$aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $user);
$result = json_decode($aiResult, true);

if (!$result || empty($result['variations'])) {
    // Fallback: return the raw AI text as single variation
    $result = ['variations' => [$aiResult ?: "Failed to generate ad copy. Please try again."]];
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
            'temperature' => 0.7,
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
