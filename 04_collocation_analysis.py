# python NEW_collocation_analysis.py
# Ein Kollokator ist ein Token innerhalb eines Fensters von maximal fünf Tokens links oder rechts eines Pattern-Treffers.
# L5 L4 L3 L2 L1 | NODE | R1 R2 R3 R4 R5
# Einschränkung: Mehrwort-Nodes funktioniert hier nicht.
from pathlib import Path
from collections import Counter, defaultdict
import csv
import re
from patterns import PATTERNS
import pandas as pd
from stopwords_russian import STOPWORDS

INPUT_DIR = Path("") 
OUTPUT_DIR = Path("")


OUTPUT_CSV = OUTPUT_DIR / "collocations_yearly.csv"
OUTPUT_PERIOD_CSV = OUTPUT_DIR / "collocations_periods.csv"
OUTPUT_STATS_CSV = OUTPUT_DIR / "collocations_statistics.csv"
OUTPUT_CSV_EXCEL = OUTPUT_DIR / "collocations_yearly_excel.csv" # für excel, sonst pain

CONTEXT_WINDOW = 5
MIN_FREQ = 1
MIN_RANGE = 1

TOKEN_RE = re.compile(r"[а-яА-ЯёЁ]+")

#patterns aus dem pattern.py wird aus Regex-String echte kompilierte Regex-Objekt
COMPILED_PATTERNS = {
    group_name: [re.compile(pattern) for pattern in pattern_list]
    for group_name, pattern_list in PATTERNS.items()
}


# ========================================================
# HILFSFUNKTIONEN
# ========================================================
#bei pre_processing vergessen 
def normalize_text(text: str) -> str:
    return text.lower().replace("ё", "е")

def extract_year_from_filename(filename: str) -> str:
    match = re.match(r"(\d{4})-\d{2}-\d{2}", filename)
    if match:
        return match.group(1)
    
    match = re.search(r"(20\d{2})", filename)
    return match.group(1) if match else "unknown"

# wichtig die Vorarbeit: die Zeichenposition muss gespeichert werden
# diese Positionen werden später benötigt, um einen Regex Treffer eindeutig 
# den entsprechenden Tokens zuzuordnen und daraus das Kontextfenster zu bestimmen:

def tokenize_with_positions(text: str):
    tokens = []
    for match in TOKEN_RE.finditer(text):
        tokens.append(
            (   match.group(),
                match.start(),
                match.end()
            )
        )

    return tokens



# Der Regex arbeitet mit Zeichenpositionen im Text, 
# die Kollokationsanalyse braucht aber Tokenpositionen. 
# Dieser Block übersetzt von Zeichenposition zu Tokenposition:

def find_collocates(text: str, tokens, compiled_patterns, context_window: int):
    results = []

    # Als Kollokatoren gelten Tokens, die sich innerhalb eines Fensters von maximal fünf Tokens 
    # links oder rechts eines Treffers aus einer definierten Pattern Gruppe befinden.

    for regex in compiled_patterns:
        for match in regex.finditer(text):
            match_start = match.start() # -> Character-Position

            # Finde Token-Position des Matches
            # _ steht für den token selbst 
            #  Character-Position in Token-Index umwandeln
            token_position = None
            for i, (_, token_start, token_end) in enumerate(tokens):
                if token_start <= match_start < token_end:
                    token_position = i #Token-Index
                    break

            if token_position is None: #also unbekannt
                    continue

                #Linker Kontext
            left_start = max(0, token_position - context_window)
            left_tokens = tokens[left_start:token_position]

                #Rechter Kontext
            right_start = token_position+1
            right_end = min(len(tokens), right_start + context_window)
            right_tokens = tokens[right_start:right_end]

            results.append({
                    "match": match.group(),
                    "left": [token[0] for token in left_tokens],
                    "right": [token[0] for token in right_tokens]
                })

    return results

# Jahr extrahieren; für den Vergleich der jährliche Entwichlung
# als auch einen verdichteten Vergleich vor und nach 2022
def get_period_from_year(year: str) -> str:
    try: 
        year_int = int(year)

        if 2019 <= year_int <= 2021:
            return "Early (2019-2021)"

        if 2022 <= year_int <= 2025:
            return "Late (2022-2025)"

        return "Unknown"
    
    except ValueError:
        return "Unknown"
    
def main():

    files = list(INPUT_DIR.glob("*.txt"))

    if not files:
        raise RuntimeError(f"Keine TXT-Dateien gefunden in {INPUT_DIR}")

# Entwickelt mit Claude (Anthropic AI) : Hierarchische defaultdict-Struktur
# für effiziente Aggregation nach Jahr, Pattern, Wort
    data = defaultdict(
        lambda: defaultdict(
            lambda: {
                "left": Counter(),
                "right": Counter(),
                "files": defaultdict(set),
                "total_matches": 0,
            }
        )
    )


