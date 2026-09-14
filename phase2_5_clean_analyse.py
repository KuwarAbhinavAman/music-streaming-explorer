"""
Phase 2-5: Data Cleaning + Full Hypothesis Analysis
Produces:
  - cleaned_data.csv
  - analysis_results.json (all stats for PPT)
  - chart images for embedding in PPT
"""
import pandas as pd
import numpy as np
import json
import os
from scipy import stats

# ── CONFIG ──────────────────────────────────────────────────────
XLSX = r"data_copy.xlsx"
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_excel(XLSX, sheet_name="Data")
results = {}
results["raw_shape"] = list(df.shape)

# ================================================================
# PHASE 2-3: CLEANING
# ================================================================

# ── 1. Drop exact duplicate rows ────────────────────────────────
n_before = len(df)
df = df.drop_duplicates()
n_exact_dups = n_before - len(df)
results["exact_duplicates_removed"] = n_exact_dups
print(f"[CLEAN] Removed {n_exact_dups} exact duplicate rows. Rows: {len(df)}")

# ── 2. Standardise casing: market_region ────────────────────────
region_map = {
    "EUROPE": "Europe",
    "ASIA PACIFIC": "Asia Pacific",
    "LATIN AMERICA": "Latin America",
    "NORTH AMERICA": "North America",
    "MIDDLE EAST & AFRICA": "Middle East & Africa",
}
df["market_region"] = df["market_region"].replace(region_map)
print(f"[CLEAN] Standardised market_region casing. Unique: {df['market_region'].dropna().unique().tolist()}")

# ── 3. Standardise casing: artist_tier ──────────────────────────
df["artist_tier"] = df["artist_tier"].str.strip().str.title()
print(f"[CLEAN] Standardised artist_tier casing. Unique: {df['artist_tier'].dropna().unique().tolist()}")

# ── 4. Standardise casing: streaming_platform ───────────────────
platform_map = {
    "SpotifY": "Spotify",
    "apple music": "Apple Music",
    "youTube Music": "YouTube Music",
    "TIDAL": "Tidal",
    "Amazon  Music": "Amazon Music",  # double space
}
df["streaming_platform"] = df["streaming_platform"].replace(platform_map)
print(f"[CLEAN] Standardised streaming_platform. Unique: {df['streaming_platform'].dropna().unique().tolist()}")

# ── 5. Standardise explicit column ──────────────────────────────
explicit_map = {"Yes": True, "No": False, "True": True, "False": False}
df["explicit"] = df["explicit"].map(explicit_map).fillna(df["explicit"])
df["explicit"] = df["explicit"].astype(bool)
print(f"[CLEAN] Standardised explicit column. Unique: {df['explicit'].unique().tolist()}")

# ── 6. Clean release_year ───────────────────────────────────────
df["release_year_raw"] = df["release_year"].copy()
df["release_year_clean"] = pd.to_numeric(df["release_year"], errors="coerce")
n_vague_years = df["release_year_clean"].isna().sum() - df["release_year"].isna().sum()
n_missing_years = df["release_year"].isna().sum()
results["release_year_vague_values"] = int(n_vague_years)
results["release_year_missing"] = int(n_missing_years)

