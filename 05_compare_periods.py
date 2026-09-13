#   python NEW_compare_periods.py
import pandas as pd
from pathlib import Path
import numpy as np


# Vergleich der beiden Perioden:
# 2019-2021 vs. 2022-2025
#
# Alle beobachteten Kollokationen bleiben in den Rohdaten erhalten.
# Sehr seltene Kollokationen können für die Auswertung gefiltert werden.
# Prozentwerte bei zu geringer Early-Häufigkeit werden nicht interpretiert.
# Die Vergleichskennzahlen dient zur Identifikation auffälliger Veränderungen.


INPUT_PERIOD_CSV = Path(
    ""
)

OUTPUT_DIR = Path(
    ""
)

OUTPUT_COMPARISON_CSV = (
    OUTPUT_DIR / "collocations_period_comparison.csv"
)
OUTPUT_COMPARISON_EXCEL_CSV = (OUTPUT_DIR / "collocations_period_comparison_excel.csv")

# Kontrollregeln für FreqLR:

MIN_FREQ_IN_ANY_PERIOD = 2
# -> Der Kollokator muss in mindestens einer der beiden Perioden mindestens zweimal innerhalb 
# des L5/R5-Fensters vorkommen.

MIN_RANGE_IN_ANY_PERIOD = 1
#-> Mind in einem Dokument muss das Kollokat vorkommen -> später varieren

MIN_EARLY_FREQ_FOR_PERCENT = 2
# -> muss evtl an gepasst werden

MIN_NODE_MATCHES_IN_PERIOD = 20
# -> 


def compare_periods():

    df_period = pd.read_csv(INPUT_PERIOD_CSV)

    # Formt die Periodentabelle so um, dass Early und Late
    # für jedes Pattern-Kollokator-Paar nebeneinander stehen.
    
    # Es werden sowohl die normalisierte Rate als auch
    # die absolute Häufigkeit und Range übernommen.
    comparison = df_period.pivot_table(
        index=["pattern", "collocate"], # -> Jede Zeile wird eindeutig durch die Kombination
# aus Pattern und Kollokator definiert.
        columns="period",
        values=[
            "collocate_per_10k_node_matches",
            "freq_lr",
            "range",
            "node_matches"
        ],
        aggfunc="sum", # -> Falls dieselbe Kombination aus Pattern, Kollokator
        # und Periode mehrfach vorkommt, werden die Werte addiert.
        fill_value=0 #-> falls in einer Periode pattern vorkommt und in der andere nicht, soll 0 sein
    )

    #https://pandas.pydata.org/docs/reference/api/pandas.pivot_table.html
    # Die mehrstufigen Spaltennamen des Pivot-Tables
    # werden in einfache Spaltennamen umgewandelt.
    # -> Für den direkten Vergleich werden die Daten über eine Pivot-Tabelle in ein Wide-Format überführt.
    comparison.columns = [
        f"{value}_{period}"
        for value, period in comparison.columns
    ]

    #wird aus der collocations_periods.csv gelesen und gespeichert
    early_rate = comparison[
        "collocate_per_10k_node_matches_Early (2019-2021)"
    ]

    late_rate = comparison[
        "collocate_per_10k_node_matches_Late (2022-2025)"
    ]

    early_freq = comparison[
        "freq_lr_Early (2019-2021)"
    ]

    late_freq = comparison[
        "freq_lr_Late (2022-2025)"
    ]

    early_range = comparison[
        "range_Early (2019-2021)"
    ]

    late_range = comparison[
        "range_Late (2022-2025)"
    ]

    early_node_matches = comparison[
    "node_matches_Early (2019-2021)"
    ]

    late_node_matches = comparison[
    "node_matches_Late (2022-2025)"
    ]
    
