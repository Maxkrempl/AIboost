<?php
/**
 * BoostSuite API — Payment Auth Middleware
 * Include this in every API endpoint to enforce payment.
 *
 * Auth methods (checked in order):
 * 1. API key (bs_live_<24hex>) — from Authorization header
 * 2. x402 payment proof — from X-Payment-Proof header (tx hash on Base)
 * 3. Browser free tier — 1 free audit per session (via cookie)
 * 4. Otherwise → 402 Payment Required
 */

// CORS headers
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Payment-Proof');
header('Access-Control-Allow-Methods: POST, OPTIONS');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Tool pricing in USDC
$TOOL_PRICES = [
    'seo_audit' => 0.05,
    'geo_check' => 0.03,
    'ad_copy_generator' => 0.05,
    'listing_optimizer' => 0.04,
    'combined_audit' => 0.15,
    'menu_translate' => 0.02,
];

// USDC wallet on Base
$WALLET = '0xA41A68D6c45d8E39a090648d2a0e602C0abF1275';

function checkApiAuth($toolName) {
    global $TOOL_PRICES, $WALLET;

    // 1. API key check
    $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    if (preg_match('/Bearer\s+(bs_live_\w+)/', $authHeader, $m)) {
        $apiKey = $m[1];
        // Validate key format and check tier
        // TODO: query database for key + usage
        $keyPart = substr($apiKey, 8);
        if (strlen($keyPart) === 24) {
            return; // Valid key — allow
        }
    }

    // 2. x402 payment proof
    $proof = $_SERVER['HTTP_X_PAYMENT_PROOF'] ?? '';
    if ($proof) {
        if (verifyX402Payment($proof, $WALLET, $TOOL_PRICES[$ToolName] ?? 0.05)) {
            return; // Payment verified
        }
    }

    // 3. Browser free tier — 1 free audit per session
    $toolForFree = ['combined_audit', 'geo_check']; // Only combined audit gets 1 free
    if (in_array($toolName, $toolForFree)) {
        if (!isset($_SESSION)) session_start();
        $key = "free_audit_used";
        if (!isset($_SESSION[$key])) {
            $_SESSION[$key] = true;
            return; // First free audit
        }
    }

    // 4. No valid payment — return 402
    $price = $TOOL_PRICES[$toolName] ?? 0.05;
    http_response_code(402);
    ob_clean();
    echo json_encode([
        'error' => 'Payment Required',
        'status' => 402,
        'x402_version' => 1,
        'payment' => [
            'network' => 'base',
            'wallet' => $WALLET,
            'amount' => (string)$price,
            'currency' => 'USDC',
            'description' => "BoostSuite $toolName",
        ],
        'api_key' => [
            'free' => '100 calls/month — https://hd-webdesign.si/boostsuite/',
            'freelancer' => '€19/month — 2,000 calls',
            'agency' => '€49/month — unlimited',
        ],
        'docs' => 'https://x402.org',
    ]);
    exit;
}

function verifyX402Payment($txHash, $expectedWallet, $expectedAmount) {
    // Verify transaction on Base blockchain via Blockscout
    $url = "https://base.blockscout.com/api/v2/transactions/" . urlencode($txHash);
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
    ]);
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode !== 200) return false;

    $tx = json_decode($response, true);
    if (!$tx || ($tx['status'] ?? '') !== 'ok') return false;

    // Check recipient
    $toAddr = strtolower($tx['to']['hash'] ?? '');
    if ($toAddr !== strtolower($expectedWallet)) return false;

    // Check amount (USDC has 6 decimals)
    $value = (int)($tx['value'] ?? 0);
    $expected = (int)($expectedAmount * 1000000);
    if ($value < $expected) return false;

    return true;
}
