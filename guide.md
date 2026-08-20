# Skupni onboarding za AdBoost MVP in ostale aplikacije

Ta dokument predstavlja enoten onboarding okvir za AdBoost MVP Pilot – 4-platform onboarding in spremljajoče aplikacije (SEOBooster, EtsyBooster, MenuBoost, GEOBoost). Namen je zagotoviti hitri, ponovljivi in meri proces za pridobivanje pilotov, zbiranje povratnih informacij ter postavitev osnove za rast.

## Obseg in cilji
- Aplikacije vključene v skupni onboarding: AdBoost, SEOBooster, EtsyBooster, MenuBoost, GEOBoost.
- Cilji onboarding programa:
  - vzpostaviti enoten onboarding tok, ki se lahko ponovi za več aplikacij,
  - pridobiti 1–3 pilote v prvem krogu,
  - vzpostaviti kanale za lead generation in komunikacijo (Wave 1 outreach),
  - omogočiti proces za zbiranje povratnih informacij in ROI indikacij.
- Ključne integracije: Gumroad (listing), Netlify (MVP site), GitHub (PR/deploy), LeadSheet (lead gen).

## Faze onboardinga

### Faza 1 – Setup & Launch (Dnevi 1-4)
- Gumroad listing: končni naziv, opis, slike, pogoji, testni način; webhook-ji usmerjeni na onboarding flow.
- GitHub PR & repozitorij: push funkcionalnosti, PR v glavno vejo z opisom.
- Netlify MVP: preveriti build in deploy, zagotoviti, da landing stran in onboarding flow delujeta.
- Dnevni digest: ustvariti predlogo za 09:00 CET dnevni digest, definirati metrike.

### Faza 2 – Outreach & onboarding (Dnevi 5-8)
- Wave 1 outreach: 8–10 prilagojenih sporočil (email/LinkedIn) iz LeadSheet targetov.
- Priprema onboardinga pilotov: onboarding materiali, welcome emaili, razporeditev terminov.
- Lead generation: dodajanje 5–10 novih leadov v LeadSheet, osvežitev ICP-jev.

### Faza 3 – Pilot onboarding & iteracija (Dnevi 9-14)
- Onboardiranje prvih pilotov (1–3): onboarding sessions, zbiranje povratnih informacij, hitre prilagoditve.
- Vsebinski optimization: prilagoditve Wave 1 template-jev, izboljšave končne onboarding uporabniške poti, posodobitev FAQ.
- Upravljanje tveganj: spremljanje blokad, log tveganj, prilagoditve plana po potrebi.

### Faza 4 – Skaliranje, zaključek & handoff (Dnevi 15-18)
- Širitev onboarding-a (če kapacitete dopuščajo): onboarding dodatnih pilotov, pridobitev pričevanj in ROI projekcij.
- Pakiranje rezultatov: 1-stranski povzetek, ROI projekcije, primeri za prihodnje kampanje.
- Zaključen dnevni digest: povzetek tedenskih rezultatov, predlog naslednjega koraka (Pro upsell, širitev).

## Kaj bomo merili (KPIs)
- Activation rate na onboardingu (delež uporabnikov, ki zaključi onboarding).
- Čas do onboard (time-to-first-pilot).
- Število onboardanih pilotov (1–3 v prvem krogu).
- Odzivi iz Wave 1 outreach (odpiranje, kliki, odgovori).
- ROI indikacije (na nivoju pilotov).
- Subjektivni kvalitativni feedback o uporabniški izkušnji.

## Deliverables
- Gumroad listing live ali pripravljen za hitro objavo.
- Open PR v GitHubu in njegove napredovanje do merge v glavno vejo.
- Netlify MVP live z onboarding flow-om preverjenim.
- Onboarding materiali za pilote (welcomne emaili, vodiči).
- Dnevni digest z napredkom, odločitvami in blokadami.

## Štiri vloge / vzorčne vsebine (priporočeni primeri)
- Welcome email (AdBoost):
  - Zadeva: Dobrodošli v AdBoost MVP Pilot – 4-Platform Onboarding
  - Telo: hvala za prijavo, kratek opis poteka onboarding-a, pričakovani časovni okvir, kontakt za podporo.
- Onboarding guide (adboost): kratek vodič po korakih onboarding-a, s časovnim okvirjem in ključnimi nalogami.
- FAQ: odgovori na najpogostejša vprašanja o prijavi, plačilih, podevanju integracij.
- Primer korespondence (LinkedIn): kratko sporočilo, ki se prilagodi na lead, s CTA za kratek mention.

## Tveganja in mitigacije
- Zadržanje PR/konflikti: sproti reševati in komunicirati status.
- Gumroad webhook ali plačila: preverjati in potrditev pravilnikov.
- Netlify deployment: spremljanje build/logov, DNS nastavitev.
- Nizka odzivnost outreach-a: pril thần ed-time cadence, A/B test sprememb.
- Omejitve kapacitet: prioritizirati pilote, planirati fallback.

## Tehnični tok (sinhronizacije)
- Gumroad listing <-> onboarding webhook
- Netlify MVP <-> landing/onboarding flow
- GitHub PR <-> deployment
- LeadSheet (ICP) <-> Wave 1 outreach

## Kaj potrebujem od tebe
- Potrdi, da shranim to kot skupni onboarding guide v guide.md (ta datoteka je ustvarjena v korenu workspace-a).
- Sporoči ali želiš, da dodam dodatne datoteke (npr. sample templates per app) ali naj ostane kotsem preprost skupni vodič.

## Naslednji koraki
- Po potrditvi bom ustvaril/dodelil dodatne materiale in, če želiš, jih povezal z repozitoriji in Netlify projekti.
