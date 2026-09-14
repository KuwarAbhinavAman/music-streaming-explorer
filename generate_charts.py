"""
Phase 6-7: Generate charts and build PowerPoint
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import json
import os

# ── Setup ───────────────────────────────────────────────────────
OUT_DIR = "output"
CHART_DIR = os.path.join(OUT_DIR, "charts")
os.makedirs(CHART_DIR, exist_ok=True)

df = pd.read_csv(os.path.join(OUT_DIR, "cleaned_data.csv"))
with open(os.path.join(OUT_DIR, "analysis_results.json"), "r") as f:
    results = json.load(f)

# ── Color Palette ───────────────────────────────────────────────
DARK_BG = "#1a1a2e"
CARD_BG = "#16213e"
ACCENT_BLUE = "#0f3460"
ACCENT_TEAL = "#00b4d8"
ACCENT_PURPLE = "#7b2cbf"
ACCENT_CORAL = "#e76f51"
ACCENT_GREEN = "#06d6a0"
ACCENT_GOLD = "#ffd166"
GRID_COLOR = "#2a2a4a"
TEXT_COLOR = "#e0e0e0"
WHITE = "#ffffff"

# Color palette for regions
REGION_COLORS = {
    "Asia Pacific": "#00b4d8",
    "Europe": "#7b2cbf",
    "Latin America": "#e76f51",
    "Middle East & Africa": "#ffd166",
    "North America": "#06d6a0",
}

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'Arial', 'Helvetica'],
    'font.size': 11,
    'axes.facecolor': CARD_BG,
    'figure.facecolor': DARK_BG,
    'text.color': TEXT_COLOR,
    'axes.labelcolor': TEXT_COLOR,
    'xtick.color': TEXT_COLOR,
    'ytick.color': TEXT_COLOR,
})

# ================================================================
# CHART 1: Energy vs Popularity (binned bar chart)
# ================================================================
print("Generating Chart 1: Energy vs Popularity...")
bins = results["h1_energy_bins"]
fig, ax = plt.subplots(figsize=(10, 5.5))

x = range(len(bins))
means = [b["mean_pop"] for b in bins]
labels = [b["energy_bin"] for b in bins]
counts = [b["count"] for b in bins]

bars = ax.bar(x, means, color=ACCENT_TEAL, alpha=0.85, edgecolor=ACCENT_TEAL, linewidth=0.5, width=0.7)

# Add count labels on bars
for i, (bar, count) in enumerate(zip(bars, counts)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'n={count}', ha='center', va='bottom', fontsize=8, color=TEXT_COLOR, alpha=0.7)

ax.set_xlabel("Energy Level", fontsize=12, fontweight='bold')
ax.set_ylabel("Mean Popularity Score", fontsize=12, fontweight='bold')
ax.set_title("Mean Popularity by Energy Level", fontsize=14, fontweight='bold', color=WHITE, pad=15)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
ax.set_ylim(0, 45)
ax.grid(axis='y', alpha=0.2, color=GRID_COLOR)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(GRID_COLOR)
ax.spines['bottom'].set_color(GRID_COLOR)

# Add correlation annotation
r = results["h1_overall"]["pearson_r"]
p = results["h1_overall"]["pearson_p"]
ax.text(0.98, 0.95, f'Pearson r = {r:.3f}\nR² = {r**2:.4f}\np = {p:.3f}',
        transform=ax.transAxes, fontsize=10, va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_BLUE, alpha=0.8, edgecolor=ACCENT_TEAL),
        color=WHITE)

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h1_energy_popularity.png"), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved h1_energy_popularity.png")

# ================================================================
# CHART 2: Energy-Popularity Correlation by Genre (top/bottom)
# ================================================================
print("Generating Chart 2: Genre Correlations...")
all_genre_corr = results["h1_genre_corr_all"]
# Get top 8 and bottom 8 by pearson_r
sorted_genres = sorted(all_genre_corr, key=lambda x: x["pearson_r"])
bottom8 = sorted_genres[:8]
top8 = sorted_genres[-8:][::-1]
show_genres = top8 + bottom8

fig, ax = plt.subplots(figsize=(10, 6))
genres = [g["genre"] for g in show_genres]
r_vals = [g["pearson_r"] for g in show_genres]
colors = [ACCENT_TEAL if r > 0 else ACCENT_CORAL for r in r_vals]
sig_markers = ['*' if g["pearson_p"] < 0.05 else '' for g in show_genres]

bars = ax.barh(range(len(genres)), r_vals, color=colors, alpha=0.8, edgecolor='none', height=0.6)

for i, (r, genre, sig) in enumerate(zip(r_vals, genres, sig_markers)):
    label = f'{r:+.3f}{sig}'
    offset = 0.01 if r >= 0 else -0.01
    ha = 'left' if r >= 0 else 'right'
    ax.text(r + offset, i, label, ha=ha, va='center', fontsize=9, color=TEXT_COLOR)

ax.set_yticks(range(len(genres)))
ax.set_yticklabels(genres, fontsize=9)
ax.set_xlabel("Pearson Correlation (r)", fontsize=12, fontweight='bold')
ax.set_title("Energy-Popularity Correlation by Genre\n(Top 8 Positive & Bottom 8 Negative)", 
             fontsize=13, fontweight='bold', color=WHITE, pad=15)
ax.axvline(x=0, color=TEXT_COLOR, linewidth=0.5, alpha=0.5)
ax.set_xlim(-0.35, 0.35)
ax.grid(axis='x', alpha=0.15, color=GRID_COLOR)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(GRID_COLOR)
ax.spines['bottom'].set_color(GRID_COLOR)
ax.invert_yaxis()

# Legend
ax.text(0.98, 0.02, '* p < 0.05', transform=ax.transAxes, fontsize=9,
        ha='right', va='bottom', color=ACCENT_GOLD, style='italic')

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h1_genre_correlations.png"), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved h1_genre_correlations.png")

# ================================================================
# CHART 3: Superstar Distribution by Region
# ================================================================
print("Generating Chart 3: Superstar Regional Distribution...")
superstar_data = results["h2_superstar_pct"]
regions = sorted(superstar_data.keys(), key=lambda r: superstar_data[r]["pct"], reverse=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), gridspec_kw={'width_ratios': [1.2, 1]})

# Left: Superstar % by region
pcts = [superstar_data[r]["pct"] for r in regions]
bar_colors = [REGION_COLORS.get(r, ACCENT_TEAL) for r in regions]
bars = ax1.barh(range(len(regions)), pcts, color=bar_colors, alpha=0.85, height=0.55)

for i, (bar, r) in enumerate(zip(bars, regions)):
    count = superstar_data[r]["count"]
    total = superstar_data[r]["total"]
    ax1.text(bar.get_width() + 0.15, i, f'{bar.get_width():.1f}%  ({count}/{total})',
             ha='left', va='center', fontsize=10, color=TEXT_COLOR)

ax1.set_yticks(range(len(regions)))
ax1.set_yticklabels(regions, fontsize=10)
ax1.set_xlabel("Superstar Artist %", fontsize=11, fontweight='bold')
ax1.set_title("Superstar Proportion by Region", fontsize=13, fontweight='bold', color=WHITE, pad=15)
ax1.set_xlim(0, 10)
ax1.grid(axis='x', alpha=0.15, color=GRID_COLOR)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['left'].set_color(GRID_COLOR)
ax1.spines['bottom'].set_color(GRID_COLOR)
ax1.invert_yaxis()

# Right: Full tier breakdown stacked
crosstab_pct = results["h2_crosstab_pct"]
tiers = ["Emerging", "Rising", "Established", "Superstar"]
tier_colors = [ACCENT_BLUE, ACCENT_TEAL, ACCENT_GREEN, ACCENT_GOLD]

region_order = regions
bottom = np.zeros(len(region_order))
for tier, color in zip(tiers, tier_colors):
    vals = []
    for r_data in crosstab_pct:
        if r_data["market_region"] in region_order:
            vals.append(r_data.get(tier, 0))
    # Reorder vals to match region_order
    vals_ordered = []
    for reg in region_order:
        for r_data in crosstab_pct:
            if r_data["market_region"] == reg:
                vals_ordered.append(r_data.get(tier, 0))
                break
    ax2.barh(range(len(region_order)), vals_ordered, left=bottom, color=color, alpha=0.85, height=0.55, label=tier)
    bottom += np.array(vals_ordered)

ax2.set_yticks(range(len(region_order)))
ax2.set_yticklabels(region_order, fontsize=10)
ax2.set_xlabel("% of Tracks", fontsize=11, fontweight='bold')
ax2.set_title("Artist Tier Distribution by Region", fontsize=13, fontweight='bold', color=WHITE, pad=15)
ax2.legend(loc='lower right', fontsize=8, framealpha=0.3)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['left'].set_color(GRID_COLOR)
ax2.spines['bottom'].set_color(GRID_COLOR)
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h2_superstar_regions.png"), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved h2_superstar_regions.png")

# ================================================================
# CHART 4: Popularity by Artist Tier
# ================================================================
print("Generating Chart 4: Popularity by Artist Tier...")
tier_data = results["tier_popularity"]
tiers_sorted = sorted(tier_data, key=lambda x: x["mean_pop"], reverse=True)

fig, ax = plt.subplots(figsize=(8, 5))
tier_names = [t["artist_tier"] for t in tiers_sorted]
tier_means = [t["mean_pop"] for t in tiers_sorted]
tier_colors_chart = [ACCENT_GOLD, ACCENT_GREEN, ACCENT_TEAL, ACCENT_BLUE]

bars = ax.bar(tier_names, tier_means, color=tier_colors_chart, alpha=0.85, width=0.5, edgecolor='none')
for bar, t in zip(bars, tiers_sorted):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f'{t["mean_pop"]:.1f}\n(n={t["count"]})',
            ha='center', va='bottom', fontsize=10, color=TEXT_COLOR, fontweight='bold')

ax.set_ylabel("Mean Popularity Score", fontsize=12, fontweight='bold')
ax.set_title("Mean Popularity by Artist Tier", fontsize=14, fontweight='bold', color=WHITE, pad=15)
ax.set_ylim(0, 70)
ax.grid(axis='y', alpha=0.15, color=GRID_COLOR)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(GRID_COLOR)
ax.spines['bottom'].set_color(GRID_COLOR)

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "popularity_by_tier.png"), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved popularity_by_tier.png")

# ================================================================
# CHART 5: Danceability Over Decades
# ================================================================
print("Generating Chart 5: Danceability Over Decades...")
decade_data = results["h3_decade_stats"]

fig, ax = plt.subplots(figsize=(9, 5))
decades = [d["decade"] for d in decade_data]
means = [d["mean_dance"] for d in decade_data]
counts = [d["count"] for d in decade_data]
stds = [d["std_dance"] for d in decade_data]
sems = [s / np.sqrt(c) for s, c in zip(stds, counts)]

ax.plot(decades, means, color=ACCENT_TEAL, marker='o', linewidth=2.5, markersize=8, zorder=3)
ax.fill_between(range(len(decades)), 
                [m - 1.96*se for m, se in zip(means, sems)],
                [m + 1.96*se for m, se in zip(means, sems)],
                alpha=0.2, color=ACCENT_TEAL)

for i, (d, m, c) in enumerate(zip(decades, means, counts)):
    ax.annotate(f'{m:.3f}\n(n={c})', (i, m), textcoords="offset points", 
                xytext=(0, 12), ha='center', fontsize=8, color=TEXT_COLOR)

ax.set_xlabel("Decade", fontsize=12, fontweight='bold')
ax.set_ylabel("Mean Danceability", fontsize=12, fontweight='bold')
ax.set_title("Mean Danceability by Decade (with 95% CI)", fontsize=14, fontweight='bold', color=WHITE, pad=15)
ax.set_ylim(0.35, 0.65)
ax.grid(axis='y', alpha=0.15, color=GRID_COLOR)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color(GRID_COLOR)
ax.spines['bottom'].set_color(GRID_COLOR)

# Add trend annotation
h3_trend = results.get("h3_trend", {})
if h3_trend:
    ax.text(0.98, 0.05, f'Spearman rho = {h3_trend["spearman_r"]:.3f}\np < 0.001',
            transform=ax.transAxes, fontsize=10, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor=ACCENT_BLUE, alpha=0.8, edgecolor=ACCENT_TEAL),
            color=WHITE)

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h3_danceability_decades.png"), dpi=200, bbox_inches='tight')
plt.close()
print("  Saved h3_danceability_decades.png")

print("\n[DONE] All charts generated successfully!")
