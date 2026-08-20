// Test DeepSeek API call using the same logic as deepseek.js
async function test() {
  const apiKey = "***REMOVED***";
  const baseUrl = "https://api.deepseek.com/v1";
  const url = baseUrl + '/chat/completions';
  const prompt = "Test prompt";

  const payload = {
    model: "deepseek-v4-flash",
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 10
  };

  console.log('Calling DeepSeek API...');
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(payload)
    });
    console.log('Status:', res.status);
    if (!res.ok) {
      const text = await res.text();
      console.error('Error response:', text);
      process.exit(1);
    }
    const data = await res.json();
    console.log('Success:', JSON.stringify(data, null, 2));
  } catch (e) {
    console.error('Fetch error:', e.message);
    process.exit(1);
  }
}

test();