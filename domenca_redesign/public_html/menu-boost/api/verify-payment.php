<?php
/**
 * MenuBoost — Verify Stripe Payment
 * POST /api/verify-payment.php
 * Body: { "session_id": "cs_xxx" }
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'Method not allowed']); exit; }

$input = json_decode(file_get_contents('php://input'), true);
$sessionId = $input['session_id'] ?? null;

if (!$sessionId) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing session_id']);
    exit;
}

// Load Stripe config
$configFile = '/home/hdwebd88/.config/stripe-config.php';
if (!file_exists($configFile)) {
    http_response_code(500);
    echo json_encode(['error' => 'Stripe config not found']);
    exit;
}
$config = require $configFile;

// Verify session with Stripe
$ch = curl_init("https://api.stripe.com/v1/checkout/sessions/{$sessionId}");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $config['secret_key'],
    ],
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode !== 200) {
    echo json_encode(['paid' => false, 'error' => 'Invalid session']);
    exit;
}

$session = json_decode($response, true);

// Check if payment was successful
$isPaid = ($session['payment_status'] === 'paid') || ($session['status'] === 'complete');

echo json_encode([
    'paid' => $isPaid,
    'status' => $session['status'] ?? 'unknown',
    'payment_status' => $session['payment_status'] ?? 'unknown',
]);
