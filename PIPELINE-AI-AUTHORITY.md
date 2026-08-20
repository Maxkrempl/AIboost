# AI Authority Pipeline — AI Izkaznica + Indeks AI-vidljivosti

## Kaj je to
Lead gen pipeline za AI Authority prodajo. Brezplačno orodje generira leadove, mi jih contactiramo.

## Komponente

### 1. AI Izkaznica (brezplačno orodje)
- **URL:** hd-webdesign.si/ai-izkaznica/
- **Kaj dela:** Vpišeš domeno → dobiš oceno A-F za AI vidljivost
- **API:** POST /ai-izkaznica/api/audit.php (brezplačen audit)
- **Za koga:** Za vse — free lead gen orodje

### 2. Indeks AI-vidljivosti Slovenije
- **URL:** hd-webdesign.si/indeks-ai-vidljivosti/
- **Kaj dela:** Javna lestvica slovenskih podjetij po AI vidljivosti
- **Trenutno:** 268 podjetij, vsa javno vidna
- **API:** /indeks-ai-vidljivosti/api/index.php + data.json

### 3. Pipeline (avtomatski)
```
AI Izkaznica (brezplačno)
    ↓
Zajem leadov (domena, email, ocena)
    ↓
Scrape kontaktnih podatkov
    ↓
Generate email z oceno (D/F = prioriteta)
    ↓
Queue (outreach/queue/)
    ↓
Cron 8:15 = send_izkaznica_batch.py
    ↓
Email od max@hd-webdesign.si
    ↓
Odgovor → prodaja AI Authority (€699 + €49/mo)
```

### 4. Cron Jobs
- **8:00** — Daily Lead Report (poročilo iz Indeksa)
- **8:15** — Send Izkaznica Emails (pošiljanje iz queue)

### 5. Scripti
- `outreach/izkaznica_pipeline.py` — generira leadove iz Indeksa v queue
- `outreach/send_izkaznica_batch.py` — pošlje email iz queue

### 6. Podatki
- **Queue:** outreach/queue/*.json (email za pošiljanje)
- **Sent:** outreach/.izkaznica-sent.json (že poslani)
- **Processed:** outreach/.izkaznica-processed.json (že obdelani)
- **Cache:** /ai-izkaznica/api/cache/ (auditi na strežniku)

### 7. Email
- **From:** Darko iz HD Web Design <max@hd-webdesign.si>
- **Reply-To:** hercegdarko@hd-webdesign.si
- **Subject:** Vaša AI Izkaznica za {domain} — ocena {score}/100 ({grade})

### 8. Pitch
"Imate stran, ampak AI vas ne vidi — mi to popravimo"
- D/F = outreach target (slaba vidljivost)
- C = manj prioritetno
- A/B = ne contactiramo ( že imajo dobro vidljivost)

### 9. Prodaja
- **AI Authority:** €699 enkratno + €49/mesec
- Vključuje: llms.txt, Schema.org, meta optimizacijo
- **Cenik paketi:** Začetni €890, Poslovni €1.990, Premium €3.490

## Ko Darko reče "AI izkaznice" ali "AI authority"
→ Ta pipeline! Ne raziskovati od začetka!
