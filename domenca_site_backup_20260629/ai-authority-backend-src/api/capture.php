<?php
/**
 * AI Authority — Capture Order from Success Page
 * POST /api/ai-authority/capture.php
 * Body: { "url": "...", "email": "...", "name": "...", "notes": "...", "session_id": "..." }
 * 
 * Called from success-ai-authority.html after Stripe payment
 * Creates order in DB + sends notification email
 */

require_once '/home/hdwebd88/public_html/data/db.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://hd-webdesign.si');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);

$url = $input['url'] ?? '';
$email = $input['email'] ?? '';
$name = $input['name'] ?? 'Ni podano';
$notes = $input['notes'] ?? '';
$sessionId = $input['session_id'] ?? '';
$product = $input['product'] ?? 'ai_authority';

if (!$url || !$email) {
    http_response_code(400);
    echo json_encode(['error' => 'URL and email required']);
    exit;
}

$db = getDb();

// Check if order already exists for this session
if ($sessionId) {
    $existing = $db->prepare('SELECT id FROM orders WHERE stripe_session_id = ?');
    $existing->execute([$sessionId]);
    $row = $existing->fetch();
    
    if ($row) {
        // Update existing order
        $stmt = $db->prepare("UPDATE orders SET customer_url = ?, customer_name = ?, customer_notes = ?, updated_at = datetime('now') WHERE id = ?");
        $stmt->execute([$url, $name, $notes, $row['id']]);
        $orderId = $row['id'];
    } else {
        // Create new order
        $shieldStart = date('Y-m-d H:i:s');
        $shieldEnd = date('Y-m-d H:i:s', strtotime('+3 months'));
        
        $stmt = $db->prepare('INSERT INTO orders (stripe_session_id, stripe_customer_email, customer_name, customer_url, customer_notes, product, amount, status, shield_start, shield_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([$sessionId, $email, $name, $url, $notes, $product, 69900, 'active', $shieldStart, $shieldEnd]);
        $orderId = $db->lastInsertId();
    }
} else {
    // No session ID — create order anyway
    $shieldStart = date('Y-m-d H:i:s');
    $shieldEnd = date('Y-m-d H:i:s', strtotime('+3 months'));
    
    $stmt = $db->prepare('INSERT INTO orders (stripe_customer_email, customer_name, customer_url, customer_notes, product, amount, status, shield_start, shield_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)');
    $stmt->execute([$email, $name, $url, $notes, $product, 69900, 'active', $shieldStart, $shieldEnd]);
    $orderId = $db->lastInsertId();
}

// Send notification email to Darko
$subject = "🎉 Nova naročnina: AI Authority — $url";
$body = "Nova naročnina AI Authority Foundation!\n\n";
$body .= "🌐 URL strani: $url\n";
$body .= "📧 Email stranke: $email\n";
$body .= "👤 Ime: $name\n";
$body .= "📝 Opombe: $notes\n";
$body .= "🆔 Order ID: #$orderId\n";
$body .= "🔑 Stripe Session: $sessionId\n\n";
$body .= "⏰ Čas: " . date('Y-m-d H:i:s') . "\n";
$body .= "🛡️ Shield do: " . date('Y-m-d H:i:s', strtotime('+3 months')) . "\n\n";
$body .= "🔗 Admin: https://hd-webdesign.si/ai-authority/admin.html\n\n";
$body .= "NASLEDNJI KORAKI:\n";
$body .= "1. Pojdi na admin dashboard\n";
$body .= "2. Zaženi GEO audit za $url\n";
$body .= "3. Generiraj llms.txt in Schema.org\n";
$body .= "4. Pošlji stranki v 24 urah\n";

// Log order to file (non-blocking)
file_put_contents('/home/hdwebd88/public_html/data/orders.log', date('c') . ' | ' . json_encode($input) . "\n", FILE_APPEND | LOCK_EX);

echo json_encode([
    'success' => true,
    'order_id' => $orderId,
    'message' => 'Naročilo shranjeno, obvestilo poslano',
]);
