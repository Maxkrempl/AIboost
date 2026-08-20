<?php
/**
 * GEO Audit Engine — analyzes a website for AI visibility
 * Used by AI Authority Foundation
 */

class GeoAudit {
    private $url;
    private $domain;
    private $html = '';
    private $dom;
    private $report = [];
    
    // Score weights
    private $weights = [
        'llms_txt' => 15,
        'schema_org' => 20,
        'open_graph' => 10,
        'meta_description' => 5,
        'structured_data' => 15,
        'robots_txt' => 5,
        'sitemap' => 5,
        'semantic_html' => 10,
        'heading_structure' => 5,
        'content_quality' => 10,
    ];
    
    public function __construct(string $url) {
        $this->url = rtrim($url, '/');
        if (!str_starts_with($this->url, 'http')) {
            $this->url = 'https://' . $this->url;
        }
        $parsed = parse_url($this->url);
        $this->domain = $parsed['scheme'] . '://' . $parsed['host'];
    }
    
    public function run(): array {
        $this->report = [
            'url' => $this->url,
            'domain' => $this->domain,
            'timestamp' => date('c'),
            'checks' => [],
            'score' => 0,
            'grade' => '',
            'schema_types' => [],
            'missing' => [],
            'recommendations' => [],
        ];
        
        // Fetch main page
        $this->html = $this->fetchUrl($this->url);
        if (!$this->html) {
            $this->report['error'] = 'Could not fetch URL';
            $this->report['score'] = 0;
            $this->report['grade'] = 'F';
            return $this->report;
        }
        
        // Parse HTML
        $this->dom = new DOMDocument();
        @$this->dom->loadHTML($this->html, LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD | LIBXML_NOERROR);
        
        // Run all checks
        $this->checkLlmsTxt();
        $this->checkSchemaOrg();
        $this->checkOpenGraph();
        $this->checkMetaDescription();
        $this->checkStructuredData();
        $this->checkRobotsTxt();
        $this->checkSitemap();
        $this->checkSemanticHtml();
        $this->checkHeadingStructure();
        $this->checkContentQuality();
        
        // Calculate total score
        $totalWeight = array_sum($this->weights);
        $earnedWeight = 0;
        foreach ($this->report['checks'] as $check) {
            $earnedWeight += $check['score'] * ($this->weights[$check['name']] ?? 0);
        }
        $this->report['score'] = min(100, round($earnedWeight / $totalWeight * 100));
        
        // Grade
        $score = $this->report['score'];
        $this->report['grade'] = match(true) {
            $score >= 90 => 'A+',
            $score >= 80 => 'A',
            $score >= 70 => 'B',
            $score >= 60 => 'C',
            $score >= 50 => 'D',
            default => 'F',
        };
        
        // Generate recommendations
        $this->generateRecommendations();
        
        return $this->report;
    }
    
