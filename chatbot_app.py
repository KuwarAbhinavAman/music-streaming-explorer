"""
Music Streaming Data Explorer — Interactive Chatbot
Flask backend with OpenAI function-calling + Pandas analytical layer

Requires: OPENAI_API_KEY environment variable
"""
import os
import json
import pandas as pd
import numpy as np
from scipy import stats
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

# ── Configuration ───────────────────────────────────────────────
app = Flask(__name__, static_folder="static")

# Load cleaned dataset
DATA_PATH = os.path.join("output", "cleaned_data.csv")
df = pd.read_csv(DATA_PATH)
# Ensure correct types
df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
df["energy"] = pd.to_numeric(df["energy"], errors="coerce")
df["danceability"] = pd.to_numeric(df["danceability"], errors="coerce")
df["release_year_clean"] = pd.to_numeric(df["release_year_clean"], errors="coerce")

print(f"[DATA] Loaded {len(df)} rows, {len(df.columns)} columns")

# OpenAI client (set key later or via env var)
client = None

def get_client():
    global client
    if client is None:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
    return client


# ================================================================
# ANALYTICAL FUNCTIONS (deterministic, Pandas-based)
# ================================================================

def get_dataset_overview():
    """Basic dataset statistics."""
    pop = df["popularity"].dropna()
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "genres": sorted(df["track_genre"].dropna().unique().tolist()),
        "genre_count": df["track_genre"].nunique(),
        "regions": sorted(df["market_region"].dropna().unique().tolist()),
        "artist_tiers": sorted(df["artist_tier"].dropna().unique().tolist()),
        "platforms": sorted(df["streaming_platform"].dropna().unique().tolist()),
        "popularity_stats": {
            "mean": round(pop.mean(), 2),
            "median": round(pop.median(), 2),
            "std": round(pop.std(), 2),
            "min": round(pop.min(), 2),
            "max": round(pop.max(), 2),
            "count": int(pop.count()),
        },
    }

def get_average_popularity_by(group_by):
    """Average popularity grouped by a categorical column."""
    valid_groups = ["track_genre", "market_region", "artist_tier", 
                    "streaming_platform", "playlist_category", "clean_decade"]
    if group_by not in valid_groups:
        return {"error": f"Invalid group. Use one of: {valid_groups}"}
    
    result = (
        df.dropna(subset=["popularity", group_by])
        .groupby(group_by)["popularity"]
        .agg(["mean", "median", "count"])
        .round(2)
        .sort_values("mean", ascending=False)
        .reset_index()
    )
    result.columns = [group_by, "mean_popularity", "median_popularity", "count"]
    return result.to_dict(orient="records")

def get_correlation(feature1, feature2):
    """Pearson and Spearman correlation between two numeric features."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if feature1 not in numeric_cols or feature2 not in numeric_cols:
        return {"error": f"Both features must be numeric. Available: {numeric_cols}"}
    
    valid = df.dropna(subset=[feature1, feature2])
    n = len(valid)
    if n < 10:
        return {"error": f"Insufficient data (n={n})"}
    
    pr, pp = stats.pearsonr(valid[feature1], valid[feature2])
    sr, sp = stats.spearmanr(valid[feature1], valid[feature2])
    
    return {
        "feature1": feature1,
        "feature2": feature2,
        "n": n,
        "pearson_r": round(pr, 4),
        "pearson_p": round(pp, 6),
        "spearman_r": round(sr, 4),
        "spearman_p": round(sp, 6),
        "r_squared": round(pr**2, 4),
    }

def get_correlation_by_genre(feature1, feature2, min_n=30):
    """Correlation between two features, broken down by genre."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if feature1 not in numeric_cols or feature2 not in numeric_cols:
        return {"error": f"Both features must be numeric. Available: {numeric_cols}"}
    
    results = []
    for genre, gdf in df.dropna(subset=[feature1, feature2]).groupby("track_genre"):
        if len(gdf) >= min_n:
            pr, pp = stats.pearsonr(gdf[feature1], gdf[feature2])
            results.append({
                "genre": genre,
                "n": len(gdf),
                "pearson_r": round(pr, 4),
                "pearson_p": round(pp, 6),
            })
    
    return sorted(results, key=lambda x: x["pearson_r"], reverse=True)

