/**
 * HD Web Design — i18n Translations (EN / SI)
 * Language auto-detection + localStorage persistence
 */

const translations = {
  en: {
    // Nav
    "nav.home": "Home",
    "nav.about": "About",
    "nav.projects": "Projects",
    "nav.blog": "Blog",
    "nav.services": "Services",
    "nav.contact": "Contact",
    // Hero
    "hero.title": "Building SaaS that solves real problems",
    "hero.subtitle": "Hi, I'm Darko — a developer and founder from Slovenia. I create AI‑powered tools that help restaurants, marketers, and businesses grow. Simple, effective, and built to scale.",
    "hero.cta1": "See my work",
    "hero.cta2": "Get in touch",
    // About
    "about.title": "About Me",
    "about.p1": "I'm a full-stack developer based in Slovenia with a passion for building products that make a difference. With years of experience in web development, I've transitioned from building websites for clients to creating SaaS products that solve real-world problems.",
    "about.p2": "My focus is on <strong>AI-powered solutions</strong> — tools that leverage artificial intelligence to automate tasks, generate content, and provide insights that would otherwise take hours of manual work.",
    "about.stat1.num": "5+",
    "about.stat1.label": "Years Experience",
    "about.stat2.num": "3",
    "about.stat2.label": "Active SaaS Products",
    "about.stat3.num": "6",
    "about.stat3.label": "Languages Supported",
    // About page (new)
    "about.page.title": "About Me",
    "about.page.subtitle": "SaaS Builder · AI Developer · Indie Maker · Slovenia 🇸🇮",
    "about.who.title": "Who Am I?",
    "about.who.p1": "I'm a <strong>Slovenian full-stack developer and SaaS founder</strong>. I'm the founder of <strong>HD Web Design</strong> and the creator of three AI-powered SaaS products: <a href='/menu-boost/'>MenuBoost</a>, <a href='/boost-suite/'>BoostSuite</a>, and <a href='/ad-boost/'>AdBoost</a>.",
    "about.who.p2": "I focus on practical AI applications — tools that automate real business tasks. From generating multilingual restaurant menus to auditing SEO performance and creating ad copy. My products serve clients across Europe, with a focus on the Slovenian, Croatian, and Italian markets.",
    "about.what.title": "What I Do",
    "about.what.p1": "<strong>HD Web Design</strong> is my brand and platform for SaaS products and web development services. Based in Slovenia (hd-webdesign.si), it's the hub for AI-powered tools I've built to help businesses grow:",
    "about.what.mb": "AI-powered multilingual menu descriptions for restaurants. Generates compelling food descriptions in 6 languages in seconds.",
    "about.what.bs": "4-in-1 AI marketing toolkit for agencies: SEO Audit, GEO Check, Ad Copy Generator, and Listing Optimizer.",
    "about.what.ab": "AI-powered ad copy generator for Google, Facebook, and Instagram campaigns.",
    "about.bg.title": "My Background",
    "about.bg.p1": "My journey in tech started with web development and evolved into building full-stack SaaS applications. I work with modern technologies including JavaScript, Python, React, Node.js, and leverage AI models like DeepSeek to power my products.",
    "about.bg.specializes": "I specialize in:",
    "about.bg.s1.title": "SaaS Product Development",
    "about.bg.s1.desc": "From idea to deployment, building complete products.",
    "about.bg.s2.title": "AI Integration",
    "about.bg.s2.desc": "Using LLMs for content generation, SEO analysis, and automation.",
    "about.bg.s3.title": "Multi-language Applications",
    "about.bg.s3.desc": "Full i18n support across European languages.",
    "about.bg.s4.title": "SEO & Marketing Automation",
    "about.bg.s4.desc": "Data-driven tools for agencies and businesses.",
    "about.facts.title": "Quick Facts",
    "about.stat4.label": "Based in Slovenia",
    "about.connect.title": "Connect",

    // Projects
    "projects.title": "My Projects",
    "projects.subtitle": "AI-powered tools built to solve real problems for businesses",
    "projects.badge": "Featured",
    "projects.menuboost.desc": "AI‑powered multilingual menu descriptions for restaurants. Generate compelling food descriptions in 6 languages in seconds.",
    "projects.bootsuite.desc": "4‑in‑1 AI marketing toolkit: SEO Audit, GEO Check, Ad Copy Generator, and Listing Optimizer for agencies.",
    "projects.adboost.desc": "AI-powered ad copy generator for Google, Facebook, and Instagram. Generate converting ad copy in seconds.",
    "projects.learn": "Learn more",
    // Services
    "services.title": "Services",
    "services.subtitle": "How I can help your business",
    "services.webdev.title": "Web Development",
    "services.webdev.desc": "Custom websites and web applications built with modern technologies.",
    "services.ai.title": "AI Integration",
    "services.ai.desc": "Integrate AI capabilities into your existing systems.",
    "services.seo.title": "SEO & Marketing",
    "services.seo.desc": "Data-driven SEO strategies and marketing automation.",
    "services.saas.title": "SaaS Consulting",
    "services.saas.desc": "From idea to launch — guidance on building your SaaS product.",
    // Blog
    "blog.title": "Blog",
    "blog.subtitle": "Articles about HD Web Design, our products, and AI development",
    "blog.post1.title": "Who is Darko Herceg?",
    "blog.post1.desc": "Meet the Slovenian SaaS builder behind MenuBoost, BoostSuite, and AdBoost. Learn about the journey from web development to AI-powered products.",
    "blog.post2.title": "What is HD Web Design?",
    "blog.post2.desc": "Discover how HD Web Design builds AI tools for restaurants, agencies, and businesses. From MenuBoost to BoostSuite — the full story.",
    "blog.readmore": "Read more",
    // Contact
    "contact.title": "Get in touch",
    "contact.desc": "Whether you're interested in collaboration, have feedback, or want to discuss a project — I'd love to hear from you.",
    // Footer
    "footer.privacy": "Privacy Policy",
    "footer.rights": "© 2026 Darko Herceg. All rights reserved.",
    "footer.built": "Slovenia · Built with 💻 and ☕️",
    // Cookie
    "cookie.title": "🍪 We value your privacy",
    "cookie.desc": 'We use cookies to enhance your browsing experience, serve personalized content, and analyze our traffic. By clicking "Accept All", you consent to our use of cookies.',
    "cookie.accept": "Accept All",
    "cookie.necessary": "Necessary Only",
    // Language selector
    "lang.selector": "EN"
  },
  si: {
    // Nav
    "nav.home": "Domov",
    "nav.about": "O meni",
    "nav.projects": "Projekti",
    "nav.blog": "Blog",
    "nav.services": "Storitve",
    "nav.contact": "Kontakt",
    // Hero
    "hero.title": "Gradim SaaS, ki rešuje realne probleme",
    "hero.subtitle": "Živjo, sem Darko — razvijalec in ustanovitelj iz Slovenije. Ustvarjam AI orodja, ki pomagajo restavracijam, tržnikom in podjetjem rasti. Preprosto, učinkovito in zgrajeno za skaliranje.",
    "hero.cta1": "Oglejte si moje delo",
    "hero.cta2": "Kontaktirajte me",
    // About
    "about.title": "O meni",
    "about.p1": "Sem full-stack razvijalec iz Slovenije, ki ga žene strast do izdelkov, ki naredijo razliko. Z leti izkušenj v spletnem razvoju sem prešel od izdelave spletnih strani za stranke do ustvarjanja SaaS produktov, ki rešujejo realne probleme.",
    "about.p2": "Moja usmeritev je <strong>AI rešitve</strong> — orodja, ki izkoriščajo umetno inteligenco za avtomatizacijo opravil, generiranje vsebin in vpoglede, ki bi drugače vzeli ure ročnega dela.",
    "about.stat1.num": "5+",
    "about.stat1.label": "Let izkušenj",
    "about.stat2.num": "3",
    "about.stat2.label": "Aktivni SaaS produkti",
    "about.stat3.num": "6",
    "about.stat3.label": "Podprti jeziki",
    // About page (new) - Slovenian
    "about.page.title": "O meni",
    "about.page.subtitle": "SaaS razvijalec · AI developer · Indie maker · Slovenija 🇸🇮",
    "about.who.title": "Kdo sem?",
    "about.who.p1": "Sem <strong>slovenski full-stack razvijalec in SaaS ustanovitelj</strong>. Ustanovitelj sem <strong>HD Web Design</strong> in ustvarjalec treh AI SaaS produktov: <a href='/menu-boost/'>MenuBoost</a>, <a href='/boost-suite/'>BoostSuite</a> in <a href='/ad-boost/'>AdBoost</a>.",
    "about.who.p2": "Usmerjen sem v praktične AI aplikacije — orodja, ki avtomatizirajo realna poslovna opravila. Od generiranja večjezičnih jedilnikov do analize SEO in ustvarjanja oglasnih besedil. Moji produkti služijo strankam po Evropi, s poudarkom na slovenskem, hrvaškem in italijanskem trgu.",
    "about.what.title": "Kaj delam",
    "about.what.p1": "<strong>HD Web Design</strong> je moja blagovna znamka in platforma za SaaS produkte in spletne storitve. Sedež imam v Sloveniji (hd-webdesign.si) in služi kot center za AI orodja, ki sem jih zgradil za pomoč podjetjem pri rasti:",
    "about.what.mb": "AI večjezični opisi jedilnikov za restavracije. Ustvarite privlačne opise jedi v 6 jezikih v nekaj sekundah.",
    "about.what.bs": "4-v-1 AI marketinška orodja za agencije: SEO audit, GEO preverjanje, generator oglasnih besedil in optimizacija oglasov.",
    "about.what.ab": "AI generator oglasnih besedil za Google, Facebook in Instagram kampanje.",
    "about.bg.title": "Moje ozadje",
    "about.bg.p1": "Moja pot v tehnologiji se je začela s spletnim razvojem in prerasla v gradnjo full-stack SaaS aplikacij. Delam z modernimi tehnologijami vključno z JavaScript, Python, React, Node.js in uporabljam AI modele kot DeepSeek za poganjanje svojih produktov.",
    "about.bg.specializes": "Specializiram se za:",
    "about.bg.s1.title": "Razvoj SaaS produktov",
    "about.bg.s1.desc": "Od ideje do implementacije, gradnja celotnih produktov.",
    "about.bg.s2.title": "AI integracija",
    "about.bg.s2.desc": "Uporaba LLM za generiranje vsebin, SEO analizo in avtomatizacijo.",
    "about.bg.s3.title": "Večjezične aplikacije",
    "about.bg.s3.desc": "Polna podpora za i18n v evropskih jezikih.",
    "about.bg.s4.title": "SEO in marketinška avtomatizacija",
    "about.bg.s4.desc": "Podatkovno gnana orodja za agencije in podjetja.",
    "about.facts.title": "Dejstva",
    "about.stat4.label": "Sedež v Sloveniji",
    "about.connect.title": "Kontakt",

    // Projects
    "projects.title": "Moji projekti",
    "projects.subtitle": "AI orodja, zgrajena za reševanje realnih problemov podjetij",
    "projects.badge": "Izpostavljeno",
    "projects.menuboost.desc": "AI večjezični opisi jedilnikov za restavracije. Ustvarite privlačne opise jedi v 6 jezikih v nekaj sekundah.",
    "projects.bootsuite.desc": "4-v-1 AI marketinški komplet: SEO revizija, GEO preverjanje, generator oglasnih besedil in optimizacija oglasov za agencije.",
    "projects.adboost.desc": "AI generator oglasnih besedil za Google, Facebook in Instagram. Ustvarite konvertirajoča besedila v sekundah.",
    "projects.learn": "Preberi več",
    // Services
    "services.title": "Storitve",
    "services.subtitle": "Kako vam lahko pomagam pri poslu",
    "services.webdev.title": "Spletni razvoj",
    "services.webdev.desc": "Po meri izdelane spletne strani in aplikacije z modernimi tehnologijami.",
    "services.ai.title": "AI integracija",
    "services.ai.desc": "Vključite AI zmogljivosti v vaše obstoječe sisteme.",
    "services.seo.title": "SEO in marketing",
    "services.seo.desc": "Podatkovno podprte SEO strategije in marketinška avtomatizacija.",
    "services.saas.title": "SaaS svetovanje",
    "services.saas.desc": "Od ideje do zagona — vodstvo pri izgradnji vašega SaaS produkta.",
    // Blog
    "blog.title": "Blog",
    "blog.subtitle": "Članki o HD Web Design, naših produktih in AI razvoju",
    "blog.post1.title": "Kdo je Darko Herceg?",
    "blog.post1.desc": "Spoznajte slovenskega SaaS graditelja za MenuBoost, BoostSuite in AdBoost. Odkrijte pot od spletnega razvoja do AI produktov.",
    "blog.post2.title": "Kaj je HD Web Design?",
    "blog.post2.desc": "Odkrijte kako HD Web Design gradi AI orodja za restavracije, agencije in podjetja. Od MenuBoost do BoostSuite — celotna zgodba.",
    "blog.readmore": "Preberi več",
    // Contact
    "contact.title": "Kontaktirajte me",
    "contact.desc": "Ne glede na to, ali vas zanima sodelovanje, imate povratne informacije ali želite razpravljati o projektu — z veseljem vas bom slišal.",
    // Footer
    "footer.privacy": "Pravila zasebnosti",
    "footer.rights": "© 2026 Darko Herceg. Vse pravice pridržane.",
    "footer.built": "Slovenija · Izdelano z 💻 in ☕️",
    // Cookie
    "cookie.title": "🍪 Vaša zasebnost je pomembna",
    "cookie.desc": "Uporabljamo piškotke za izboljšanje vaše izkušnje, prikaz prilagojenih vsebin in analizo prometa. Z klikom \"Sprejmi vse\" soglašate z našo uporabo piškotkov.",
    "cookie.accept": "Sprejmi vse",
    "cookie.necessary": "Samo nujni",
    // Language selector
    "lang.selector": "SI"
  }
};

