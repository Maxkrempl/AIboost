<?php
/**
 * MenuBoost — AI Menu Description Generator
 * POST /api/generate-menu.php
 * Body: { "prompt": "..." }
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
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$prompt = $input['prompt'] ?? null;

if (!$prompt) {
    http_response_code(400);
    echo json_encode(['error' => 'Prompt required']);
    exit;
}

// DeepSeek API key
$apiKey = getenv('DEEPSEEK_API_KEY');
if (!$apiKey) {
    // Fallback: read from config file
    $configFile = __DIR__ . '/deepseek-config.php';
    if (file_exists($configFile)) {
        $config = require $configFile;
        $apiKey = $config['api_key'] ?? '';
    }
}

if (!$apiKey) {
    http_response_code(500);
    echo json_encode(['error' => 'API key not configured']);
    exit;
}

// Call DeepSeek API
$ch = curl_init('https://api.deepseek.com/v1/chat/completions');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'model' => 'deepseek-v4-flash',
        'messages' => [
            [
                'role' => 'system',
                'content' => 'You are a professional food writer and translator. Write appetizing, evocative menu descriptions that make diners want to order. Never start with the dish name. Use sensory language. Keep descriptions concise (2-4 sentences, max 80 words per language).'
            ],
            [
                'role' => 'user',
                'content' => $prompt
            ]
        ],
        'temperature' => 0.7,
        'max_tokens' => 2000,
    ]),
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey,
    ],
    CURLOPT_TIMEOUT => 30,
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($error) {
    http_response_code(500);
    echo json_encode(['error' => 'cURL error: ' . $error]);
    exit;
}

if ($httpCode !== 200) {
    http_response_code(502);
    echo json_encode(['error' => 'AI service error: ' . $httpCode]);
    exit;
}

$data = json_decode($response, true);
$content = $data['choices'][0]['message']['content'] ?? $data['choices'][0]['message']['reasoning_content'] ?? '';

echo json_encode([
    'content' => [['text' => $content]]
]);
