<?php
/**
 * Listing Optimizer — PHP version
 * POST /api/functions/listing-optimize.php
 * Body: {"product":"...", "category":"...", "features":"...", "persona":"...", "platform":"..."}
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('listing_optimizer');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('listing_optimizer');

$DEEPSEEK_KEY = '***REMOVED***';

$input = json_decode(file_get_contents('php://input'), true);
$product = $input['product'] ?? '';
$category = $input['category'] ?? '';
$features = $input['features'] ?? '';
$persona = $input['persona'] ?? '';
$platform = $input['platform'] ?? 'etsy';

if (!$product) {
    http_response_code(400);
    echo json_encode(['error' => 'Product name is required']);
    exit;
}

$system = "You are an expert e-commerce listing copywriter. Optimize product listings. Respond with ONLY valid JSON.";
$user = "Optimize this $platform listing:\nProduct: $product\nCategory: $category\nFeatures: $features\nTarget buyer: $persona\n\nRespond with JSON:\n{\"title\":\"Optimized title\",\"description\":\"Optimized description\",\"tags\":[\"tag1\",\"tag2\",\"tag3\",\"tag4\",\"tag5\"],\"tips\":[\"tip1\",\"tip2\",\"tip3\"]}";

$aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $user);
$result = json_decode($aiResult, true);

if (!$result || !isset($result['title'])) {
    $result = [
        'title' => $product,
        'description' => "Optimized listing for $product. " . ($features ?: "High quality product."),
        'tags' => [$product, $category, $platform],
        'tips' => ['Add high-quality photos', 'Use all available tags', 'Write detailed descriptions']
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
