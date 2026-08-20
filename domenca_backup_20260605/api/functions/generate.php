<?php
/**
 * Generate — Unified AI generation function
 * POST /api/functions/generate.php
 * 
 * Handles two request formats:
 * 1. MenuBoost: { "prompt": "..." } → returns { "content": [{ "text": "..." }, ...] }
 * 2. AdBoost:   { "template": "...", "product": "...", "audience": "...", "tone": "...", "CTA": "..." }
 *               → returns { "success": true, "content": "..." }
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

$DEEPSEEK_KEY = '***REMOVED***';

$input = json_decode(file_get_contents('php://input'), true);
if (!$input) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON input']);
    exit;
}

// Detect request type
if (isset($input['prompt'])) {
    // MenuBoost mode
    $userPrompt = $input['prompt'];
    
    $system = "You are a professional restaurant menu description writer. Generate appetizing, multilingual menu descriptions. Respond with ONLY valid JSON.";
    
    $aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $userPrompt);
    $parsed = json_decode($aiResult, true);
    
    if ($parsed && is_array($parsed)) {
        // Return the flat JSON directly — frontend expects {"en": "...", "de": "...", ...}
        echo json_encode($parsed);
    } else {
        // Raw fallback
        echo json_encode(['content' => [['text' => $aiResult]]]);
    }
} else {
    // AdBoost mode
    $template = $input['template'] ?? 'google';
    $product = $input['product'] ?? '';
    $audience = $input['audience'] ?? '';
    $tone = $input['tone'] ?? 'professional';
    $cta = $input['CTA'] ?? 'Learn More';

    if (!$product || !$audience) {
        http_response_code(400);
        echo json_encode(['error' => 'Product and audience are required']);
        exit;
    }

    $system = "You are an expert advertising copywriter. Generate compelling ad copy.";
    $user = "Create a $template ad for:\nProduct: $product\nTarget Audience: $audience\nTone: $tone\nCall to Action: $cta\n\nProvide the ad copy in a professional format.";

    $aiResult = callDeepSeek($DEEPSEEK_KEY, $system, $user);
    
    if ($aiResult) {
        echo json_encode(['success' => true, 'content' => $aiResult]);
    } else {
        echo json_encode(['success' => false, 'error' => 'Failed to generate content']);
    }
}

function callDeepSeek($key, $system, $user) {
    $ch = curl_init('https://api.deepseek.com/v1/chat/completions');
    curl_setopt_array($ch, array(
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => array('Content-Type: application/json', 'Authorization: Bearer ' . $key),
        CURLOPT_POSTFIELDS => json_encode(array(
            'model' => 'deepseek-chat',
            'messages' => array(
                array('role' => 'system', 'content' => $system),
                array('role' => 'user', 'content' => $user),
            ),
            'temperature' => 0.7,
            'max_tokens' => 1000,
        )),
        CURLOPT_TIMEOUT => 30,
    ));
    $resp = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode !== 200) {
        return '';
    }
    
    $data = json_decode($resp, true);
    if (isset($data['choices'][0]['message']['content'])) {
        return $data['choices'][0]['message']['content'];
    }
    return '';
}