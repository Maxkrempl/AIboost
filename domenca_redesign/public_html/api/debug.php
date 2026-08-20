<?php
/**
 * Debug endpoint — logs all request details
 */
header('Content-Type: application/json');

$log = [
    'time' => date('Y-m-d H:i:s'),
    'method' => $_SERVER['REQUEST_METHOD'],
    'content_type' => $_SERVER['CONTENT_TYPE'] ?? 'none',
    'content_length' => $_SERVER['CONTENT_LENGTH'] ?? '0',
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'none',
    'origin' => $_SERVER['HTTP_ORIGIN'] ?? 'none',
    'referer' => $_SERVER['HTTP_REFERER'] ?? 'none',
    'body' => substr(file_get_contents('php://input'), 0, 500),
];

file_put_contents('/tmp/debug_requests.log', json_encode($log) . "\n", FILE_APPEND);

echo json_encode(['status' => 'ok', 'logged' => true]);
