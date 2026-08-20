#!/usr/bin/env python3
"""
AI Visibility Audit — Indeks AI-vidljivosti Slovenije
Checks: llms.txt, Schema.org, meta tags, OG tags, sitemap, robots.txt
"""

import requests
import json
import time
import sys
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# All 108 companies from the spreadsheet
COMPANIES = [
    # Banke in zavarovalnice
    {"sektor": "Banke in zavarovalnice", "podjetje": "NLB", "domena": "nlb.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Nova KBM", "domena": "nkbm.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Abanka", "domena": "abanka.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Banka Intesa Sanpaolo", "domena": "intesasanpaolobanka.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Sparkasse", "domena": "sparkasse.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Hranilnica LON", "domena": "lon.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Delavska hranilnica", "domena": "dhs.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Hranilnica Vipava", "domena": "hr-vipava.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Zavarovalnica Triglav", "domena": "triglav.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Zavarovalnica Sava", "domena": "sava.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Adriatic Slovenica", "domena": "adriatic-slovenica.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Modra zavarovalnica", "domena": "modra.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Vzajemna", "domena": "vzajemna.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Triglav Skladi", "domena": "triglav-skladi.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "KD Skupina", "domena": "kd.si"},
    {"sektor": "Banke in zavarovalnice", "podjetje": "Ilirika", "domena": "ilirika.si"},
    # Trgovina
    {"sektor": "Trgovina", "podjetje": "Mercator", "domena": "mercator.si"},
    {"sektor": "Trgovina", "podjetje": "Hofer", "domena": "hofer.si"},
    {"sektor": "Trgovina", "podjetje": "Lidl Slovenija", "domena": "lidl.si"},
    {"sektor": "Trgovina", "podjetje": "Spar", "domena": "spar.si"},
    {"sektor": "Trgovina", "podjetje": "Tuš", "domena": "tus.si"},
    {"sektor": "Trgovina", "podjetje": "Eurospin", "domena": "eurospin.si"},
    {"sektor": "Trgovina", "podjetje": "Jager", "domena": "jager.si"},
    {"sektor": "Trgovina", "podjetje": "dm Slovenija", "domena": "dm.si"},
    {"sektor": "Trgovina", "podjetje": "Müller", "domena": "mueller.si"},
    {"sektor": "Trgovina", "podjetje": "Big Bang", "domena": "bigbang.si"},
    {"sektor": "Trgovina", "podjetje": "Hervis", "domena": "hervis.si"},
    {"sektor": "Trgovina", "podjetje": "Sportina", "domena": "sportina.si"},
    {"sektor": "Trgovina", "podjetje": "Minka", "domena": "minka.si"},
    {"sektor": "Trgovina", "podjetje": "Kea", "domena": "kea.si"},
    {"sektor": "Trgovina", "podjetje": "Liophil", "domena": "liophil.si"},
    # Telekom in IT
    {"sektor": "Telekom in IT", "podjetje": "Telekom Slovenije", "domena": "telekom.si"},
    {"sektor": "Telekom in IT", "podjetje": "A1 Slovenija", "domena": "a1.si"},
    {"sektor": "Telekom in IT", "podjetje": "Telemach", "domena": "telemach.si"},
    {"sektor": "Telekom in IT", "podjetje": "T-2", "domena": "t-2.si"},
    {"sektor": "Telekom in IT", "podjetje": "SiOL", "domena": "siol.net"},
    {"sektor": "Telekom in IT", "podjetje": "Iskratel", "domena": "iskratel.si"},
    {"sektor": "Telekom in IT", "podjetje": "SRC", "domena": "src.si"},
    {"sektor": "Telekom in IT", "podjetje": "Kolektor", "domena": "kolektor.si"},
    {"sektor": "Telekom in IT", "podjetje": "Inea", "domena": "inea.si"},
    {"sektor": "Telekom in IT", "podjetje": "Xlab", "domena": "xlab.si"},
    {"sektor": "Telekom in IT", "podjetje": "Celtra", "domena": "celtra.com"},
    {"sektor": "Telekom in IT", "podjetje": "Bitstamp", "domena": "bitstamp.net"},
    {"sektor": "Telekom in IT", "podjetje": "Sportradar", "domena": "sportradar.com"},
    {"sektor": "Telekom in IT", "podjetje": "Perftech", "domena": "perftech.si"},
    # Energetika in industrija
    {"sektor": "Energetika in industrija", "podjetje": "Petrol", "domena": "petrol.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Gen energija", "domena": "gen-energija.si"},
    {"sektor": "Energetika in industrija", "podjetje": "HSE", "domena": "hse.si"},
    {"sektor": "Energetika in industrija", "podjetje": "ELES", "domena": "eles.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Plinovodi", "domena": "plinovodi.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Adriaplin", "domena": "adriaplin.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Cinkarna Celje", "domena": "cinkarna-celje.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Salonit Anhovo", "domena": "salonit.si"},
    {"sektor": "Energetika in industrija", "podjetje": "SIJ Acroni", "domena": "acroni.si"},
    {"sektor": "Energetika in industrija", "podjetje": "SIJ Slovenian Steel", "domena": "sij.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Talum", "domena": "talum.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Hidria", "domena": "hidria.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Intereuropa", "domena": "intereuropa.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Helios", "domena": "helios.si"},
    {"sektor": "Energetika in industrija", "podjetje": "Belinka", "domena": "belinka.si"},
    {"sektor": "Energetika in industrija", "podjetje": "JUB", "domena": "jub.si"},
    # Farmacija in kemija
    {"sektor": "Farmacija in kemija", "podjetje": "Krka", "domena": "krka.si"},
    {"sektor": "Farmacija in kemija", "podjetje": "Lek", "domena": "lek.si"},
    {"sektor": "Farmacija in kemija", "podjetje": "Kemiplas", "domena": "kemiplas.si"},
    # FMCG in prehrana
    {"sektor": "FMCG in prehrana", "podjetje": "Gorenje", "domena": "gorenje.com"},
    {"sektor": "FMCG in prehrana", "podjetje": "Mlinotest", "domena": "mlinotest.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Žito", "domena": "zito.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Droga Kolinska", "domena": "droga-kolinska.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Atlantic Brda", "domena": "atlanticbrda.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Fructal", "domena": "fructal.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Radenska", "domena": "radenska.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Pivovarna Laško", "domena": "lasko.eu"},
    {"sektor": "FMCG in prehrana", "podjetje": "Pivovarna Union", "domena": "pivovarna-union.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Perutnina Ptuj", "domena": "perutnina-ptuj.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Panvita", "domena": "panvita.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Ljubljanske mlekarne", "domena": "ljubljanske-mlekarne.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Mlekarna Celeia", "domena": "mlekarna-celeia.si"},
    {"sektor": "FMCG in prehrana", "podjetje": "Jata", "domena": "jata.si"},
    # Turizem in gostinstvo
    {"sektor": "Turizem in gostinstvo", "podjetje": "Terme Čatež", "domena": "terme-catez.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Sava Turizem", "domena": "sava-turizem.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Hoteli Bernardin", "domena": "bernardin.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "HIT Nova Gorica", "domena": "hit.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Terme Olimia", "domena": "terme-olimia.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Terme Maribor", "domena": "terme-maribor.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "LifeClass Portorož", "domena": "lifeclass.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Hotel Union", "domena": "hotel-union.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Hotel Milka", "domena": "hotelmilka.si"},
    {"sektor": "Turizem in gostinstvo", "podjetje": "Grand Koper", "domena": "grandkoper.com"},
    # Avtomobilska in mobilnost
    {"sektor": "Avtomobilska in mobilnost", "podjetje": "Revoz", "domena": "revoz.si"},
    {"sektor": "Avtomobilska in mobilnost", "podjetje": "TPV", "domena": "tpv.si"},
    {"sektor": "Avtomobilska in mobilnost", "podjetje": "Unior Tools", "domena": "unior.si"},
    {"sektor": "Avtomobilska in mobilnost", "podjetje": "Cimos", "domena": "cimos.eu"},
    # Mediji
    {"sektor": "Mediji", "podjetje": "Delo", "domena": "delo.si"},
    {"sektor": "Mediji", "podjetje": "Dnevnik", "domena": "dnevnik.si"},
    {"sektor": "Mediji", "podjetje": "Večer", "domena": "vecer.si"},
    {"sektor": "Mediji", "podjetje": "RTV Slovenija", "domena": "rtvslo.si"},
    {"sektor": "Mediji", "podjetje": "24ur.com / POP TV", "domena": "24ur.com"},
    {"sektor": "Mediji", "podjetje": "Finance", "domena": "finance.si"},
    {"sektor": "Mediji", "podjetje": "Mladina", "domena": "mladina.si"},
    {"sektor": "Mediji", "podjetje": "Reporter", "domena": "reporter.si"},
    {"sektor": "Mediji", "podjetje": "STA", "domena": "sta.si"},
    # Gradnja in nepremičnine
    {"sektor": "Gradnja in nepremičnine", "podjetje": "Intera", "domena": "intera.si"},
    {"sektor": "Gradnja in nepremičnine", "podjetje": "Triglav Nepremičnine", "domena": "triglav-nepremicnine.si"},
    {"sektor": "Gradnja in nepremičnine", "podjetje": "APlace", "domena": "aplace.si"},
    # Promet in logistika
    {"sektor": "Promet in logistika", "podjetje": "Pošta Slovenije", "domena": "posta.si"},
    {"sektor": "Promet in logistika", "podjetje": "Luka Koper", "domena": "luka.si"},
    # Šport
    {"sektor": "Šport", "podjetje": "NK Maribor", "domena": "nkmaribor.si"},
    {"sektor": "Šport", "podjetje": "NK Olimpija", "domena": "nkolimpija.si"},
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; AIVisibilityBot/1.0)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def check_url(url, timeout=10):
    """Check if URL exists and return status + content"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, verify=False)
        return r.status_code, r.text[:5000] if r.status_code == 200 else None
    except:
        return None, None

def audit_company(company):
    """Run full AI visibility audit on a company"""
    domain = company['domena']
    base_url = f"https://{domain}"
    result = {
        **company,
        'http_status': None,
        'llms_txt': False,
        'llms_txt_content': None,
        'schema_org': False,
        'schema_types': [],
        'meta_description': False,
        'og_tags': False,
        'sitemap': False,
        'robots_txt': False,
        'score': 0,
        'issues': [],
    }
    
    # 1. Check main page
    status, content = check_url(base_url)
    result['http_status'] = status
    
    if not content:
        result['issues'].append('Stran nedostopna')
        result['score'] = 0
        return result
    
    # 2. Check llms.txt
    status_llms, llms_content = check_url(f"{base_url}/llms.txt")
    if status_llms == 200 and llms_content and len(llms_content) > 50:
        result['llms_txt'] = True
        result['llms_txt_content'] = llms_content[:500]
    
    # 3. Check Schema.org (in page source)
    if 'application/ld+json' in content or 'schema.org' in content:
        result['schema_org'] = True
        # Extract schema types
        import re
        schema_matches = re.findall(r'"@type"\s*:\s*"([^"]+)"', content)
        result['schema_types'] = list(set(schema_matches))[:5]
    
    # 4. Check meta description
    if 'meta' in content.lower() and 'description' in content.lower():
        result['meta_description'] = True
    else:
        result['issues'].append('Ni meta description')
    
    # 5. Check OG tags
    if 'og:title' in content or 'og:description' in content:
        result['og_tags'] = True
    else:
        result['issues'].append('Ni Open Graph tagov')
    
    # 6. Check sitemap
    status_sitemap, _ = check_url(f"{base_url}/sitemap.xml")
    if status_sitemap == 200:
        result['sitemap'] = True
    else:
        result['issues'].append('Ni sitemap.xml')
    
    # 7. Check robots.txt
    status_robots, robots_content = check_url(f"{base_url}/robots.txt")
    if status_robots == 200:
        result['robots_txt'] = True
    else:
        result['issues'].append('Ni robots.txt')
    
    # Calculate score (0-100)
    score = 0
    if result['llms_txt']: score += 30  # Most important for AI
    if result['schema_org']: score += 25
    if result['meta_description']: score += 15
    if result['og_tags']: score += 10
    if result['sitemap']: score += 10
    if result['robots_txt']: score += 5
    if result['http_status'] == 200: score += 5
    
    # Bonus for rich Schema.org
    if len(result['schema_types']) >= 3: score += 5
    
    result['score'] = min(score, 100)
    
    # Classify
    if score >= 70:
        result['razred'] = 'A'
    elif score >= 50:
        result['razred'] = 'B'
    elif score >= 30:
        result['razred'] = 'C'
    elif score >= 10:
        result['razred'] = 'D'
    else:
        result['razred'] = 'F'
    
    return result

def main():
    print(f"🔍 AI Visibility Audit — {len(COMPANIES)} podjetij")
    print("=" * 60)
    
    results = []
    
    # Run audits with ThreadPoolExecutor (5 concurrent)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(audit_company, c): c for c in COMPANIES}
        
        for i, future in enumerate(as_completed(futures)):
            company = futures[future]
            try:
                result = future.result()
                results.append(result)
                status_icon = '✅' if result['score'] >= 50 else '⚠️' if result['score'] >= 20 else '❌'
                print(f"[{i+1}/{len(COMPANIES)}] {status_icon} {company['podjetje']}: {result['score']}/100 ({result['razred']})")
            except Exception as e:
                print(f"[{i+1}/{len(COMPANIES)}] ❌ {company['podjetje']}: ERROR - {e}")
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Save results
    output_file = '/home/darko/.openclaw/workspace/tools/ai_visibility_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 REZULTATI")
    print("=" * 60)
    
    # Count by grade
    grades = {}
    for r in results:
        g = r['razred']
        grades[g] = grades.get(g, 0) + 1
    
    for g in ['A', 'B', 'C', 'D', 'F']:
        count = grades.get(g, 0)
        bar = '█' * count
        print(f"  {g}: {count:>3} {bar}")
    
    # Top 10
    print("\n🏆 TOP 10:")
    for i, r in enumerate(results[:10]):
        print(f"  {i+1}. {r['podjetje']}: {r['score']}/100 — {', '.join(r['schema_types'][:3]) or 'brez Schema.org'}")
    
    # Bottom 10
    print("\n💀 BOTTOM 10:")
    for i, r in enumerate(results[-10:]):
        print(f"  {108-9+i}. {r['podjetje']} ({r['domena']}): {r['score']}/100")
    
    # Stats
    with_llms = sum(1 for r in results if r['llms_txt'])
    with_schema = sum(1 for r in results if r['schema_org'])
    invisible = sum(1 for r in results if r['score'] < 30)
    
    print(f"\n📈 STATISTIKA:")
    print(f"  Z llms.txt: {with_llms}/{len(results)} ({with_llms*100//len(results)}%)")
    print(f"  Z Schema.org: {with_schema}/{len(results)} ({with_schema*100//len(results)}%)")
    print(f"  Nevidnih za AI (ocena <30): {invisible}/{len(results)} ({invisible*100//len(results)}%)")
    
    print(f"\n💾 Rezultati shranjeni: {output_file}")

if __name__ == '__main__':
    main()
