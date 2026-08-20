// ListTranslate — AI翻译引擎
// POST /translate-listing

const DEEPSEEK_API_KEY = process.env.DEEPSEEK_API_KEY;

const PLATFORM_PROMPTS = {
  'amazon-us': {
    name: '亚马逊美国站',
    lang: 'English',
    langCode: 'en',
    prompt: `You are an expert Amazon US listing optimizer. Convert the Chinese product information into a high-converting Amazon US listing.

Output format:
TITLE: [Product title, max 200 chars, include core keywords naturally]
BULLETS: [5 bullet points, each max 150 chars, start with CAPS benefit keyword]
DESCRIPTION: [Product description, 150-200 words, persuasive and keyword-rich]
KEYWORDS: [5 backend search terms, lowercase, no commas]`
  },
  'amazon-uk': {
    name: '亚马逊英国站',
    lang: 'British English',
    langCode: 'en',
    prompt: `You are an expert Amazon UK listing optimizer. Convert Chinese product info into a high-converting Amazon UK listing using British English spelling and conventions.

Output format:
TITLE: [Product title, max 200 chars, use British spelling]
BULLETS: [5 bullet points, each max 150 chars]
DESCRIPTION: [Product description, 150-200 words]
KEYWORDS: [5 backend search terms, lowercase]`
  },
  'amazon-jp': {
    name: '亚马逊日本站',
    lang: 'Japanese',
    langCode: 'ja',
    prompt: `あなたはAmazon日本站のリスティング最適化の専門家です。中国語の製品情報を高コンバージョンのAmazon日本語リスティングに変換してください。

出力形式：
TITLE: [商品タイトル、150文字以内]
BULLETS: [5つのポイント説明、各100文字以内]
DESCRIPTION: [商品説明、200文字以内]
KEYWORDS: [5つのバックエンドキーワード]`
  },
  'shopee-th': {
    name: 'Shopee 泰国站',
    lang: 'Thai',
    langCode: 'th',
    prompt: `คุณเป็นผู้เชี่ยวชาญด้านการเขียนคำโฆษณาสำหรับ Shopee แปลงข้อมูลสินค้าภาษาจีนเป็นรายการสินค้าภาษาไทยที่น่าสนใจ

รูปแบบผลลัพธ์:
TITLE: [ชื่อสินค้า, ไม่เกิน 120 ตัวอักษร]
BULLETS: [5 จุดเด่น, แต่ละจุดไม่เกิน 80 ตัวอักษร]
DESCRIPTION: [คำอธิบายสินค้า, 150-200 คำ]
KEYWORDS: [5 คำค้นหาหลัก]`
  },
  'shopee-my': {
    name: 'Shopee 马来站',
    lang: 'Malay',
    langCode: 'ms',
    prompt: `Anda adalah pakar pengoptimuman penyenaraian Shopee. Tukar maklumat produk Cina kepada penyenaraian Shopee Melayu yang tinggi penukaran.

Format output:
TITLE: [Nama produk, maks 120 aksara]
BULLETS: [5 titik jualan, setiap satu maks 80 aksara]
DESCRIPTION: [Penerangan produk, 150-200 patah perkataan]
KEYWORDS: [5 istilah carian utama]`
  },
  'tiktok-us': {
    name: 'TikTok Shop 美国站',
    lang: 'English',
    langCode: 'en',
    prompt: `You are a TikTok Shop listing expert. Convert Chinese product info into a short, punchy, trend-aware TikTok Shop listing that drives impulse purchases.

Output format:
TITLE: [Catchy product name, max 80 chars, emoji-friendly]
BULLETS: [5 short punchy selling points, max 60 chars each, use emojis]
DESCRIPTION: [Short engaging description, 80-100 words, casual tone]
KEYWORDS: [5 trending search terms]`
  },
  'etsy': {
    name: 'Etsy',
    lang: 'English',
    langCode: 'en',
    prompt: `You are an Etsy listing optimization expert. Convert Chinese product info into a warm, handcrafted-feeling Etsy listing that appeals to artisan buyers.

Output format:
TITLE: [Descriptive title with keywords, max 140 chars]
BULLETS: [5 detailed feature bullets]
DESCRIPTION: [Storytelling product description, 150-200 words, warm and personal tone]
KEYWORDS: [5 Etsy search tags]`
  }
};

exports.handler = async (event) => {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  try {
    const { input, platform, language } = JSON.parse(event.body);

    if (!input || !platform) {
      return { statusCode: 400, body: JSON.stringify({ error: 'Missing input or platform' }) };
    }

    const platformConfig = PLATFORM_PROMPTS[platform] || PLATFORM_PROMPTS['amazon-us'];

    const systemPrompt = `${platformConfig.prompt}

Important rules:
1. All output must be in ${platformConfig.lang}
2. Use natural, native-sounding language, not machine translation
3. Include relevant keywords that buyers would actually search for
4. Make the listing conversion-focused — highlight benefits, not just features
5. Format cleanly with the labels TITLE:, BULLETS:, DESCRIPTION:, KEYWORDS:`;

    const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${DEEPSEEK_API_KEY}`,
        'User-Agent': 'ListTranslate/1.0'
      },
      body: JSON.stringify({
        model: 'deepseek-v4-flash',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: `请将以下中文产品信息转换为${platformConfig.name}的${platformConfig.lang}listing：\n\n${input}` }
        ],
        max_tokens: 2000,
        temperature: 0.7
      })
    });

    const data = await response.json();

    if (data.error) {
      return { statusCode: 502, body: JSON.stringify({ error: data.error.message || 'AI service error' }) };
    }

    const content = data.choices[0].message.content || data.choices[0].message.reasoning_content || '';

    // Parse the response
    const result = {};
    const sections = content.split(/(?=TITLE:|BULLETS:|DESCRIPTION:|KEYWORDS:)/i);
    
    for (const section of sections) {
      const trimmed = section.trim();
      if (trimmed.startsWith('TITLE:')) {
        result.title = trimmed.replace(/^TITLE:\s*/i, '').trim();
      } else if (trimmed.startsWith('BULLETS:')) {
        result.bullets = trimmed.replace(/^BULLETS:\s*/i, '').trim();
      } else if (trimmed.startsWith('DESCRIPTION:')) {
        result.description = trimmed.replace(/^DESCRIPTION:\s*/i, '').trim();
      } else if (trimmed.startsWith('KEYWORDS:')) {
        result.keywords = trimmed.replace(/^KEYWORDS:\s*/i, '').trim();
      }
    }

    // If parsing failed, return the full content
    if (!result.title && !result.bullets) {
      result.title = content;
    }

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(result)
    };

  } catch (err) {
    return { statusCode: 500, body: JSON.stringify({ error: err.message }) };
  }
};
