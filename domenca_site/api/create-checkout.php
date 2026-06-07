<?php
/**
 * Stripe Checkout — creates a Checkout Session and returns the URL.
 * POST /api/create-checkout.php
 * Body: { "price_id": "price_xxx", "email": "optional@example.com" }
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://hd-webdesign.si');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Load config
$config = require '/home/hdwebd88/.config/stripe-config.php';

if (strpos($config['secret_key'], 'REPLACE') !== false) {
    http_response_code(500);
    echo json_encode(['error' => 'Stripe keys not configured yet. Add your keys to api/stripe-config.php']);
    exit;
}

// Parse input
$input = json_decode(file_get_contents('php://input'), true);
$priceId = $input['price_id'] ?? null;

if (!$priceId) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing price_id']);
    exit;
}

// Map product names to price IDs
$priceMap = [
    'menuboost' => $config['prices']['menuboost_monthly'],
    'boostsuite' => $config['prices']['boostsuite_monthly'],
    'boostsuite_freelancer' => $config['prices']['boostsuite_freelancer'],
    'boostsuite_agency' => $config['prices']['boostsuite_agency'],
];

$resolvedPrice = $priceMap[$priceId] ?? $priceId;

// Determine product name for metadata
$productName = 'Unknown';
foreach ($priceMap as $name => $id) {
    if ($id === $resolvedPrice || $name === $priceId) {
        $productName = ucfirst($name);
        break;
    }
}

// Build Stripe Checkout Session via REST API
$postData = [
    'mode' => 'subscription',
    'payment_method_types[]' => 'card',
    'line_items[0][price]' => $resolvedPrice,
    'line_items[0][quantity]' => '1',
    'success_url' => $config['success_url'] . '?session_id={CHECKOUT_SESSION_ID}',
    'cancel_url' => $config['cancel_url'],
    'metadata[product]' => $productName,
    'metadata[source]' => 'hd-webdesign.si',
    'subscription_data[metadata][product]' => $productName,
    'subscription_data[metadata][source]' => 'hd-webdesign.si',
];

// Optional: pre-fill email
if (!empty($input['email'])) {
    $postData['customer_email'] = $input['email'];
}

$ch = curl_init('https://api.stripe.com/v1/checkout/sessions');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => http_build_query($postData),
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $config['secret_key'],
    ],
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$result = json_decode($response, true);

if ($httpCode === 200 && !empty($result['url'])) {
    echo json_encode([
        'checkout_url' => $result['url'],
        'session_id' => $result['id'],
    ]);
} else {
    http_response_code(500);
    echo json_encode([
        'error' => 'Failed to create checkout session',
        'details' => $result['error']['message'] ?? 'Unknown error',
    ]);
}
