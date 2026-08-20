# Lead Hunter

Napredni iskalnik leadov za vse storitve na hd-webdesign.si.

## Storitve

| Storitev | Koga iščemo | Viri |
|----------|-------------|------|
| **MenuBoost** | Restavracije, hoteli, kavarne, turistične kmetije | Overpass API, web search |
| **BoostSuite** | SEO agencije, freelancerji, digitalni marketing | Web search, Clutch.co |
| **AI Authority** | Podjetja za GEO optimizacijo (AI vidljivost) | Web search, Clutch.co |
| **Subvencije** | Slovenska podjetja, iskalci EU sredstev | Web search, SPI.si |
| **HD Web Design** | Podjetja brez spletne strani | Web search |

## Uporaba

```bash
# Iskanje za eno storitev
python3 scrapers/lead_hunter.py --service menuboost --region si

# Vse storitve, vse regije
python3 scrapers/lead_hunter.py --service all --region si,hr,it

# Z auditom (schema.org, llm.txt, SEO)
python3 scrapers/lead_hunter.py --service menuboost --region si --audit

# Export v en CSV
python3 scrapers/lead_hunter.py --service all --region si,hr,it --export all-leads.csv
```

## Regije

| Regija | Opis |
|--------|------|
| `si` | Celotna Slovenija |
| `si-coast` | Slovenska obala |
| `si-ljubljana` | Ljubljana |
| `hr` | Hrvaška |
| `hr-istra` | Istra |
| `it` | Italija |
| `it-trieste` | Trst |
| `de` | Nemčija |
| `at` | Avstrija |
| `global` | Globalno |

## Kaj najde

- **Email naslove** iz spletnih strani
- **Telefonske številke** iz Overpass API
- **Spletne strani** podjetij
- **Audit podatke**: schema.org, llm.txt, SEO score
- **Kuhinjo** (za restavracije) iz Overpass API

## Shrani

Rezultati gredo v `lead-gen/{service}/hunter-{region}-{timestamp}.csv`

## Opombe

- Overpass API je brezplačen (poskusi več endpointov)
- Firecrawl search stane 2 kredita na iskanje
- Dedup avtomatsko odstrani že obstoječe leadse
- Generic emaili (info@, contact@) se preskočijo
