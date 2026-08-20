<?php
/**
 * API Proxy — forwards requests to Netlify functions
 * POST /api/proxy.php?fn=seo-audit
 * POST /api/proxy.php?fn=geo-check
 * POST /api/proxy.php?fn=ad-copy
 * POST /api/proxy.php?fn=listing-optimize
 * POST /api/proxy.php?fn=generate&host=menuboostai.netlify.app
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

$fn = $_GET['fn'] ?? '';

$allowed_fns = ['seo-audit', 'geo-check', 'ad-copy', 'listing-optimize', 'generate'];

if (!in_array($fn, $allowed_fns)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid function']);
    exit;
}

// Route to local PHP function
$localPath = __DIR__ . '/functions/' . $fn . '.php';
if (!file_exists($localPath)) {
    http_response_code(500);
    echo json_encode(['error' => 'Function not found']);
    exit;
}

// Forward the request to the local PHP script
$body = file_get_contents('php://input');
$_SERVER['REQUEST_METHOD'] = 'POST';

// Include the local function file - it handles its own headers and output
include $localPath;