# Für jede Datei

    for index, file in enumerate(files, start=1):

        year = extract_year_from_filename(file.name)

        # praktisch um erste und jede hunderste Datei in der Bearbeitung sehen zu können 
        if index % 100 == 0 or index == 1:
            print(f"[{index}/{len(files)}] Verarbeite: {year} | {file.name}")

        try:
                text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
                print(f" Fehler beim Lesen: {file.name}: {e}")
                continue

        text = normalize_text(text)
        tokens = tokenize_with_positions(text)

        if not tokens:
                continue

            # Analyse für jedes Pattern
        for group_name, compiled_patterns_list in COMPILED_PATTERNS.items():

                matches = find_collocates(text, tokens, compiled_patterns_list, CONTEXT_WINDOW)
                data[year][group_name]["total_matches"] += len(matches) 
                # += len(matches) -> Addiert die Anzahl der gerade gefundenen Treffer
                # zur bisherigen Gesamtzahl dieser Pattern-Gruppe im jeweiligen Jahr,
                # um alle Treffer über die Dateien hinweg zu sammeln.

                for match in matches:

                    # Linker Kontext:
                    for word in match["left"]:
                        # Stopwords (ausgewählte) werden nicht in die Kollokationszählung einbezogen
                        if word in STOPWORDS:
                            continue

                        # Zählt das aktuelle Nicht-Stopword im linken Kontext
                        data[year][group_name]["left"][word] += 1
                        # speichert, in welcher Datei das Wort vorkam. Relevant für Range
                        data[year][group_name]["files"][word].add(file.name)

                    # Rechter Kontext
                    for word in match["right"]:
                        if word in STOPWORDS:
                            continue

                        data[year][group_name]["right"][word] += 1
                        data[year][group_name]["files"][word].add(file.name)

    print(f"\n[INFO] Verarbeitung abgeschlossen. Schreibe Ergebnisse...") 

        # Schreibe Ergebnisse
    write_yearly_results(data)
    write_period_results(data)
    #write_period_comparison(data)
    write_statistics(data)
    
    print(f"\n[SUCCESS] Alle Ergebnisse gespeichert in: {OUTPUT_DIR}")          

# ========================================================
# ERGEBNISSE SCHREIBEN ヘ⁠(⁠￣⁠ω⁠￣⁠ヘ⁠)
# ========================================================
def write_yearly_results(data):
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames  = [
        "year",
        "period",
        "pattern",
        "collocate",
        "freq_lr",
        "freq_l",
        "freq_r",
        "range",
        "node_matches",
        "collocate_per_10k_node_matches",
    ]

    # https://www.geeksforgeeks.org/python/writing-csv-files-in-python/
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames )
        writer.writeheader()

        for year in sorted(data.keys()): #data.keys sind alle Jahre; aufsteigend sortiert

            period = get_period_from_year(year) # Early (2019-2021) || Late (2022-2025)


            # Verbessert durch Claud (Anthropic AI) bis all_words
            for pattern_name in sorted(data[year].keys()):

                left = data[year][pattern_name]["left"]
                right = data[year][pattern_name]["right"]
                ranges = data[year][pattern_name]["files"]
                total_matches = data[year][pattern_name]["total_matches"]

                all_words = set(left.keys()) | set(right.keys())

                rows = []

                for word in all_words:
                    freq_l = left.get(word, 0)
                    freq_r = right.get(word, 0)
                    freq_lr = freq_l + freq_r
                    word_range=len(ranges[word])

                    # Filter
                    # Wenn der Kollokator entweder zu selten vorkommt 
                    # oder in zu wenigen Dateien vorkommt, wird er übersprungen.

                    if freq_lr < MIN_FREQ or word_range < MIN_RANGE:
                        continue

                    # Relative Kollokationsrate:
                    # Häufigkeit des Kollokators pro 10.000 Treffer der jeweiligen Pattern-Gruppe
                    collocate_rate = round((freq_lr / max(total_matches, 1)) * 10000, 2)

                    rows.append({
                        "year": year,
                        "period": period,
                        "pattern": pattern_name,
                        "collocate": word,
                        "freq_lr": freq_lr,
                        "freq_l": freq_l,
                        "freq_r": freq_r,
                        "range": word_range,
                        "node_matches": total_matches,
                        "collocate_per_10k_node_matches": collocate_rate,
                    })

                    # Sortiere nach Häufigkeit
                    # Verbessert und gekürzt durch Claud (Anthropic AI) -> (key=lambda x: x["freq_lr"]
                rows.sort(key=lambda x: x["freq_lr"], reverse=True)
                writer.writerows(rows)
                        
    print(f"Jährliche Ergebnisse gespeichert in: {OUTPUT_CSV}")

            #Zusätzliche Excel_Version
    df_yearly = pd.read_csv(OUTPUT_CSV)

    df_yearly.to_csv(
                OUTPUT_CSV_EXCEL,
                sep= ";",
                decimal=",",
                encoding="utf-8-sig",
                index= False
            )

    print(f"Excel-Version gespeichtert in: {OUTPUT_CSV_EXCEL}")