/**
 * Apply translations to all elements with data-i18n attribute
 */
function applyTranslations(lang) {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (translations[lang] && translations[lang][key]) {
      // Use innerHTML for keys that contain HTML (like about.p2)
      if (translations[lang][key].includes('<')) {
        el.innerHTML = translations[lang][key];
      } else {
        el.textContent = translations[lang][key];
      }
    }
  });
  // Update lang attribute
  document.documentElement.lang = lang === 'si' ? 'sl' : 'en';
  // Update selector button
  const btn = document.getElementById('langToggle');
  if (btn) btn.textContent = lang === 'si' ? 'EN' : 'SI';
}

/**
 * Toggle between EN and SI
 */
function toggleLanguage() {
  const current = localStorage.getItem('hd-lang') || 'en';
  const next = current === 'en' ? 'si' : 'en';
  localStorage.setItem('hd-lang', next);
  applyTranslations(next);
}

/**
 * Detect browser language on first visit
 */
function detectLanguage() {
  const saved = localStorage.getItem('hd-lang');
  if (saved) return saved;
  const browserLang = navigator.language || navigator.userLanguage || '';
  return browserLang.startsWith('sl') ? 'si' : 'en';
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  const lang = detectLanguage();
  localStorage.setItem('hd-lang', lang);
  applyTranslations(lang);
});
