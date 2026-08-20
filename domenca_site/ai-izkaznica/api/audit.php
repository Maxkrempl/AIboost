<?php
/**
 * AI Visibility Audit API v2 — Full Audit
 * POST /ai-izkaznica/api/audit.php
 * Body: { "domain": "example.si" }
 * Returns: comprehensive audit results JSON
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); echo json_encode(['error' => 'POST required']); exit; }

$input = json_decode(file_get_contents('php://input'), true);
$domain = $input['domain'] ?? '';
$citation_test = $input['citation_test'] ?? false;
$domain = preg_replace('/^https?:\/\//', '', $domain);
$domain = preg_replace('/\/.*$/', '', $domain);
$domain = preg_replace('/[^a-z0-9.-]/i', '', $domain);

if (empty($domain) || !filter_var("https://{$domain}", FILTER_VALIDATE_URL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid domain']);
    exit;
}

// ═══ CACHE (24h) ═══
$cache_dir = __DIR__ . '/cache';
if (!is_dir($cache_dir)) mkdir($cache_dir, 0755, true);
$cache_file = $cache_dir . '/' . md5($domain) . '.json';
$cache_ttl = 86400;

if (file_exists($cache_file)) {
    $cached = json_decode(file_get_contents($cache_file), true);
    if ($cached && (time() - ($cached['cached_at'] ?? 0)) < $cache_ttl) {
        $cached['from_cache'] = true;
        echo json_encode($cached, JSON_UNESCAPED_UNICODE);
        exit;
    }
}

$base = "https://{$domain}";
$timeout = 8;

function fetch_url($url, $timeout = 8, $method = 'GET') {
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 3,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; AIVisibilityBot/1.0)',
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_NOBODY => $method === 'HEAD',
    ]);
    $response = curl_exec($ch);
    $info = curl_getinfo($ch);
    curl_close($ch);
    return ['status' => $info['http_code'], 'body' => $response, 'ok' => $info['http_code'] >= 200 && $info['http_code'] < 400, 'headers' => $info];
}

$result = [
    'domain' => $domain,
    'score' => 0,
    'checks' => [],
    'technical' => [],
    'seo' => [],
    'contact' => [],
    'opportunities' => [],
];

// ═══ SCORING CONFIG ═══
// Max raw points = 110, normalized to 0-100
$MAX_RAW = 110;
$raw_score = 0;

// ═══ 1. MAIN PAGE ═══
$main = fetch_url($base, $timeout);
$result['checks']['main'] = ['pass' => $main['ok'], 'label' => 'Dostopnost strani', 'points' => 5];
if ($main['ok']) $raw_score += 5;

$body = $main['body'];

// ═══ 2. LLMS.TXT (25 pts) ═══
$llms = fetch_url("{$base}/llms.txt", $timeout);
$llms_pass = $llms['ok'] && strlen($llms['body']) > 50;
$result['checks']['llms'] = ['pass' => $llms_pass, 'label' => 'llms.txt', 'points' => 25];
if ($llms_pass) $raw_score += 25;

// ═══ 3. SCHEMA.ORG (20 pts) ═══
preg_match_all('/<script[^>]+type=["\']application\/ld\+json["\'][^>]*>(.*?)<\/script>/si', $body, $schema_matches);
$has_schema = !empty($schema_matches[1]);
$schema_types = [];
$schema_pts = 0;
if ($has_schema) {
    foreach ($schema_matches[1] as $m) {
        $j = json_decode($m, true);
        if ($j && isset($j['@type'])) $schema_types[] = $j['@type'];
    }
    // Type-based scoring
    $important_types = ['Organization', 'LocalBusiness', 'WebSite'];
    $content_types = ['Article', 'BlogPosting', 'NewsArticle'];
    foreach ($schema_types as $t) {
        if (in_array($t, $important_types)) $schema_pts = max($schema_pts, 10);
        if (in_array($t, $content_types)) $schema_pts = max($schema_pts, 5);
        if ($t === 'FAQPage') $schema_pts = max($schema_pts, 15);
    }
    if ($schema_pts === 0 && !empty($schema_types)) $schema_pts = 5; // generic schema
}
$schema_pts = min(20, $schema_pts);
$result['checks']['schema'] = ['pass' => $has_schema, 'label' => 'Schema.org', 'points' => 20, 'earned' => $schema_pts, 'types' => $schema_types];
$raw_score += $schema_pts;

// ═══ 4. META DESCRIPTION (10 pts) ═══
preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']/i', $body, $meta_match);
$has_meta = !empty($meta_match[1]) && strlen($meta_match[1]) > 20;
$result['checks']['meta'] = ['pass' => $has_meta, 'label' => 'Meta description', 'points' => 10];
if ($has_meta) $raw_score += 10;

// ═══ 5. OPEN GRAPH (5 pts) ═══
preg_match('/<meta[^>]+property=["\']og:title["\']/i', $body, $og_title);
preg_match('/<meta[^>]+property=["\']og:description["\']/i', $body, $og_desc);
$has_og = !empty($og_title[0]) && !empty($og_desc[0]);
$result['checks']['og'] = ['pass' => $has_og, 'label' => 'Open Graph', 'points' => 5];
if ($has_og) $raw_score += 5;

// ═══ 6. SITEMAP (5 pts) ═══
$sitemap = fetch_url("{$base}/sitemap.xml", $timeout);
$result['checks']['sitemap'] = ['pass' => $sitemap['ok'], 'label' => 'Sitemap.xml', 'points' => 5];
if ($sitemap['ok']) $raw_score += 5;

// ═══ 7. ROBOTS.TXT (5 pts) ═══
$robots = fetch_url("{$base}/robots.txt", $timeout);
$result['checks']['robots'] = ['pass' => $robots['ok'], 'label' => 'Robots.txt', 'points' => 5];
if ($robots['ok']) $raw_score += 5;

// ═══ 8. CONTENT STRUCTURE — Answer-First (10 pts) ═══
$plain_text = strip_tags($body);
$plain_text = preg_replace('/\s+/', ' ', trim($plain_text));
$first_1000 = substr($plain_text, 0, 1000);
$sentences = preg_split('/[.!?]+/', $first_1000, -1, PREG_SPLIT_NO_EMPTY);
$first_5 = array_slice($sentences, 0, 5);
$has_answer = false;
foreach ($first_5 as $s) {
    // Contains a number, definition keyword, or direct statement
    if (preg_match('/\d+|je |so |ponujamo|zagotavljamo|specializiran|certificiran|let izkušenj|od leta/i', $s)) {
        $has_answer = true;
        break;
    }
}
$result['checks']['content_structure'] = ['pass' => $has_answer, 'label' => 'Content structure', 'points' => 10];
if ($has_answer) $raw_score += 10;

// ═══ 9. FAQ CONTENT (10 pts) ═══
$has_faq_section = false;
$has_faq_schema = false;
// Check for FAQ in Schema.org
if ($has_schema) {
    foreach ($schema_matches[1] as $m) {
        $j = json_decode($m, true);
        if ($j && isset($j['@type']) && $j['@type'] === 'FAQPage') $has_faq_schema = true;
    }
}
// Check for FAQ section in HTML (details/summary or questions in headings)
preg_match_all('/<h[2-6][^>]*>(.*?)<\/h[2-6]>/si', $body, $headings_for_faq);
foreach ($headings_for_faq[1] as $h) {
    if (preg_match('/\?|kako|zakaj|koliko|ali |kje |kaj |kdaj /i', $h)) {
        $has_faq_section = true;
        break;
    }
}
// Also check for <details>/<summary>
if (preg_match('/<details|<summary/i', $body)) $has_faq_section = true;
$faq_pts = 0;
if ($has_faq_section) $faq_pts += 5;
if ($has_faq_schema) $faq_pts += 5;
$result['checks']['faq'] = ['pass' => $faq_pts > 0, 'label' => 'FAQ content', 'points' => 10, 'earned' => $faq_pts];
$raw_score += $faq_pts;

// ═══ 10. CONTENT FRESHNESS (5 pts) ═══
$freshness_pts = 0;
// Check dateModified in Schema.org
$date_modified_schema = '';
if ($has_schema) {
    foreach ($schema_matches[1] as $m) {
        $j = json_decode($m, true);
        if ($j && isset($j['dateModified'])) $date_modified_schema = $j['dateModified'];
    }
}
// Check article:modified_time
preg_match('/<meta[^>]+property=["\']article:modified_time["\'][^>]+content=["\']([^"\']*)["\']/i', $body, $modified_meta);
$modified_time = $modified_meta[1] ?? $date_modified_schema ?? '';
if ($modified_time) {
    $mod_date = strtotime($modified_time);
    if ($mod_date) {
        $age_months = (time() - $mod_date) / (30 * 24 * 3600);
        if ($age_months < 6) $freshness_pts = 5;
        elseif ($age_months < 12) $freshness_pts = 2;
    }
}
$result['checks']['freshness'] = ['pass' => $freshness_pts > 0, 'label' => 'Content freshness', 'points' => 5, 'earned' => $freshness_pts];
$raw_score += $freshness_pts;

// ═══ 11. E-E-A-T SIGNALS (5 pts) ═══
$eeat_pts = 0;
// Author meta tag or <address>
if (preg_match('/<meta[^>]+name=["\']author["\']/i', $body)) $eeat_pts++;
if (preg_match('/<address/i', $body)) $eeat_pts++;
// Email on page
if (preg_match('/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/i', $body)) $eeat_pts++;
// Phone on page
if (preg_match('/tel:[+0-9]/i', $body) || preg_match('/\+386|0[1-7]\d{2}\s?\d{3}/', $body)) $eeat_pts++;
// Social links
if (preg_match('/facebook\.com|instagram\.com|linkedin\.com|x\.com|twitter\.com/i', $body)) $eeat_pts++;
$eeat_pts = min(5, $eeat_pts);
$result['checks']['eeat'] = ['pass' => $eeat_pts >= 3, 'label' => 'E-E-A-T signali', 'points' => 5, 'earned' => $eeat_pts];
$raw_score += $eeat_pts;

// ═══ 12. INTERNAL LINKING (5 pts) ═══
preg_match_all('/href=["\']https?:\/\/([^"\']*)["\']/i', $body, $all_links_for_il);
$internal_count = 0;
foreach ($all_links_for_il[1] as $link) {
    if (strpos($link, $domain) !== false) $internal_count++;
}
$il_pts = 0;
if ($internal_count >= 6) $il_pts = 5;
elseif ($internal_count >= 3) $il_pts = 2;
$result['checks']['internal_links'] = ['pass' => $il_pts >= 2, 'label' => 'Internal linking', 'points' => 5, 'earned' => $il_pts];
$raw_score += $il_pts;

// ═══ NORMALIZE SCORE (0-100) ═══
$result['score'] = min(100, round(($raw_score / $MAX_RAW) * 100));
$result['raw_score'] = $raw_score;
$result['max_raw'] = $MAX_RAW;

// ═══ GRADE ═══
if ($result['score'] >= 70) $result['grade'] = 'A';
elseif ($result['score'] >= 50) $result['grade'] = 'B';
elseif ($result['score'] >= 30) $result['grade'] = 'C';
elseif ($result['score'] >= 10) $result['grade'] = 'D';
else $result['grade'] = 'F';

$labels = [
    'A' => ['text' => 'Odlično!', 'sub' => 'Vaše podjetje je vidno za AI modele.'],
    'B' => ['text' => 'Dobro', 'sub' => 'Skoraj pripravljeno za AI priporočila.'],
    'C' => ['text' => 'Povprečno', 'sub' => 'Nekaj manjka — AI modeli vas ne priporočajo.'],
    'D' => ['text' => 'Slabo', 'sub' => 'Vaše podjetje je komaj vidno za AI.'],
    'F' => ['text' => 'Nevidno', 'sub' => 'AI modeli ne vidijo vašega podjetja.'],
];
$result['label'] = $labels[$result['grade']];

// ═══ AI CITATION TEST (optional) ═══
if ($citation_test && in_array($result['grade'], ['C', 'D', 'F'])) {
    $citation = runCitationTest($domain);
    $result['citation_test'] = $citation;
}

// ═══════════════════════════════════════
// EXTENDED AUDIT (for internal use)
// ═══════════════════════════════════════

// --- TECHNICAL ---
$result['technical']['https'] = (strpos($base, 'https://') === 0);
$result['technical']['ssl_valid'] = false;
$ssl_check = @stream_socket_client("ssl://{$domain}:443", $errno, $errstr, 5);
if ($ssl_check) {
    $cert = stream_context_get_params($ssl_check)['options']['ssl'];
    $result['technical']['ssl_valid'] = true;
    fclose($ssl_check);
}

// Viewport (mobile)
preg_match('/<meta[^>]+name=["\']viewport["\']/i', $body, $vp);
$result['technical']['mobile_friendly'] = !empty($vp[0]);

// Hreflang
preg_match_all('/<link[^>]+rel=["\']alternate["\'][^>]+hreflang=["\']([^"\']*)["\']/i', $body, $hl);
$result['technical']['languages'] = array_unique($hl[1]);

// JS/CSS count
preg_match_all('/<script[^>]+src=["\']([^"\']*)["\']/i', $body, $js);
preg_match_all('/<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']*)["\']/i', $body, $css);
$result['technical']['js_files'] = count($js[0]);
$result['technical']['css_files'] = count($css[0]);

// Word count
$text = strip_tags($body);
$text = preg_replace('/\s+/', ' ', $text);
$result['technical']['word_count'] = str_word_count($text);

// --- SEO ---
preg_match('/<title>(.*?)<\/title>/si', $body, $title_match);
$result['seo']['title'] = $title_match[1] ?? '';
$result['seo']['title_length'] = strlen($result['seo']['title']);
$result['seo']['title_optimal'] = $result['seo']['title_length'] >= 30 && $result['seo']['title_length'] <= 60;

preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']/i', $body, $desc_match);
$result['seo']['meta_description'] = $desc_match[1] ?? '';
$result['seo']['meta_length'] = strlen($result['seo']['meta_description']);
$result['seo']['meta_optimal'] = $result['seo']['meta_length'] >= 120 && $result['seo']['meta_length'] <= 160;

// H1 tags
preg_match_all('/<h1[^>]*>(.*?)<\/h1>/si', $body, $h1s);
$result['seo']['h1_count'] = count($h1s[0]);
$result['seo']['h1_first'] = strip_tags($h1s[0][0] ?? '');

// Heading hierarchy
preg_match_all('/<h([1-6])[^>]*>(.*?)<\/h\1>/si', $body, $headings);
$heading_levels = array_count_values($headings[1]);
$result['seo']['heading_hierarchy'] = $heading_levels;

// Images without alt
preg_match_all('/<img[^>]+>/i', $body, $imgs);
$no_alt = 0;
foreach ($imgs[0] as $img) {
    if (!preg_match('/alt=["\'][^"\']+["\']/', $img)) $no_alt++;
}
$result['seo']['total_images'] = count($imgs[0]);
$result['seo']['images_without_alt'] = $no_alt;

// Internal/external links
preg_match_all('/href=["\']https?:\/\/([^"\']*)["\']/i', $body, $all_links);
$internal = 0; $external = 0;
foreach ($all_links[1] as $link) {
    if (strpos($link, $domain) !== false) $internal++;
    else $external++;
}
$result['seo']['internal_links'] = $internal;
$result['seo']['external_links'] = $external;

// --- CONTACT ---
preg_match_all('/mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i', $body, $emails);
$result['contact']['emails'] = array_unique($emails[1]);

preg_match_all('/tel:([+0-9\s-]+)/i', $body, $phones);
$result['contact']['phones'] = array_unique(array_map('trim', $phones[1]));

// Social links
$social_patterns = [
    'facebook' => '/facebook\.com\/([^"\'?\s]+)/i',
    'instagram' => '/instagram\.com\/([^"\'?\s]+)/i',
    'linkedin' => '/linkedin\.com\/(company|in)\/([^"\'?\s]+)/i',
    'twitter' => '/(twitter\.com|x\.com)\/([^"\'?\s]+)/i',
    'youtube' => '/youtube\.com\/(c\/|channel\/|@)([^"\'?\s]+)/i',
];
$result['contact']['social'] = [];
foreach ($social_patterns as $name => $pattern) {
    if (preg_match($pattern, $body, $m)) {
        $result['contact']['social'][] = $name;
    }
}

// --- CMS DETECTION ---
$cms = 'unknown';
if (preg_match('/wp-content|wordpress/i', $body)) $cms = 'WordPress';
elseif (preg_match('/wix\.com|wixstatic/i', $body)) $cms = 'Wix';
elseif (preg_match('/squarespace/i', $body)) $cms = 'Squarespace';
elseif (preg_match('/shopify/i', $body)) $cms = 'Shopify';
elseif (preg_match('/joomla/i', $body)) $cms = 'Joomla';
elseif (preg_match('/drupal/i', $body)) $cms = 'Drupal';
elseif (preg_match('/webflow/i', $body)) $cms = 'Webflow';
$result['technical']['cms'] = $cms;

// --- GOOGLE ANALYTICS / TAG MANAGER ---
$result['technical']['google_analytics'] = preg_match('/G-[A-Z0-9]+|UA-[0-9]+|gtag|googletagmanager/i', $body) > 0;
$result['technical']['google_tag_manager'] = preg_match('/googletagmanager\.com\/gtm/i', $body) > 0;
$result['technical']['cookie_consent'] = preg_match('/cookie|consent|gdpr|privacy.*policy/i', $body) > 0;

// --- WEBSITE AGE (footer copyright) ---
preg_match('/©\s*(\d{4})/i', $body, $copyr);
preg_match('/copyright\s*(\d{4})/i', $body, $copyr2);
$year = $copyr[1] ?? ($copyr2[1] ?? null);
$result['technical']['copyright_year'] = $year ? (int)$year : null;
$result['technical']['website_age_years'] = $year ? (int)date('Y') - (int)$year : null;

// --- OPPORTUNITIES ---
$opps = [];

if ($result['technical']['website_age_years'] && $result['technical']['website_age_years'] > 3) {
    $opps[] = ['type' => 'redesign', 'priority' => 'high', 'reason' => "Strarost: {$result['technical']['website_age_years']} let — priložnost za prenovo"];
}
if ($cms !== 'unknown' && in_array($cms, ['WordPress', 'Wix', 'Squarespace'])) {
    $opps[] = ['type' => 'migration', 'priority' => 'medium', 'reason' => "CMS: {$cms} — priložnost za custom rebuild"];
}
if (!$has_schema) {
    $opps[] = ['type' => 'ai_authority', 'priority' => 'high', 'reason' => 'Nimajo Schema.org — AI Authority Foundation prodaja'];
}
if (!$llms_pass) {
    $opps[] = ['type' => 'ai_authority', 'priority' => 'high', 'reason' => 'Nimajo llms.txt — AI Authority Foundation prodaja'];
}
if ($no_alt > 0) {
    $opps[] = ['type' => 'seo', 'priority' => 'medium', 'reason' => "{$no_alt} slik brez alt tagov"];
}
if (!$result['technical']['cookie_consent']) {
    $opps[] = ['type' => 'compliance', 'priority' => 'low', 'reason' => 'Ni vidnega GDPR consent-a'];
}
if (empty($result['contact']['social'])) {
    $opps[] = ['type' => 'social', 'priority' => 'low', 'reason' => 'Ni socialnih povezav na strani'];
}
if ($result['technical']['word_count'] < 300) {
    $opps[] = ['type' => 'content', 'priority' => 'medium', 'reason' => "Samo {$result['technical']['word_count']} besed — malo vsebine za SEO"];
}
if ($result['seo']['h1_count'] === 0) {
    $opps[] = ['type' => 'seo', 'priority' => 'high', 'reason' => 'Ni H1 oznake'];
} elseif ($result['seo']['h1_count'] > 1) {
    $opps[] = ['type' => 'seo', 'priority' => 'medium', 'reason' => "{$result['seo']['h1_count']} H1 oznak — priporočljiva je samo 1"];
}

$result['opportunities'] = $opps;

// ═══════════════════════════════════════
// AUTO-SCRAPE CONTACTS (C/D/F grades)
// ═══════════════════════════════════════
if (in_array($result['grade'], ['C', 'D', 'F'])) {
    $scraped = autoScrapeContacts($domain, $body, $result);
    if ($scraped) {
        $result['auto_scraped'] = true;
    }
}

// Save to cache
$result['cached_at'] = time();
file_put_contents($cache_file, json_encode($result, JSON_UNESCAPED_UNICODE));

echo json_encode($result, JSON_UNESCAPED_UNICODE);

// ═══════════════════════════════════════
// AUTO-SCRAPE FUNCTION
// ═══════════════════════════════════════
function autoScrapeContacts($domain, $mainBody, $auditResult) {
    $scrapedFile = '/home/hdwebd88/public_html/ai-izkaznica/api/scraped-contacts.json';
    $contactPaths = ['/kontakt', '/kontakti', '/contact', '/contact-us', '/o-nas', '/about', '/about-us', '/kdo-smo'];
    
    // Load existing scraped data
    $existing = [];
    if (file_exists($scrapedFile)) {
        $existing = json_decode(file_get_contents($scrapedFile), true) ?: [];
    }
    
    // Dedup — don't scrape same domain again
    foreach ($existing as $entry) {
        if (($entry['domain'] ?? '') === $domain) {
            return false; // already scraped
        }
    }
    
    $allEmails = [];
    
    // Extract from main page body (already fetched)
    extractContactsFromHtml($mainBody, $allEmails);
    
    // Scrape contact pages if no emails found on main page
    if (empty($allEmails)) {
        $base = "https://{$domain}";
        foreach ($contactPaths as $path) {
            $pageBody = fetchUrlCached($base . $path);
            if ($pageBody) {
                extractContactsFromHtml($pageBody, $allEmails);
                if (!empty($allEmails)) break;
            }
        }
    }
    
    // Filter junk emails
    $junkPatterns = ['@example', '@domain', '@email', '.png', '.jpg', '.svg', '.gif', 
                     'noreply', 'no-reply', 'mailer-daemon', 'postmaster',
                     'webmaster@', 'abuse@', 'spam@', 'donotreply'];
    $allEmails = array_filter($allEmails, function($e) use ($junkPatterns) {
        $e = strtolower($e);
        foreach ($junkPatterns as $junk) {
            if (strpos($e, $junk) !== false) return false;
        }
        return true;
    });
    $allEmails = array_values(array_unique($allEmails));
    
    if (empty($allEmails)) {
        return false; // no contacts found
    }
    
    // Build scraped entry
    $entry = [
        'domain' => $domain,
        'grade' => $auditResult['grade'],
        'score' => $auditResult['score'],
        'emails' => $allEmails,
        'primary_email' => $allEmails[0] ?? null,
        'cms' => $auditResult['technical']['cms'] ?? 'unknown',
        'missing' => $auditResult['missing'] ?? [],
        'opportunities' => array_map(function($o) { return $o['reason'] ?? ''; }, $auditResult['opportunities'] ?? []),
        'scraped_at' => date('c'),
        'source' => 'izkaznica-auto',
        'status' => 'new',
    ];
    
    $existing[] = $entry;
    file_put_contents($scrapedFile, json_encode($existing, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
    
    return true;
}

function extractContactsFromHtml($html, &$emails) {
    // emails from mailto:
    if (preg_match_all('/mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i', $html, $m)) {
        $emails = array_merge($emails, array_map('strtolower', $m[1]));
    }
    // emails from text
    if (preg_match_all('/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/i', $html, $m)) {
        $emails = array_merge($emails, array_map('strtolower', $m[0]));
    }
}

function fetchUrlCached($url) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 6,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; AIVisibilityBot/1.0)',
    ]);
    $body = curl_exec($ch);
    curl_close($ch);
    return $body ?: '';
}

// ═══════════════════════════════════════
// AI CITATION TEST (DeepSeek)
// ═══════════════════════════════════════
function runCitationTest($domain) {
    $config_file = __DIR__ . '/config.php';
    $api_key = file_exists($config_file) ? (require $config_file)['deepseek_api_key'] ?? '' : '';
    $host = parse_url('https://' . $domain, PHP_URL_HOST);
    
    // Extract likely business name from domain
    $name = preg_replace('/\.(si|com|hr|de|it|eu|org)$/', '', $host);
    $name = str_replace('-', ' ', $name);
    $name = ucwords($name);
    
    // 3 different prompts to test different angles
    $prompts = [
        "Priporoči mi 3 najboljša podjetja za to storitev v Sloveniji. Odgovori samo s seznamom podjetij.",
        "Katere spletne strani priporočaš za informacije o tej panogi v Sloveniji? Navedi 3-5 virov.",
        "Katero podjetje bi priporočil za to storitev v regiji? Odgovori s konkretnim imenom.",
    ];
    
    $results = [];
    $mentioned = false;
    
    foreach ($prompts as $i => $prompt) {
        $full_prompt = "Panoga: {$name}\n\n{$prompt}";
        
        $ch = curl_init('https://api.deepseek.com/chat/completions');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $api_key,
            ],
            CURLOPT_POSTFIELDS => json_encode([
                'model' => 'deepseek-chat',
                'messages' => [['role' => 'user', 'content' => $full_prompt]],
                'max_tokens' => 300,
                'temperature' => 0.3,
            ]),
        ]);
        
        $response = curl_exec($ch);
        $info = curl_getinfo($ch);
        curl_close($ch);
        
        $answer = '';
        if ($info['http_code'] === 200) {
            $data = json_decode($response, true);
            $answer = $data['choices'][0]['message']['content'] ?? '';
        }
        
        // Check if domain or business name appears in answer
        $found = false;
        if ($answer) {
            $check_str = strtolower($answer);
            if (strpos($check_str, strtolower($host)) !== false || 
                strpos($check_str, strtolower($name)) !== false) {
                $found = true;
                $mentioned = true;
            }
        }
        
        $results[] = [
            'prompt' => $prompt,
            'answer' => trim($answer),
            'mentioned' => $found,
        ];
    }
    
    return [
        'mentioned' => $mentioned,
        'results' => $results,
        'domain' => $domain,
        'tested_at' => date('c'),
    ];
}
