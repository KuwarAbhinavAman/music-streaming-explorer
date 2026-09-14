"""
Phase 1 — Workbook Inspection & Data Profiling
"""
import pandas as pd
import numpy as np
import json

XLSX = r"Music Streaming Assessment.xlsx"

# ── 1. Sheet names ──────────────────────────────────────────────
xl = pd.ExcelFile(XLSX)
print("=" * 70)
print("SHEET NAMES:", xl.sheet_names)
print("=" * 70)

# ── 2. Read Assessment Instructions sheet ────────────────────────
instructions = pd.read_excel(XLSX, sheet_name="Music Streaming Assessment", header=None)
print("\n\n===== ASSESSMENT INSTRUCTIONS (first 60 rows) =====")
pd.set_option("display.max_colwidth", 200)
pd.set_option("display.max_rows", 60)
pd.set_option("display.width", 200)
print(instructions.to_string())

# ── 3. Read Data sheet ──────────────────────────────────────────
df = pd.read_excel(XLSX, sheet_name="Data")
print("\n\n===== DATA SHEET =====")
print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nColumns ({len(df.columns)}):")
for c in df.columns:
    print(f"  - {c}")

# ── 4. Data types & first rows ──────────────────────────────────
print("\n\n===== DTYPES =====")
print(df.dtypes)

print("\n\n===== FIRST 10 ROWS =====")
pd.set_option("display.max_columns", None)
print(df.head(10).to_string())

print("\n\n===== LAST 5 ROWS =====")
print(df.tail(5).to_string())

# ── 5. Missingness ──────────────────────────────────────────────
print("\n\n===== MISSING VALUES =====")
miss = df.isnull().sum()
miss_pct = (df.isnull().sum() / len(df) * 100).round(2)
miss_df = pd.DataFrame({"missing_count": miss, "missing_pct": miss_pct})
miss_df = miss_df[miss_df.missing_count > 0].sort_values("missing_count", ascending=False)
if len(miss_df) == 0:
    print("No missing values found.")
else:
    print(miss_df.to_string())

# ── 6. Numeric column stats ────────────────────────────────────
print("\n\n===== NUMERIC DESCRIBE =====")
print(df.describe().to_string())

# ── 7. Categorical columns — unique values & casing issues ─────
print("\n\n===== CATEGORICAL COLUMNS — UNIQUE VALUES =====")
cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
for c in cat_cols:
    vals = df[c].dropna().unique()
    print(f"\n--- {c} ({len(vals)} unique) ---")
    # Show all if few, else first 30
    show = sorted(vals, key=str) if len(vals) <= 40 else sorted(vals, key=str)[:30]
    for v in show:
        print(f"  '{v}'  (count={df[c].eq(v).sum()})")
    if len(vals) > 40:
        print(f"  ... and {len(vals) - 30} more")

# ── 8. Case-insensitive duplicates in categoricals ─────────────
print("\n\n===== CASING INCONSISTENCIES =====")
for c in cat_cols:
    lower_map = df[c].dropna().str.lower().value_counts()
    original_map = df[c].dropna().value_counts()
    # find values that have more than one casing variant
    lower_uniq = lower_map.index.tolist()
    for lv in lower_uniq:
        variants = [v for v in original_map.index if str(v).lower() == lv]
        if len(variants) > 1:
            detail = {v: int(original_map[v]) for v in variants}
            print(f"  Column '{c}': casing variants for '{lv}' -> {detail}")

# ── 9. Duplicates ───────────────────────────────────────────────
print("\n\n===== DUPLICATE ROWS =====")
full_dups = df.duplicated().sum()
print(f"Fully duplicated rows: {full_dups}")

# Check for duplicate track_id (if exists)
id_cols = [c for c in df.columns if "id" in c.lower() or "track" in c.lower()]
print(f"Potential ID columns: {id_cols}")
for ic in id_cols:
    dup_count = df[ic].duplicated().sum()
    print(f"  Duplicates in '{ic}': {dup_count}")
    if dup_count > 0 and dup_count < 20:
        dup_vals = df[df[ic].duplicated(keep=False)][ic].unique()
        print(f"    Duplicated values: {dup_vals[:10]}")

# ── 10. release_year inspection ─────────────────────────────────
print("\n\n===== RELEASE_YEAR INSPECTION =====")
if "release_year" in df.columns:
    ry = df["release_year"]
    print(f"dtype: {ry.dtype}")
    # Try numeric conversion
    ry_num = pd.to_numeric(ry, errors="coerce")
    non_numeric = ry[ry_num.isna() & ry.notna()]
    print(f"Non-numeric release_year values ({len(non_numeric)}):")
    if len(non_numeric) > 0:
        print(non_numeric.value_counts().to_string())
    # Numeric range
    valid_years = ry_num.dropna()
    if len(valid_years) > 0:
        print(f"\nNumeric range: {int(valid_years.min())} – {int(valid_years.max())}")
        # Suspicious years
        suspect = valid_years[(valid_years < 1900) | (valid_years > 2026)]
        if len(suspect) > 0:
            print(f"Suspicious years (<1900 or >2026): {suspect.value_counts().to_string()}")
else:
    print("No release_year column found.")

# ── 11. release_decade inspection ──────────────────────────────
print("\n\n===== RELEASE_DECADE INSPECTION =====")
if "release_decade" in df.columns:
    rd = df["release_decade"]
    print(f"dtype: {rd.dtype}")
    print(rd.value_counts().sort_index().to_string())
else:
    print("No release_decade column found.")

# ── 12. Consistency: release_year vs release_decade ─────────────
print("\n\n===== YEAR vs DECADE CONSISTENCY =====")
if "release_year" in df.columns and "release_decade" in df.columns:
    ry_num = pd.to_numeric(df["release_year"], errors="coerce")
    derived_decade = (ry_num // 10 * 10).astype("Int64")
    rd_num = pd.to_numeric(df["release_decade"], errors="coerce")
    mask = ry_num.notna() & rd_num.notna()
    mismatches = df[mask & (derived_decade != rd_num)]
    print(f"Rows with valid year & decade but mismatch: {len(mismatches)}")
    if len(mismatches) > 0 and len(mismatches) <= 20:
        print(mismatches[["release_year", "release_decade"]].to_string())
    elif len(mismatches) > 20:
        print(mismatches[["release_year", "release_decade"]].head(20).to_string())

# ── 13. Numeric outliers / suspicious values ────────────────────
print("\n\n===== NUMERIC OUTLIER CHECK =====")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
for c in numeric_cols:
    vals = df[c].dropna()
    q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 3 * iqr, q3 + 3 * iqr
    outliers = vals[(vals < lower) | (vals > upper)]
    if len(outliers) > 0:
        print(f"\n  '{c}': {len(outliers)} extreme outliers (outside 3×IQR)")
        print(f"    Range: {vals.min():.2f} – {vals.max():.2f}, Q1={q1:.2f}, Q3={q3:.2f}")
    else:
        print(f"  '{c}': no extreme outliers")

# ── 14. Popularity distribution ─────────────────────────────────
print("\n\n===== POPULARITY DISTRIBUTION =====")
if "popularity" in df.columns:
    pop = df["popularity"].dropna()
    print(f"Count: {len(pop)}")
    print(f"Mean: {pop.mean():.2f}, Median: {pop.median():.2f}, Std: {pop.std():.2f}")
    print(f"Min: {pop.min()}, Max: {pop.max()}")
    print(f"Skewness: {pop.skew():.3f}")
    # Bins
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    print(pd.cut(pop, bins=bins, right=True).value_counts().sort_index().to_string())

print("\n\nDONE — Phase 1 inspection complete.")
