<?php
/**
 * Import existing audit results into API data.json
 * Run once: curl -X POST https://hd-webdesign.si/indeks-ai-vidljivosti/api/import.php
 */

header('Content-Type: application/json');

$JSON_FILE = '/home/darko/.openclaw/workspace/tools/ai_visibility_results.json';
$DB_FILE = __DIR__ . '/data.json';

if (!file_exists($JSON_FILE)) {
    echo json_encode(['error' => 'JSON file not found']);
    exit;
}

$results = json_decode(file_get_contents($JSON_FILE), true);
if (!$results) {
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// Industry detection
function detectIndustry($domain, $name = '') {
    $d = strtolower($domain . ' ' . $name);
    $rules = [
        'Banke in zavarovalnice' => ['bank', 'zavar', 'insurance', 'finance', 'kredit', 'leasing', 'skladi', 'invest', 'intesa', 'sparkasse', 'kd-group', 'triglav', 'modra', 'generali'],
        'Telekom in IT' => ['telekom', 'telecom', 'internet', 'digital', 'software', 'tech', 'cyber', 'cloud', 't-2', 'telemach', 'a1.si', 'iskratel', 'bitstamp', 'src.si'],
        'Trgovina' => ['trgovin', 'shop', 'store', 'market', 'mall', 'prodaj', 'nakup', 'spletna trgov', 'dm.si', 'hervis', 'eurospin', 'spar', 'mercator', 'jager'],
        'Energetika in industrija' => ['energij', 'elektr', 'plin', 'nafta', 'industri', 'proizvodn', 'jekl', 'kovin', 'salonit', 'cinkarna', 'eles', 'hse', 'helios', 'jub', 'belinka', 'hidria'],
        'Turizem in gostinstvo' => ['hotel', 'turizem', 'resort', 'spa', 'wellness', 'gostiln', 'restavrac', 'apartm', 'bernardin', 'olimia', 'terme', 'hit.si', 'grandkoper', 'sava-hotels'],
        'Farmacija in kemija' => ['pharm', 'zdravil', 'lekarn', 'kemij', 'laborator', 'krka', 'kemiplas', 'lek'],
        'FMCG in prehrana' => ['prehran', 'food', 'pivovarn', 'mlekar', 'mesar', 'pekarn', 'pijač', 'gorenje', 'mlinotest', 'fructal', 'celeia', 'l-m.si', 'lasko.eu', 'union'],
        'Promet in logistika' => ['logisti', 'transport', 'luka', 'pošta', 'dostav', 'shipping', 'intereuropa'],
        'Mediji' => ['medijs', 'novice', 'časopis', 'tv ', 'radio', 'portal', 'news', 'vecer', 'mladina', 'finance.si', '24ur'],
        'Gradnja in nepremičnine' => ['nepremičnin', 'gradnja', 'construction', 'real estate', 'arhitekt', 'tiglav', 'aplace'],
        'Šport' => ['sport', 'nk ', 'fk ', 'klub', 'stadion', 'nkmaribor'],
        'Avtomobilska in mobilnost' => ['avto', 'automobil', 'mobilnost', 'vozil', 'motor', 'revoz'],
    ];
    foreach ($rules as $industry => $keywords) {
        foreach ($keywords as $kw) {
            if (strpos($d, $kw) !== false) return $industry;
        }
    }
    return 'Ostalo';
}

$entries = [];
foreach ($results as $r) {
    $sector = detectIndustry($r['domena'] ?? '', $r['podjetje'] ?? '');
    $entries[] = [
        'id' => uniqid(),
        'domain' => $r['domena'] ?? '',
        'podjetje' => $r['podjetje'] ?? '',
        'score' => $r['score'] ?? 0,
        'grade' => $r['razred'] ?? 'F',
        'sector' => $r['sektor'] ?? $sector,
        'checks' => [
            'main' => ['pass' => ($r['http_status'] ?? 0) == 200],
            'llms' => ['pass' => !empty($r['llms_txt'])],
            'schema' => ['pass' => !empty($r['schema_org'])],
            'meta' => ['pass' => !empty($r['meta_description'])],
            'og' => ['pass' => !empty($r['og_tags'])],
            'sitemap' => ['pass' => !empty($r['sitemap'])],
            'robots' => ['pass' => !empty($r['robots_txt'])],
        ],
        'visible' => true,
        'created_at' => date('c'),
        'updated_at' => date('c'),
    ];
}

file_put_contents($DB_FILE, json_encode($entries, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));

echo json_encode(['imported' => count($entries), 'file' => $DB_FILE]);
