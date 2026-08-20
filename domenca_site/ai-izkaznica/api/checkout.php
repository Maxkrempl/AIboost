<?php
/**
 * Create Stripe Checkout Session for Full PDF Report (€50)
 * POST /ai-izkaznica/api/checkout.php
 * Body: { "domain": "example.si", "email": "user@example.com" }
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'POST required']); exit; }

$input = json_decode(file_get_contents('php://input'), true);
$domain = $input['domain'] ?? '';
$email = $input['email'] ?? '';

$domain = preg_replace('/^https?:\/\//', '', $domain);
$domain = preg_replace('/\/.*$/', '', $domain);
$domain = preg_replace('/[^a-z0-9.-]/i', '', $domain);

if (empty($domain) || empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Valid domain and email required']);
    exit;
}

// Stripe config
$stripe_key = '***REMOVED***';

// Create checkout session via Stripe API
$checkout_data = json_encode([
    'payment_method_types' => ['card'],
    'line_items' => [[
        'price_data' => [
            'currency' => 'eur',
            'product_data' => [
                'name' => "AI Visibility Full Report — {$domain}",
                'description' => 'Celovito PDF poročilo z analizo, priložnostmi in priporočili',
            ],
            'unit_amount' => 2000, // €50.00
        ],
        'quantity' => 1,
    ]],
    'mode' => 'payment',
    'success_url' => "https://hd-webdesign.si/ai-izkaznica/?domain={$domain}&paid=1",
    'cancel_url' => "https://hd-webdesign.si/ai-izkaznica/?domain={$domain}&cancelled=1",
    'customer_email' => $email,
    'metadata' => [
        'domain' => $domain,
        'email' => $email,
        'product' => 'ai-report-full',
    ],
]);

$ch = curl_init('https://api.stripe.com/v1/checkout/sessions');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query(json_decode($checkout_data, true)),
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $stripe_key,
        'Content-Type: application/x-www-form-urlencoded',
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$result = json_decode($response, true);

if ($http_code === 200 && isset($result['url'])) {
    echo json_encode([
        'checkout_url' => $result['url'],
        'session_id' => $result['id'],
    ]);
} else {
    http_response_code(500);
    echo json_encode([
        'error' => 'Stripe checkout failed',
        'detail' => $result['error']['message'] ?? 'Unknown error',
    ]);
}
