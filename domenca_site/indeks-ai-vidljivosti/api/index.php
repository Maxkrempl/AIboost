<?php
/**
 * AI Visibility Index — API
 * GET /indeks-ai-vidljivosti/api/index.php — list all entries
 * POST /indeks-ai-vidljivosti/api/index.php — add new entry
 * PUT /indeks-ai-vidljivosti/api/index.php — update entry
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

$DB_FILE = __DIR__ . '/data.json';

function loadDB() {
    global $DB_FILE;
    if (!file_exists($DB_FILE)) return [];
    return json_decode(file_get_contents($DB_FILE), true) ?: [];
}

function saveDB($data) {
    global $DB_FILE;
    file_put_contents($DB_FILE, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}

// Industry detection based on domain/content keywords
function detectIndustry($domain, $body = '') {
    $d = strtolower($domain . ' ' . $body);
    
    $rules = [
        'Banke in zavarovalnice' => ['bank', 'zavar', 'insurance', 'finance', 'kredit', 'leasing', 'skladi', 'invest'],
        'Telekom in IT' => ['telekom', 'telecom', 'internet', 'digital', 'software', 'tech', 'IT ', 'cyber', 'cloud'],
        'Trgovina' => ['trgovin', 'shop', 'store', 'market', 'mall', 'prodaj', 'nakup', 'spletna trgov'],
        'Energetika in industrija' => ['energij', 'elektr', 'plin', 'nafta', 'industri', 'proizvodn', 'jekl', 'kovin'],
        'Turizem in gostinstvo' => ['hotel', 'turizem', 'resort', 'spa', 'wellness', 'gostiln', 'restavrac', 'apartm'],
        'Farmacija in kemija' => ['pharm', 'zdravil', 'lekarn', 'kemij', 'laborator'],
        'FMCG in prehrana' => ['prehran', 'food', 'pivovarn', 'mlekar', 'mesar', 'pekarn', 'pijač'],
        'Promet in logistika' => ['logisti', 'transport', 'luka', 'pošta', 'dostav', 'shipping'],
        'Mediji' => ['medijs', 'novice', 'časopis', 'TV ', 'radio', 'portal', 'news'],
        'Gradnja in nepremičnine' => ['nepremičnin', 'gradnja', 'construction', 'real estate', 'arhitekt'],
        'Šport' => ['sport', 'nk ', 'fk ', 'klub', 'stadion'],
        'Avtomobilska in mobilnost' => ['avto', 'automobil', 'mobilnost', 'vozil', 'motor'],
    ];
    
    foreach ($rules as $industry => $keywords) {
        foreach ($keywords as $kw) {
            if (strpos($d, $kw) !== false) return $industry;
        }
    }
    return 'Ostalo';
}

function getStats($entries) {
    $total = count($entries);
    $grades = ['A'=>0, 'B'=>0, 'C'=>0, 'D'=>0, 'F'=>0];
    $sectors = [];
    $invisible = 0;
    $with_llms = 0;
    $with_schema = 0;
    
    foreach ($entries as $e) {
        $g = $e['grade'] ?? 'F';
        $grades[$g] = ($grades[$g] ?? 0) + 1;
        
        $s = $e['sector'] ?? 'Ostalo';
        if (!isset($sectors[$s])) $sectors[$s] = ['total'=>0, 'sum'=>0];
        $sectors[$s]['total']++;
        $sectors[$s]['sum'] += $e['score'] ?? 0;
        
        if (($e['score'] ?? 0) < 30) $invisible++;
        if (!empty($e['checks']['llms']['pass'])) $with_llms++;
        if (!empty($e['checks']['schema']['pass'])) $with_schema++;
    }
    
    return [
        'total' => $total,
        'grades' => $grades,
        'invisible_pct' => $total > 0 ? round($invisible / $total * 100) : 0,
        'no_llms_pct' => $total > 0 ? round(($total - $with_llms) / $total * 100) : 0,
        'no_schema_pct' => $total > 0 ? round(($total - $with_schema) / $total * 100) : 0,
        'grade_a_pct' => $total > 0 ? round($grades['A'] / $total * 100) : 0,
        'sectors' => $sectors,
    ];
}

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $db = loadDB();
    $stats = getStats($db);
    echo json_encode(['entries' => $db, 'stats' => $stats], JSON_UNESCAPED_UNICODE);
    exit;
}

if ($method === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $domain = $input['domain'] ?? '';
    $domain = preg_replace('/^https?:\/\//', '', $domain);
    $domain = preg_replace('/\/.*$/', '', $domain);
    
    if (empty($domain)) { http_response_code(400); echo json_encode(['error'=>'domain required']); exit; }
    
    $db = loadDB();
    
    // Check if already exists
    foreach ($db as $i => $e) {
        if ($e['domain'] === $domain) {
            // Update — never downgrade visible from true to false
            $update = array_merge($db[$i], $input);
            if (!empty($db[$i]['visible']) && isset($input['visible']) && $input['visible'] === false) {
                $update['visible'] = true; // keep visible
            }
            $update['updated_at'] = date('c');
            $db[$i] = $update;
            saveDB($db);
            echo json_encode($db[$i], JSON_UNESCAPED_UNICODE);
            exit;
        }
    }
    
    // Use user-provided sector or auto-detect
    $sector = !empty($input['sector']) ? $input['sector'] : detectIndustry($domain, json_encode($input));
    
    $entry = array_merge([
        'id' => uniqid(),
        'domain' => $domain,
        'sector' => $sector,
        'created_at' => date('c'),
        'updated_at' => date('c'),
        'visible' => false,
    ], $input);
    
    $entry['sector'] = $sector;
    $db[] = $entry;
    saveDB($db);
    
    echo json_encode($entry, JSON_UNESCAPED_UNICODE);
    exit;
}

if ($method === 'PUT') {
    $input = json_decode(file_get_contents('php://input'), true);
    $id = $input['id'] ?? '';
    
    $db = loadDB();
    foreach ($db as $i => $e) {
        if ($e['id'] === $id) {
            $db[$i] = array_merge($db[$i], $input);
            $db[$i]['updated_at'] = date('c');
            saveDB($db);
            echo json_encode($db[$i], JSON_UNESCAPED_UNICODE);
            exit;
        }
    }
    
    http_response_code(404);
    echo json_encode(['error'=>'not found']);
}
