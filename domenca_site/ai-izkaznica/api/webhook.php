<?php
/**
 * Stripe Webhook — AI Report
 * POST /ai-izkaznica/api/webhook.php
 * Handles checkout.session.completed → generates HTML report → emails it
 */

require_once __DIR__ . '/generate-report.php';

// Load webhook secret
$webhookSecret = null;
$secretFile = '/home/hdwebd88/.config/stripe-webhook-secret.php';
if (file_exists($secretFile)) {
    $config = require $secretFile;
    $webhookSecret = $config['webhook_secret'] ?? null;
}

// Verify Stripe signature
$payload = file_get_contents('php://input');
$sigHeader = $_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '';

if ($webhookSecret && $sigHeader) {
    $elements = [];
    foreach (explode(',', $sigHeader) as $pair) {
        $parts = explode('=', trim($pair), 2);
        if (count($parts) === 2) $elements[$parts[0]] = $parts[1];
    }
    if (isset($elements['t'], $elements['v1'])) {
        $signedPayload = $elements['t'] . '.' . $payload;
        $expectedSig = hash_hmac('sha256', $signedPayload, $webhookSecret);
        if (!hash_equals($expectedSig, $elements['v1'] ?? '')) {
            http_response_code(401);
            echo json_encode(['error' => 'Invalid signature']);
            exit;
        }
    }
}

$event = json_decode($payload, true);
$eventType = $event['type'] ?? 'unknown';
$data = $event['data']['object'] ?? [];

if ($eventType !== 'checkout.session.completed') {
    echo json_encode(['status' => 'ignored', 'type' => $eventType]);
    exit;
}

// Only handle AI Report purchases
$product = $data['metadata']['product'] ?? '';
if ($product !== 'ai-report-full') {
    echo json_encode(['status' => 'ignored', 'product' => $product]);
    exit;
}

$domain = $data['metadata']['domain'] ?? '';
$email = $data['metadata']['email'] ?? $data['customer_email'] ?? $data['customer_details']['email'] ?? '';
$session_id = $data['id'] ?? '';

if (empty($domain) || empty($email)) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing domain or email']);
    exit;
}

// Log purchase
$log_dir = '/home/hdwebd88/public_html/data/ai-reports';
if (!is_dir($log_dir)) mkdir($log_dir, 0755, true);

file_put_contents($log_dir . '/purchases.json',
    json_encode(['domain'=>$domain,'email'=>$email,'session_id'=>$session_id,'paid_at'=>date('Y-m-d H:i:s'),'amount'=>50]) . "\n",
    FILE_APPEND | LOCK_EX
);

// Generate HTML report
$html = generateReportHTML($domain);
if (!$html) {
    http_response_code(500);
    echo json_encode(['error' => 'Report generation failed']);
    exit;
}

// Send via Resend
$re_api_key = '***REMOVED***';

$ch = curl_init('https://api.resend.com/emails');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'from' => 'HD Web Design <max@hd-webdesign.si>',
        'to' => [$email],
        'subject' => "AI Visibility Report — {$domain}",
        'html' => $html,
    ]),
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $re_api_key,
        'Content-Type: application/json',
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$result = json_decode($response, true);

if ($http_code === 200) {
    echo json_encode(['status' => 'sent', 'email_id' => $result['id'] ?? null, 'domain' => $domain]);
} else {
    // Fallback: SMTP
    $to = $email;
    $subject = "AI Visibility Report — {$domain}";
    $headers = "From: HD Web Design <max@hd-webdesign.si>\r\nContent-Type: text/html; charset=UTF-8\r\n";
    mail($to, $subject, $html, $headers);
    echo json_encode(['status' => 'sent_via_smtp', 'domain' => $domain]);
}
