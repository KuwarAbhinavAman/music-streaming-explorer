import requests, json

# Full integration test - simulate what the serverless function does
raw = open('chatbot/api/chat.js', encoding='utf-8').read()
start = raw.find('`You are the Music Streaming')
end = raw.find('- All statistical tests are two-tailed`;')
SYSTEM_PROMPT = raw[start+1:end+len('- All statistical tests are two-tailed')]

print(f'System prompt length: {len(SYSTEM_PROMPT)} chars')
print()

import os
# Test with OpenRouter/Qwen
openrouter_key = os.environ.get('OPENROUTER_API_KEY', '')
resp = requests.post(
    'https://openrouter.ai/api/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {openrouter_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://music-streaming-analysis.vercel.app',
        'X-Title': 'Music Streaming Data Explorer'
    },
    json={
        'model': 'qwen/qwen3.6-plus',
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': 'What data quality issues did you find?'}
        ],
        'max_tokens': 4096,
        'temperature': 0.4
    },
    timeout=60
)

print(f'Status: {resp.status_code}')
data = resp.json()
msg = data['choices'][0]['message']
content = msg.get('content') or ''
reasoning = msg.get('reasoning') or ''
print(f'Content length: {len(content)}')
print(f'Reasoning length: {len(reasoning)}')
print()
print('=== RESPONSE ===')
print(content[:800] if content else f'(no content, reasoning tail: {reasoning[-200:]})')
print()
usage = data.get('usage', {})
print(f"Tokens: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}, total={usage.get('total_tokens')}")
