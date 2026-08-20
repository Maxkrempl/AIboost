<?php
/**
 * Generate AI Visibility Report (HTML)
 * Returns: HTML string
 */

function generateReportHTML($domain) {
    $base = "https://{$domain}";
    $timeout = 8;
    
    function fetch_url($url, $timeout = 8) {
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => $url, CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $timeout, CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 3,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; AIVisibilityBot/1.0)',
        ]);
        $r = curl_exec($ch);
        $i = curl_getinfo($ch);
        curl_close($ch);
        return ['ok' => $i['http_code'] >= 200 && $i['http_code'] < 400, 'body' => $r];
    }
    
    $main = fetch_url($base, $timeout);
    if (!$main['ok']) return null;
    $body = $main['body'];
    
    $score = 0;
    $c = [];
    
    $c['main'] = ['p'=>true, 'l'=>'Stran dostopna', 'n'=>5]; $score += 5;
    
    $ll = fetch_url("{$base}/llms.txt", $timeout);
    $lp = $ll['ok'] && strlen($ll['body']) > 50;
    $c['llms'] = ['p'=>$lp, 'l'=>'llms.txt', 'n'=>$lp?30:0];
    if ($lp) $score += 30;
    
    preg_match_all('/<script[^>]+type=["\']application\/ld\+json["\'][^>]*>(.*?)<\/script>/si', $body, $sm);
    $hs = !empty($sm[1]);
    $c['schema'] = ['p'=>$hs, 'l'=>'Schema.org', 'n'=>$hs?25:0];
    if ($hs) $score += 25;
    
    preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']/i', $body, $mm);
    $hm = !empty($mm[1]) && strlen($mm[1]) > 20;
    $c['meta'] = ['p'=>$hm, 'l'=>'Meta description', 'n'=>$hm?15:0];
    if ($hm) $score += 15;
    
    preg_match('/<meta[^>]+property=["\']og:title["\']/i', $body, $ot);
    preg_match('/<meta[^>]+property=["\']og:description["\']/i', $body, $od);
    $hog = !empty($ot[0]) && !empty($od[0]);
    $c['og'] = ['p'=>$hog, 'l'=>'Open Graph', 'n'=>$hog?10:0];
    if ($hog) $score += 10;
    
    $sm = fetch_url("{$base}/sitemap.xml", $timeout);
    $c['sitemap'] = ['p'=>$sm['ok'], 'l'=>'Sitemap.xml', 'n'=>$sm['ok']?10:0];
    if ($sm['ok']) $score += 10;
    
    $rb = fetch_url("{$base}/robots.txt", $timeout);
    $c['robots'] = ['p'=>$rb['ok'], 'l'=>'Robots.txt', 'n'=>$rb['ok']?5:0];
    if ($rb['ok']) $score += 5;
    
    $grade = $score >= 70 ? 'A' : ($score >= 50 ? 'B' : ($score >= 30 ? 'C' : ($score >= 10 ? 'D' : 'F')));
    $gc = ['A'=>'#34d399','B'=>'#60a5fa','C'=>'#fbbf24','D'=>'#fb923c','F'=>'#f87171'];
    $color = $gc[$grade];
    
    $lb = ['A'=>['t'=>'Odlično!','s'=>'Vase podjetje je vidno za AI modele.'],'B'=>['t'=>'Dobro','s'=>'Skoraj pripravljeno za AI priporocila.'],'C'=>['t'=>'Povprecno','s'=>'Nekaj manjka — AI vas ne priporoca.'],'D'=>['t'=>'Slabo','s'=>'Vase podjetje je komaj vidno za AI.'],'F'=>['t'=>'Nevidno','s'=>'AI modeli ne vidijo vasega podjetja.']];
    
    // Technical
    $cms = 'unknown';
    if (preg_match('/wp-content|wordpress/i', $body)) $cms = 'WordPress';
    elseif (preg_match('/wix/i', $body)) $cms = 'Wix';
    elseif (preg_match('/squarespace/i', $body)) $cms = 'Squarespace';
    $mob = (strpos($body, 'viewport') !== false);
    $ga = (preg_match('/G-[A-Z0-9]+|gtag|googletagmanager/i', $body) > 0);
    $ck = (preg_match('/cookie|consent|gdpr/i', $body) > 0);
    $wc = str_word_count(strip_tags(preg_replace('/\s+/', ' ', $body)));
    
    // SEO
    preg_match('/<title>(.*?)<\/title>/si', $body, $tm);
    $title = strip_tags($tm[1] ?? '');
    $tl = strlen($title);
    $to = $tl >= 30 && $tl <= 60;
    
    preg_match('/<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']/i', $body, $dm);
    $ml = strlen($dm[1] ?? '');
    $mo = $ml >= 120 && $ml <= 160;
    
    preg_match_all('/<h1[^>]*>(.*?)<\/h1>/si', $body, $h1s);
    $h1c = count($h1s[0]);
    
    preg_match_all('/<img[^>]+>/i', $body, $imgs);
    $na = 0;
    foreach ($imgs[0] as $img) { if (!preg_match('/alt=["\'][^"\']+["\']/', $img)) $na++; }
    
    // Contact
    preg_match_all('/mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i', $body, $em);
    $el = implode(', ', array_unique($em[1]));
    
    preg_match_all('/tel:([+0-9\s-]+)/i', $body, $ph);
    $pl = implode(', ', array_unique(array_map('trim', $ph[1])));
    
    $sc = [];
    if (preg_match('/facebook\.com/i', $body)) $sc[] = 'Facebook';
    if (preg_match('/instagram\.com/i', $body)) $sc[] = 'Instagram';
    if (preg_match('/linkedin\.com/i', $body)) $sc[] = 'LinkedIn';
    $scl = implode(', ', $sc);
    
    // Opportunities
    $op = '';
    $opp = [];
    if (!$hs) $opp[] = ['h','Ni Schema.org — AI ne razume strukture'];
    if (!$lp) $opp[] = ['h','Ni llms.txt — AI ne ve kdo ste'];
    if ($na > 0) $opp[] = ['m',"{$na} slik brez alt tagov"];
    if (!$ck) $opp[] = ['l','Ni vidnega GDPR consent-a'];
    if ($wc < 300) $opp[] = ['m',"Samo {$wc} besed — malo vsebine"];
    if ($h1c === 0) $opp[] = ['h','Ni H1 oznake'];
    
    if (empty($opp)) {
        $op = '<p style="color:#34d399;padding:12px 0;">✅ Stran je dobro optimizirana!</p>';
    } else {
        foreach ($opp as $o) {
            $pc = $o[0]==='h' ? '#f87171' : ($o[0]==='m' ? '#fbbf24' : '#71717a');
            $pl2 = $o[0]==='h' ? 'HIGH' : ($o[0]==='m' ? 'MEDIUM' : 'LOW');
            $op .= "<div style='margin:8px 0;padding:12px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:3px solid {$pc};'><span style='color:{$pc};font-weight:700;font-size:11px;'>[{$pl2}]</span> <span style='color:#a1a1aa;'>{$o[1]}</span></div>";
        }
    }
    
    // Build checks rows
    $ch = '';
    foreach ($c as $v) {
        $d = $v['p'] ? '✅' : '❌';
        $cl = $v['p'] ? '#34d399' : '#f87171';
        $ch .= "<tr><td style='padding:10px 0;border-bottom:1px solid #27272a;color:#a1a1aa;'>{$d} {$v['l']}</td><td style='padding:10px 0;border-bottom:1px solid #27272a;text-align:right;color:{$cl};'>{$v['n']}</td></tr>";
    }
    
    $mcl = $mob ? '#34d399' : '#f87171';
    $mobv = $mob ? 'Da' : 'Ne';
    $gcl = $ga ? '#34d399' : '#f87171';
    $gav = $ga ? 'Da' : 'Ne';
    $ccl = $ck ? '#34d399' : '#f87171';
    $ckv = $ck ? 'Da' : 'Ne';
    $tcl = $to ? '#34d399' : '#fbbf24';
    $mcl2 = $mo ? '#34d399' : '#fbbf24';
    $h1cl = $h1c === 1 ? '#34d399' : '#f87171';
    $nacl = $na === 0 ? '#34d399' : '#f87171';
    $title_escaped = htmlspecialchars($title);
    $el_v = $el ?: 'Ni podatkov';
    $pl_v = $pl ?: 'Ni podatkov';
    $scl_v = $scl ?: 'Ni podatkov';
    $lt = $lb[$grade]['t'];
    $ls = $lb[$grade]['s'];
    $now = date('d.m.Y');
    $yr = date('Y');
    
    $html = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:0;background:#09090b;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;"><div style="max-width:680px;margin:0 auto;padding:40px 24px;color:#e8e8ed;">';
    
    $html .= '<div style="text-align:center;margin-bottom:36px;"><div style="font-size:42px;margin-bottom:12px;">📄</div>';
    $html .= '<h1 style="font-size:26px;font-weight:800;margin:0 0 6px;color:#fff;">AI Visibility Full Report</h1>';
    $html .= "<p style=\"color:#71717a;font-size:15px;margin:0;\">{$domain} · {$now}</p></div>";
    
    $html .= "<div style=\"text-align:center;margin-bottom:36px;padding:28px;background:#18181b;border-radius:16px;border:1px solid #3f3f46;\">";
    $html .= "<div style=\"font-size:64px;font-weight:900;color:{$color};\">{$grade}</div>";
    $html .= "<div style=\"font-size:22px;color:#fff;\">{$score}/100</div>";
    $html .= "<div style=\"font-size:15px;color:#a1a1aa;margin-top:6px;\">{$lt}</div>";
    $html .= "<div style=\"font-size:13px;color:#71717a;margin-top:2px;\">{$ls}</div></div>";
    
    $html .= '<h2 style="font-size:16px;font-weight:700;color:#818cf8;margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid #27272a;">1. AI Visibility Checks</h2>';
    $html .= '<table style="width:100%;border-collapse:collapse;">' . $ch;
    $html .= "<tr style=\"font-weight:700;\"><td style=\"padding:12px 0;color:#fff;\">Skupaj</td><td style=\"padding:12px 0;color:{$color};text-align:right;\">{$score}/100</td></tr></table>";
    
    $html .= '<h2 style="font-size:16px;font-weight:700;color:#818cf8;margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid #27272a;">2. Technical Analysis</h2>';
    $html .= '<table style="width:100%;border-collapse:collapse;">';
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">CMS</td><td style=\"padding:8px 0;color:#fff;text-align:right;\">{$cms}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Mobile</td><td style=\"padding:8px 0;color:{$mcl};text-align:right;\">{$mobv}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Google Analytics</td><td style=\"padding:8px 0;color:{$gcl};text-align:right;\">{$gav}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Cookie Consent</td><td style=\"padding:8px 0;color:{$ccl};text-align:right;\">{$ckv}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Besede na strani</td><td style=\"padding:8px 0;color:#fff;text-align:right;\">{$wc}</td></tr></table>";
    
    $html .= '<h2 style="font-size:16px;font-weight:700;color:#818cf8;margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid #27272a;">3. SEO Analysis</h2>';
    $html .= '<table style="width:100%;border-collapse:collapse;">';
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Title</td><td style=\"padding:8px 0;color:#fff;text-align:right;max-width:380px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;\">{$title_escaped}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Title dolzina</td><td style=\"padding:8px 0;color:{$tcl};text-align:right;\">{$tl} znakov</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Meta dolzina</td><td style=\"padding:8px 0;color:{$mcl2};text-align:right;\">{$ml} znakov</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">H1 oznake</td><td style=\"padding:8px 0;color:{$h1cl};text-align:right;\">{$h1c}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Slike brez alt</td><td style=\"padding:8px 0;color:{$nacl};text-align:right;\">{$na}</td></tr></table>";
    
    $html .= '<h2 style="font-size:16px;font-weight:700;color:#818cf8;margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid #27272a;">4. Contact Information</h2>';
    $html .= '<table style="width:100%;border-collapse:collapse;">';
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Emaili</td><td style=\"padding:8px 0;color:#fff;text-align:right;\">{$el_v}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Telefoni</td><td style=\"padding:8px 0;color:#fff;text-align:right;\">{$pl_v}</td></tr>";
    $html .= "<tr><td style=\"padding:8px 0;color:#a1a1aa;\">Social</td><td style=\"padding:8px 0;color:#fff;text-align:right;\">{$scl_v}</td></tr></table>";
    
    $html .= '<h2 style="font-size:16px;font-weight:700;color:#818cf8;margin:28px 0 12px;padding-bottom:8px;border-bottom:1px solid #27272a;">5. Opportunities & Recommendations</h2>';
    $html .= $op;
    
    // ═══ SOLUTIONS SECTION ═══
    $sol = '';
    $sol_count = 0;
    
    if (!$lp) {
        $sol_count++;
        $llms_sample = '# ' . strtoupper($domain) . '\n';
        $llms_sample .= '# AI Visibility File\n\n';
        $llms_sample .= '> Opis: Podjetje za izdelavo spletnih strani in AI orodja.\n\n';
        $llms_sample .= '## Kontakt\n';
        $llms_sample .= '- Email: hercegdarko@hd-webdesign.si\n';
        $llms_sample .= '- Telefon: +386 40 270 696\n\n';
        $llms_sample .= '## Storitve\n';
        $llms_sample .= '- Izdelava spletnih strani\n';
        $llms_sample .= '- AI optimizacija (GEO)\n';
        $llms_sample .= '- SEO analiza';
        $llms_escaped = htmlspecialchars($llms_sample);
        $sol .= '<div style="margin:12px 0;padding:16px;background:#18181b;border-radius:12px;border:1px solid #3f3f46;">';
        $sol .= '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="background:#6c5ce7;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;">REŠITEV 1</span><span style="color:#fff;font-weight:600;">Ustvarite llms.txt</span></div>';
        $sol .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 10px;">Datoteka llms.txt AI pove kdo ste in kaj delajete. Dodajte jo v koren spletne strani:</p>';
        $sol .= '<div style="background:#09090b;border-radius:8px;padding:14px;font-family:monospace;font-size:12px;color:#a1a1aa;white-space:pre-wrap;line-height:1.6;border:1px solid #27272a;">' . $llms_escaped . '</div>';
        $sol .= '<p style="color:#71717a;font-size:12px;margin:10px 0 0;">📍 Naložite kot <code style="background:#27272a;padding:2px 6px;border-radius:4px;">/llms.txt</code> v koren domene</p>';
        $sol .= '</div>';
    }
    
    if (!$hs) {
        $sol_count++;
        $schema_sample = '{\n  "@context": "https://schema.org",\n  "@type": "LocalBusiness",\n  "name": "' . $domain . '",\n  "url": "https://' . $domain . '",\n  "description": "Vpisite opis podjetja",\n  "address": {\n    "@type": "PostalAddress",\n    "addressLocality": "Ljubljana",\n    "addressCountry": "SI"\n  },\n  "telephone": "+386..."\n}';
        $schema_escaped = htmlspecialchars($schema_sample);
        $sol .= '<div style="margin:12px 0;padding:16px;background:#18181b;border-radius:12px;border:1px solid #3f3f46;">';
        $sol .= '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="background:#6c5ce7;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;">REŠITEV 2</span><span style="color:#fff;font-weight:600;">Dodajte Schema.org markup</span></div>';
        $sol .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 10px;">Schema.org pove AI modelom strukturo vašega podjetja. Dodajte v <code style="background:#27272a;padding:2px 6px;border-radius:4px;">&lt;head&gt;</code>:</p>';
        $sol .= '<div style="background:#09090b;border-radius:8px;padding:14px;font-family:monospace;font-size:11px;color:#a1a1aa;white-space:pre-wrap;line-height:1.5;border:1px solid #27272a;">&lt;script type="application/ld+json"&gt;\n' . $schema_escaped . '\n&lt;/script&gt;</div>';
        $sol .= '</div>';
    }
    
    if (!$hm) {
        $sol_count++;
        $sol .= '<div style="margin:12px 0;padding:16px;background:#18181b;border-radius:12px;border:1px solid #3f3f46;">';
        $sol .= '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="background:#6c5ce7;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;">REŠITEV 3</span><span style="color:#fff;font-weight:600;">Optimizirajte Meta Description</span></div>';
        $sol .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 10px;">Meta description naj bo 120-160 znakov, naj vključuje glavno besedo in poziv k dejanju:</p>';
        $sol .= '<div style="background:#09090b;border-radius:8px;padding:14px;font-family:monospace;font-size:12px;color:#a1a1aa;white-space:pre-wrap;border:1px solid #27272a;">&lt;meta name="description" content="Vpisite 120-160 znakov z glavno besedo in CTA." /&gt;</div>';
        $sol .= '</div>';
    }
    
    if (!$hog) {
        $sol_count++;
        $sol .= '<div style="margin:12px 0;padding:16px;background:#18181b;border-radius:12px;border:1px solid #3f3f46;">';
        $sol .= '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="background:#6c5ce7;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;">REŠITEV 4</span><span style="color:#fff;font-weight:600;">Dodajte Open Graph tagi</span></div>';
        $sol .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 10px;">OG tagi poskrbijo za lep prikaz ob deljenju na socialnih omrežjih:</p>';
        $sol .= '<div style="background:#09090b;border-radius:8px;padding:14px;font-family:monospace;font-size:11px;color:#a1a1aa;white-space:pre-wrap;border:1px solid #27272a;">&lt;meta property="og:title" content="Naslov strani" /&gt;\n&lt;meta property="og:description" content="Opis za socialna omrezja" /&gt;\n&lt;meta property="og:image" content="https://'. $domain . '/slika.jpg" /&gt;\n&lt;meta property="og:url" content="https://'. $domain . '" /&gt;</div>';
        $sol .= '</div>';
    }
    
    if ($na > 0) {
        $sol_count++;
        $sol .= '<div style="margin:12px 0;padding:16px;background:#18181b;border-radius:12px;border:1px solid #3f3f46;">';
        $sol .= '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="background:#6c5ce7;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;">REŠITEV 5</span><span style="color:#fff;font-weight:600;">Dodajte alt atribute slikam</span></div>';
        $sol .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 10px;">Najdeno ' . $na . ' slik brez alt taga. Vsaka slika naj ima opis:</p>';
        $sol .= '<div style="background:#09090b;border-radius:8px;padding:14px;font-family:monospace;font-size:12px;color:#a1a1aa;white-space:pre-wrap;border:1px solid #27272a;">&lt;img src="slika.jpg" alt="Opis slike z glavno besedo" /&gt;</div>';
        $sol .= '</div>';
    }
    
    if ($wc < 300) {
        $sol_count++;
        $sol .= '<div style="margin:12px 0;padding:16px;background:#18181b;border-radius:12px;border:1px solid #3f3f46;">';
        $sol .= '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;"><span style="background:#6c5ce7;color:#fff;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;">REŠITEV 6</span><span style="color:#fff;font-weight:600;">Povečajte količino besedila</span></div>';
        $sol .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 10px;">Trenutno imate samo ' . $wc . ' besed. AI modeli potrebujejo vsaj 500+ besed za razumevanje dejavnosti. Dodajte:</p>';
        $sol .= '<div style="color:#a1a1aa;font-size:13px;line-height:1.7;">• Opis storitev z besedami strank<br>• Lokalne reference (mesto, regija)<br>• Reference strank / mnenja<br>• Podroben opis postopka sodelovanja<br>• FAQ odgovori na pogosta vprašanja</div>';
        $sol .= '</div>';
    }
    
    if ($sol_count > 0) {
        $html .= '<h2 style="font-size:16px;font-weight:700;color:#34d399;margin:32px 0 12px;padding-bottom:8px;border-bottom:1px solid #27272a;">💡 Konkretna rešitev za vašo stran</h2>';
        $html .= '<p style="color:#a1a1aa;font-size:13px;margin:0 0 8px;">Tukaj so pripravljeni predlogi in koda, ki jo lahko takoj implementirate:</p>';
        $html .= $sol;
    }
    
    $html .= '<div style="margin-top:36px;padding:24px;background:#18181b;border-radius:16px;border:1px solid #3f3f46;">';
    $html .= '<h2 style="font-size:16px;font-weight:700;color:#818cf8;margin:0 0 12px;">6. Next Steps</h2>';
    $html .= '<div style="margin:10px 0;color:#a1a1aa;"><strong style="color:#fff;">1.</strong> Dodajte llms.txt</div>';
    $html .= '<div style="margin:10px 0;color:#a1a1aa;"><strong style="color:#fff;">2.</strong> Implementirajte Schema.org</div>';
    $html .= '<div style="margin:10px 0;color:#a1a1aa;"><strong style="color:#fff;">3.</strong> Izboljsajte meta podatke</div>';
    $html .= '<div style="margin:10px 0;color:#a1a1aa;"><strong style="color:#fff;">4.</strong> Zberite Google Reviews</div>';
    $html .= '<div style="margin:10px 0;color:#a1a1aa;"><strong style="color:#fff;">5.</strong> Ponovno preverite cez 30 dni</div></div>';
    
    $html .= '<div style="margin-top:36px;padding:24px;background:linear-gradient(135deg,#18181b,#1e1b4b);border-radius:16px;border:1px solid #312e81;text-align:center;">';
    $html .= '<p style="color:#a1a1aa;font-size:14px;margin:0 0 12px;">Zelite pomoc pri izboljsavi?</p>';
    $html .= '<p style="margin:0;"><a href="mailto:hercegdarko@hd-webdesign.si" style="color:#818cf8;font-weight:700;text-decoration:none;">Kontaktirajte nas →</a></p>';
    $html .= '<p style="color:#71717a;font-size:12px;margin:8px 0 0;">AI Authority paket · €699 + €49/mesec</p></div>';
    
    $html .= "<p style=\"text-align:center;color:#52525b;font-size:11px;margin-top:36px;\">HD Web Design · AI Visibility Tool · {$yr}</p>";
    $html .= '</div></body></html>';
    
    return $html;
}
