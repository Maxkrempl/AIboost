<?php
/**
 * Full PDF Report — Stripe Checkout + PDF Generation
 * GET  /ai-izkaznica/api/report.php?domain=example.si — generate PDF
 * POST /ai-izkaznica/api/report.php — create Stripe checkout session
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

$domain = '';
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $domain = $_GET['domain'] ?? '';
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents('php://input'), true);
    $domain = $input['domain'] ?? '';
}

$domain = preg_replace('/^https?:\/\//', '', $domain);
$domain = preg_replace('/\/.*$/', '', $domain);
$domain = preg_replace('/[^a-z0-9.-]/i', '', $domain);

if (empty($domain)) {
    http_response_code(400);
    echo json_encode(['error' => 'Domain required']);
    exit;
}

// ═══ STRIPE CHECKOUT (POST) ═══
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $input['email'] ?? '';
    
    // Create Stripe checkout session
    $stripe_key = '***REMOVED***'; // placeholder — use env var in production
    
    // For now, return checkout URL
    // In production: use Stripe API to create session
    $checkout_url = "https://hd-webdesign.si/ai-izkaznica/checkout.php?domain=" . urlencode($domain) . "&email=" . urlencode($email);
    
    echo json_encode([
        'checkout_url' => $checkout_url,
        'domain' => $domain,
        'price' => '€50',
    ]);
    exit;
}

// ═══ PDF GENERATION (GET) ═══
// Run full audit
$audit_url = 'https://hd-webdesign.si/ai-izkaznica/api/audit.php';
$ch = curl_init($audit_url);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode(['domain' => $domain]),
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 30,
]);
$audit_json = curl_exec($ch);
curl_close($ch);

$audit = json_decode($audit_json, true);
if (!$audit || !isset($audit['score'])) {
    http_response_code(500);
    echo json_encode(['error' => 'Audit failed']);
    exit;
}

// Generate PDF
require_once __DIR__ . '/vendor/autoload.php'; // fpdf2

use FPDF;

$pdf = new FPDF();
$pdf->AddPage();
$pdf->SetFont('Arial', 'B', 24);

// Title
$pdf->SetFillColor(9, 9, 11);
$pdf->Rect(0, 0, 210, 297, 'F');
$pdf->SetTextColor(255, 255, 255);
$pdf->SetXY(20, 30);
$pdf->SetFont('Arial', 'B', 28);
$pdf->Cell(170, 15, 'AI Visibility Full Report', 0, 1);
$pdf->SetXY(20, 48);
$pdf->SetFont('Arial', '', 14);
$pdf->SetTextColor(160, 160, 170);
$pdf->Cell(170, 10, $domain, 0, 1);
$pdf->SetXY(20, 60);
$pdf->SetFont('Arial', 'B', 40);
$grade_colors = ['A'=>[52,211,153], 'B'=>[96,165,250], 'C'=>[251,191,36], 'D'=>[251,146,60], 'F'=>[248,113,113]];
$c = $grade_colors[$audit['grade']] ?? [255,255,255];
$pdf->SetTextColor($c[0], $c[1], $c[2]);
$pdf->Cell(170, 20, "Grade: {$audit['grade']} ({$audit['score']}/100)", 0, 1);

// Section helper
function section($pdf, $title, $y_start) {
    $pdf->SetXY(20, $y_start);
    $pdf->SetTextColor(129, 140, 248);
    $pdf->SetFont('Arial', 'B', 16);
    $pdf->Cell(170, 10, $title, 0, 1);
    return $y_start + 12;
}

function item($pdf, $label, $value, $y, $pass = null) {
    $pdf->SetXY(25, $y);
    $pdf->SetTextColor(200, 200, 210);
    $pdf->SetFont('Arial', '', 11);
    $pdf->Cell(80, 7, $label, 0, 0);
    if ($pass !== null) {
        $pdf->SetTextColor($pass ? 52 : 248, $pass ? 211 : 113, $pass ? 153 : 113);
    } else {
        $pdf->SetTextColor(250, 250, 250);
    }
    $pdf->Cell(80, 7, $value, 0, 1);
    return $y + 7;
}

// Core checks
$y = section($pdf, '1. AI Visibility Checks', 80);
$checks = $audit['checks'] ?? [];
foreach ($checks as $key => $check) {
    $status = $check['pass'] ? 'PASS' : 'FAIL';
    $y = item($pdf, $check['label'], "{$status} (+{$check['points']} points)", $y, $check['pass']);
}

// Technical
$y = section($pdf, '2. Technical Analysis', $y + 5);
$tech = $audit['technical'] ?? [];
$y = item($pdf, 'CMS', $tech['cms'] ?? 'unknown', $y);
$y = item($pdf, 'Mobile Friendly', ($tech['mobile_friendly'] ?? false) ? 'Yes' : 'No', $y, $tech['mobile_friendly'] ?? false);
$y = item($pdf, 'SSL Valid', ($tech['ssl_valid'] ?? false) ? 'Yes' : 'No', $y, $tech['ssl_valid'] ?? false);
$y = item($pdf, 'Google Analytics', ($tech['google_analytics'] ?? false) ? 'Yes' : 'No', $y, $tech['google_analytics'] ?? false);
$y = item($pdf, 'Google Tag Manager', ($tech['google_tag_manager'] ?? false) ? 'Yes' : 'No', $y, $tech['google_tag_manager'] ?? false);
$y = item($pdf, 'Cookie Consent', ($tech['cookie_consent'] ?? false) ? 'Yes' : 'No', $y, $tech['cookie_consent'] ?? false);
$y = item($pdf, 'Word Count', (string)($tech['word_count'] ?? 0), $y);
$y = item($pdf, 'JS Files', (string)($tech['js_files'] ?? 0), $y);
$y = item($pdf, 'CSS Files', (string)($tech['css_files'] ?? 0), $y);
$y = item($pdf, 'Copyright Year', (string)($tech['copyright_year'] ?? 'N/A'), $y);
$y = item($pdf, 'Website Age', ($tech['website_age_years'] ?? null) ? "{$tech['website_age_years']} years" : 'N/A', $y);
$languages = implode(', ', $tech['languages'] ?? []);
$y = item($pdf, 'Languages (hreflang)', $languages ?: 'None', $y);

// SEO
$y = section($pdf, '3. SEO Analysis', $y + 5);
$seo = $audit['seo'] ?? [];
$y = item($pdf, 'Title', $seo['title'] ?? 'N/A', $y);
$y = item($pdf, 'Title Length', (string)($seo['title_length'] ?? 0) . ' chars', $y, $seo['title_optimal'] ?? false);
$y = item($pdf, 'Meta Description Length', (string)($seo['meta_length'] ?? 0) . ' chars', $y, $seo['meta_optimal'] ?? false);
$y = item($pdf, 'H1 Tags', (string)($seo['h1_count'] ?? 0), $y, ($seo['h1_count'] ?? 0) === 1);
$y = item($pdf, 'Total Images', (string)($seo['total_images'] ?? 0), $y);
$y = item($pdf, 'Images Without Alt', (string)($seo['images_without_alt'] ?? 0), $y, ($seo['images_without_alt'] ?? 0) === 0);
$y = item($pdf, 'Internal Links', (string)($seo['internal_links'] ?? 0), $y);
$y = item($pdf, 'External Links', (string)($seo['external_links'] ?? 0), $y);

// Contact
$y = section($pdf, '4. Contact Information', $y + 5);
$contact = $audit['contact'] ?? [];
$y = item($pdf, 'Emails', implode(', ', $contact['emails'] ?? []) ?: 'None', $y);
$y = item($pdf, 'Phones', implode(', ', $contact['phones'] ?? []) ?: 'None', $y);
$y = item($pdf, 'Social Networks', implode(', ', $contact['social'] ?? []) ?: 'None', $y);

// Opportunities
$y = section($pdf, '5. Opportunities & Recommendations', $y + 5);
$opps = $audit['opportunities'] ?? [];
if (empty($opps)) {
    $y = item($pdf, 'No issues found', 'Great job!', $y);
} else {
    foreach ($opps as $opp) {
        $priority_label = strtoupper($opp['priority']);
        $y = item($pdf, "[{$priority_label}]", $opp['reason'], $y, false);
    }
}

// Footer
$pdf->SetXY(20, 270);
$pdf->SetTextColor(100, 100, 110);
$pdf->SetFont('Arial', '', 9);
$pdf->Cell(170, 5, 'Generated by AI Visibility Tool — hd-webdesign.si/ai-izkaznica/', 0, 1);
$pdf->Cell(170, 5, date('Y-m-d H:i') . ' | This report is for internal use only.', 0, 1);

// Output
$pdf_path = sys_get_temp_dir() . "/ai-report-{$domain}.pdf";
$pdf->Output('F', $pdf_path);

header('Content-Type: application/pdf');
header('Content-Disposition: attachment; filename="ai-report-{$domain}.pdf"');
readfile($pdf_path);
unlink($pdf_path);
