# python visualize_frequency_heatmap.py

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


CSV_FILE = Path ("C:/Users/PeppermintButler/Desktop/Bachelorarbeit/Audio/frequency_by_year_raw.csv")

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

heatmap_data = df.set_index("year")[patterns].T

#Erstellt mit ChatGPT -5.6
heatmap_data.index=[
    labels.get(pattern, pattern)
    for pattern in heatmap_data.index
]

plt.figure(figsize=(14, 10))
sns.heatmap(
    heatmap_data,
    
    annot=True,
    fmt=".3f",
    cmap="Purples",
    cbar_kws={"label":"Treffer pro 10.000 Tokens"}
)

# plt.imshow(heatmap_data, aspect="auto")

# plt.colorbar(label="Treffer pro 10.000 Tokens")

# plt.xticks(
#     range(len(heatmap_data.columns)),
#     heatmap_data.columns.tolist(),
#     rotation=45
# )

# plt.yticks(
#     range(len(heatmap_data.index)),
#     heatmap_data.index.tolist()
# )

plt.title("Jährliche Entwicklung reproduktionsbezogener Pattern im Zeitraum 2019–2025")

plt.xlabel("Jahr")

plt.ylabel("Pattern")

plt.tight_layout()
plt.show()