    private function fetchUrl(string $url): string {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; GEOAuditBot/1.0)',
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_HTTPHEADER => ['Accept: text/html,application/xhtml+xml'],
        ]);
        $html = curl_exec($ch);
        curl_close($ch);
        return $html ?: '';
    }
    
    private function fetchText(string $url): string {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_TIMEOUT => 10,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; GEOAuditBot/1.0)',
        ]);
        $text = curl_exec($ch);
        curl_close($ch);
        return $text ?: '';
    }
    
    private function checkLlmsTxt(): void {
        $llmsUrl = $this->domain . '/llms.txt';
        $content = $this->fetchText($llmsUrl);
        $found = strlen($content) > 20 && stripos($content, 'llms') !== false;
        
        $this->report['checks']['llms_txt'] = [
            'name' => 'llms_txt',
            'label' => 'llms.txt file',
            'passed' => $found,
            'score' => $found ? 1 : 0,
            'detail' => $found ? 'Found at ' . $llmsUrl : 'Not found at ' . $llmsUrl,
        ];
        
        if (!$found) {
            $this->report['missing'][] = 'llms.txt';
        }
    }
    
    private function checkSchemaOrg(): void {
        $scripts = $this->dom->getElementsByTagName('script');
        $found = false;
        $types = [];
        
        for ($i = 0; $i < $scripts->length; $i++) {
            $script = $scripts->item($i);
            if ($script->getAttribute('type') === 'application/ld+json') {
                $json = json_decode($script->textContent, true);
                if ($json) {
                    $found = true;
                    if (isset($json['@type'])) {
                        $types[] = $json['@type'];
                    }
                    if (isset($json['@graph'])) {
                        foreach ($json['@graph'] as $item) {
                            if (isset($item['@type'])) {
                                $types[] = $item['@type'];
                            }
                        }
                    }
                }
            }
        }
        
        $this->report['checks']['schema_org'] = [
            'name' => 'schema_org',
            'label' => 'Schema.org structured data',
            'passed' => $found,
            'score' => $found ? 1 : 0,
            'detail' => $found ? 'Found types: ' . implode(', ', $types) : 'No Schema.org markup found',
        ];
        
        $this->report['schema_types'] = $types;
        
        if (!$found) {
            $this->report['missing'][] = 'Schema.org markup';
        }
    }
    
    private function checkOpenGraph(): void {
        $metas = $this->dom->getElementsByTagName('meta');
        $ogTags = [];
        
        for ($i = 0; $i < $metas->length; $i++) {
            $prop = $metas->item($i)->getAttribute('property') ?? $metas->item($i)->getAttribute('name');
            if (str_starts_with($prop, 'og:')) {
                $ogTags[] = $prop;
            }
        }
        
        $required = ['og:title', 'og:description', 'og:image', 'og:url'];
        $found = count($ogTags) >= 3;
        
        $this->report['checks']['open_graph'] = [
            'name' => 'open_graph',
            'label' => 'Open Graph meta tags',
            'passed' => $found,
            'score' => $found ? 1 : (count($ogTags) > 0 ? 0.5 : 0),
            'detail' => $found 
                ? 'Found: ' . implode(', ', $ogTags) 
                : 'Missing OG tags (found ' . count($ogTags) . '/4 required)',
        ];
        
        if (!$found) {
            $this->report['missing'][] = 'Open Graph meta tags';
        }
    }
    
    private function checkMetaDescription(): void {
        $metas = $this->dom->getElementsByTagName('meta');
        $found = false;
        
        for ($i = 0; $i < $metas->length; $i++) {
            if ($metas->item($i)->getAttribute('name') === 'description') {
                $content = $metas->item($i)->getAttribute('content');
                if (strlen($content) > 20) {
                    $found = true;
                    break;
                }
            }
        }
        
        $this->report['checks']['meta_description'] = [
            'name' => 'meta_description',
            'label' => 'Meta description',
            'passed' => $found,
            'score' => $found ? 1 : 0,
            'detail' => $found ? 'Meta description found' : 'No meta description',
        ];
        
        if (!$found) {
            $this->report['missing'][] = 'Meta description';
        }
    }
    
    private function checkStructuredData(): void {
        // Check for microdata, RDFa, or JSON-LD beyond basic Schema.org
        $html = $this->html;
        $hasMicrodata = strpos($html, 'itemscope') !== false;
        $hasRdfa = strpos($html, 'vocab=') !== false || strpos($html, 'typeof=') !== false;
        
        // Count JSON-LD scripts
        $jsonLdCount = preg_match_all('/type=["\']application\/ld\+json["\']/', $html);
        
        $found = $hasMicrodata || $hasRdfa || $jsonLdCount > 1;
        
        $this->report['checks']['structured_data'] = [
            'name' => 'structured_data',
            'label' => 'Rich structured data',
            'passed' => $found,
            'score' => $found ? 1 : ($jsonLdCount > 0 ? 0.5 : 0),
            'detail' => 'JSON-LD: ' . $jsonLdCount . ' blocks, Microdata: ' . ($hasMicrodata ? 'yes' : 'no') . ', RDFa: ' . ($hasRdfa ? 'yes' : 'no'),
        ];
    }
    
    private function checkRobotsTxt(): void {
        $content = $this->fetchText($this->domain . '/robots.txt');
        $found = strlen($content) > 10;
        
        $this->report['checks']['robots_txt'] = [
            'name' => 'robots_txt',
            'label' => 'robots.txt',
            'passed' => $found,
            'score' => $found ? 1 : 0,
            'detail' => $found ? 'robots.txt found' : 'No robots.txt',
        ];
        
        if (!$found) {
            $this->report['missing'][] = 'robots.txt';
        }
    }
    
    private function checkSitemap(): void {
        $content = $this->fetchText($this->domain . '/sitemap.xml');
        $found = strpos($content, '<urlset') !== false || strpos($content, '<sitemapindex') !== false;
        
        $this->report['checks']['sitemap'] = [
            'name' => 'sitemap',
            'label' => 'XML Sitemap',
            'passed' => $found,
            'score' => $found ? 1 : 0,
            'detail' => $found ? 'Sitemap found' : 'No XML sitemap',
        ];
        
        if (!$found) {
            $this->report['missing'][] = 'XML Sitemap';
        }
    }
    
    private function checkSemanticHtml(): void {
        $semanticTags = ['article', 'section', 'nav', 'aside', 'header', 'footer', 'main'];
        $found = 0;
        
        foreach ($semanticTags as $tag) {
            if ($this->dom->getElementsByTagName($tag)->length > 0) {
                $found++;
            }
        }
        
        $score = min(1, $found / 4);
        
        $this->report['checks']['semantic_html'] = [
            'name' => 'semantic_html',
            'label' => 'Semantic HTML elements',
            'passed' => $found >= 4,
            'score' => $score,
            'detail' => "Found $found/7 semantic tags: " . implode(', ', array_slice($semanticTags, 0, $found)),
        ];
        
        if ($found < 4) {
            $this->report['missing'][] = 'Semantic HTML structure';
        }
    }
    
    private function checkHeadingStructure(): void {
        $headings = [];
        for ($i = 1; $i <= 6; $i++) {
            $count = $this->dom->getElementsByTagName("h$i")->length;
            if ($count > 0) {
                $headings["h$i"] = $count;
            }
        }
        
        $hasH1 = isset($headings['h1']) && $headings['h1'] >= 1;
        $hasStructure = count($headings) >= 2;
        $score = ($hasH1 ? 0.5 : 0) + ($hasStructure ? 0.5 : 0);
        
        $this->report['checks']['heading_structure'] = [
            'name' => 'heading_structure',
            'label' => 'Heading hierarchy',
            'passed' => $hasH1 && $hasStructure,
            'score' => $score,
            'detail' => 'Headings: ' . implode(', ', array_map(fn($k, $v) => "$k×$v", array_keys($headings), $headings)),
        ];
    }
    
    private function checkContentQuality(): void {
        // Extract text content
        $xpath = new DOMXPath($this->dom);
        $body = $xpath->query('//body');
        $text = '';
        if ($body->length > 0) {
            $text = $body->item(0)->textContent;
        }
        
        $wordCount = str_word_count($text);
        $score = min(1, $wordCount / 500);
        
        $this->report['checks']['content_quality'] = [
            'name' => 'content_quality',
            'label' => 'Content richness',
            'passed' => $wordCount >= 300,
            'score' => $score,
            'detail' => "$wordCount words on page",
        ];
    }
    
    private function generateRecommendations(): void {
        $recs = [];
        
        if (!$this->report['checks']['llms_txt']['passed']) {
            $recs[] = [
                'priority' => 'high',
                'category' => 'llms.txt',
                'title' => 'Create llms.txt file',
                'description' => 'Add an llms.txt file at your domain root. This tells AI models what your site is about and how to reference it.',
                'impact' => '+15 GEO score points',
            ];
        }
        
        if (!$this->report['checks']['schema_org']['passed']) {
            $recs[] = [
                'priority' => 'high',
                'category' => 'Schema.org',
                'title' => 'Add Schema.org structured data',
                'description' => 'Add JSON-LD structured data with Organization, WebSite, and relevant type (LocalBusiness, Product, etc.).',
                'impact' => '+20 GEO score points',
            ];
        }
        
        if (!$this->report['checks']['open_graph']['passed']) {
            $recs[] = [
                'priority' => 'medium',
                'category' => 'Meta',
                'title' => 'Add Open Graph tags',
                'description' => 'Add og:title, og:description, og:image, and og:url meta tags.',
                'impact' => '+10 GEO score points',
            ];
        }
        
        if (!$this->report['checks']['meta_description']['passed']) {
            $recs[] = [
                'priority' => 'medium',
                'category' => 'Meta',
                'title' => 'Add meta description',
                'description' => 'Add a descriptive meta description tag (150-160 characters).',
                'impact' => '+5 GEO score points',
            ];
        }
        
        if (!$this->report['checks']['robots_txt']['passed']) {
            $recs[] = [
                'priority' => 'low',
                'category' => 'Crawling',
                'title' => 'Create robots.txt',
                'description' => 'Add a robots.txt file to guide AI crawlers.',
                'impact' => '+5 GEO score points',
            ];
        }
        
        if (!$this->report['checks']['sitemap']['passed']) {
            $recs[] = [
                'priority' => 'low',
                'category' => 'Crawling',
                'title' => 'Create XML sitemap',
                'description' => 'Add an XML sitemap to help AI models discover all pages.',
                'impact' => '+5 GEO score points',
            ];
        }
        
        $this->report['recommendations'] = $recs;
    }
    
    /**
     * Generate llms.txt content from analyzed site
     */
    public function generateLlmsTxt(): string {
        $xpath = new DOMXPath($this->dom);
        
        // Get title
        $titleTags = $this->dom->getElementsByTagName('title');
        $title = $titleTags->length > 0 ? $titleTags->item(0)->textContent : '';
        
        // Get meta description
        $description = '';
        $metas = $this->dom->getElementsByTagName('meta');
        for ($i = 0; $i < $metas->length; $i++) {
            if ($metas->item($i)->getAttribute('name') === 'description') {
                $description = $metas->item($i)->getAttribute('content');
                break;
            }
        }
        
        // Get headings for structure
        $h1Tags = $this->dom->getElementsByTagName('h1');
        $h1 = $h1Tags->length > 0 ? $h1Tags->item(0)->textContent : '';
        
        // Get links for page map
        $links = $this->dom->getElementsByTagName('a');
        $pages = [];
        for ($i = 0; $i < $links->length && $i < 20; $i++) {
            $href = $links->item($i)->getAttribute('href');
            $text = trim($links->item($i)->textContent);
            if ($href && $text && !str_starts_with($href, '#') && !str_starts_with($href, 'javascript')) {
                if (!str_starts_with($href, 'http')) {
                    $href = $this->domain . '/' . ltrim($href, '/');
                }
                $pages[] = ['- ' . $text . ': ' . $href];
            }
        }
        
        $llms = "# " . ($title ?: $this->domain) . "\n\n";
        $llms .= "> " . ($description ?: "Website at {$this->domain}") . "\n\n";
        $llms .= "## About\n\n";
        $llms .= ($h1 ?: $title ?: $this->domain) . "\n\n";
        
        if (!empty($pages)) {
            $llms .= "## Pages\n\n";
            foreach (array_unique($pages) as $page) {
                $llms .= $page[0] . "\n";
            }
            $llms .= "\n";
        }
        
        $llms .= "## Contact\n\n";
        $llms .= "- Email: info@" . parse_url($this->domain, PHP_URL_HOST) . "\n";
        $llms .= "- URL: " . $this->domain . "\n";
        
        return $llms;
    }
    
    /**
     * Generate Schema.org JSON-LD for a business
     */
    public function generateSchemaOrg(string $businessName, string $description, string $type = 'LocalBusiness'): string {
        $schema = [
            '@context' => 'https://schema.org',
            '@type' => $type,
            'name' => $businessName,
            'url' => $this->domain,
            'description' => $description,
            'potentialAction' => [
                '@type' => 'SearchAction',
                'target' => $this->domain . '/?q={search_term_string}',
                'query-input' => 'required name=search_term_string',
            ],
        ];
        
        // Add WebSite wrapper
        $output = [
            '@context' => 'https://schema.org',
            '@graph' => [
                $schema,
                [
                    '@type' => 'WebSite',
                    'name' => $businessName,
                    'url' => $this->domain,
                ],
            ],
        ];
        
        return json_encode($output, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    }
}