# -----------------------------------    
#Für die Mindesthäufigkeit genügt es, wenn ein Kollokator in einer der beiden Perioden die definierte Schwelle erreicht, 
#da auch neu auftretende oder verschwindende Kollokationen analytisch relevant sein können.
# -----------------------------------  

    # Mindestens eine der beiden Perioden muss
    # die Mindesthäufigkeit erreichen.
    comparison["Passes_Min_Freq"] = (
        (early_freq >= MIN_FREQ_IN_ANY_PERIOD)
        | (late_freq >= MIN_FREQ_IN_ANY_PERIOD)
    )

    # Mindestens eine der beiden Perioden muss
    # die Mindest-Range erreichen.
    comparison["Passes_Min_Range"] = (
        (early_range >= MIN_RANGE_IN_ANY_PERIOD)
        | (late_range >= MIN_RANGE_IN_ANY_PERIOD)
    )

    comparison["Passes_Min_Node_Matches"] = (
        (early_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
        & (late_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
    )

    # Markiert Kollokationen, die beide Bedingungen erfüllen.
    # Die übrigen Zeilen bleiben trotzdem in der CSV erhalten.
    comparison["Included"] = (
        comparison["Passes_Min_Freq"]
        & comparison["Passes_Min_Range"]
        & comparison["Passes_Min_Node_Matches"]
    )
        



    # Differenz der normalisierten Kollokationsraten.
    comparison["Change"] = (late_rate - early_rate).round(2)

    # Prozentuale Veränderung wird nur berechnet,
    # wenn Early nicht null ist und mindestens die
    # definierte Anzahl tatsächlicher Treffer besitzt.
    comparison["Change_Percent"] = (
        ((late_rate - early_rate) / early_rate * 100)
        .where(
            (early_rate > 0)
            & (early_freq >= MIN_EARLY_FREQ_FOR_PERCENT)
            & (early_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
            & (late_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
        )
        .round(2)
    )

    # Verhältnis Late zu Early.
    # Auch dieses wird nur bei ausreichender
    # Early-Häufigkeit berechnet.
    comparison["Ratio"] = (
        (late_rate / early_rate)
        .where(
            (early_rate != 0) # -> Divison durch 0 verhindern
            & (early_freq >= MIN_EARLY_FREQ_FOR_PERCENT)
            & (early_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
            & (late_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
        )
        .round(2)
    )
    # Ratio = 1    → gleich
    # Ratio = 2    → doppelt so hoch
    # Ratio = 3    → dreimal so hoch
    # Ratio = 0,5  → halb so hoch
    # Ratio = 0,25 → nur ein Viertel so hoch
#--------------------------------------------------------------------

    # Log-Ratio:
    # logarithmierte und symmetrische Darstellung
    # des Verhältnisses zwischen Late und Early.
    # LogRatio = log2(Late/Early)
    comparison["Log_Ratio"]=(
        (late_rate / early_rate).where(
            (early_rate > 0)
            & (late_rate > 0)
            & (early_freq >= MIN_EARLY_FREQ_FOR_PERCENT)
            & (early_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
            & (late_node_matches >= MIN_NODE_MATCHES_IN_PERIOD)
        )
        .apply(np.log2)
        .round(2)
    )
    
    comparison = comparison.sort_values(
        "Change",
        ascending=False # Größte positive Veränderungen zuerst.
    )
    diagnostic_columns = [
        "Passes_Min_Freq",
        "Passes_Min_Range",
        "Passes_Min_Node_Matches"
    ]

    other_columns = [
        column
        for column in comparison.columns
        if column not in diagnostic_columns
]

    comparison = comparison[other_columns + diagnostic_columns]

    comparison.to_csv(
        OUTPUT_COMPARISON_CSV,
        encoding="utf-8-sig"
    )
    comparison.to_csv(
        OUTPUT_COMPARISON_EXCEL_CSV,
        encoding="utf-8-sig",
        sep=";",
        decimal=","
    )

    print(
        f"Periodenvergleich gespeichert: "
        f"{OUTPUT_COMPARISON_CSV}"
    )

    # Für die Konsolenausgabe werden nur Kollokationen
    # berücksichtigt, die die Mindestbedingungen erfüllen.
    comparison_filtered = comparison[
        comparison["Included"]
    ]

    print("\n" + "=" * 70)
    print(
        "TOP 20 GROWING COLLOCATES "
        "(2022-2025 vs 2019-2021)"
    )
    print("=" * 70)

    top_growing = comparison_filtered.nlargest(
        20,
        "Change"
    )

    print(
        top_growing[
            [
                "collocate_per_10k_node_matches_Early (2019-2021)",
                "collocate_per_10k_node_matches_Late (2022-2025)",
                "freq_lr_Early (2019-2021)",
                "freq_lr_Late (2022-2025)",
                "range_Early (2019-2021)",
                "range_Late (2022-2025)",
                "Change",
                "Change_Percent",
                "Ratio",
                "Log_Ratio"
            ]
        ].to_string()
    )

    print("\n" + "=" * 70)
    print(
        "TOP 20 DECLINING COLLOCATES "
        "(2022-2025 vs 2019-2021)"
    )
    print("=" * 70)

    top_declining = comparison_filtered.nsmallest(
        20,
        "Change"
    )

    print(
        top_declining[
            [
                "collocate_per_10k_node_matches_Early (2019-2021)",
                "collocate_per_10k_node_matches_Late (2022-2025)",
                "freq_lr_Early (2019-2021)",
                "freq_lr_Late (2022-2025)",
                "range_Early (2019-2021)",
                "range_Late (2022-2025)",
                "Change",
                "Change_Percent",
                "Ratio"
            ]
        ].to_string()
    )


if __name__ == "__main__":
    compare_periods()
