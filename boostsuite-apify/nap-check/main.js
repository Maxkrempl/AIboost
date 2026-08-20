import { Actor } from 'apify';

await Actor.init();

const input = await Actor.getInput();
const { businessName, phone, address, website, email } = input;

console.log(`Checking NAP consistency for: ${businessName}`);

// Normalize NAP data for comparison
const normalize = (str) => str?.toLowerCase().replace(/[^a-z0-9]/g, '') || '';
const normalizePhone = (str) => str?.replace(/[^0-9+]/g, '') || '';

const canonicalNap = {
  name: businessName,
  nameNormalized: normalize(businessName),
  phone: phone,
  phoneNormalized: normalizePhone(phone),
  address: address,
  addressNormalized: normalize(address),
  website: website?.toLowerCase(),
  email: email?.toLowerCase(),
};

// Directories to check (in real implementation, these would be API calls)
const directories = [
  { name: 'Google Business Profile', url: 'https://business.google.com', checkMethod: 'manual' },
  { name: 'Yelp', url: 'https://yelp.com', checkMethod: 'manual' },
  { name: 'Facebook', url: 'https://facebook.com', checkMethod: 'manual' },
  { name: 'Apple Maps', url: 'https://maps.apple.com', checkMethod: 'manual' },
  { name: 'Bing Places', url: 'https://bing.com/places', checkMethod: 'manual' },
  { name: 'TripAdvisor', url: 'https://tripadvisor.com', checkMethod: 'manual' },
  { name: 'Foursquare', url: 'https://foursquare.com', checkMethod: 'manual' },
  { name: 'Yellow Pages', url: 'https://yellowpages.com', checkMethod: 'manual' },
];

// Generate verification URLs for manual checking
const verificationUrls = {
  google: `https://www.google.com/search?q=${encodeURIComponent(businessName + ' ' + address)}`,
  yelp: `https://www.yelp.com/search?find_desc=${encodeURIComponent(businessName)}&find_loc=${encodeURIComponent(address)}`,
  facebook: `https://www.facebook.com/search/pages/?q=${encodeURIComponent(businessName)}`,
  apple: `https://maps.apple.com/?q=${encodeURIComponent(businessName)}`,
  bing: `https://www.bing.com/maps?q=${encodeURIComponent(businessName + ' ' + address)}`,
};

// NAP consistency issues to check for
const commonIssues = [
  { issue: 'Inconsistent name formatting', examples: ['Inc. vs LLC', 'St. vs Street', 'Ampersand vs and'] },
  { issue: 'Phone number format differences', examples: ['+386 40 123 456 vs 040 123 456', '(555) 123-4567 vs 555-123-4567'] },
  { issue: 'Address abbreviation variations', examples: ['Street vs St.', 'Avenue vs Ave.', 'Suite vs Ste.'] },
  { issue: 'Missing or outdated listings', examples: ['Old business name', 'Previous address', 'Disconnected phone'] },
  { issue: 'Duplicate listings', examples: ['Multiple Google profiles', 'Old Yelp page', 'Forgotten Facebook page'] },
];

// Build result
const result = {
  business: businessName,
  canonicalNap,
  directories: directories.map(d => ({
    name: d.name,
    url: d.url,
    status: 'needs_verification',
    action: `Search for "${businessName}" on ${d.name}`,
  })),
  verificationUrls,
  commonIssues,
  recommendations: [
    'Search for your business on each directory listed above',
    'Ensure NAP is EXACTLY the same everywhere (including punctuation)',
    'Update any inconsistent or outdated listings',
    'Remove duplicate listings if found',
    'Use a consistent format: "Business Name" not "business name"',
    'Include suite/unit numbers in address if applicable',
    'Use the same phone format everywhere',
  ],
  napTemplate: {
    name: businessName,
    phone: phone,
    address: address,
    website: website,
    email: email || '',
    note: 'Use this exact format on ALL directories',
  },
  importance: {
    localSeo: 'NAP consistency is a top ranking factor for local SEO',
    aiVisibility: 'AI assistants use NAP data to verify business legitimacy',
    customerTrust: 'Consistent information builds trust with customers',
    mapRanking: 'Inconsistent NAP hurts Google Maps ranking',
  },
};

console.log(`Generated NAP check report for ${businessName}`);
await Actor.pushData(result);
await Actor.exit();
