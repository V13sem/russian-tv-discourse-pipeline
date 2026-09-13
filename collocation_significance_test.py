#   python collocation_significance_test.py


import pandas as pd
from statsmodels.stats.rates import test_poisson_2indep
from statsmodels.stats.multitest import multipletests

INPUT = r"collocations_period_comparison.csv"
OUTPUT = "collocation_significance_test.csv" 

df = pd.read_csv(INPUT)

EARLY_FREQ = "freq_lr_Early (2019-2021)"
LATE_FREQ = "freq_lr_Late (2022-2025)"

EARLY_NODE = "node_matches_Early (2019-2021)"
LATE_NODE = "node_matches_Late (2022-2025)"

SELECTED = [
        "поколение",
        "ребенок",
        "человек",
        "война",
        "мир"


]

df = df[
    (df["pattern"] == "zukunft")
    & (df["collocate"].isin(SELECTED))
]

results = []

for _, row in df.iterrows():

    early_freq = row[EARLY_FREQ]
    late_freq = row[LATE_FREQ]

    early_node = row[EARLY_NODE]
    late_node = row[LATE_NODE]

    # Nur testen, wenn beide Perioden eine Bezugsgröße haben
    if early_node == 0 or late_node == 0:
        continue

    test = test_poisson_2indep(
        count1=late_freq,
        exposure1=late_node,
        count2=early_freq,
        exposure2=early_node,
        compare="ratio"
    )

    results.append({
        "pattern": row["pattern"],
        "collocate": row["collocate"],
        "early_freq": early_freq,
        "late_freq": late_freq,
        "early_node_matches": early_node,
        "late_node_matches": late_node,
        "rate_ratio": test.ratio,
        "p_value": test.pvalue
    })


results_df = pd.DataFrame(results)

# Benjamini-Hochberg-Korrektur
results_df["p_adjusted"] = multipletests(
    results_df["p_value"],
    method="fdr_bh"
)[1]

results_df["significant"] = results_df["p_adjusted"] < 0.05

results_df = results_df.sort_values("p_adjusted")

print(results_df.to_string(index=False))

results_df.to_csv(
    "collocation_significance_results.csv",
    index=False,
    encoding="utf-8-sig"
)