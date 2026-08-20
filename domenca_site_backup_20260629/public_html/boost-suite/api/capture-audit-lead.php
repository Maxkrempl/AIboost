<?php
// BoostSuite Audit Lead Capture
// Saves email + audit results for outreach follow-up

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);

if (!$input || empty($input['email']) || empty($input['url'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Email and URL are required']);
    exit;
}

$email = filter_var(trim($input['email']), FILTER_VALIDATE_EMAIL);
if (!$email) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email address']);
    exit;
}

$url = trim($input['url']);
$score = isset($input['score']) ? intval($input['score']) : 0;
$grade = isset($input['grade']) ? trim($input['grade']) : '';
$categoryScores = isset($input['categoryScores']) ? $input['categoryScores'] : [];
$topIssues = isset($input['topIssues']) ? $input['topIssues'] : [];
$timestamp = date('Y-m-d H:i:s');

// Determine outreach priority based on score
$priority = 'low';
$offerType = '';
if ($score < 40) {
    $priority = 'critical';
    $offerType = 'SEO + GEO Audit';
} elseif ($score < 60) {
    $priority = 'high';
    $offerType = 'SEO Optimization';
} elseif ($score < 80) {
    $priority = 'medium';
    $offerType = 'Performance Boost';
}

// Save to CSV
$csvFile = __DIR__ . '/audit-leads.csv';
$fileExists = file_exists($csvFile);

$fp = fopen($csvFile, 'a');
if (!$fp) {
    http_response_code(500);
    echo json_encode(['error' => 'Could not save data']);
    exit;
}

flock($fp, LOCK_EX);

if (!$fileExists) {
    fputcsv($fp, ['timestamp', 'email', 'url', 'score', 'grade', 'priority', 'offerType', 'seo_score', 'security_score', 'performance_score', 'accessibility_score', 'cookies_score', 'top_issues']);
}

fputcsv($fp, [
    $timestamp,
    $email,
    $url,
    $score,
    $grade,
    $priority,
    $offerType,
    $categoryScores['seo'] ?? '',
    $categoryScores['security'] ?? '',
    $categoryScores['performance'] ?? '',
    $categoryScores['accessibility'] ?? '',
    $categoryScores['cookies'] ?? '',
    implode(' | ', array_slice($topIssues, 0, 5))
]);

fflush($fp);
flock($fp, LOCK_UN);
fclose($fp);

// Also save as JSON for easier reading
$jsonFile = __DIR__ . '/audit-leads.json';
$leads = [];
if (file_exists($jsonFile)) {
    $leads = json_decode(file_get_contents($jsonFile), true) ?: [];
}

$leads[] = [
    'timestamp' => $timestamp,
    'email' => $email,
    'url' => $url,
    'score' => $score,
    'grade' => $grade,
    'priority' => $priority,
    'offerType' => $offerType,
    'categoryScores' => $categoryScores,
    'topIssues' => array_slice($topIssues, 0, 5)
];

file_put_contents($jsonFile, json_encode($leads, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

echo json_encode([
    'success' => true,
    'message' => 'Lead captured',
    'priority' => $priority,
    'offerType' => $offerType
]);
