"""
Music Streaming Data Explorer — Advanced Pandas Code Interpreter Backend
Runs locally on http://localhost:5050
Executes real-time Pandas / SciPy code directly against 10,058 rows of cleaned data.
"""
import os
import sys
import time
import json
import traceback
import io
import contextlib
import numpy as np
import pandas as pd
from scipy import stats
import sklearn
from sklearn.linear_model import LinearRegression
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".")

# ── Load Dataset ────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "cleaned_data.csv")
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join(os.path.dirname(__file__), "cleaned_data.csv")
if not os.path.exists(DATA_PATH):
    DATA_PATH = os.path.join("output", "cleaned_data.csv")
if not os.path.exists(DATA_PATH):
    DATA_PATH = "cleaned_data.csv"

df = pd.read_csv(DATA_PATH)
df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
df["energy"] = pd.to_numeric(df["energy"], errors="coerce")
df["danceability"] = pd.to_numeric(df["danceability"], errors="coerce")
df["release_year_clean"] = pd.to_numeric(df["release_year_clean"], errors="coerce")

# Try loading from .env if present
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip().replace("\n", "").replace("\r", "").replace(" ", "")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip().replace("\n", "").replace("\r", "").replace(" ", "")

SYSTEM_PROMPT = f"""You are the Music Streaming Data Explorer — an expert Senior Data Analyst assistant designed and built by Kuwar Abhinav Aman for the Data Analyst Technical Assessment. You have direct access to a Python Pandas execution environment running on the assessment dataset.

If asked who created, built, or developed you, state that you were built by Kuwar Abhinav Aman as an interactive analysis companion for this technical assessment.

═══════════════════════════════════════════
DATASET SCHEMA & IN-MEMORY DATAFRAME
═══════════════════════════════════════════
You have a live Pandas DataFrame `df` with {len(df)} rows and 27 columns:
- Numerical: popularity (0-100), duration_ms, danceability (0-1), energy (0-1), key (0-11), loudness (dB), mode (0/1), speechiness (0-1), acousticness (0-1), instrumentalness (0-1), liveness (0-1), valence (0-1), tempo (BPM), time_signature, release_year_clean (numeric year)
- Categorical:
  • track_genre (114 genres, e.g. 'pop-film', 'k-pop', 'grunge', 'reggaeton', 'rock', 'hip-hop', etc.)
  • market_region (5 regions: 'Asia Pacific', 'Europe', 'Latin America', 'Middle East & Africa', 'North America')
  • artist_tier (4 tiers: 'Emerging', 'Rising', 'Established', 'Superstar')
  • streaming_platform (e.g. 'Spotify', 'Apple Music', 'Amazon Music', 'YouTube Music')
  • playlist_category ('Editorial', 'Algorithmic', 'User-Curated', 'Radio')
  • clean_decade ('1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s')
  • explicit (True/False boolean)
  • artists (artist names string)
  • track_id (unique string)

Also available in namespace: `df`, `pd`, `np`, `stats` (scipy.stats).

═══════════════════════════════════════════
CORE ASSESSMENT FINDINGS & RULES
═══════════════════════════════════════════
1. Hypothesis 1 (Energy vs Popularity):
   - Overall: Pearson r = 0.0109 (p = 0.285), Spearman ρ = -0.0128 (p = 0.207), R² = 0.0001 (N = 9,637).
   - No overall linear or monotonic association. Mean popularity is remarkably flat (~26-35) across energy deciles.
   - Genre level (H1b): 24 of 114 genres have nominally significant correlations (p < 0.05, |r| > 0.1). Results are exploratory due to multiple testing. Context matters.
2. Hypothesis 2 (Superstar Regional Distribution):
   - Chi-square test: χ² = 8.0, df = 12, p = 0.785. Cramér's V = 0.0168 (N = 9,436).
   - Superstar tracks are uniformly distributed across regions (3.91% to 5.27%). No evidence of regional concentration.
3. Artist Tier: Strongest observed association with popularity (Superstar: 76.1 vs Emerging: 11.9). Frame as observational association, NOT causation.
4. Data Cleaning Decisions:
   - 74 exact duplicates removed.
   - 20 out-of-range popularities set to NaN.
   - 250 vague release years ('late 90s', etc.) and 394 missing set to NaN.
   - 4 negative durations set to NaN.
   - Inconsistent casing standardized to Title Case.
   - Philosophy: Set invalid values to NaN rather than dropping rows.
5. Analytical Tone:
   - Always distinguish correlation from causation. Use "association", "observed pattern", not "cause" or "proven".
   - If asked an out-of-scope question (weather, jokes, coding other apps), politely decline and redirect to the music streaming dataset.

# ═══════════════════════════════════════════
# STRICT ANALYTICAL RIGOR (TECHNICAL ASSESSMENT STANDARD)
# ═══════════════════════════════════════════
- STRICT PROHIBITION: DO NOT speculate about or invent qualitative/subjective musical attributes (e.g. NEVER say "fortissimo passages", "dramatic climaxes", "mellow, acoustic-driven intimacy", "chaotic tracks", "soothing lullabies", or "bedtime listening"). The dataset contains only numerical audio features and metadata — subjective musical attributes were NEVER measured or established in this dataset.
- Stay strictly analytical, data-grounded, and objective. Report empirical statistical metrics: genre name, sample size (N), Pearson correlation (r), and p-value.
- Frame all findings strictly as observational associations: e.g., "Classical shows a positive association (r = +0.286, p = 0.008, N = 84), while Detroit Techno shows a negative association (r = -0.289, p = 0.008, N = 82). These are observational associations in cross-sectional data and should not be interpreted as causal effects or subjective musical interpretations."
- Always remind the user that testing across 114 genres simultaneously inflates the family-wise error rate, so nominally significant associations (p < 0.05) must be interpreted as exploratory.

# ═══════════════════════════════════════════
# TABLE FORMATTING RULES (CRITICAL)
# ═══════════════════════════════════════════
- When outputting tables, ALWAYS format them as a continuous, valid GitHub Flavored Markdown (GFM) pipe table:
  | Genre | Pearson r | p-value | N | Direction & Significance |
  |---|---|---|---|---|
  | Emo | -0.404 | 0.0002 | 82 | Negative (Nominally Significant) |
- NEVER insert empty blank lines or empty rows (e.g. | | | | |) between the header row and data rows! The table MUST be a single unbroken block.
- Keep table rows compact, cleanly aligned, and devoid of ungrounded musical speculation.

═══════════════════════════════════════════
TOOL USAGE INSTRUCTIONS
═══════════════════════════════════════════
Whenever a user asks a calculation, aggregation, filtering, rank, or statistical question that requires querying the raw data:
- ALWAYS call the `run_pandas_code` tool with clean, idiomatic Pandas/SciPy code.
- Variables created in one tool call (e.g. `corr_df = ...`, `sig_genres = ...`) PERSIST in the session namespace and can be referenced in subsequent tool calls.
- Never guess or approximate numbers when you can calculate them exactly!
- After receiving the tool result, present the answer clearly with formatted numbers, sample sizes, and proper statistical framing.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_pandas_code",
            "description": "Execute a Python/Pandas expression or script on the DataFrame `df` (10,058 rows) and return the computed result.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code using df, pd, np, stats. E.g. df.groupby('market_region')['popularity'].agg(['mean', 'count']).round(2).to_dict()"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

import ast
import scipy

# Persistent session namespace so variables like corr_df survive across tool calls & conversation turns
SESSION_ENV = {
    "__builtins__": __builtins__,
    "df": df,
    "pd": pd,
    "np": np,
    "stats": stats,
    "scipy": scipy,
    "sklearn": sklearn,
    "LinearRegression": LinearRegression
}

def execute_user_code(code_str, exec_env=None):
    """Safely executes a Python snippet against df in a persistent session namespace like Jupyter."""
    if exec_env is None:
        exec_env = SESSION_ENV

    start_t = time.time()
    code_str = code_str.strip()
    if not code_str:
        return "", 0.0, None

    stdout_capture = io.StringIO()
    try:
        parsed = ast.parse(code_str)
        if not parsed.body:
            return "", round((time.time() - start_t) * 1000, 1), None

        last_is_expr = isinstance(parsed.body[-1], ast.Expr)

        with contextlib.redirect_stdout(stdout_capture):
            if last_is_expr:
                # Compile and exec all statements except the last
                if len(parsed.body) > 1:
                    exec_mod = ast.Module(body=parsed.body[:-1], type_ignores=[])
                    exec(compile(exec_mod, filename="<code_interpreter>", mode="exec"), exec_env)

                # Evaluate the last expression (capturing return value like Jupyter)
                expr_ast = ast.Expression(body=parsed.body[-1].value)
                last_val = eval(compile(expr_ast, filename="<code_interpreter>", mode="eval"), exec_env)

                output = stdout_capture.getvalue().strip()
                if last_val is not None:
                    if isinstance(last_val, (pd.DataFrame, pd.Series)):
                        val_str = last_val.to_string()
                    else:
                        val_str = str(last_val)

                    output = f"{output}\n{val_str}".strip() if output else val_str
            else:
                exec(compile(parsed, filename="<code_interpreter>", mode="exec"), exec_env)
                output = stdout_capture.getvalue().strip()

        if not output:
            output = "Code executed successfully."

        duration_ms = round((time.time() - start_t) * 1000, 1)
        return output, duration_ms, None

    except Exception as e:
        duration_ms = round((time.time() - start_t) * 1000, 1)
        return None, duration_ms, f"Execution Error: {e}\n{traceback.format_exc()}"

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.errorhandler(Exception)
def handle_all_exceptions(e):
    trace = traceback.format_exc()
    print(f"[UNHANDLED EXCEPTION] {e}\n{trace}")
    return jsonify({"error": str(e), "traceback": trace}), 500

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        body = request.get_json(force=True) or {}
        messages = body.get("messages", [])
        model_key = body.get("model", "qwen")

        # Target model config
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        model_id = "qwen/qwen3.6-plus"
        api_key = (OPENROUTER_KEY or os.environ.get("OPENROUTER_API_KEY", "")).strip().replace("\n", "").replace("\r", "").replace(" ", "")

        if not api_key:
            return jsonify({
                "error": "OPENROUTER_API_KEY is missing on the server. Please add it to your Render Environment Variables."
            }), 400

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://music-streaming-explorer.onrender.com",
            "X-Title": "Music Streaming Data Explorer"
        }

        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        executed_code_history = []
        total_exec_time = 0
        max_iterations = 6
        current_iteration = 0
        final_reply = ""

        while current_iteration < max_iterations:
            current_iteration += 1
            payload = {
                "model": model_id,
                "messages": full_messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "temperature": 0.2,
                "max_tokens": 4096
            }

            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )

            if resp.status_code != 200:
                return jsonify({"error": f"API error {resp.status_code}: {resp.text}"}), resp.status_code

            data = resp.json()
            choice = data["choices"][0]
            msg = choice["message"]
            tool_calls = msg.get("tool_calls")

            if tool_calls:
                full_messages.append(msg)
                for tc in tool_calls:
                    fn_name = tc.get("function", {}).get("name")
                    args_str = tc.get("function", {}).get("arguments", "{}")
                    try:
                        args = json.loads(args_str)
                    except Exception:
                        args = {"code": args_str}

                    code = args.get("code", "")
                    print(f"\n[PANDAS ITERATION {current_iteration}] Running:\n{code}")
                    output, exec_time, error = execute_user_code(code)
                    total_exec_time += exec_time
                    executed_code_history.append({
                        "code": code,
                        "output": output if not error else error,
                        "time_ms": exec_time,
                        "has_error": bool(error)
                    })

                    tool_result_content = output if not error else f"Error: {error}"
                    if len(tool_result_content) > 3000:
                        tool_result_content = tool_result_content[:3000] + "\n...[truncated]"

                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result_content
                    })
                # Continue loop so model can process results or make next calculation
                continue
            else:
                # Model produced final answer
                final_reply = msg.get("content") or ""
                if not final_reply and msg.get("reasoning"):
                    final_reply = msg.get("reasoning").split("\n")[-1]
                break

        # Fallback if loop ended with tool calls pending
        if not final_reply:
            resp_final = requests.post(
                endpoint,
                headers=headers,
                json={
                    "model": model_id,
                    "messages": full_messages + [{"role": "user", "content": "Now please provide your complete, detailed analysis based on all calculations performed above."}],
                    "temperature": 0.2,
                    "max_tokens": 4096
                },
                timeout=60
            )
            if resp_final.status_code == 200:
                final_reply = resp_final.json()["choices"][0]["message"].get("content") or ""

        return jsonify({
            "reply": final_reply,
            "model": "Qwen 3.6 Plus (Pandas Code Interpreter)" if executed_code_history else "Qwen 3.6 Plus",
            "code_executed": executed_code_history,
            "total_exec_time_ms": round(total_exec_time, 1)
        })

    except Exception as e:
        print(f"[ERROR] {e}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("\n" + "=" * 65)
    print(" [ENGINE] Music Streaming Data Explorer — Code Interpreter Active")
    print(" [DATASET] 10,058 tracks in memory with Pandas & SciPy")
    print(f" [SERVER] http://localhost:{port}")
    print("=" * 65 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
