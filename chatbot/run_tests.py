import requests
import json
import os
import sys

# Load system prompt accurately from chat.js
with open('chatbot/api/chat.js', encoding='utf-8') as f:
    raw = f.read()

start = raw.find('You are the Music Streaming')
end = raw.find('// Model configurations')
SYSTEM_PROMPT = raw[start:end].strip().rstrip('`;').strip()

print(f"[SYSTEM PROMPT LOADED] Length: {len(SYSTEM_PROMPT)} characters\n")

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")

TEST_QUESTIONS = [
    "What data quality issues were found and how were they cleaned?",
    "Does energy correlate with popularity in this dataset? What were the stats?",
    "Are Superstar artists concentrated in any particular region according to the Chi-square test?",
    "What is the capital of France?"  # Out-of-context test (should be declined)
]

def test_openrouter(question):
    print(f"\n--- [OpenRouter / Qwen 3.6 Plus] Testing: '{question}' ---")
    try:
        resp = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://music-streaming-analysis.vercel.app',
                'X-Title': 'Music Streaming Data Explorer'
            },
            json={
                'model': 'qwen/qwen3.6-plus',
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': question}
                ],
                'max_tokens': 2048,
                'temperature': 0.3
            },
            timeout=45
        )
        if resp.status_code == 200:
            data = resp.json()
            msg = data['choices'][0]['message']
            content = msg.get('content') or ''
            if not content and msg.get('reasoning'):
                content = msg.get('reasoning').split('\n')[-1]
            print(f"[STATUS 200] Output length: {len(content)}")
            print("[RESPONSE SAMPLE]:\n", content[:500], "...\n")
            return True, content
        else:
            print(f"[ERROR {resp.status_code}] {resp.text}")
            return False, resp.text
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return False, str(e)

if __name__ == '__main__':
    # Test Question 1 (Data Quality)
    test_openrouter(TEST_QUESTIONS[0])
    # Test Question 2 (Energy vs Popularity)
    test_openrouter(TEST_QUESTIONS[1])
    # Test Question 3 (Superstar Regional Concentration)
    test_openrouter(TEST_QUESTIONS[2])
    # Test Question 4 (Out of Context Refusal)
    test_openrouter(TEST_QUESTIONS[3])
