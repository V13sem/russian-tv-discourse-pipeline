# frequency_by_year_raw.py

from pathlib import Path
import csv
import re


# ============================================================
# Einstellungen
# ============================================================

INPUT_DIR = Path("C:/Users/PeppermintButler/Desktop/Bachelorarbeit/Audio/lemmatisiert")
OUTPUT_CSV = Path("C:/Users/PeppermintButler/Desktop/Bachelorarbeit/Audio/frequency_by_year_raw.csv")

# Russische Wörter zählen
TOKEN_RE = re.compile(r"[а-яА-ЯёЁ]+")

# Suchmuster für Begriffsfelder
# Die Texte werden vorher auf Kleinschreibung gesetzt und ё -> е normalisiert.
PATTERNS = {
    # ========================================================
    # Reproduktionsdiskurs im engeren Sinn
    # Familie und soziale Reproduktion
    # ========================================================

    "familie": [
        r"\bсемь(?:я|и|е|ю|ей|ями|ях)\b",
        r"\bсемейн\w*",
        r"\bсемейств\w*",
    ],

    "kinder": [
        r"\bребен\w*",
        r"\bдет(?:и|ей|ям|ьми|ями|ях|ск\w*)\b",
    ],

    "mutter_mutterschaft": [
        r"\bмать\b",
        r"\bматер(?:и|ью|ей|ям|ями|ях)\b",
        r"\bматеринств\w*",
    ],

    "vater_vaterschaft": [
        r"\bот(?:ец|ца|цу|цом|це|цы|цов|цам|цами|цах)\b",
        r"\bотцовств\w*",
    ],
    "muetterlich_vaeterlich": [
    r"\bматеринск\w*",
    r"\bотцовск\w*",
    ],    

    "eltern_elternschaft": [
        r"\bродител\w*",
    ],

    "frau": [
        r"\bженщин\w*",
    ],

    "mann": [
        r"\bмужчин\w*",
    ],

    "ehe": [
        r"\bбрак(?:а|е|ом|и|ов|ам|ами|ах)?\b",
        r"\bсупруг\w*",
        r"\bсупруже\w*",
    ],
    "zuhause_haeuslichkeit": [
    r"\bдом\b",
    r"\bдома\b",
    r"\bдому\b",
    r"\bдомом\b",
    r"\bдоме\b",
    r"\bдомашн\w*",
],
   
  "geburt_gebaeren": [
    r"\bрожд(?!аемост|еств)\w*",
    r"\bрожать\b",
    r"\bрожаю\b",
    r"\bрожаешь\b",
    r"\bрожает\b",
    r"\bрожают\b",
    r"\bрожал\w*",
    r"\bродить\b",
    r"\bродил\w*",
    r"\bродит\b",
    r"\bродят\b",
    r"\bродив\w*",
],

    "schwangerschaft": [
        r"\bберемен\w*",
    ],
    "schwangerschaftsabbruch": [
    r"\bпрерыван\w*\s+беременност\w*",
    r"\bпрервать\s+беременност\w*",
    r"\bпрервал\w*\s+беременност\w*",
    
    ],

    "abtreibung": [
    r"\bаборт\w*",
],

    "sorge_fuersorge": [
        r"\bзабот\w*",
        r"\bпозабот\w*",
    ],
        "verantwortung_pflicht": [
        r"\bответственност\w*",
        r"\bответственн\w*",
        r"\bобязанност\w*",
        r"\bобязан\w*",
        r"\bдолг\b",
        r"\bдолга\b",
        r"\bдолгу\b",
        r"\bдолгом\b",
        r"\bдолге\b",
    ],

    "erziehung": [
    r"\bвоспитан\w*",
    r"\bвоспитыва\w*",
    r"\bвоспитать\w*",
    ],

    "reproduktion_fachbegriff": [
        r"\bрепродукц\w*",
        r"\bрепродуктив\w*",
    ],

    "unfruchtbarkeit": [
        r"\bбесплод\w*",
    ],

    "empfaengnis": [
        r"\bзачати\w*",
    ],  
    



    # ========================================================
    # Demografische und politische Rahmung
    # ========================================================

    "demografie": [
        r"\bдемограф\w*",
    ],

    "bevoelkerung": [
        r"\bнаселен\w*",
    ],

    "volk": [
        r"\bнарод\w*",
        
    ],
        "generation": [
        r"\bпоколени\w*",
    ],
    
    "geburtenrate": [
        r"\bрождаем\w*",
    ],
    
    "mutterschaftskapital": [
        r"\bматеринск\w*\s+капитал\w*",
        r"\bматкапитал\w*",
    ],
    
    "zukunft": [
        r"\bбудущ\w*",
    ],

    "staat": [
        r"\bгосударств\w*",
    ],

    "nation_national": [
        r"\bнаци(?:я|и|ю|ей|ями|ях)\b",
        r"\bнациональн\w*",
    ],

    "gesetz": [
        r"\bзакон\w*",
    ],

    "regierung": [
        r"\bправительств\w*",
    ],

    "duma": [
        r"\bгосдум\w*",
        r"\bдум(?:а|ы|е|у|ой)\b",
    ],

    "land_staatlicher_raum": [
        r"\bстран(?:а|ы|е|у|ой|ою|ами|ах)?\b",
    ],

    "russland_russisch": [
        r"\bросси\w*",
        r"\bрусск\w*",
    ],
    "bevoelkerungszahl": [
        r"\bчисленност\w*",        # численность, численности ...
    ],

    "bevoelkerungszuwachs": [
        r"\bприрост\w*",           # прирост, прироста ...        
    ],

    "bevoelkerungsrueckgang": [
        r"\bсокращени\w*\s+населен\w*",
        r"\bсокращени\w*\s+численност\w*",
        r"\bснижени\w*\s+рождаемост\w*",
        r"\bпадени\w*\s+рождаемост\w*",
    ],
        "demografische_krise": [
        r"\bдемограф\w*\s+кризис\w*",
        r"\bкризис\w*\s+рождаемост\w*",
        r"\bкризис\w*\s+семь\w*",
    ],

    "demografischer_mangel_verlust": [
        r"\bдефицит\w*\s+населен\w*",
        r"\bдемограф\w*\s+дефицит\w*",
        r"\bпотер\w*\s+населен\w*",
        r"\bдемограф\w*\s+потер\w*",
    ],

    "aussterben": [
        r"\bвымирани\w*",
        r"\bвымира\w*",
    ],


    # ========================================================
    # Werte, Moral und traditionelle Ordnung
    # ========================================================

    "werte_moral_tradition": [
        r"\bценност\w*",          # ценность, ценности, ценностный ...
        r"\bтрадиц\w*",           # традиция, традиции ... традиционный, традиционная ...               
        r"\bморал\w*",            # мораль, моральный ...
        r"\bнравственн\w*",       # нравственный, нравственность ...
    ],
        "geistig_religioes": [
        r"\bдуховн\w*",           # духовный, духовность ...
        r"\bправослав\w*",        # православие, православный ...
        r"\bвер(?:а|ы|е|у|ой)\b", # вера, верующий ...
        r"\bверующ\w*",
        r"\bрелиги\w*",
    ],
        "norm_ordnung_kultur_gesellschaft": [
        r"\bнорм\w*",             # норма, нормы, нормативный ...
        r"\bпоряд\w*",            # порядок, порядки ...
        r"\bкультур\w*",          # культура, культурный ...
        r"\bобществ\w*",          # общество, общественный ...
    ],
        "patriotismus_identitaet_souveraenitaet": [
        r"\bпатриот\w*",          # патриотизм, патриотический ...
        r"\bидентичност\w*",      # идентичность ...
        r"\bсуверенитет\w*",      # суверенитет, суверенный ...
        r"\bсуверенн\w*",
    ],

    "heimat_vaterland": [
        r"\bродин\w*",
        r"\bотечеств\w*",
    ],

    "west_liberal_lgbt": [
        r"\bзапад\w*",            # Запад, западный ...
        r"\bлиберальн\w*",        # либеральный ...
        r"\bтолерантност\w*",     # толерантность ...        
        r"\bлгбт\w*",             # ЛГБТ-...
    ],

    "propaganda": [
        r"\bпропаганд\w*",        # пропаганда, пропагандировать ...
    ],
}