# Aggregiert Kollokationen pro Periode (2019-2021 vs 2022-2025)
# Idee: mehrere Jahre zu zwei Perioden zusammenfassen, um diese zu vergleichen 
def write_period_results(data):
    OUTPUT_PERIOD_CSV.parent.mkdir(parents=True, exist_ok=True)

    period_data = defaultdict(
        lambda: defaultdict(
            lambda: {
                "left": Counter(),
                "right": Counter(),
                "files": defaultdict(set),
                "total_matches": 0,
            }
        )
    )

    for year, patterns in data.items():
        period = get_period_from_year(year)

        for pattern_name, pattern_data in patterns.items():
            period_data[period][pattern_name]["left"].update( 
                pattern_data["left"] #update wegen dem Counter; man braucht die Häufigkeit wortweise und nicht sum für eine einzige Zahl
            )
            period_data[period][pattern_name]["right"].update(
                pattern_data["right"] 
            )
            for word, files in pattern_data["files"].items():
                period_data[period][pattern_name]["files"][word].update(files)

            period_data[period][pattern_name]["total_matches"] += (
                    pattern_data["total_matches"]
                )
    fieldnames = [
        "period",
        "pattern",
        "collocate",
        "freq_lr",
        "freq_l",
        "freq_r",
        "range",
        "node_matches",
        "collocate_per_10k_node_matches",
    ]

    with OUTPUT_PERIOD_CSV.open("w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for period in sorted(period_data.keys()):
            for pattern_name in sorted(period_data[period].keys()):

                left = period_data[period][pattern_name]["left"]
                right = period_data[period][pattern_name]["right"]
                ranges = period_data[period][pattern_name]["files"]
                total_matches = period_data[period][pattern_name]["total_matches"]
                
                all_words = set(left.keys()) | set(right.keys())
                
                rows = []

                for word in all_words:
                    
                    freq_l = left.get(word, 0)
                    freq_r = right.get(word, 0)
                    freq_lr = freq_l + freq_r
                    word_range = len(ranges[word])
                    
                    if freq_lr < MIN_FREQ or word_range < MIN_RANGE:
                        continue

                    #total_matches -> Gesamtzahl der Node-Treffer innerhalb der jeweiligen Periode
                    collocate_rate= round(
                        (freq_lr / max(total_matches, 1)) * 10000, 2
                    )
                    rows.append({
                        "period": period,
                        "pattern": pattern_name,
                        "collocate": word,
                        "freq_lr": freq_lr,
                        "freq_l": freq_l,
                        "freq_r": freq_r,
                        "range": word_range,
                        "node_matches": total_matches,
                        "collocate_per_10k_node_matches": collocate_rate,
                    })
                
                rows.sort(key=lambda x: x["freq_lr"], reverse=True)
                writer.writerows(rows)
    
    print(f"Periode-Ergebnisse gespeichert: {OUTPUT_PERIOD_CSV}")


def write_statistics(data):
    """
    Schreibt Basis-Statistiken pro Pattern pro Jahr.
    """
    OUTPUT_STATS_CSV.parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    
    for year in sorted(data.keys()):
        period = get_period_from_year(year)
        
        for pattern_name in sorted(data[year].keys()):
            
            pattern_data = data[year][pattern_name]
            
            left = pattern_data["left"]
            right = pattern_data["right"]
            
            total_collocates_lr = sum(left.values()) + sum(right.values())
            unique_collocates = len(set(left.keys()) | set(right.keys()))
            avg_freq = round(
                total_collocates_lr / max(unique_collocates, 1), 2
            )
            total_matches = pattern_data["total_matches"]
            
            rows.append({
                "year": year,
                "period": period,
                "pattern": pattern_name,
                "total_pattern_matches": total_matches,
                "total_collocates_lr": total_collocates_lr,
                "unique_collocates": unique_collocates,
                "avg_freq_per_collocate": avg_freq,
            })
    
    df_stats = pd.DataFrame(rows)
    df_stats.to_csv(OUTPUT_STATS_CSV, index=False, encoding="utf-8-sig")
    
    print(f"Statistiken berechnet und gespeichert: {OUTPUT_STATS_CSV}")

if __name__ == "__main__":
    main()
