<?php
/**
 * MenuBoost — Photo Menu Analyzer & Description Generator
 * POST /api/analyze-photo.php
 *
 * Mode 1 — Analyze + generate from photo:
 *   { "image": "base64...", "style": "poetic", "langs": ["sl","en"] }
 *
 * Mode 2 — Generate from dish names:
 *   { "dishes": ["Jota", "Štruklji"], "style": "poetic", "langs": ["sl","en"] }
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

$input = json_decode(file_get_contents('php://input'), true);
$imageBase64 = $input['image'] ?? null;
$analyzeOnly = $input['analyze_only'] ?? false;
$dishNames = $input['dishes'] ?? null;
$style = $input['style'] ?? 'poetic';
$langs = $input['langs'] ?? ['sl', 'en'];

// Load API key
$configFile = __DIR__ . '/deepseek-config.php';
$apiKey = file_exists($configFile) ? (require $configFile)['api_key'] ?? '' : getenv('DEEPSEEK_API_KEY');
if (!$apiKey) { http_response_code(500); echo json_encode(['error' => 'API key not configured']); exit; }

// Language names for prompt
$langNames = [
    'sl' => 'Slovenian', 'en' => 'English', 'de' => 'German', 'it' => 'Italian',
    'hr' => 'Croatian', 'sr' => 'Serbian', 'fr' => 'French', 'es' => 'Spanish',
    'tr' => 'Turkish', 'el' => 'Greek'
];

// Style prompts
$stylePrompts = [
    'poetic'   => 'Write appetizing, evocative descriptions using sensory language — aromas, textures, emotions. 2-4 sentences per dish.',
    'classic'  => 'Write elegant, traditional descriptions. Formal but inviting. Focus on quality ingredients. 2-4 sentences per dish.',
    'simple'   => 'Write clear, friendly descriptions. Simple words, short sentences. 2-3 sentences per dish.',
    'delivery' => 'Write practical descriptions for delivery platforms. Highlight key ingredients and portions. 1-2 sentences per dish.',
    'social'   => 'Write energetic, modern descriptions with emojis (🔥, 😍, 🤤). Casual, fun language. 2-3 sentences per dish.',
    'michelin' => 'Write sophisticated fine dining descriptions. Focus on technique, terroir, and seasonal ingredients. 2-3 sentences per dish.'
];

$stylePrompt = $stylePrompts[$style] ?? $stylePrompts['poetic'];
$langList = implode(', ', array_map(fn($l) => $langNames[$l] ?? $l, $langs));

// Load OpenRouter key for vision
$openRouterKey = getenv('OPENROUTER_API_KEY') ?: '';
if (!$openRouterKey) {
    $orConfig = __DIR__ . '/openrouter-config.php';
    if (file_exists($orConfig)) $openRouterKey = (require $orConfig)['api_key'] ?? '';
}

// ===== MODE 1: FROM PHOTO (Gemma 4 vision for analysis) =====
if ($imageBase64 && !$dishNames) {
    if (strlen($imageBase64) > 14000000) { http_response_code(400); echo json_encode(['error' => 'Image too large']); exit; }
    if (!$openRouterKey) { http_response_code(500); echo json_encode(['error' => 'OpenRouter API key not configured']); exit; }

    // Use Gemma 4 to extract dish names from photo
    $extractPrompt = "Prepiši vse jedi s te slike jedilnika. Vrni samo JSON tabelo z imeni jedi. Primer: [\"Jota\", \"Štruklji\", \"Potica\"]";

    $visionPayload = [
        'model' => 'google/gemma-4-26b-a4b-it:free',
        'messages' => [[
            'role' => 'user',
            'content' => [
                ['type' => 'text', 'text' => $extractPrompt],
                ['type' => 'image_url', 'image_url' => 'data:image/jpeg;base64,' . $imageBase64]
            ]
        ]],
        'max_tokens' => 500,
    ];

    $ch = curl_init('https://openrouter.ai/api/v1/chat/completions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($visionPayload),
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . $openRouterKey,
            'HTTP-Referer: https://hd-webdesign.si',
            'X-Title: MenuBoost',
        ],
        CURLOPT_TIMEOUT => 60,
    ]);
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) { http_response_code(500); echo json_encode(['error' => 'Vision API error: ' . $error]); exit; }

    $data = json_decode($response, true);
    $content = $data['choices'][0]['message']['content'] ?? '';
    $content = trim($content);
    $content = preg_replace('/```json\s*/i', '', $content);
    $content = preg_replace('/```\s*/i', '', $content);
    $content = preg_replace('/^[^\[]*/', '', $content);
    $content = preg_replace('/[^\]]*$/', '', $content);

    $dishNames = json_decode($content, true);
    if (!is_array($dishNames) || empty($dishNames)) {
        http_response_code(502);
        echo json_encode(['error' => 'Could not read menu from image', 'raw' => substr($content, 0, 300)]);
        exit;
    }

    $dishNames = array_slice($dishNames, 0, 20);

    // If analyze_only, just return dish names
    if ($analyzeOnly) {
        $dishes = array_map(fn($n) => ['name' => $n, 'descriptions' => []], $dishNames);
        echo json_encode(['success' => true, 'dishes' => $dishes, 'count' => count($dishes)]);
        exit;
    }
    // Otherwise fall through to description generation
}

// ===== GENERATE DESCRIPTIONS (from dish names — photo or manual) =====
if ($dishNames && is_array($dishNames)) {
    $dishNames = array_slice($dishNames, 0, 20);

    $prompt = "Za naslednje jedi iz menija napiši opise:\n\n";
    foreach ($dishNames as $i => $name) {
        $prompt .= ($i + 1) . ". {$name}\n";
    }
    $prompt .= "\nSlog: {$stylePrompt}\n\n";
    $prompt .= "Prevedi vsak opis v te jezike: {$langList}\n\n";
    $prompt .= "Vrni kot JSON tabelo:\n";
    $prompt .= "[{\"name\": \"Ime jedi\", \"descriptions\": {\"sl\": \"...\", \"en\": \"...\", ...}}]\n";
    $prompt .= "Vrni SAMO JSON, nič drugega.";

    $payload = [
        'model' => 'deepseek-chat',
        'messages' => [
            ['role' => 'system', 'content' => 'Si profesionalni pisec jedilnikov in prevajalec. Vrni samo veljaven JSON.'],
            ['role' => 'user', 'content' => $prompt]
        ],
        'temperature' => 0.7,
        'max_tokens' => 3000,
    ];

    $ch = curl_init('https://api.deepseek.com/v1/chat/completions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload),
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . $apiKey,
        ],
        CURLOPT_TIMEOUT => 60,
    ]);
    $response = curl_exec($ch);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) { http_response_code(500); echo json_encode(['error' => 'API error: ' . $error]); exit; }

    $data = json_decode($response, true);
    $content = $data['choices'][0]['message']['content'] ?? '';
    $content = trim($content);
    $content = preg_replace('/```json\s*/i', '', $content);
    $content = preg_replace('/```\s*/i', '', $content);

    $dishes = json_decode($content, true);

    if (!is_array($dishes) || empty($dishes)) {
        http_response_code(502);
        echo json_encode(['error' => 'Could not generate descriptions', 'raw' => substr($content, 0, 500)]);
        exit;
    }

    echo json_encode(['success' => true, 'dishes' => $dishes, 'count' => count($dishes)]);
    exit;
}

http_response_code(400);
echo json_encode(['error' => 'Provide image or dishes array']);
