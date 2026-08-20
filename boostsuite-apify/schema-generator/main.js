import { Actor } from 'apify';

await Actor.init();

const input = await Actor.getInput();
const { type, name, url, description, phone, address, email, logo, socialMedia } = input;

console.log(`Generating ${type} schema for: ${name}`);

// Build base schema
let schema = {
  '@context': 'https://schema.org',
  '@type': type,
  name,
  url,
};

// Add optional fields
if (description) schema.description = description;
if (phone) schema.telephone = phone;
if (email) schema.email = email;
if (logo) schema.logo = logo;

// Type-specific fields
if (type === 'Organization' || type === 'LocalBusiness') {
  if (socialMedia) {
    schema.sameAs = Array.isArray(socialMedia) ? socialMedia : [socialMedia];
  }
}

if (type === 'LocalBusiness') {
  if (address) {
    schema.address = {
      '@type': 'PostalAddress',
      streetAddress: address.street || address,
      addressLocality: address.city || '',
      addressRegion: address.region || '',
      postalCode: address.postalCode || '',
      addressCountry: address.country || 'SI',
    };
  }
  if (input.geo) {
    schema.geo = {
      '@type': 'GeoCoordinates',
      latitude: input.geo.latitude,
      longitude: input.geo.longitude,
    };
  }
  if (input.openingHours) {
    schema.openingHoursSpecification = input.openingHours;
  }
  if (input.priceRange) {
    schema.priceRange = input.priceRange;
  }
}

if (type === 'FAQPage' && input.faqs) {
  schema.mainEntity = input.faqs.map(faq => ({
    '@type': 'Question',
    name: faq.question,
    acceptedAnswer: {
      '@type': 'Answer',
      text: faq.answer,
    },
  }));
}

if (type === 'Product') {
  if (input.brand) schema.brand = { '@type': 'Brand', name: input.brand };
  if (input.offers) {
    schema.offers = {
      '@type': 'Offer',
      price: input.offers.price,
      priceCurrency: input.offers.currency || 'EUR',
      availability: 'https://schema.org/InStock',
    };
  }
}

if (type === 'Service') {
  if (input.provider) schema.provider = { '@type': 'Organization', name: input.provider };
  if (input.areaServed) schema.areaServed = input.areaServed;
  if (input.serviceType) schema.serviceType = input.serviceType;
}

// Generate HTML embed code
const htmlEmbed = `<!-- BoostSuite Schema Markup -->
<script type="application/ld+json">
${JSON.stringify(schema, null, 2)}
</script>`;

const result = {
  schemaType: type,
  schema,
  htmlEmbed,
  instructions: [
    '1. Copy the HTML embed code above',
    '2. Paste it in the <head> or <body> of your HTML page',
    '3. Test at https://search.google.com/structured-data/testing-tool',
    '4. Submit to Google Search Console for indexing',
  ],
  validationUrl: 'https://search.google.com/structured-data/testing-tool',
};

console.log(`Generated ${type} schema for ${name}`);
await Actor.pushData(result);
await Actor.exit();
