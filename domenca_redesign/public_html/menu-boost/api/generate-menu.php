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

// Detect style from prompt to build a matching system prompt
$style = 'poetic'; // default
if (preg_match('/Style:\s*(.+?)(?:\.\s*Languages|\.?\s*Languages)/i', $prompt, $m)) {
    $styleDesc = strtolower(trim($m[1]));
    if (strpos($styleDesc, 'professional') !== false || strpos($styleDesc, 'elegant') !== false || strpos($styleDesc, 'traditional') !== false) {
        $style = 'classic';
    } elseif (strpos($styleDesc, 'clear') !== false || strpos($styleDesc, 'direct') !== false || strpos($styleDesc, 'friendly') !== false) {
        $style = 'simple';
    } elseif (strpos($styleDesc, 'practical') !== false || strpos($styleDesc, 'wolt') !== false || strpos($styleDesc, 'delivery') !== false) {
        $style = 'delivery';
    } elseif (strpos($styleDesc, 'energetic') !== false || strpos($styleDesc, 'emoji') !== false || strpos($styleDesc, 'modern') !== false) {
        $style = 'social';
    } elseif (strpos($styleDesc, 'evocative') !== false || strpos($styleDesc, 'sensory') !== false || strpos($styleDesc, 'aroma') !== false) {
        $style = 'poetic';
    }
}

// Style-specific system prompts
$systemPrompts = [
    'poetic' => 'You are a professional food writer. Write appetizing, evocative menu descriptions that make diners want to order. Use sensory language — aromas, textures, emotions. Never start with the dish name. 2-4 sentences per dish per language, max 80 words.',
    'classic' => 'You are a professional menu writer for an upscale restaurant. Write elegant, traditional menu descriptions. Formal but inviting tone. Focus on quality ingredients and preparation. Never start with the dish name. 2-4 sentences per dish per language, max 80 words.',
    'simple' => 'You are a clear, friendly menu writer. Write straightforward menu descriptions that are easy to read. Use simple words, short sentences. No flowery language. Never start with the dish name. 2-3 sentences per dish per language, max 60 words.',
    'delivery' => 'You are a food delivery menu writer for platforms like Wolt and Bolt Food. Write practical, appetizing descriptions that work on small screens. Highlight key ingredients and portions. Never start with the dish name. 1-2 sentences per dish per language, max 40 words.',
    'social' => 'You are a social media food content creator. Write energetic, modern menu descriptions with emojis (🔥, 😍, 🤤, 👨‍🍳, etc.). Use casual, fun language that works on Instagram and TikTok. Never start with the dish name. 2-3 sentences per dish per language, max 50 words.',
];

$systemPrompt = $systemPrompts[$style] ?? $systemPrompts['poetic'];

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
                'content' => $systemPrompt
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