def get_superstar_by_region():
    """Superstar artist distribution across regions."""
    valid = df.dropna(subset=["artist_tier", "market_region"])
    
    superstar = valid[valid["artist_tier"] == "Superstar"]
    total_by_region = valid.groupby("market_region").size()
    superstar_by_region = superstar.groupby("market_region").size()
    
    result = {}
    for region in total_by_region.index:
        count = int(superstar_by_region.get(region, 0))
        total = int(total_by_region[region])
        result[region] = {
            "superstar_count": count,
            "total_tracks": total,
            "superstar_pct": round(count / total * 100, 2) if total > 0 else 0,
        }
    
    # Chi-square test
    crosstab = pd.crosstab(valid["market_region"], valid["artist_tier"])
    chi2, p, dof, _ = stats.chi2_contingency(crosstab)
    n = crosstab.sum().sum()
    min_dim = min(crosstab.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
    
    return {
        "regions": result,
        "chi_square": round(chi2, 2),
        "p_value": round(p, 6),
        "dof": int(dof),
        "cramers_v": round(cramers_v, 4),
        "conclusion": "No significant regional bias" if p > 0.05 else "Significant regional differences detected",
    }

def get_popularity_by_tier():
    """Popularity statistics by artist tier."""
    valid = df.dropna(subset=["popularity", "artist_tier"])
    result = (
        valid.groupby("artist_tier")["popularity"]
        .agg(["mean", "median", "std", "count"])
        .round(2)
        .sort_values("mean", ascending=False)
        .reset_index()
    )
    result.columns = ["artist_tier", "mean_popularity", "median_popularity", "std", "count"]
    return result.to_dict(orient="records")

def get_data_quality_summary():
    """Summary of data quality issues found and cleaning applied."""
    return {
        "raw_rows": 10132,
        "cleaned_rows": len(df),
        "exact_duplicates_removed": 74,
        "issues_found": [
            "Casing inconsistencies in market_region (Europe vs EUROPE), artist_tier (Emerging vs emerging), streaming_platform (Spotify vs SpotifY), and explicit (True/False vs Yes/No)",
            "250 non-numeric release_year values ('late 90s', 'circa 2010', 'unknown', 'pre-2000') — set to NaN",
            "394 missing release_year values",
            "20 invalid popularity scores (negative or >100) — set to NaN",
            "4 negative track durations (-1000ms) — set to NaN",
            "74 exact duplicate rows removed",
            "114 granular genre labels with same tracks appearing under multiple genres"
        ],
        "cleaning_applied": [
            "Standardised categorical casing to title case",
            "Fixed 'Amazon  Music' (double space) to 'Amazon Music'",
            "Non-numeric release years set to NaN; clean_decade derived from valid years only",
            "Invalid popularity (outside 0-100) set to NaN",
            "Negative durations set to NaN",
            "Exact duplicate rows removed; non-identical duplicates (same track, different context) retained"
        ],
    }

def get_analysis_limitations():
    """Key limitations of the analysis."""
    return {
        "limitations": [
            "ASSOCIATION ≠ CAUSATION: All findings are correlational. We cannot conclude that energy 'causes' popularity.",
            "OBSERVATIONAL DATA: Tracks are not randomly assigned features. Many confounders exist (genre, artist brand, marketing, playlist placement).",
            "SNAPSHOT DATA: Popularity scores reflect a single point in time, not long-term success.",
            "NON-INDEPENDENT OBSERVATIONS: Same track can appear under multiple genres/contexts, violating independence assumptions.",
            "MULTIPLE TESTING: With 114 genres, some significant correlations may be false positives.",
            "VAGUE RELEASE YEARS: 250 tracks have imprecise release dates, limiting temporal analysis.",
            "GENRE SAMPLE SIZES: ~80-90 tracks per genre is modest for correlation analysis.",
            "SELECTION BIAS: The dataset may not represent all music streaming — only tracks captured in this collection.",
        ]
    }

def get_top_tracks_by_genre(genre, n=10):
    """Top n tracks by popularity in a specific genre."""
    valid = df[(df["track_genre"] == genre) & df["popularity"].notna()]
    if len(valid) == 0:
        genres = sorted(df["track_genre"].dropna().unique().tolist())
        return {"error": f"Genre '{genre}' not found. Available: {genres[:20]}..."}
    
    top = valid.nlargest(n, "popularity")[["track_id", "artists", "popularity", "energy", "danceability"]].round(3)
    return {
        "genre": genre,
        "top_tracks": top.to_dict(orient="records"),
        "total_in_genre": len(valid),
    }


# ── Function registry for OpenAI ───────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_dataset_overview",
            "description": "Get basic statistics about the cleaned music streaming dataset including row count, column names, genres, regions, and popularity distribution.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_average_popularity_by",
            "description": "Get average popularity grouped by a categorical column like genre, region, artist tier, platform, playlist category, or decade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "string",
                        "enum": ["track_genre", "market_region", "artist_tier", "streaming_platform", "playlist_category", "clean_decade"],
                        "description": "The column to group by"
                    }
                },
                "required": ["group_by"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_correlation",
            "description": "Calculate Pearson and Spearman correlation between two numeric features like energy, popularity, danceability, loudness, tempo, valence, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature1": {"type": "string", "description": "First numeric feature (e.g., 'energy', 'popularity')"},
                    "feature2": {"type": "string", "description": "Second numeric feature"},
                },
                "required": ["feature1", "feature2"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_correlation_by_genre",
            "description": "Calculate correlation between two numeric features broken down by genre. Shows which genres have the strongest positive or negative relationship.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feature1": {"type": "string", "description": "First numeric feature"},
                    "feature2": {"type": "string", "description": "Second numeric feature"},
                    "min_n": {"type": "integer", "description": "Minimum sample size per genre (default 30)", "default": 30},
                },
                "required": ["feature1", "feature2"]
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_superstar_by_region",
            "description": "Analyse the distribution of Superstar-tier artists across market regions with chi-square test for independence.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_popularity_by_tier",
            "description": "Get popularity statistics broken down by artist tier (Superstar, Established, Rising, Emerging).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_quality_summary",
            "description": "Get a summary of data quality issues found in the raw dataset and the cleaning steps applied.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analysis_limitations",
            "description": "Get the key limitations, assumptions, and caveats of the analysis.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_tracks_by_genre",
            "description": "Get the top tracks by popularity in a specific genre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre name (e.g., 'pop', 'rock', 'k-pop')"},
                    "n": {"type": "integer", "description": "Number of tracks to return (default 10)", "default": 10},
                },
                "required": ["genre"]
            },
        }
    },
]