# Derive clean decade from valid year only
df["clean_decade"] = (df["release_year_clean"] // 10 * 10).astype("Int64").astype(str) + "s"
df.loc[df["release_year_clean"].isna(), "clean_decade"] = np.nan
print(f"[CLEAN] release_year: {n_vague_years} vague values set to NaN, {n_missing_years} already missing")
print(f"  Clean decade distribution:\n{df['clean_decade'].value_counts().sort_index().to_string()}")

# ── 7. Set invalid popularity to NaN ────────────────────────────
invalid_pop_mask = (df["popularity"] < 0) | (df["popularity"] > 100)
n_invalid_pop = invalid_pop_mask.sum()
df.loc[invalid_pop_mask, "popularity"] = np.nan
results["invalid_popularity_removed"] = int(n_invalid_pop)
print(f"[CLEAN] Set {n_invalid_pop} invalid popularity values to NaN")

# ── 8. Set negative durations to NaN ────────────────────────────
neg_dur_mask = df["duration_ms"] < 0
n_neg_dur = neg_dur_mask.sum()
df.loc[neg_dur_mask, "duration_ms"] = np.nan
results["negative_durations_removed"] = int(n_neg_dur)
print(f"[CLEAN] Set {n_neg_dur} negative duration values to NaN")

# ── 9. Save cleaned dataset ────────────────────────────────────
df.to_csv(os.path.join(OUT_DIR, "cleaned_data.csv"), index=False)
results["cleaned_shape"] = list(df.shape)
print(f"\n[CLEAN] Saved cleaned dataset: {df.shape[0]} rows x {df.shape[1]} columns")

# Quick cleaning summary
print("\n--- CLEANING SUMMARY ---")
cleaning_summary = {
    "exact_duplicates_removed": n_exact_dups,
    "casing_standardised": ["market_region", "artist_tier", "streaming_platform", "explicit"],
    "invalid_popularity_set_nan": n_invalid_pop,
    "negative_durations_set_nan": n_neg_dur,
    "vague_release_years_set_nan": int(n_vague_years),
    "missing_release_years": int(n_missing_years),
}
results["cleaning_summary"] = cleaning_summary
for k, v in cleaning_summary.items():
    print(f"  {k}: {v}")

# ================================================================
# PHASE 4-5: HYPOTHESIS ANALYSIS
# ================================================================

# Working dataset: exclude rows missing popularity (our outcome)
df_pop = df.dropna(subset=["popularity"]).copy()
print(f"\n\n[ANALYSIS] Working dataset (non-null popularity): {len(df_pop)} rows")

# ────────────────────────────────────────────────────────────────
# HYPOTHESIS 1: Energy vs Popularity
# ────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("HYPOTHESIS 1: Energy vs Popularity")
print("=" * 60)

# Overall correlation
h1_data = df_pop.dropna(subset=["energy", "popularity"])
n_h1 = len(h1_data)

pearson_r, pearson_p = stats.pearsonr(h1_data["energy"], h1_data["popularity"])
spearman_r, spearman_p = stats.spearmanr(h1_data["energy"], h1_data["popularity"])

print(f"  N = {n_h1}")
print(f"  Pearson r = {pearson_r:.4f}, p = {pearson_p:.2e}")
print(f"  Spearman rho = {spearman_r:.4f}, p = {spearman_p:.2e}")
print(f"  R-squared = {pearson_r**2:.4f} ({pearson_r**2*100:.2f}% variance explained)")

results["h1_overall"] = {
    "n": n_h1,
    "pearson_r": round(pearson_r, 4),
    "pearson_p": float(f"{pearson_p:.2e}"),
    "spearman_r": round(spearman_r, 4),
    "spearman_p": float(f"{spearman_p:.2e}"),
    "r_squared": round(pearson_r ** 2, 4),
}

# By energy bins (for visualisation)
h1_data["energy_bin"] = pd.cut(h1_data["energy"], bins=10, labels=[f"{i/10:.1f}-{(i+1)/10:.1f}" for i in range(10)])
energy_bin_stats = h1_data.groupby("energy_bin", observed=True)["popularity"].agg(["mean", "median", "std", "count"]).reset_index()
energy_bin_stats.columns = ["energy_bin", "mean_pop", "median_pop", "std_pop", "count"]
print(f"\n  Popularity by Energy Bin:")
print(energy_bin_stats.to_string(index=False))
results["h1_energy_bins"] = energy_bin_stats.to_dict(orient="records")

# ── Hypothesis 1b: By Genre ────────────────────────────────────
print("\n--- Energy-Popularity Correlation by Genre ---")
genre_corr = []
for genre, gdf in h1_data.groupby("track_genre"):
    if len(gdf) >= 30:  # minimum sample size for meaningful correlation
        r, p = stats.pearsonr(gdf["energy"], gdf["popularity"])
        sr, sp = stats.spearmanr(gdf["energy"], gdf["popularity"])
        genre_corr.append({
            "genre": genre,
            "n": len(gdf),
            "pearson_r": round(r, 4),
            "pearson_p": round(p, 6),
            "spearman_r": round(sr, 4),
            "spearman_p": round(sp, 6),
        })

genre_corr_df = pd.DataFrame(genre_corr).sort_values("pearson_r", ascending=False)
print(genre_corr_df.to_string(index=False))

# Top and bottom genres
top5 = genre_corr_df.head(5).to_dict(orient="records")
bot5 = genre_corr_df.tail(5).to_dict(orient="records")
results["h1_genre_corr_top5"] = top5
results["h1_genre_corr_bot5"] = bot5
results["h1_genre_corr_all"] = genre_corr_df.to_dict(orient="records")

# Significant genres (p < 0.05 and |r| > 0.1)
sig_genres = genre_corr_df[(genre_corr_df["pearson_p"] < 0.05) & (genre_corr_df["pearson_r"].abs() > 0.1)]
print(f"\n  Genres with significant correlation (p<0.05 & |r|>0.1): {len(sig_genres)}")
print(sig_genres.to_string(index=False))
results["h1_significant_genres"] = sig_genres.to_dict(orient="records")

# ────────────────────────────────────────────────────────────────
# HYPOTHESIS 2: Superstar Regional Distribution
# ────────────────────────────────────────────────────────────────
print("\n\n" + "=" * 60)
print("HYPOTHESIS 2: Superstar Artists & Regional Distribution")
print("=" * 60)

h2_data = df_pop.dropna(subset=["artist_tier", "market_region"])

# Cross-tab: artist_tier x market_region
crosstab = pd.crosstab(h2_data["market_region"], h2_data["artist_tier"])
print("\n  Raw counts (Artist Tier x Market Region):")
print(crosstab.to_string())

# Proportions within each region
crosstab_pct = pd.crosstab(h2_data["market_region"], h2_data["artist_tier"], normalize="index") * 100
print("\n  Proportions within each region (%):")
print(crosstab_pct.round(1).to_string())

results["h2_crosstab_raw"] = crosstab.reset_index().to_dict(orient="records")
results["h2_crosstab_pct"] = crosstab_pct.round(2).reset_index().to_dict(orient="records")

# Chi-square test for independence
chi2, chi2_p, chi2_dof, chi2_expected = stats.chi2_contingency(crosstab)
print(f"\n  Chi-square test of independence:")
print(f"    Chi2 = {chi2:.2f}, df = {chi2_dof}, p = {chi2_p:.2e}")

# Cramer's V (effect size)
n_chi = crosstab.sum().sum()
min_dim = min(crosstab.shape) - 1
cramers_v = np.sqrt(chi2 / (n_chi * min_dim))
print(f"    Cramer's V = {cramers_v:.4f} (effect size)")
print(f"    N = {n_chi}")

results["h2_chi2"] = {
    "chi2": round(chi2, 2),
    "p_value": float(f"{chi2_p:.2e}"),
    "dof": int(chi2_dof),
    "cramers_v": round(cramers_v, 4),
    "n": int(n_chi),
}

# Focus on Superstar specifically
superstar_by_region = h2_data[h2_data["artist_tier"] == "Superstar"].groupby("market_region").size()
total_by_region = h2_data.groupby("market_region").size()
superstar_pct = (superstar_by_region / total_by_region * 100).round(2)
print(f"\n  Superstar % by region:")
for region in superstar_pct.sort_values(ascending=False).index:
    print(f"    {region}: {superstar_pct[region]:.1f}% ({superstar_by_region.get(region, 0)} / {total_by_region[region]})")

results["h2_superstar_pct"] = {
    region: {
        "pct": round(float(superstar_pct.get(region, 0)), 2),
        "count": int(superstar_by_region.get(region, 0)),
        "total": int(total_by_region[region]),
    }
    for region in total_by_region.index
}

# ────────────────────────────────────────────────────────────────
# HYPOTHESIS 3: Danceability Over Decades
# ────────────────────────────────────────────────────────────────
print("\n\n" + "=" * 60)
print("HYPOTHESIS 3: Danceability Over Decades")
print("=" * 60)

h3_data = df_pop.dropna(subset=["danceability", "clean_decade"])
print(f"  N = {len(h3_data)}")

decade_dance = h3_data.groupby("clean_decade")["danceability"].agg(["mean", "median", "std", "count"]).reset_index()
decade_dance.columns = ["decade", "mean_dance", "median_dance", "std_dance", "count"]
print(decade_dance.to_string(index=False))

# Trend test (Spearman correlation of decade midpoint vs danceability)
decade_midpoints = {
    "1960s": 1965, "1970s": 1975, "1980s": 1985, "1990s": 1995,
    "2000s": 2005, "2010s": 2015, "2020s": 2025
}
h3_data = h3_data.copy()
h3_data["decade_mid"] = h3_data["clean_decade"].map(decade_midpoints)
h3_valid = h3_data.dropna(subset=["decade_mid"])

if len(h3_valid) > 30:
    sr3, sp3 = stats.spearmanr(h3_valid["decade_mid"], h3_valid["danceability"])
    print(f"\n  Spearman rho (decade_midpoint vs danceability) = {sr3:.4f}, p = {sp3:.2e}")
    results["h3_trend"] = {
        "spearman_r": round(sr3, 4),
        "spearman_p": float(f"{sp3:.2e}"),
        "n": len(h3_valid),
    }
else:
    print("  Insufficient data for trend test")
    results["h3_trend"] = None

results["h3_decade_stats"] = decade_dance.to_dict(orient="records")

# ────────────────────────────────────────────────────────────────
# ADDITIONAL: Key descriptive stats for Executive Summary
# ────────────────────────────────────────────────────────────────
print("\n\n" + "=" * 60)
print("DESCRIPTIVE STATS FOR EXECUTIVE SUMMARY")
print("=" * 60)

# Popularity by genre (top 10 most popular)
genre_pop = df_pop.groupby("track_genre")["popularity"].agg(["mean", "median", "count"]).sort_values("mean", ascending=False)
genre_pop.columns = ["mean_pop", "median_pop", "count"]
print("\nTop 10 genres by mean popularity:")
print(genre_pop.head(10).to_string())
results["genre_popularity_top10"] = genre_pop.head(10).reset_index().to_dict(orient="records")

# Popularity by artist_tier
tier_pop = df_pop.dropna(subset=["artist_tier"]).groupby("artist_tier")["popularity"].agg(["mean", "median", "count"]).sort_values("mean", ascending=False)
tier_pop.columns = ["mean_pop", "median_pop", "count"]
print("\nPopularity by Artist Tier:")
print(tier_pop.to_string())
results["tier_popularity"] = tier_pop.reset_index().to_dict(orient="records")

# Overall popularity stats
pop_stats = df_pop["popularity"].describe()
results["popularity_describe"] = {k: round(v, 2) for k, v in pop_stats.items()}
print(f"\nPopularity describe:\n{pop_stats.to_string()}")

# ── Save all results ────────────────────────────────────────────
with open(os.path.join(OUT_DIR, "analysis_results.json"), "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n\n[DONE] All results saved to {OUT_DIR}/analysis_results.json")
print(f"[DONE] Cleaned dataset saved to {OUT_DIR}/cleaned_data.csv")
