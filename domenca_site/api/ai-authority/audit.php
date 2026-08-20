<?php
/**
 * AI Authority — Run GEO Audit
 * POST /api/ai-authority/audit.php
 * Body: { "url": "https://example.com" }
 * 
 * Returns full GEO audit report with score, checks, recommendations
 */

require_once '/home/hdwebd88/public_html/data/db.php';
require_once __DIR__ . '/geo-audit.php';

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
$url = $input['url'] ?? null;
$order_id = $input['order_id'] ?? null;

if (!$url) {
    http_response_code(400);
    echo json_encode(['error' => 'URL required']);
    exit;
}

// Validate URL
if (!filter_var($url, FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid URL']);
    exit;
}

// Run the audit
$audit = new GeoAudit($url);
$report = $audit->run();

// Generate deliverables
$llmsTxt = $audit->generateLlmsTxt();

// Store in database
$db = getDb();
$stmt = $db->prepare('INSERT INTO audits (order_id, url, score, has_llms_txt, has_schema_org, has_open_graph, has_meta_description, has_structured_data, has_robots_txt, has_sitemap, schema_types, missing_items, recommendations, raw_report) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');

$checks = $report['checks'];
$stmt->execute([
    $order_id,
    $url,
    $report['score'],
    $checks['llms_txt']['passed'] ? 1 : 0,
    $checks['schema_org']['passed'] ? 1 : 0,
    $checks['open_graph']['passed'] ? 1 : 0,
    $checks['meta_description']['passed'] ? 1 : 0,
    $checks['structured_data']['passed'] ? 1 : 0,
    $checks['robots_txt']['passed'] ? 1 : 0,
    $checks['sitemap']['passed'] ? 1 : 0,
    json_encode($report['schema_types']),
    json_encode($report['missing']),
    json_encode($report['recommendations']),
    json_encode($report),
]);

$auditId = $db->lastInsertId();

// Store generated llms.txt
$db->prepare('INSERT INTO generated_files (order_id, audit_id, file_type, content) VALUES (?, ?, ?, ?)')
   ->execute([$order_id, $auditId, 'llms_txt', $llmsTxt]);

// Generate Schema.org if missing
$schemaOrg = null;
if (!$checks['schema_org']['passed']) {
    $schemaOrg = $audit->generateSchemaOrg(
        parse_url($url, PHP_URL_HOST),
        $checks['meta_description']['detail'] ?? 'Website at ' . $url
    );
    $db->prepare('INSERT INTO generated_files (order_id, audit_id, file_type, content) VALUES (?, ?, ?, ?)')
       ->execute([$order_id, $auditId, 'schema_org', $schemaOrg]);
}

echo json_encode([
    'success' => true,
    'audit_id' => $auditId,
    'report' => $report,
    'deliverables' => [
        'llms_txt' => $llmsTxt,
        'schema_org' => $schemaOrg,
    ],
], JSON_PRETTY_PRINT);
