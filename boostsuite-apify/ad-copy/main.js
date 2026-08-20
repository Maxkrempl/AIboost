import { Actor } from 'apify';

await Actor.init();

const input = await Actor.getInput();
const { product, audience, platform, language, usps, cta } = input;

console.log(`Generating ${platform} ad copy for: ${product}`);

// Default USPs if not provided
const features = usps || [
  'Hitro in enostavno',
  'AI-podprto',
  'Brezplačna preskusna verzija',
  'Cena od €19/mesec',
];

// Generate headlines (max 30 chars for Google, unlimited for Meta)
const headlines = {
  google: [
    `${product} — Hitro in Zanesljivo`,
    `Najboljša Ponudba za ${product}`,
    `${product} po Meri`,
    `Zaupajte Strokovnjakom`,
    `${product} Od €19/mesec`,
    `Brezplačen Poskus — ${product}`,
    `${product} za ${audience || 'Vas'}`,
    `AI ${product} Orodje`,
    `Prihranite Čas z ${product}`,
    `${product} — Takojšnji Rezultati`,
  ],
  meta: [
    `${product} — Revolucija v ${audience || 'Vašem Poslu'}`,
    `Zakaj ${audience || 'Podjetja'} Izbirajo ${product}?`,
    `${product}: AI Orodje ki Deluje`,
    `Končajte z Ročnim Delom — ${product}`,
    `${product} v 5 minutah`,
  ],
};

// Generate descriptions
const descriptions = {
  google: [
    `Odkrijte ${product} — AI-podprto orodje${audience ? ` za ${audience}` : ''}. Brezplačna preskusna verzija, takojšnji rezultati.`,
    `Z ${product} prihranite čas in denar. Enostavna nastavitev, profesionalni rezultati. Začnite danes.`,
    `${product} — Vaše orodje za uspeh${audience ? ` v ${audience}` : ''}. Preizvusite brezplačno.`,
    `Ne izgubljajte časa. ${product} naredi vse za vas. Od €19/mesec.`,
    `AI tehnologija za ${audience || 'vaše podjetje'}. ${product} — hitro, pametno, ugodno.`,
  ],
  meta: [
    `Ste ${audience || 'podjetje'} ki išče boljše orodje? ${product} je rešitev. AI-podprto, hitro, ugodno.`,
    `🚀 ${product} — končajte z enim orodjem vse kar potrebujete. Brezplačen poskus!`,
    `Zakaj ${audience || 'podjetja'} prehajajo na ${product}? Ker deluje. Preizvusite sami.`,
    `⏰ Prihranite 10+ ur tedensko z ${product}. AI naredi težko delo namesto vas.`,
    `💎 Premium ${product} po ugodni ceni. Od €19/mesec. Brezplačen poskus.`,
  ],
};

// CTA options
const ctaOptions = {
  learn: 'Več Informacij',
  signup: 'Prijavite se Brezplačno',
  buy: 'Nakupite Zdaj',
  trial: 'Preizvusite Brezplačno',
  contact: 'Kontaktirajte Nas',
};

const selectedCta = ctaOptions[cta] || ctaOptions.trial;

// Assemble result
const result = {
  product,
  audience: audience || 'General',
  platform,
  cta: selectedCta,
  google: platform === 'google' || platform === 'both' ? {
    headlines: headlines.google.slice(0, 15),
    descriptions: descriptions.google.slice(0, 5),
    characterLimits: {
      headline: 'Max 30 characters',
      description: 'Max 90 characters',
    },
    tips: [
      'Include keywords in headlines',
      'Use numbers and specific benefits',
      'Include a clear CTA',
      'Test multiple headline variations',
    ],
  } : null,
  meta: platform === 'meta' || platform === 'both' ? {
    headlines: headlines.meta.slice(0, 5),
    descriptions: descriptions.meta.slice(0, 5),
    primaryText: `${product} — AI orodje za ${audience || 'vaše podjetje'}. Brezplačen poskus, takojšnji rezultati.`,
    characterLimits: {
      headline: 'Max 40 characters',
      description: 'Max 125 characters',
      primaryText: 'Max 125 characters',
    },
    tips: [
      'Use eye-catching emojis',
      'Focus on benefits, not features',
      'Include social proof',
      'Test different audiences',
    ],
  } : null,
  tips: [
    'A/B test your ads regularly',
    'Track conversions with UTM parameters',
    'Refresh ad copy every 2-4 weeks',
    'Use audience-specific messaging',
    'Include pricing when competitive',
  ],
};

console.log(`Generated ${platform} ad copy for ${product}`);
await Actor.pushData(result);
await Actor.exit();
