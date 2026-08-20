<?php
/**
 * AI Authority — Stripe Webhook
 * POST /api/ai-authority/webhook.php
 * 
 * Handles checkout.session.completed and subscription events
 * Verifies Stripe signature for security
 */

require_once '/home/hdwebd88/public_html/data/db.php';

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
    $verified = false;
    $elements = [];
    
    foreach (explode(',', $sigHeader) as $pair) {
        $parts = explode('=', trim($pair), 2);
        if (count($parts) === 2) {
            $elements[$parts[0]] = $parts[1];
        }
    }
    
    if (isset($elements['t'], $elements['v1'])) {
        $signedPayload = $elements['t'] . '.' . $payload;
        $expectedSig = hash_hmac('sha256', $signedPayload, $webhookSecret);
        
        if (hash_equals($expectedSig, $elements['v1'])) {
            $verified = true;
        }
    }
    
    if (!$verified) {
        http_response_code(401);
        echo json_encode(['error' => 'Invalid signature']);
        exit;
    }
}

$event = json_decode($payload, true);
$eventType = $event['type'] ?? 'unknown';
$data = $event['data']['object'] ?? [];

$db = getDb();

switch ($eventType) {
    case 'checkout.session.completed':
        $sessionId = $data['id'] ?? '';
        $customerEmail = $data['customer_email'] ?? $data['customer_details']['email'] ?? '';
        $customerName = $data['customer_details']['name'] ?? '';
        $amount = $data['amount_total'] ?? 0;
        $metadata = $data['metadata'] ?? [];
        $product = $metadata['product'] ?? 'AI Authority';
        
        $productType = stripos($product, 'monthly') !== false ? 'ai_authority_monthly' : 'ai_authority';
        
        // Check if already exists
        $existing = $db->prepare('SELECT id FROM orders WHERE stripe_session_id = ?');
        $existing->execute([$sessionId]);
        
        if (!$existing->fetch()) {
            $shieldStart = date('Y-m-d H:i:s');
            $shieldEnd = date('Y-m-d H:i:s', strtotime('+3 months'));
            
            $stmt = $db->prepare('INSERT INTO orders (stripe_session_id, stripe_customer_email, customer_name, product, amount, status, shield_start, shield_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?)');
            $stmt->execute([$sessionId, $customerEmail, $customerName, $productType, $amount, 'active', $shieldStart, $shieldEnd]);
            
            $orderId = $db->lastInsertId();
            
            // Log + email notification
            file_put_contents('/home/hdwebd88/public_html/data/orders.log', date('c') . " | webhook | #$orderId | $product | $customerEmail | $customerName\n", FILE_APPEND | LOCK_EX);
            
            $subject = "🎉 Nova naročnina: $product — $customerEmail";
            $body = "Nova naročnina AI Authority Foundation!\n\n";
            $body .= "📦 Produkt: $product\n";
            $body .= "📧 Email: $customerEmail\n";
            $body .= "👤 Ime: $customerName\n";
            $body .= "💰 Znesek: " . ($amount / 100) . " EUR\n";
            $body .= "🆔 Order ID: #$orderId\n";
            $body .= "🛡️ Shield do: $shieldEnd\n\n";
            $body .= "🔗 Admin: https://hd-webdesign.si/ai-authority/admin.html\n";
            
            @mail('hercegdarko@hd-webdesign.si', $subject, $body, "From: max@hd-webdesign.si\r\nReply-To: $customerEmail");
        }
        break;
    
    case 'customer.subscription.deleted':
        $subId = $data['id'] ?? '';
        if ($subId) {
            $db->prepare("UPDATE orders SET status = 'cancelled' WHERE stripe_subscription_id = ?")->execute([$subId]);
        }
        break;
    
    case 'invoice.payment_failed':
        $subId = $data['subscription'] ?? '';
        if ($subId) {
            $db->prepare("UPDATE orders SET status = 'payment_failed' WHERE stripe_subscription_id = ?")->execute([$subId]);
        }
        break;
}

header('Content-Type: application/json');
echo json_encode(['received' => true]);
