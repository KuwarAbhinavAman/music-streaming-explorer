import requests
import json

tools = [
    {
        "type": "function",
        "function": {
            "name": "run_pandas_query",
            "description": "Execute a Python/Pandas expression on the dataset df (10,058 rows).",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python expression or statement using df, e.g. df.groupby('market_region')['popularity'].mean().round(2).to_dict()"}
                },
                "required": ["code"]
            }
        }
    }
]

import os
openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

resp = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "qwen/qwen3.6-plus",
        "messages": [
            {"role": "system", "content": "You are a data assistant with access to df. Use run_pandas_query to get exact data."},
            {"role": "user", "content": "What is the average popularity of tracks in Asia Pacific?"}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "max_tokens": 1024
    },
    timeout=30
)

print("Status:", resp.status_code)
data = resp.json()
msg = data["choices"][0]["message"]
tool_calls = msg.get("tool_calls")
print("Tool calls:", json.dumps(tool_calls, indent=2))

if tool_calls:
    import pandas as pd
    df = pd.read_csv("output/cleaned_data.csv")
    
    messages = [
        {"role": "system", "content": "You are a data assistant with access to df. Use run_pandas_query to get exact data."},
        {"role": "user", "content": "What is the average popularity of tracks in Asia Pacific?"},
        msg
    ]
    for tc in tool_calls:
        args = json.loads(tc["function"]["arguments"])
        code = args.get("code", "")
        print(f"\n[EXECUTING PANDAS]: {code}")
        try:
            val = eval(code, {"df": df, "pd": pd})
            print(f"[PANDAS RESULT]: {val}")
            result_str = str(round(val, 2) if isinstance(val, float) else val)
        except Exception as e:
            result_str = f"Error: {e}"
        
        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result_str
        })
    
    # Second completion
    resp2 = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "qwen/qwen3.6-plus",
            "messages": messages,
            "max_tokens": 1024
        },
        timeout=30
    )
    final_reply = resp2.json()["choices"][0]["message"]["content"]
    print("\n[FINAL SYNTHESIZED ANSWER]:\n", final_reply)

