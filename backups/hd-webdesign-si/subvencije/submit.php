<?php
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
    echo json_encode(['success' => false, 'error' => 'Method not allowed']);
    exit;
}

// Rate limiting
$rate_file = sys_get_temp_dir() . '/subvencije_rate_' . md5($_SERVER['REMOTE_ADDR'] ?? 'unknown');
$rate_limit = 5;
$rate_window = 3600;

if (file_exists($rate_file)) {
    $rate_data = json_decode(file_get_contents($rate_file), true);
    if ($rate_data && time() - $rate_data['first'] < $rate_window) {
        if ($rate_data['count'] >= $rate_limit) {
            echo json_encode(['success' => false, 'error' => 'Preveč poskusov. Poskusite čez eno uro.']);
            exit;
        }
        $rate_data['count']++;
    } else {
        $rate_data = ['first' => time(), 'count' => 1];
    }
} else {
    $rate_data = ['first' => time(), 'count' => 1];
}
file_put_contents($rate_file, json_encode($rate_data));

// Sanitize input
$name = trim(htmlspecialchars($_POST['name'] ?? ''));
$email = filter_var(trim($_POST['email'] ?? ''), FILTER_VALIDATE_EMAIL);
$phone = trim(htmlspecialchars($_POST['phone'] ?? ''));
$company = trim(htmlspecialchars($_POST['company'] ?? ''));
$activity = trim(htmlspecialchars($_POST['activity'] ?? ''));
$funding = trim(htmlspecialchars($_POST['funding'] ?? ''));
$description = trim(htmlspecialchars($_POST['description'] ?? ''));

// Validate required fields
if (!$name || !$email || !$activity) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Manjkajo obvezna polja (ime, email, dejavnost).']);
    exit;
}

// Labels
$activity_labels = [
    'it' => 'IT / SaaS / Digitalne rešitve',
    'tourism' => 'Turizem / Gostinstvo',
    'manufacturing' => 'Proizvodnja',
    'agriculture' => 'Kmetijstvo',
    'services' => 'Storitve',
    'trade' => 'Trgovina',
    'other' => 'Drugo',
];

$funding_labels = [
    'small' => 'Do €10.000',
    'medium' => '€10.000 - €50.000',
    'large' => '€50.000 - €200.000',
    'xlarge' => 'Nad €200.000',
];

$activity_text = $activity_labels[$activity] ?? $activity;
$funding_text = $funding_labels[$funding] ?? ($funding ?: 'Ni podano');

// Build email body
$body = "Novo povpraševanje s strani hd-webdesign.si/subvencije:\n\n";
$body .= "👤 Ime: {$name}\n";
$body .= "📧 Email: {$email}\n";
if ($phone) $body .= "📞 Telefon: {$phone}\n";
if ($company) $body .= "🏢 Podjetje: {$company}\n";
$body .= "📋 Dejavnost: {$activity_text}\n";
$body .= "💰 Sredstva: {$funding_text}\n";
if ($description) $body .= "📝 Opis: {$description}\n";
$body .= "\n---\nPoslano z hd-webdesign.si/subvencije";

// Send via Resend API
$api_key = '***REMOVED***';

$payload = json_encode([
    'from' => 'HD Web Design <max@hd-webdesign.si>',
    'to' => ['rose@hd-webdesign.si'],
    'reply_to' => $email,
    'subject' => "Novo povpraševanje — Subvencije od {$name}",
    'text' => $body,
]);

$ch = curl_init('https://api.resend.com/emails');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Authorization: Bearer ' . $api_key,
        'Content-Type: application/json',
    ],
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 15,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code >= 200 && $http_code < 300) {
    echo json_encode(['success' => true, 'message' => 'Hvala za vaše povpraševanje! Odgovorili vam bomo v 24 urah.']);
} else {
    error_log("Resend API error: {$http_code} — {$response}");
    http_response_code(500);
    echo json_encode(['success' => false, 'error' => 'Napaka pri pošiljanju. Poskusite znova.']);
}
