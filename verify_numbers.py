import json
with open('output/analysis_results.json') as f:
    R = json.load(f)

print('H1 Overall Pearson r:', R['h1_overall']['pearson_r'])
print('H1 Overall p:', R['h1_overall']['pearson_p'])
print('H1 R-squared:', R['h1_overall']['r_squared'])
print('H1 Spearman:', R['h1_overall']['spearman_r'])
print('H2 Chi2:', R['h2_chi2']['chi2'])
print('H2 p:', R['h2_chi2']['p_value'])
print('H2 Cramers V:', R['h2_chi2']['cramers_v'])
print()

print('Energy bins:')
for b in R['h1_energy_bins']:
    print(f"  {b['energy_bin']}: mean={b['mean_pop']:.1f}, n={b['count']}")

print()
print('Sig genres count:', len(R['h1_significant_genres']))
pos = [g for g in R['h1_significant_genres'] if g['pearson_r'] > 0]
neg = [g for g in R['h1_significant_genres'] if g['pearson_r'] < 0]
print('Top 5 positive:')
for g in pos[:5]:
    print(f"  {g['genre']}: r={g['pearson_r']}, p={g['pearson_p']}")
print('Top 5 negative:')
for g in neg[-5:]:
    print(f"  {g['genre']}: r={g['pearson_r']}, p={g['pearson_p']}")

print()
print('Superstar %:')
for reg, data in R['h2_superstar_pct'].items():
    print(f"  {reg}: {data['pct']}% ({data['count']}/{data['total']})")
