# Russian TV Discourse Pipeline

Dieses Repository enthält den für die Bachelorarbeit verwendeten Code, ausgewählte Ergebnisdateien sowie ergänzende Materialien zur Analyse des Reproduktionsdiskurses in der russischen Fernsehtalkshow `60 минут` auf Russia-1.

Untersucht wird der Zeitraum 2019 bis 2025.

## Inhalt des Repositories

### Daten und Verarbeitung

- `transkripte/`  
  Automatisch erzeugte Rohtranskripte der untersuchten Sendungen.

- `lemmatisiert/`  
  Lemmatisierte Versionen der Transkripte.

- `lemmatisiert_no.stopwords/`  
  Lemmatisierte Texte nach Anwendung der angepassten russischen Stopwortliste.

- `logs/`  
  Protokolle der Verarbeitungsschritte und auftretender Fehler.

- `results/`  
  Ergebnisdateien der Frequenz-, Kollokations- und statistischen Analysen.

- `visualisation/`  
  Code für Visualisierungen von Heatmaps.

### Zentrale Skripte

- `01_links_sammeln_playwright_ansatz.py`  
  Erfassung der Episodenlinks und Metadaten von Smotrim.ru.

- `02_download_transcription_with_faster_whisper...py`  
  Ermittlung der Stream-URLs, Download der Audiospuren und automatische Transkription.

- `03_frequency_by_year_raw.py`  
  Berechnung der jährlichen absoluten und normalisierten Pattern-Häufigkeiten.

- `04_collocation_analysis.py`  
  Erzeugung der Kollokationsdaten.

- `05_compare_periods.py`  
  Vergleich der Kollokationsprofile zwischen Early (2019–2021) und Late (2022–2025).

- `chi_test_frequenz_yearly.py`  
  Inferenzstatistische Prüfung der Pattern-Häufigkeiten mittels Chi-Quadrat-Test und Benjamini-Hochberg-Korrektur.

- `collocation_significance_test.py`  
  Statistische Prüfung ausgewählter Kollokationsveränderungen mittels Poisson-Ratenvergleich und Benjamini-Hochberg-Korrektur.

- `pre_processing_all_txt.py`  
  Sprachliche Vorverarbeitung der Transkripte.

- `patterns.py`  
  Definition der für die Analyse verwendeten Suchpattern.

- `stopwords_russian.py`  
  Angepasste russische Stopwortliste.

### Ergänzende Dateien

- `links.csv`  
  Übersicht der erfassten Episoden und zugehörigen Metadaten.

- `legislation_russia_reproduction_family_gender_...`  
  Ergänzender Datensatz zu gesetzlichen und politischen Entwicklungen im Bereich Reproduktion, Familie und Geschlecht in Russland.

## Methodischer Ablauf

Die Verarbeitung erfolgte in mehreren Schritten:

1. Erfassung der Episodenlinks
2. Ermittlung der temporären Stream-URLs
3. Download und Aufbereitung der Audiospuren
4. automatische Transkription
5. sprachliche Vorverarbeitung und Lemmatisierung
6. Frequenzanalyse
7. Kollokationsanalyse
8. Vergleich der Untersuchungsperioden
9. inferenzstatistische Prüfung ausgewählter Veränderungen
10. Visualisierung der Ergebnisse

## Verwendete Software und Bibliotheken

Unter anderem wurden verwendet:

- Python
- Playwright
- yt-dlp
- FFmpeg
- Faster Whisper
- spaCy
- pandas
- numpy
- scipy
- statsmodels
- matplotlib
- seaborn

Für die sprachliche Verarbeitung wurde unter anderem das russische spaCy-Modell `ru_core_news_md` verwendet.

## Datenbasis

Erfasst wurden 3.470 Sendungen aus dem Zeitraum 2019 bis 2025. Für 3.378 Sendungen konnte erfolgreich ein Transkript erstellt und in den finalen Arbeitskorpus übernommen werden.

Die Transkripte wurden automatisiert erzeugt und stellen keine manuell geprüften Abschriften dar.

## Große Dateien

Ein Teil der größeren Dateien wird über Git LFS verwaltet. Für einen vollständigen Abruf des Repositories sollte Git LFS installiert sein.

## KI-Unterstützung

Bei einzelnen Schritten der technischen Umsetzung und Codeentwicklung wurde generative KI unterstützend eingesetzt. KI-gestützte Änderungen und Ergänzungen sind im Code entsprechend gekennzeichnet.

Die inhaltliche Auswahl der untersuchten Pattern, die Auswertung der Ergebnisse sowie die abschließende wissenschaftliche Interpretation erfolgten eigenständig.

## Bachelorarbeit

Das Repository dient als ergänzende Dokumentation zur Bachelorarbeit:

**Der Reproduktionsdiskurs als politisches Steuerungsfeld im russischen Staatsfernsehen**

Eine korpusgestützte Analyse von `60 минут` auf Russia-1 im Zeitraum 2019–2025.
