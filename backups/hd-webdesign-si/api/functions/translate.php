<?php
/**
 * MenuBoost — AI Menu Translation API
 * Accepts dish names, returns multilingual descriptions via DeepSeek
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
// Payment check — require API key or x402 payment
if (!session_id()) session_start();
require_once __DIR__ . '/payment-auth.php';
checkApiAuth('menu_translate');
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

// Config
$DEEPSEEK_KEY = '***REMOVED***';
$DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions';

// Rate limiting (simple file-based)
$rate_file = sys_get_temp_dir() . '/menuboost_rate_' . md5($_SERVER['REMOTE_ADDR'] ?? 'unknown');
$max_per_hour = 20;

if (file_exists($rate_file)) {
    $data = json_decode(file_get_contents($rate_file), true);
    if ($data && time() - $data['first'] < 3600) {
        if ($data['count'] >= $max_per_hour) {
            http_response_code(429);
            echo json_encode(['error' => 'Rate limit exceeded. Try again later.']);
            exit;
        }
        $data['count']++;
    } else {
        $data = ['first' => time(), 'count' => 1];
    }
} else {
    $data = ['first' => time(), 'count' => 1];
}
file_put_contents($rate_file, json_encode($data));

// Parse input
$input = json_decode(file_get_contents('php://input'), true);
$dishes = $input['dishes'] ?? [];
$restaurant = $input['restaurant'] ?? '';
$rest_type = $input['rest_type'] ?? 'Mediterranean restaurant';
$style = $input['style'] ?? 'Professional and appetizing';
$languages = $input['languages'] ?? ['en', 'de', 'it'];

if (empty($dishes)) {
    http_response_code(400);
    echo json_encode(['error' => 'No dishes provided']);
    exit;
}

// Limit to 10 dishes per request
$dishes = array_slice($dishes, 0, 10);

// Build prompt
$lang_labels = [
    'en' => 'English', 'de' => 'German', 'it' => 'Italian',
    'hr' => 'Croatian', 'sl' => 'Slovenian', 'sr' => 'Serbian'
];

$dish_list = '';
foreach ($dishes as $i => $dish) {
    $name = $dish['name'] ?? $dish;
    $ingredients = $dish['ingredients'] ?? '';
    $dish_list .= ($i + 1) . ". " . $name;
    if ($ingredients) $dish_list .= " — Ingredients: " . $ingredients;
    $dish_list .= "\n";
}

$lang_str = implode(', ', array_map(fn($l) => $l . ' (write in ' . ($lang_labels[$l] ?? $l) . ')', $languages));

$json_keys = implode(', ', array_map(fn($l) => '"' . $l . '": "description here"', $languages));

$prompt = "Write appetizing menu descriptions for these dishes from " . ($restaurant ?: "a restaurant") . ".\n";
$prompt .= "Restaurant type: " . $rest_type . ". Style: " . $style . ".\n\n";
$prompt .= $dish_list . "\n";
$prompt .= "Languages: " . $lang_str . ".\n";
$prompt .= "Rules: 2-4 sentences, max 80 words per language, do not start with dish name. Be evocative and sensory.\n";
$prompt .= "Return ONLY this JSON: {\"dishes\": [{\"name\": \"dish name\", " . $json_keys . "}]}";

// Call DeepSeek
$ch = curl_init($DEEPSEEK_URL);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $DEEPSEEK_KEY,
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'model' => 'deepseek-v4-flash',
        'messages' => [
            ['role' => 'system', 'content' => 'You are a professional food writer and translator. Write appetizing, evocative menu descriptions that make diners want to order. Never start with the dish name. Use sensory language. Keep descriptions concise (2-4 sentences, max 80 words per language).'],
            ['role' => 'user', 'content' => $prompt]
        ],
        'temperature' => 0.7,
        'max_tokens' => 3000,
    ]),
    CURLOPT_TIMEOUT => 30,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code !== 200 || !$response) {
    http_response_code(502);
    echo json_encode(['error' => 'AI service temporarily unavailable']);
    exit;
}

$data = json_decode($response, true);
$content = $data['choices'][0]['message']['content']
    ?? $data['choices'][0]['message']['reasoning_content']
    ?? '';

// Parse JSON from AI response
$start = strpos($content, '{');
$end = strrpos($content, '}');
if ($start !== false && $end !== false) {
    $result = json_decode(substr($content, $start, $end - $start + 1), true);
    if ($result && isset($result['dishes'])) {
        echo json_encode($result);
        exit;
    }
}

// Fallback
echo json_encode(['dishes' => [], 'raw' => $content]);
