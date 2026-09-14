"""
Phase 1b — Deep-dive on suspicious values, duplicates, and edge cases
"""
import pandas as pd
import numpy as np

XLSX = r"data_copy.xlsx"
df = pd.read_excel(XLSX, sheet_name="Data")

pd.set_option("display.max_columns", None)
pd.set_option("display.max_colwidth", 80)
pd.set_option("display.width", 250)

# ── 1. Popularity outliers ──────────────────────────────────────
print("=" * 70)
print("POPULARITY OUTLIERS")
print("=" * 70)
pop = df["popularity"].dropna()
neg = df[df["popularity"] < 0]
print(f"\nNegative popularity ({len(neg)} rows):")
print(neg[["track_id", "artists", "popularity", "track_genre"]].to_string())

high = df[df["popularity"] > 100]
print(f"\nPopularity > 100 ({len(high)} rows):")
print(high[["track_id", "artists", "popularity", "track_genre"]].to_string())

# ── 2. Duration outliers ────────────────────────────────────────
print("\n\n" + "=" * 70)
print("DURATION OUTLIERS")
print("=" * 70)
neg_dur = df[df["duration_ms"] <= 0]
print(f"\nduration_ms <= 0 ({len(neg_dur)} rows):")
if len(neg_dur) > 0:
    print(neg_dur[["track_id", "artists", "duration_ms", "track_genre"]].to_string())

extreme_dur = df[df["duration_ms"] > 600000]  # > 10 minutes
print(f"\nduration_ms > 10 minutes ({len(extreme_dur)} rows):")
if len(extreme_dur) > 0:
    print(extreme_dur[["track_id", "artists", "duration_ms", "track_genre"]].head(20).to_string())

very_extreme = df[df["duration_ms"] > 1800000]  # > 30 minutes
print(f"\nduration_ms > 30 minutes ({len(very_extreme)} rows):")
if len(very_extreme) > 0:
    print(very_extreme[["track_id", "artists", "duration_ms", "track_genre"]].to_string())

# ── 3. Tempo = 0 ───────────────────────────────────────────────
print("\n\n" + "=" * 70)
print("TEMPO = 0")
print("=" * 70)
zero_tempo = df[df["tempo"] == 0]
print(f"tempo = 0: {len(zero_tempo)} rows")
if len(zero_tempo) > 0 and len(zero_tempo) <= 10:
    print(zero_tempo[["track_id", "artists", "tempo", "track_genre"]].to_string())

# ── 4. Duplicate track_id investigation ─────────────────────────
print("\n\n" + "=" * 70)
print("DUPLICATE TRACK_ID INVESTIGATION")
print("=" * 70)
dup_ids = df[df["track_id"].duplicated(keep=False)].sort_values("track_id")
print(f"Total rows with duplicated track_id: {len(dup_ids)}")
print(f"Unique duplicated track_ids: {dup_ids['track_id'].nunique()}")

# Show a sample of duplicated pairs to understand their nature
sample_ids = dup_ids["track_id"].unique()[:5]
for tid in sample_ids:
    rows = df[df["track_id"] == tid]
    print(f"\n--- track_id: {tid} ({len(rows)} rows) ---")
    print(rows.to_string())

# Check: are duplicates EXACT or do they differ?
print("\n\nDuplicate rows — checking which columns differ:")
for tid in dup_ids["track_id"].unique()[:10]:
    rows = df[df["track_id"] == tid]
    for col in df.columns:
        vals = rows[col].dropna().unique()
        if len(vals) > 1:
            print(f"  track_id={tid}, col='{col}', values={vals}")

# ── 5. Workout category count ──────────────────────────────────
print("\n\n" + "=" * 70)
print("PLAYLIST_CATEGORY = 'Workout'")
print("=" * 70)
workout = df[df["playlist_category"] == "Workout"]
print(f"Workout count: {len(workout)}")
# Check if it exists in the data differently
print("Unique playlist_category values:")
print(df["playlist_category"].value_counts(dropna=False).to_string())

# ── 6. New Releases (only 10) ──────────────────────────────────
print("\n\n" + "=" * 70)
print("PLAYLIST_CATEGORY = 'New Releases' (10 rows)")
print("=" * 70)
nr = df[df["playlist_category"] == "New Releases"]
print(nr[["track_id", "artists", "playlist_category", "track_genre", "release_year"]].to_string())

# ── 7. time_signature = 0 ──────────────────────────────────────
print("\n\n" + "=" * 70)
print("TIME_SIGNATURE = 0")
print("=" * 70)
ts0 = df[df["time_signature"] == 0]
print(f"time_signature = 0: {len(ts0)} rows")

# ── 8. Loudness > 0 ────────────────────────────────────────────
print("\n\n" + "=" * 70)
print("LOUDNESS > 0 (unusual)")
print("=" * 70)
loud_pos = df[df["loudness"] > 0]
print(f"Loudness > 0: {len(loud_pos)} rows")
if len(loud_pos) > 0 and len(loud_pos) <= 10:
    print(loud_pos[["track_id", "artists", "loudness", "track_genre"]].to_string())

# ── 9. Explicit column inspection ──────────────────────────────
print("\n\n" + "=" * 70)
print("EXPLICIT COLUMN")
print("=" * 70)
print(df["explicit"].value_counts(dropna=False).to_string())

# ── 10. Non-numeric release_year — rows detail ─────────────────
print("\n\n" + "=" * 70)
print("NON-NUMERIC RELEASE_YEAR ROWS")
print("=" * 70)
ry_num = pd.to_numeric(df["release_year"], errors="coerce")
non_num = df[ry_num.isna() & df["release_year"].notna()]
print(non_num[["track_id", "artists", "release_year", "release_decade", "track_genre"]].to_string())

# ── 11. Rows with most missing values ───────────────────────────
print("\n\n" + "=" * 70)
print("ROWS WITH MANY MISSING VALUES")
print("=" * 70)
row_miss = df.isnull().sum(axis=1)
high_miss = df[row_miss >= 3]
print(f"Rows with ≥3 missing values: {len(high_miss)}")
if len(high_miss) > 0:
    print(high_miss[["track_id", "artists", "popularity", "market_region", "artist_tier"]].head(20).to_string())
    print(f"\nMissing counts per row (top):")
    print(row_miss[row_miss >= 3].value_counts().sort_index().to_string())

print("\n\nDONE — Phase 1b deep-dive complete.")
