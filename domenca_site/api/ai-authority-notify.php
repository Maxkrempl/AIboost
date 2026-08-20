<?php
/**
 * AI Authority Foundation — notify on new order
 * POST /api/ai-authority-notify.php
 * Body: { "url": "...", "email": "...", "name": "...", "notes": "..." }
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

$input = json_decode(file_get_contents('php://input'), true);

$url = $input['url'] ?? '';
$email = $input['email'] ?? '';
$name = $input['name'] ?? 'Ni podano';
$notes = $input['notes'] ?? 'Ni opomb';
$product = $input['product'] ?? 'AI Authority Foundation';
$session_id = $input['session_id'] ?? 'ni znano';

if (!$url || !$email) {
    http_response_code(400);
    echo json_encode(['error' => 'Manjkata URL in email']);
    exit;
}

// Send email notification to Darko
$to = 'hercegdarko@hd-webdesign.si';
$subject = "🎉 Nova naročnina: $product — $url";

$body = "Nova naročnina AI Authority Foundation!\n\n";
$body .= "📦 Produkt: $product\n";
$body .= "🌐 URL strani: $url\n";
$body .= "📧 Email stranke: $email\n";
$body .= "👤 Ime: $name\n";
$body .= "📝 Opombe: $notes\n";
$body .= "🔑 Session ID: $session_id\n\n";
$body .= "⏰ Čas: " . date('Y-m-d H:i:s') . "\n\n";
$body .= "NASLEDNJI KORAKI:\n";
$body .= "1. Preveri stran (SEO, Schema.org, llms.txt)\n";
$body .= "2. Pripravi optimizirane datoteke\n";
$body .= "3. Pošlji stranki v 24 urah\n";

$headers = "From: max@hd-webdesign.si\r\n";
$headers .= "Reply-To: $email\r\n";
$headers .= "X-Mailer: HD-WebDesign/1.0";

$sent = mail($to, $subject, $body, $headers);

// Also try to log to a file for backup
$log_entry = date('Y-m-d H:i:s') . " | $product | $url | $email | $name | $session_id\n";
file_put_contents('/home/hdwebd88/logs/ai-authority-orders.log', $log_entry, FILE_APPEND | LOCK_EX);

echo json_encode([
    'success' => true,
    'message' => 'Obvestilo poslano',
    'email_sent' => $sent
]);
