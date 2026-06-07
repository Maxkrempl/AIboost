<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
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

require_once __DIR__ . '/config.php';

// Rate limiting (simple file-based)
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$rate_file = sys_get_temp_dir() . '/chatbot_rate_' . md5($ip);
$rate_data = [];
if (file_exists($rate_file)) {
    $rate_data = json_decode(file_get_contents($rate_file), true) ?: [];
}
$hour_ago = time() - 3600;
$rate_data = array_filter($rate_data, fn($ts) => $ts > $hour_ago);
if (count($rate_data) >= MAX_REQUESTS_PER_IP) {
    http_response_code(429);
    echo json_encode(['error' => 'Preveč zahtev. Poskusite čez eno uro.']);
    exit;
}
$rate_data[] = time();
file_put_contents($rate_file, json_encode($rate_data));

// Parse input
$input = json_decode(file_get_contents('php://input'), true);
$user_message = trim($input['message'] ?? '');
$history = $input['history'] ?? [];

if (empty($user_message)) {
    http_response_code(400);
    echo json_encode(['error' => 'Sporočilo je prazno']);
    exit;
}

// Limit message length
$user_message = substr($user_message, 0, 1000);

// Load knowledge base
$knowledge = file_get_contents(__DIR__ . '/knowledge.txt');

// Build messages
$system_prompt = "Ti si HD Web Design chatbot. Odgovarjaj kratko (1-3 stavki), prijazno in koristno. 
Uporabljaj isti jezik kot uporabnik (slovenščina, angleščina, itd).
Če ne veš odgovora, usmeri na kontakt: hercegdarko@hd-webdesign.si ali pošlji link na /#contact.
Ne izmišljuj si informacij. Bodi konkreten s cenami in podrobnostmi iz baze znanja.

## BAZA ZNANJA:
" . $knowledge;

$messages = [['role' => 'system', 'content' => $system_prompt]];

// Add conversation history (last 10 messages)
foreach (array_slice($history, -10) as $msg) {
    $messages[] = [
        'role' => $msg['role'] === 'user' ? 'user' : 'assistant',
        'content' => $msg['content']
    ];
}

$messages[] = ['role' => 'user', 'content' => $user_message];

// Call DeepSeek API
$ch = curl_init(DEEPSEEK_API_URL);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'model' => DEEPSEEK_MODEL,
        'messages' => $messages,
        'max_tokens' => MAX_TOKENS,
        'temperature' => TEMPERATURE,
    ]),
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . DEEPSEEK_API_KEY,
    ],
    CURLOPT_TIMEOUT => 30,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curl_error = curl_error($ch);
curl_close($ch);

if ($curl_error) {
    http_response_code(500);
    echo json_encode(['error' => 'Napaka pri povezavi z AI. Poskusite znova.']);
    exit;
}

if ($http_code !== 200) {
    error_log("DeepSeek API error: $http_code - $response");
    http_response_code(500);
    echo json_encode(['error' => 'AI servis ni na voljo. Poskusite znova.']);
    exit;
}

$data = json_decode($response, true);
$reply = $data['choices'][0]['message']['content'] ?? 'Odgovor ni na voljo.';

echo json_encode([
    'reply' => $reply,
    'usage' => $data['usage'] ?? null,
]);