FUNCTION_MAP = {
    "get_dataset_overview": get_dataset_overview,
    "get_average_popularity_by": get_average_popularity_by,
    "get_correlation": get_correlation,
    "get_correlation_by_genre": get_correlation_by_genre,
    "get_superstar_by_region": get_superstar_by_region,
    "get_popularity_by_tier": get_popularity_by_tier,
    "get_data_quality_summary": get_data_quality_summary,
    "get_analysis_limitations": get_analysis_limitations,
    "get_top_tracks_by_genre": get_top_tracks_by_genre,
}

SYSTEM_PROMPT = """You are a Music Streaming Data Analyst assistant. You help users explore a cleaned music streaming dataset of ~10,000 tracks.

Key facts about the dataset:
- 10,058 cleaned tracks with 114 genres across 5 market regions
- Popularity scale: 0-100 (higher = more popular)
- Audio features: energy, danceability, loudness, tempo, valence, etc. (all 0-1 scale except loudness and tempo)
- Artist tiers: Emerging, Rising, Established, Superstar
- Key finding: Energy has virtually no overall correlation with popularity (r=0.01), but varies dramatically by genre
- Key finding: Superstar artists are evenly distributed across regions (no regional bias)
- Key finding: Artist tier is the strongest predictor of popularity

IMPORTANT RULES:
1. Always use the provided functions to get exact numbers from the data. Never make up statistics.
2. Distinguish between association and causation — this is observational data.
3. Be concise but informative. Format results clearly.
4. When showing correlations, mention sample size and statistical significance.
5. Acknowledge limitations when relevant.
"""


# ── API Routes ──────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        history = data.get("history", [])
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        cl = get_client()
        
        # Build messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in history[-10:]:  # Keep last 10 exchanges
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})
        
        # First call — may trigger tool use
        response = cl.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1000,
        )
        
        msg = response.choices[0].message
        
        # Handle tool calls
        if msg.tool_calls:
            messages.append(msg)
            
            for tool_call in msg.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                print(f"[TOOL] Calling {fn_name}({fn_args})")
                
                if fn_name in FUNCTION_MAP:
                    result = FUNCTION_MAP[fn_name](**fn_args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                })
            
            # Second call — generate natural language response
            response2 = cl.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
            )
            answer = response2.choices[0].message.content
        else:
            answer = msg.content
        
        return jsonify({"response": answer})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "dataset_rows": len(df),
        "api_key_set": bool(os.environ.get("OPENAI_API_KEY")),
    })


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Music Streaming Data Explorer")
    print("=" * 50)
    print(f"Dataset: {len(df)} rows loaded")
    print(f"API Key: {'Set' if os.environ.get('OPENAI_API_KEY') else 'NOT SET — set OPENAI_API_KEY env var'}")
    print(f"\nOpen http://localhost:5000 in your browser")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
