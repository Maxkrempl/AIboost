<?php
header('Content-Type: text/event-stream');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Cache-Control: no-cache');
header('X-Accel-Buffering: no');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$body = file_get_contents('php://input');

$ch = curl_init('http://127.0.0.1:8787/mcp');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => false,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $body,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_TIMEOUT => 60,
    CURLOPT_CONNECTTIMEOUT => 5,
    CURLOPT_WRITEFUNCTION => function($ch, $chunk) {
        echo $chunk;
        if (ob_get_level()) ob_flush();
        flush();
        return strlen($chunk);
    },
]);

$response = curl_exec($ch);
$err = curl_error($ch);
curl_close($ch);

if ($err) {
    echo "data: " . json_encode(["error" => "Proxy error: " . $err]) . "\n\n";
}
