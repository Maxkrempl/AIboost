// BoostSuite - Frontend Application
document.addEventListener('DOMContentLoaded', function() {
    // ============ STATE ============
    const STORAGE_KEY = 'boostsuite_usage';
    let usageCount = parseInt(localStorage.getItem(STORAGE_KEY)) || 0;

    // ============ DOM ELEMENTS ============
    const tabs = document.querySelectorAll('.tab');
    const toolCards = document.querySelectorAll('.tool-card');
    const upgradeBtn = document.getElementById('upgradeBtn');
    const upgradeModal = document.getElementById('upgradeModal');
    const closeModal = document.getElementById('closeModal');
    const usageCountEl = document.getElementById('usageCount');
    const langSelect = document.getElementById('langSelect');

    // Tool inputs
    const seoUrlInput = document.getElementById('seo-url');
    const seoResult = document.getElementById('seo-result');
    const geoBusinessInput = document.getElementById('geo-business');
    const geoLocationInput = document.getElementById('geo-location');
    const geoNicheInput = document.getElementById('geo-niche');
    const geoResult = document.getElementById('geo-result');
    const adProductInput = document.getElementById('ad-product');
    const adAudienceInput = document.getElementById('ad-audience');
    const adToneSelect = document.getElementById('ad-tone');
    const adCtaInput = document.getElementById('ad-cta');
    const adPlatformSelect = document.getElementById('ad-platform');
    const adResult = document.getElementById('ad-result');
    const listingProductInput = document.getElementById('listing-product');
    const listingCategoryInput = document.getElementById('listing-category');
    const listingFeaturesTextarea = document.getElementById('listing-features');
    const listingTargetInput = document.getElementById('listing-target');
    const listingPlatformSelect = document.getElementById('listing-platform');
    const listingResult = document.getElementById('listing-result');

    // ============ i18n ============
    function applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const val = t(key);
            if (val) el.textContent = val;
        });
        // Update placeholders
        seoUrlInput.placeholder = 'https://example.com';
    }

    langSelect.value = getLang();
    langSelect.addEventListener('change', () => {
        localStorage.setItem('boostsuite_lang', langSelect.value);
        applyTranslations();
    });
    applyTranslations();

    // ============ INIT ============
    updateUsageDisplay();

    // ============ TAB SWITCHING ============
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const toolId = tab.getAttribute('data-tool');
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            toolCards.forEach(card => {
                card.classList.remove('active');
                if (card.id === toolId) card.classList.add('active');
            });
        });
    });

    // ============ USAGE MANAGEMENT ============
    function incrementUsage() {
        usageCount++;
        localStorage.setItem(STORAGE_KEY, usageCount.toString());
        updateUsageDisplay();
        if (usageCount >= 3) showUpgradeModal();
    }

    function updateUsageDisplay() {
        usageCountEl.textContent = usageCount;
    }

    function showUpgradeModal() { upgradeModal.style.display = 'flex'; }
    function hideUpgradeModal() { upgradeModal.style.display = 'none'; }

    upgradeBtn.addEventListener('click', showUpgradeModal);
    closeModal.addEventListener('click', hideUpgradeModal);
    upgradeModal.addEventListener('click', (e) => { if (e.target === upgradeModal) hideUpgradeModal(); });

    // ============ HELPERS ============
    function showLoader(container) {
        container.innerHTML = `<div class="placeholder"><div class="loader"></div><p>${t('processing')}</p></div>`;
    }

    function showError(container, message) {
        container.innerHTML = `<div class="result-content"><div style="color:var(--accent-red)"><i class="fas fa-exclamation-triangle"></i> <strong>${t('error')}:</strong> ${message}</div></div>`;
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => showToast(t('copied'))).catch(() => {});
    }

    function showToast(msg) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => { toast.classList.remove('show'); setTimeout(() => toast.remove(), 300); }, 2000);
    }

    function checkLimit() {
        if (usageCount >= 3) { showUpgradeModal(); return false; }
        return true;
    }

    // Parse AI response — handles both JSON and free-text
    function parseAIResponse(text, schema) {
        // Try direct JSON parse
        try {
            const obj = JSON.parse(text);
            // Validate it has at least one expected field
            if (schema.some(k => k in obj)) return obj;
        } catch (e) {}

        // Try extracting JSON from markdown code block
        const codeBlock = text.match(/```(?:json)?\s*([\s\S]*?)```/);
        if (codeBlock) {
            try {
                const obj = JSON.parse(codeBlock[1].trim());
                if (schema.some(k => k in obj)) return obj;
            } catch (e) {}
        }

        // Try finding JSON object in text
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            try {
                const obj = JSON.parse(jsonMatch[0]);
                if (schema.some(k => k in obj)) return obj;
            } catch (e) {}
        }

        // Fallback: extract fields from text
        const result = {};
        const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

        // Extract score
        const scoreMatch = text.match(/(?:score|rating|ocena|bewertung|punteggio)[:\s]*(\d{1,3})/i)
            || text.match(/\b(\d{1,3})\s*\/\s*100\b/)
            || text.match(/\b(\d{1,3})\s*(?:out of|von|di)\s*100\b/i);
        if (scoreMatch) result.score = parseInt(scoreMatch[1]);

        // Extract analysis
        const analysisMatch = text.match(/(?:analysis|analiza|analyse|analisi)[:\s]*([^\n]+)/i);
        if (analysisMatch) {
            result.analysis = analysisMatch[1].trim();
        } else {
            // Use first substantial paragraph as analysis
            const para = lines.find(l => l.length > 40 && !l.match(/^\d+[\.\)]/));
            if (para) result.analysis = para;
        }

        // Extract fixes/suggestions
        const fixes = [];
        for (const line of lines) {
            const fixMatch = line.match(/^\d+[\.\)]\s*(.+)/) || line.match(/^[-•]\s*(.+)/);
            if (fixMatch && fixMatch[1].length > 10) fixes.push(fixMatch[1].trim());
        }
        if (fixes.length) result.fixes = fixes.slice(0, 5);

        // For GEO: extract platforms and suggestions
        if (!result.platforms) result.platforms = [];
        if (!result.suggestions) result.suggestions = fixes.length ? fixes : [];

        // For ad copy: extract variations
        if (!result.variations) {
            const parts = text.split(/\n---\n|\n\n(?=\d[\.\)])/).filter(p => p.trim().length > 20);
            if (parts.length > 1) result.variations = parts;
            else result.variations = [text];
        }

        // For listing: extract title, description, tags
        const titleMatch = text.match(/(?:title|naslov|titel|titolo)[:\s]*([^\n]+)/i);
        if (titleMatch) result.title = titleMatch[1].trim();
        const descMatch = text.match(/(?:description|opis|beschreibung|descrizione)[:\s]*([\s\S]*?)(?=\n(?:tags|oznake|tag|labels)|$)/i);
        if (descMatch) result.description = descMatch[1].trim().substring(0, 500);
        const tagsMatch = text.match(/(?:tags|oznake|tag|labels)[:\s]*([^\n]+)/i);
        if (tagsMatch) {
            result.tags = tagsMatch[1].split(/[,|]/).map(t => t.trim().replace(/["\[\]]/g, '')).filter(Boolean);
        }

        return result;
    }

    // ============ SEO AUDIT ============
    document.getElementById('seo-submit').addEventListener('click', async () => {
        const url = seoUrlInput.value.trim();
        if (!url) return alert(t('required'));
        if (!checkLimit()) return;
        showLoader(seoResult);
        try {
            const resp = await fetch('/.netlify/functions/seo-audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || 'Audit failed');
            renderSeoResult(data);
            incrementUsage();
        } catch (err) { showError(seoResult, err.message); }
    });

    function renderSeoResult(data) {
        const score = data.score ?? 0;
        const analysis = data.analysis || 'No analysis available.';
        const fixes = data.fixes || [];
        const rawData = data.rawData || {};
        const scoreClass = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';

        let html = `<div class="result-content">
            <div class="result-header"><h3>${t('seoScore')}</h3><div class="result-score ${scoreClass}">${score}/100</div></div>
            <div class="score-gauge"><div class="score-fill" style="width:${score}%"></div></div>
            <p><strong>${t('seoAnalysis')}:</strong> ${analysis}</p>`;

        // Show raw data if available
        if (rawData.title) {
            html += `<div class="result-details">
                <h4>Page Details</h4>
                <table class="detail-table">
                    <tr><td>Title</td><td>${rawData.title || 'Missing'}</td></tr>
                    <tr><td>Meta Description</td><td>${rawData.metaDescription || 'Missing'}</td></tr>
                    <tr><td>H1 Tags</td><td>${rawData.h1Count ?? '?'}</td></tr>
                    <tr><td>Images</td><td>${rawData.imageCount ?? '?'} (${rawData.imagesWithAlt ?? '?'} with alt)</td></tr>
                    <tr><td>Internal Links</td><td>${rawData.internalLinks ?? '?'}</td></tr>
                    <tr><td>External Links</td><td>${rawData.externalLinks ?? '?'}</td></tr>
                    <tr><td>Word Count</td><td>${rawData.wordCount ?? '?'}</td></tr>
                    <tr><td>Canonical</td><td>${rawData.canonical || 'Missing'}</td></tr>
                    <tr><td>OG Title</td><td>${rawData.ogTitle || 'Missing'}</td></tr>
                </table>
            </div>`;
        }

        if (fixes.length) {
            html += `<h4>${t('seoFixes')}</h4><ul class="result-list">${fixes.map(f => `<li>${f}</li>`).join('')}</ul>`;
        }

        html += `<button class="copy-btn" onclick="copyToClipboard('SEO Score: ${score}\\nAnalysis: ${analysis}\\nFixes:\\n${fixes.join('\\n')}')"><i class="fas fa-copy"></i> ${t('copyReport')}</button></div>`;
        seoResult.innerHTML = html;
    }

    // Make copyToClipboard available globally for inline onclick
    window.copyToClipboard = copyToClipboard;

    // ============ GEO CHECK ============
    document.getElementById('geo-submit').addEventListener('click', async () => {
        const business = geoBusinessInput.value.trim();
        const location = geoLocationInput.value.trim();
        const niche = geoNicheInput.value.trim();
        if (!business || !location || !niche) return alert(t('required'));
        if (!checkLimit()) return;
        showLoader(geoResult);
        try {
            const resp = await fetch('/.netlify/functions/geo-check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ business, location, niche })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || 'Check failed');
            renderGeoResult(data);
            incrementUsage();
        } catch (err) { showError(geoResult, err.message); }
    });

    function renderGeoResult(data) {
        const d = parseAIResponse(typeof data === 'string' ? data : JSON.stringify(data), ['score', 'analysis', 'platforms', 'suggestions']);
        const score = d.score ?? data.score ?? 0;
        const analysis = d.analysis ?? data.analysis ?? '';
        const platforms = d.platforms ?? data.platforms ?? [];
        const suggestions = d.suggestions ?? data.suggestions ?? [];
        const scoreClass = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';

        let html = `<div class="result-content">
            <div class="result-header"><h3>${t('geoScore')}</h3><div class="result-score ${scoreClass}">${score}/100</div></div>
            <div class="score-gauge"><div class="score-fill" style="width:${score}%"></div></div>
            <p><strong>${t('geoAnalysis')}:</strong> ${analysis}</p>`;

        if (platforms.length) {
            html += `<h4>${t('geoPlatforms')}</h4><ul class="result-list">${platforms.map(p => `<li>${p}</li>`).join('')}</ul>`;
        }
        if (suggestions.length) {
            html += `<h4>${t('geoSuggestions')}</h4><ul class="result-list">${suggestions.map(s => `<li>${s}</li>`).join('')}</ul>`;
        }
        html += `<button class="copy-btn" onclick="copyToClipboard('AI Visibility: ${score}\\n${analysis}\\nPlatforms: ${platforms.join(', ')}\\nSuggestions: ${suggestions.join('\\n')}')"><i class="fas fa-copy"></i> ${t('copyReport')}</button></div>`;
        geoResult.innerHTML = html;
    }

    // ============ AD COPY ============
    document.getElementById('ad-submit').addEventListener('click', async () => {
        const product = adProductInput.value.trim();
        const audience = adAudienceInput.value.trim();
        const cta = adCtaInput.value.trim();
        if (!product || !audience || !cta) return alert(t('required'));
        if (!checkLimit()) return;
        showLoader(adResult);
        try {
            const resp = await fetch('/.netlify/functions/ad-copy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product, audience, tone: adToneSelect.value, cta, platform: adPlatformSelect.value })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || 'Generation failed');
            renderAdResult(data);
            incrementUsage();
        } catch (err) { showError(adResult, err.message); }
    });

    function renderAdResult(data) {
        const d = parseAIResponse(typeof data === 'string' ? data : JSON.stringify(data), ['variations']);
        const variations = d.variations ?? data.variations ?? [JSON.stringify(data)];
        const platformName = adPlatformSelect.options[adPlatformSelect.selectedIndex].text;

        let html = `<div class="result-content"><h3>${platformName}</h3>`;
        variations.forEach((v, i) => {
            const text = typeof v === 'string' ? v : JSON.stringify(v);
            html += `<div class="variation-card">
                <h4>${t('adVariation')} ${i + 1}</h4>
                <pre>${text}</pre>
                <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)"><i class="fas fa-copy"></i> Copy</button>
            </div>`;
        });
        html += `<button class="copy-btn" onclick="copyToClipboard(Array.from(this.parentElement.querySelectorAll('pre')).map(p=>p.textContent).join('\\n---\\n'))"><i class="fas fa-copy"></i> ${t('adCopyAll')}</button></div>`;
        adResult.innerHTML = html;
    }

    // ============ LISTING OPTIMIZER ============
    document.getElementById('listing-submit').addEventListener('click', async () => {
        const product = listingProductInput.value.trim();
        const category = listingCategoryInput.value.trim();
        const features = listingFeaturesTextarea.value.trim();
        if (!product || !category || !features) return alert(t('required'));
        if (!checkLimit()) return;
        showLoader(listingResult);
        try {
            const resp = await fetch('/.netlify/functions/listing-optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product, category, features, target: listingTargetInput.value.trim(), platform: listingPlatformSelect.value })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || 'Optimization failed');
            renderListingResult(data);
            incrementUsage();
        } catch (err) { showError(listingResult, err.message); }
    });

    function renderListingResult(data) {
        const d = parseAIResponse(typeof data === 'string' ? data : JSON.stringify(data), ['title', 'description', 'tags']);
        const title = d.title ?? data.title ?? '';
        const description = d.description ?? data.description ?? '';
        const tags = d.tags ?? data.tags ?? [];
        const platformName = listingPlatformSelect.options[listingPlatformSelect.selectedIndex].text;

        let html = `<div class="result-content"><h3>${platformName}</h3>`;

        if (title) {
            html += `<div class="result-field"><h4>${t('listingSeoTitle')} (${title.length} chars)</h4>
                <div class="field-box">${title}</div>
                <button class="copy-btn" onclick="copyToClipboard('${title.replace(/'/g, "\\'")}')"><i class="fas fa-copy"></i> Copy</button></div>`;
        }
        if (description) {
            html += `<div class="result-field"><h4>${t('listingDescription')} (${description.length} chars)</h4>
                <div class="field-box">${description}</div>
                <button class="copy-btn" onclick="copyToClipboard(this.previousElementSibling.textContent)"><i class="fas fa-copy"></i> Copy</button></div>`;
        }
        if (tags.length) {
            html += `<div class="result-field"><h4>${t('listingTags')} (${tags.length})</h4>
                <div class="tags-wrap">${tags.map(t => `<span class="tag">${t}</span>`).join('')}</div>
                <button class="copy-btn" onclick="copyToClipboard('${tags.join(', ')}')"><i class="fas fa-copy"></i> Copy</button></div>`;
        }

        // If no structured data was parsed, show raw text
        if (!title && !description && !tags.length) {
            html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }

        html += `</div>`;
        listingResult.innerHTML = html;
    }
});
