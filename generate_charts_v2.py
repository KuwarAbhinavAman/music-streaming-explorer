"""
Revised Charts — Light, Clean, Professional
White backgrounds, restrained blue, sparse magenta accent
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
CHART_DIR = os.path.join(OUT_DIR, "charts_v2")
os.makedirs(CHART_DIR, exist_ok=True)

with open(os.path.join(OUT_DIR, "analysis_results.json"), "r") as f:
    results = json.load(f)

# ── Colour Palette (light, corporate) ──────────────────────────
PRIMARY_BLUE   = "#1769AA"
DEEP_BLUE      = "#174A73"
SOFT_BLUE      = "#EAF4FA"
LIGHT_BLUE_BG  = "#F5F9FC"
MAGENTA        = "#B83A7A"
SOFT_MAGENTA   = "#F8EDF4"
CHARCOAL       = "#27343D"
MUTED_GREY     = "#6B7280"
LIGHT_BORDER   = "#DCE6EC"
WHITE          = "#FFFFFF"
LIGHT_GRID     = "#E8EDF2"

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Segoe UI', 'Calibri', 'Arial'],
    'font.size': 10,
    'axes.facecolor': WHITE,
    'figure.facecolor': WHITE,
    'text.color': CHARCOAL,
    'axes.labelcolor': CHARCOAL,
    'xtick.color': MUTED_GREY,
    'ytick.color': MUTED_GREY,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# ================================================================
# CHART 1: Energy vs Popularity (binned bar chart)
# ================================================================
print("Chart 1: Energy vs Popularity...")
bins = results["h1_energy_bins"]
fig, ax = plt.subplots(figsize=(9, 4.5))

x = range(len(bins))
means = [b["mean_pop"] for b in bins]
labels = [b["energy_bin"] for b in bins]
counts = [b["count"] for b in bins]

# All bars blue, no special highlight needed here
bars = ax.bar(x, means, color=PRIMARY_BLUE, alpha=0.75, width=0.65, edgecolor='none')

# Sample size labels above bars
for i, (bar, count) in enumerate(zip(bars, counts)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.4,
            f'n={count}', ha='center', va='bottom', fontsize=7.5, color=MUTED_GREY)

ax.set_xlabel("Energy Level", fontsize=11, color=CHARCOAL)
ax.set_ylabel("Mean Popularity", fontsize=11, color=CHARCOAL)
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=8.5)
ax.set_ylim(0, 42)
ax.grid(axis='y', alpha=0.4, color=LIGHT_GRID, linewidth=0.5)
ax.spines['left'].set_color(LIGHT_BORDER)
ax.spines['bottom'].set_color(LIGHT_BORDER)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h1_energy_popularity.png"), dpi=220, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
plt.close()
print("  Saved h1_energy_popularity.png")

# ================================================================
# CHART 2: Genre Correlations (horizontal bars)
# ================================================================
print("Chart 2: Genre Correlations...")
sig_genres = results["h1_significant_genres"]
pos = [g for g in sig_genres if g["pearson_r"] > 0]
neg = [g for g in sig_genres if g["pearson_r"] < 0]

# Top 5 positive and top 5 negative
show_pos = sorted(pos, key=lambda x: x["pearson_r"], reverse=True)[:5]
show_neg = sorted(neg, key=lambda x: x["pearson_r"])[:5]
show_genres = show_pos + show_neg

fig, ax = plt.subplots(figsize=(8.5, 5))
genres = [g["genre"] for g in show_genres]
r_vals = [g["pearson_r"] for g in show_genres]

# Blue for positive, magenta for negative
colors = [PRIMARY_BLUE if r > 0 else MAGENTA for r in r_vals]

bars = ax.barh(range(len(genres)), r_vals, color=colors, alpha=0.75, height=0.55, edgecolor='none')

for i, (r, genre) in enumerate(zip(r_vals, genres)):
    offset = 0.008 if r >= 0 else -0.008
    ha = 'left' if r >= 0 else 'right'
    ax.text(r + offset, i, f'{r:+.3f}', ha=ha, va='center', fontsize=9, color=CHARCOAL)

ax.set_yticks(range(len(genres)))
ax.set_yticklabels(genres, fontsize=9.5)
ax.set_xlabel("Correlation with Popularity (r)", fontsize=10.5, color=CHARCOAL)
ax.axvline(x=0, color=LIGHT_BORDER, linewidth=0.8)
ax.set_xlim(-0.48, 0.48)
ax.grid(axis='x', alpha=0.3, color=LIGHT_GRID, linewidth=0.5)
ax.spines['left'].set_color(LIGHT_BORDER)
ax.spines['bottom'].set_color(LIGHT_BORDER)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h1_genre_correlations.png"), dpi=220, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
plt.close()
print("  Saved h1_genre_correlations.png")

# ================================================================
# CHART 3: Superstar % by Region (horizontal bar)
# ================================================================
print("Chart 3: Superstar Regional Distribution...")
superstar_data = results["h2_superstar_pct"]
regions = sorted(superstar_data.keys(), key=lambda r: superstar_data[r]["pct"], reverse=True)

fig, ax = plt.subplots(figsize=(7.5, 3.8))

pcts = [superstar_data[r]["pct"] for r in regions]
bar_colors = [PRIMARY_BLUE] * len(regions)

bars = ax.barh(range(len(regions)), pcts, color=bar_colors, alpha=0.75, height=0.5, edgecolor='none')

for i, (bar, r) in enumerate(zip(bars, regions)):
    count = superstar_data[r]["count"]
    total = superstar_data[r]["total"]
    ax.text(bar.get_width() + 0.12, i, f'{bar.get_width():.1f}%  ({count} / {total})',
            ha='left', va='center', fontsize=9.5, color=CHARCOAL)

ax.set_yticks(range(len(regions)))
ax.set_yticklabels(regions, fontsize=10)
ax.set_xlabel("Superstar Tracks (%)", fontsize=10.5, color=CHARCOAL)
ax.set_xlim(0, 8.5)
ax.grid(axis='x', alpha=0.3, color=LIGHT_GRID, linewidth=0.5)
ax.spines['left'].set_color(LIGHT_BORDER)
ax.spines['bottom'].set_color(LIGHT_BORDER)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)
ax.invert_yaxis()

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "h2_superstar_regions.png"), dpi=220, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
plt.close()
print("  Saved h2_superstar_regions.png")

# ================================================================
# CHART 4: Popularity by Artist Tier
# ================================================================
print("Chart 4: Popularity by Artist Tier...")
tier_data = results["tier_popularity"]
tiers_sorted = sorted(tier_data, key=lambda x: x["mean_pop"], reverse=True)

fig, ax = plt.subplots(figsize=(7, 4))
tier_names = [t["artist_tier"] for t in tiers_sorted]
tier_means = [t["mean_pop"] for t in tiers_sorted]

# Highlight Superstar with magenta, rest blue
tier_colors = [MAGENTA if t == "Superstar" else PRIMARY_BLUE for t in tier_names]
alphas = [0.85 if t == "Superstar" else 0.65 for t in tier_names]

for i, (name, mean, color, alpha) in enumerate(zip(tier_names, tier_means, tier_colors, alphas)):
    bar = ax.bar(i, mean, color=color, alpha=alpha, width=0.5, edgecolor='none')

for i, t in enumerate(tiers_sorted):
    ax.text(i, t["mean_pop"] + 1.0,
            f'{t["mean_pop"]:.1f}', ha='center', va='bottom',
            fontsize=11, color=CHARCOAL, fontweight='bold')
    ax.text(i, t["mean_pop"] + 5.5,
            f'n={t["count"]}', ha='center', va='bottom',
            fontsize=8, color=MUTED_GREY)

ax.set_xticks(range(len(tier_names)))
ax.set_xticklabels(tier_names, fontsize=10)
ax.set_ylabel("Mean Popularity", fontsize=10.5, color=CHARCOAL)
ax.set_ylim(0, 95)
ax.grid(axis='y', alpha=0.3, color=LIGHT_GRID, linewidth=0.5)
ax.spines['left'].set_color(LIGHT_BORDER)
ax.spines['bottom'].set_color(LIGHT_BORDER)
ax.spines['left'].set_linewidth(0.5)
ax.spines['bottom'].set_linewidth(0.5)

plt.tight_layout()
plt.savefig(os.path.join(CHART_DIR, "popularity_by_tier.png"), dpi=220, bbox_inches='tight',
            facecolor=WHITE, edgecolor='none')
plt.close()
print("  Saved popularity_by_tier.png")

print("\n[DONE] All revised charts generated.")