# ============================================================
# Hilfsfunktionen
# ============================================================

def normalize_text(text: str) -> str:
    """
    Vereinheitlicht den Text für die Suche.
    ё wird zu е, weil russische Texte ё oft uneinheitlich verwenden.
    """
    return text.lower().replace("ё", "е")


def extract_year(filename: str) -> str:
    """
    Extrahiert das Jahr aus Dateinamen wie:
    2019-01-09_1859410.txt
    """
    match = re.search(r"(20\d{2})", filename)
    return match.group(1) if match else "unknown"


def count_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(text))


def count_pattern_group(text: str, pattern_list: list[str]) -> int:
    count = 0

    for pattern in pattern_list:
        count += len(re.findall(pattern, text))

    return count



# ============================================================
# Hauptprogramm
# ============================================================

def main():
    files = list(INPUT_DIR.glob("*.txt"))

    if not files:
        raise RuntimeError(f"Keine TXT-Dateien gefunden in: {INPUT_DIR}")

    print(f"Gefundene TXT-Dateien: {len(files)}")

    # Jahresdaten sammeln
    yearly = {}

    for index, file in enumerate(files, start=1):
        year = extract_year(file.name)

        if year not in yearly:
            yearly[year] = {
                "year": year,
                "files": 0,
                "tokens": 0,
            }

            for group_name in PATTERNS:
                yearly[year][group_name] = 0

        print(f"[{index}/{len(files)}] {file.name}")

        raw_text = file.read_text(encoding="utf-8", errors="ignore")
        text = normalize_text(raw_text)

        yearly[year]["files"] += 1
        yearly[year]["tokens"] += count_tokens(text)

        for group_name, pattern_list in PATTERNS.items():
            # Sowohl zählen (alte Logik) als auch Positionen speichern (neue Logik)
            yearly[year][group_name] += count_pattern_group(text, pattern_list)



        
    # CSV-Spalten bauen
    fieldnames = ["year", "files", "tokens"]

    for group_name in PATTERNS:
        fieldnames.append(group_name)
        fieldnames.append(f"{group_name}_per_10k")

    # CSV schreiben
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for year in sorted(yearly.keys()):
            row = yearly[year]
            tokens = row["tokens"]

            output_row = {
                "year": year,
                "files": row["files"],
                "tokens": tokens,
            }

            for group_name in PATTERNS:
                absolute = row[group_name]

                if tokens > 0:
                    relative = absolute / tokens * 10_000
                else:
                    relative = 0

                output_row[group_name] = absolute
                output_row[f"{group_name}_per_10k"] = round(relative, 3)

            writer.writerow(output_row)

    print("\nFertig.")
    print(f"CSV gespeichert unter: {OUTPUT_CSV}")
    print(f"JSON gespeichert.")


if __name__ == "__main__":
    main()