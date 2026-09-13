# https://www.youtube.com/watch?v=921IgQ6T6_4


import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.multitest import multipletests

INPUT = "frequency_by_year_raw.csv"

df = pd.read_csv(INPUT)

PATTERNS = [
    "familie",
    "kinder",
    "mutter_mutterschaft",
    "vater_vaterschaft",
    "muetterlich_vaeterlich",
    "eltern_elternschaft",
    "frau",
    "mann",
    "ehe",
    "zuhause_haeuslichkeit",
    "geburt_gebaeren",
    "schwangerschaft",
    "schwangerschaftsabbruch",
    "abtreibung",
    "sorge_fuersorge",
    "verantwortung_pflicht",
    "erziehung",
    "reproduktion_fachbegriff",
    "unfruchtbarkeit",
    "empfaengnis",
    "demografie",
    "bevoelkerung",
    "volk",
    "generation",
    "geburtenrate",
    "mutterschaftskapital",
    "zukunft",
    "staat",
    "nation_national",
    "gesetz",
    "regierung",
    "duma",
    "land_staatlicher_raum",
    "russland_russisch",
    "bevoelkerungszahl",
    "bevoelkerungszuwachs",
    "bevoelkerungsrueckgang",
    "demografische_krise",
    "demografischer_mangel_verlust",
    "aussterben",
    "werte_moral_tradition",
    "geistig_religioes",
    "norm_ordnung_kultur_gesellschaft",
    "patriotismus_identitaet_souveraenitaet",
    "heimat_vaterland",
    "west_liberal_lgbt",
    "propaganda",
]

early = df[df["year"].between(2019, 2021)]
late = df[df["year"].between(2022, 2025)]

early_tokens = early["tokens"].sum()
late_tokens = late["tokens"].sum()

results = []

for pattern in PATTERNS:

    early_freq = early[pattern].sum()
    late_freq = late[pattern].sum()

    table = [
        [early_freq, early_tokens - early_freq],
        [late_freq, late_tokens - late_freq]
    ]

    chi2, p_value, dof, expected = chi2_contingency(table)

    results.append({
        "pattern": pattern,
        "early_freq": early_freq,
        "late_freq": late_freq,
        "p_value": p_value
    })

results_df = pd.DataFrame(results)

# Von ChatGPT-5.6 Sol verändert
# Korrektur, weil viele Patterns getestet werden
# ***False Discovery Rate, Benjamini Hochberg***
results_df["p_adjusted"] = multipletests(
    results_df["p_value"],
    method="fdr_bh"
)[1]

results_df["significant"] = results_df["p_adjusted"] < 0.05

results_df = results_df.sort_values("p_adjusted")

print(results_df.to_string(index=False))

results_df.to_csv(
    "frequency_significance_results.csv",
    index=False,
    encoding="utf-8-sig"
)