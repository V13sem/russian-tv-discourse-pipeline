# python visualize_frequency_per_period_heatmap.py



from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


CSV_FILE = Path ("frequency_by_year_raw.csv")

df = pd.read_csv(CSV_FILE)

patterns = [

    # Soziale Reproduktion
    "familie_per_10k",
    "kinder_per_10k",
    "mutter_mutterschaft_per_10k",
    "vater_vaterschaft_per_10k",
    "eltern_elternschaft_per_10k",
    "ehe_per_10k",
    "erziehung_per_10k",

    # Körperliche Reproduktion
    "geburt_gebaeren_per_10k",
    "schwangerschaft_per_10k",
    "abtreibung_per_10k",

    # Geschlecht und Rollen
    "frau_per_10k",
    "mann_per_10k",
    "muetterlich_vaeterlich_per_10k",

    # Demografie und politische Rahmung
    "geburtenrate_per_10k",
    "bevoelkerungszahl_per_10k",
    "demografie_per_10k",
    "volk_per_10k",
    "zukunft_per_10k",
    "werte_moral_tradition_per_10k",
    "nation_national_per_10k",
    "patriotismus_identitaet_souveraenitaet_per_10k",
    "west_liberal_lgbt_per_10k",
    "propaganda_per_10k"
]

labels = {

    "familie_per_10k": "Familie",
    "kinder_per_10k": "Kinder",
    "mutter_mutterschaft_per_10k": "Mutter / Mutterschaft",
    "vater_vaterschaft_per_10k": "Vater / Vaterschaft",
    "eltern_elternschaft_per_10k": "Eltern / Elternschaft",
    "ehe_per_10k": "Ehe",
    "erziehung_per_10k": "Erziehung",

    "geburt_gebaeren_per_10k": "Geburt / Gebären",
    "schwangerschaft_per_10k": "Schwangerschaft",
    "abtreibung_per_10k": "Abtreibung",

    "frau_per_10k": "Frau",
    "mann_per_10k": "Mann",
    "muetterlich_vaeterlich_per_10k": "Mütterlich / Väterlich",

    "geburtenrate_per_10k": "Geburtenrate",
    "bevoelkerungszahl_per_10k": "Bevölkerungszahl",
    "demografie_per_10k": "Demografie",
    "volk_per_10k": "Volk",
    "zukunft_per_10k": "Zukunft",
    "werte_moral_tradition_per_10k": "Werte / Moral / Tradition",
    "nation_national_per_10k": "Nation / National",
    "patriotismus_identitaet_souveraenitaet_per_10k": "Patriotismus / Identität / Souveränität",
    "west_liberal_lgbt_per_10k": "West / Liberal / LGBT",
    "propaganda_per_10k": "Propaganda"
}

#https://seaborn.pydata.org/generated/seaborn.heatmap.html

df["period"] = np.where(
    df["year"] <= 2021,
    "Frühe Periode (2019–2021)",
    "Späte Periode (2022–2025)"
)

period_values = {}

#Lazy Ansatz: aus dem alten Code kopiere die Pattern aber benötigt wird die absolute Zahlen 
# aus der Tabelle.
for pattern in patterns:
    raw_pattern = pattern.replace("_per_10k", "")


    period_values[pattern] = (
        df.groupby("period")[raw_pattern].sum()
        /
        df.groupby("period")["tokens"].sum()*10000
    )

period_table = pd.DataFrame(period_values).T

# Reihenfolge der Periode festlegen
period_table = period_table[
    ["Frühe Periode (2019–2021)", 
     "Späte Periode (2022–2025)"]]

period_table.index = [
    labels.get(pattern, pattern)
    for pattern in period_table.index
]

print(period_table.round(3))

# Heatmap erstellen

plt.figure(figsize=(9, 10))

sns.heatmap(
    period_table,
    annot=True,
    fmt=".3f",
    cmap="Purples",
    cbar_kws={"label":"Treffer pro 10.000 Tokens"}
)

plt.title("Entwicklung reproduktionsbezogener Pattern in zwei Perioden (2019–2021 vs. 2022–2025)")
plt.xlabel("Untersuchungsperiode")
plt.ylabel("Pattern")
plt.tight_layout()
OUTPUT_FILE = Path(
    "C:/Users/PeppermintButler/Desktop/Bachelorarbeit/Audio/"
    "frequency_per_period_heatmap.png"
)

plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches="tight")
#plt.show()



