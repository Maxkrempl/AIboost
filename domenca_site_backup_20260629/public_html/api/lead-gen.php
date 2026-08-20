<?php
/**
 * Lead Generator API Endpoint
 * 
 * POST /api/lead-gen.php
 * {
 *   "type": "restaurant",
 *   "location": "Ljubljana, Slovenia",
 *   "email": "user@example.com",
 *   "limit": 10
 * }
 * 
 * Returns: CSV file as attachment or JSON with lead data
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://hd-webdesign.si');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get POST data
$input = json_decode(file_get_contents('php://input'), true);

if (!$input) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$type = $input['type'] ?? 'restaurant';
$location = $input['location'] ?? '';
$email = $input['email'] ?? '';
$limit = min((int)($input['limit'] ?? 10), 50); // Max 50 for free tier

if (empty($location)) {
    http_response_code(400);
    echo json_encode(['error' => 'Location is required']);
    exit;
}

if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Valid email is required']);
    exit;
}

// Valid business types
$valid_types = ['restaurant', 'cafe', 'bar', 'hotel', 'fast_food', 'dentist', 'doctor', 'gym', 'salon', 'mechanic'];
if (!in_array($type, $valid_types)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid business type']);
    exit;
}

// Run the lead generator script
$script_path = '/home/hdwebd88/lead-gen/lead-generator/overpass_leads.py';
$escaped_location = escapeshellarg($location);
$escaped_type = escapeshellarg($type);
$escaped_email = escapeshellarg($email);

$cmd = "python3 {$script_path} --type {$escaped_type} --location {$escaped_location} --limit {$limit} --email {$escaped_email} 2>&1";
$output = shell_exec($cmd);

// Parse output to get stats
$stats = [
    'total' => 0,
    'with_email' => 0,
    'with_phone' => 0,
    'with_website' => 0,
];

if (preg_match('/Total:\s+(\d+)/', $output, $matches)) {
    $stats['total'] = (int)$matches[1];
}
if (preg_match('/With email:\s+(\d+)/', $output, $matches)) {
    $stats['with_email'] = (int)$matches[1];
}
if (preg_match('/With phone:\s+(\d+)/', $output, $matches)) {
    $stats['with_phone'] = (int)$matches[1];
}
if (preg_match('/With website:\s+(\d+)/', $output, $matches)) {
    $stats['with_website'] = (int)$matches[1];
}

// Check if email was sent
$email_sent = strpos($output, 'Email sent to') !== false;

echo json_encode([
    'success' => true,
    'stats' => $stats,
    'email_sent' => $email_sent,
    'message' => $email_sent 
        ? "Found {$stats['total']} leads. Email sent to {$email}."
        : "Found {$stats['total']} leads but email delivery failed.",
]);
