"""
faster whisper transcription for smotrim.ru audio
03_download_transcription_with_faster_whisper.py
--------------------------
Liest links.csv (erzeugt von 01_links_sammeln_playwright_anstatz1.py),
öffnet jede Episodenseite (smotrim.ru/video/XXXXX) per Playwright (Firefox),
fängt die m3u8-URL mit sign ab,
lädt Audio per yt-dlp (Format 400 = kleinste Qualität) herunter.

CSV-Spalten (von 01_links_sammeln_playwright_anstatz1.py):
    video_id, jahr, datum_text, titel, seiten_url

Voraussetzungen:
    pip install playwright faster-whisper
    playwright install firefox
"""

import csv
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright
from faster_whisper import WhisperModel

# ── Konfiguration ─────────────────────────────────────────────────────────────

BASE_DIR       = Path(__file__).resolve().parent
AUDIO_DIR      = BASE_DIR / "roh"
TRANSCRIPT_DIR = BASE_DIR / "transkripte"
LOG_DIR        = BASE_DIR / "logs"
INPUT_CSV      = BASE_DIR / "links.csv"
LOG_CSV        = LOG_DIR  / "download_log.csv"



YT_DLP         = Path(r"D:\yt-dlp\yt-dlp.exe")

HEADLESS       = True      # True = unsichtbar, False = Browser sichtbar (zum Debuggen)
MAX_ROWS       = None      # Zum Testen 1. Sonst auf None setzen für alle.

WAV_NACH_TRANSKRIPTION_LOESCHEN = True #WAV nach Whisper löschen

PAUSE_ZWISCHEN_EPISODEN = 4   # Sekunden Pause zwischen Episoden
YT_DLP_RETRIES          = 3   # Anzahl Download-Versuche bei Timeout/Fehler

# ── Konfiguration Transkription ──────────────────────────────────────────────────────

WHISPER_MODEL        = "small"
WHISPER_DEVICE       = "cuda"       # oder "cpu"
WHISPER_COMPUTE_TYPE = "float16"    # cuda: "float16"
WHISPER_BEAM_SIZE    = 4            # wie viele Hypothesen werden pro Segment erzeugt (größer = besser, langsamer)
WHISPER_VAD_FILTER   = True         # True = Stille überspringen (schneller, aber evtl. fehlende Wörter am Anfang/Ende)


# Russische Monate für Datumsumwandlung
RU_MONTHS = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
}

for folder in [AUDIO_DIR, TRANSCRIPT_DIR, LOG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def clean_filename(text: str) -> str: 
    return re.sub(r'[<>:"/\\|?*\s]+', "_", text.strip())


def parse_datum(datum_text: str, jahr: str) -> str:
    """
    Extrahiert ein sauberes Datum YYYY-MM-DD aus z.B.
    '30 июня 106 мин Эфир 30.06.2026' oder '26 декабря'.
    Sucht zuerst nach einem fertigen TT.MM.JJJJ Muster (zuverlässiger),
    fällt sonst auf Tag+Monatsname zurück.
    """
    # Variante 1: TT.MM.JJJJ irgendwo im Text (z.B. aus "Эфир 30.06.2026")
    match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", datum_text)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"

    # Variante 2: "30 июня" + Jahr separat
    pattern = r"(\d{1,2})\s+(" + "|".join(RU_MONTHS.keys()) + r")"
    match = re.search(pattern, datum_text.lower())
    if match:
        day = match.group(1).zfill(2)
        month = RU_MONTHS[match.group(2)]
        return f"{jahr}-{month}-{day}"

    return f"{jahr}-unbekannt"

#Schon tranksipierte Audios nicht mehr bearbeiten
def transkript_existiert(stem: str, datum: str) -> bool:
    # 1.  Exakte Prüfung: neue Datei mit video_id im Namen
    # z.B. 2022-12-29_2539395.txt
    if any(TRANSCRIPT_DIR.glob(f"{stem}*.txt")):
        return True
    
    # 2. "Alte" Dateien: Prüfung nach Datum im transkripte-Ordner
    # z.B. 2021-07-08_60_minut.txt + 2021-07-08.2_60_minut.txt = 2 → beide da
    vorhandene  = list(TRANSCRIPT_DIR.glob(f"{datum}*.txt"))
    if len(vorhandene) >=2:
        return True
    
    return False

def write_log(entry: dict) -> None:
    fieldnames = ["timestamp", "video_id", "seiten_url",
                   "status", "meldung", "ausgabe_datei"]
    file_exists = LOG_CSV.exists()
    with LOG_CSV.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)


def read_csv() -> list[dict]:
    if not INPUT_CSV.exists():
        print(f"Keine links.csv gefunden: {INPUT_CSV}")
        return []
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if MAX_ROWS is not None:
        rows = rows[:MAX_ROWS]
    return rows


# ── Playwright: frische m3u8-URL abgreifen; ヽ(°◇° )ノ ────────────────────────────────────
    
def find_m3u8(context, seiten_url: str) -> str | None:
    """
    Öffnet eine Episodenseite (smotrim.ru/video/XXXXX) im Browser
    und fängt automatisch die m3u8-Stream-URL ab.
    
    Das Problem: smotrim.ru generiert für jeden Aufruf eine neue m3u8-URL
    mit einem einmaligen 'sign'-Token (z.B. sign=64b6d7b6...). Diesen Token
    kann man nicht vorab berechnen — er muss live aus dem Browser abgegriffen werden.
    
    Gibt die vollständige m3u8-URL zurück, oder None wenn keine gefunden wurde.
    """
    
    # Liste für gefundene m3u8-URLs — wird von on_request befüllt
    found = []
    
    # Neue Browser-Seite öffnen (innerhalb des bestehenden Browser-Kontexts)
    page = context.new_page()

    def on_request(request):
        """
        Wird automatisch aufgerufen bei JEDER Netzwerkanfrage der Seite.
        Filtern gezielt nach der m3u8-Playlist-URL des Video-Servers.
        """
        url = request.url
        if (
            "vod.smotrim.ru" in url        # nur Anfragen an den Video-Server
            and "playlist.m3u8" in url     # nur die Haupt-Playlist, nicht Segmente
            and "sign=" in url             # nur URLs mit dem Authentifizierungs-Token
            and "chunklist" not in url     # chunklist = einzelne Videosegmente, nicht die Haupt-Playlist
            and url not in found           # keine Duplikate
        ):
            found.append(url)
            print(f"    m3u8 gefunden: ...sign={url.split('sign=')[-1][:8]}...")

    # Lauscher registrieren: on_request wird bei jeder Netzwerkanfrage aufgerufen
    page.on("request", on_request)

    try:
        print(f"    Öffne: {seiten_url}")
        
        # Seite laden und warten bis keine neuen Netzwerkanfragen mehr kommen
        # wait_until="networkidle" = Seite ist fertig geladen
        # timeout=60_000 = maximal 60 Sekunden warten
        page.goto(seiten_url, wait_until="networkidle", timeout=60_000)
        
        # Zusätzliche 5 Sekunden warten damit JavaScript vollständig initialisiert ist
        # (der Video-Player braucht Zeit zum Starten)
        page.wait_for_timeout(5_000)

        # Verschiedene CSS-Selektoren für den Play-Button probieren
        # Die Seite kann unterschiedliche Player-Versionen haben
        play_selectors = [
            ".vjs-big-play-button",              # Video.js Standard Play-Button
            ".vjs-play-control",                 # Video.js Play-Steuerung
            "button[aria-label*='play' i]",      # Button mit aria-label "play" (englisch)
            "button[aria-label*='Play' i]",      # Button mit aria-label "Play" (Großschreibung)
            "button[aria-label*='Воспроизвести']", # Button mit aria-label auf Russisch
            ".play-button",                      # generischer Play-Button
            "[class*='play']",                   # jedes Element mit 'play' im Klassennamen
            "[class*='Play']",                   # jedes Element mit 'Play' im Klassennamen
            "video",                             # das Video-Element selbst als Fallback
        ]
        
        clicked = False
        for selector in play_selectors:
            try:
                loc = page.locator(selector)
                if loc.count() > 0:
                    # Zum Element scrollen falls es nicht sichtbar ist
                    loc.first.scroll_into_view_if_needed()
                    loc.first.click(timeout=5_000)
                    clicked = True
                    print(f"    Play geklickt ({selector})")
                    break  # erster gefundener Button reicht
            except Exception:
                continue  # dieser Selektor hat nicht funktioniert, nächsten probieren

        if not clicked:
            # Kein Button gefunden: Video direkt per JavaScript starten
            page.evaluate("document.querySelector('video')?.play()")

        # Warten bis die m3u8-URL erscheint (maximal 30 Sekunden = 60 × 500ms)
        # Sobald found nicht mehr leer ist, bricht die Schleife ab
        for _ in range(60):
            if found:
                break
            page.wait_for_timeout(500)  # 500ms warten, dann erneut prüfen

    except Exception as e:
        print(f"    Playwright-Fehler: {e}")
    finally:
        # Seite immer schließen — auch bei Fehlern
        # Verhindert Speicherlecks bei ueber 4000 Episoden
        page.close()

    # Erste gefundene URL zurückgeben, oder None wenn nichts gefunden
    return found[0] if found else None




# ── yt-dlp: Audio herunterladen mit Retry, alter code erweitert─────────────────────────────────────
def download_audio(m3u8_url: str, seiten_url: str, stem: str) -> Path:
    """
    Lädt das Video im kleinsten Format (400kbps) herunter,
    extrahiert nur die Audiospur als WAV (16kHz, Mono).
    Bei Fehler wird es bis zu YT_DLP_RETRIES mal wiederholt.
    16kHz Mono ist das optimale Format für Whisper
    """
    output_template = AUDIO_DIR / f"{stem}.%(ext)s"
    final_wav       = AUDIO_DIR / f"{stem}.wav"

    if final_wav.exists():
        print(f"    Audio bereits vorhanden: {final_wav.name}")
        return final_wav

   
    command = [
        str(YT_DLP),
        "-f", "400",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--concurrent-fragments", "8",
        "--no-keep-video",
        "--cookies-from-browser", "firefox",
        "--hls-use-mpegts",       
        "--referer", seiten_url,
        "--socket-timeout", "60",          
        "--retries", "5",                  # interne yt-dlp Retries bei Netzwerkfehlern
        "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1 -c:a pcm_s16le",
        "-o", str(output_template),
        m3u8_url,
    ]

    
    for attempt in range(1, YT_DLP_RETRIES + 1):
        print(f"    Download Versuch {attempt}/{YT_DLP_RETRIES} ...")
        try:
            subprocess.run(command, check=True, timeout=600)

            if final_wav.exists():
                return final_wav



        except subprocess.CalledProcessError as e:            
            print(f"    Download-Fehler (Versuch {attempt}): {e}")            
        except subprocess.TimeoutExpired as e:            
            print(f"    Timeout nach 600s (Versuch {attempt})")
        time.sleep(3)

    raise FileNotFoundError(f"WAV nach {YT_DLP_RETRIES} Versuchen nicht erzeugt: {final_wav}")

# ── Whsiper ─────────────────────────────────────────────────────────────
    
    
def lade_asr_model() -> WhisperModel:
    # Lädt das faster-whisper Modell einmalig in den GPU-Speicher.
    # Wird nur beim ersten Video aufgerufen und dann für alle weitere
    print(f"Lade faster-whisper Modell: {WHISPER_MODEL} ({WHISPER_DEVICE}, {WHISPER_COMPUTE_TYPE})")
    return WhisperModel(
        WHISPER_MODEL,
        device=WHISPER_DEVICE,
        compute_type=WHISPER_COMPUTE_TYPE
    )

def transcribe(audio_file: Path, model: WhisperModel) -> Path:
    txt_file = TRANSCRIPT_DIR / f"{audio_file.stem}.txt"

    if txt_file.exists():
        print(f"    Transkript existiert bereits: {txt_file.name}")
        return txt_file

    print(f"    Transkribiere {audio_file.name} mit faster-whisper...")
    segments, info = model.transcribe(
        str(audio_file),
        language="ru",
        task="transcribe",
        beam_size=WHISPER_BEAM_SIZE,
        vad_filter=WHISPER_VAD_FILTER,  #vad_filter=True überspringt Stille automatisch → schneller
        condition_on_previous_text=False, #True: berücksichtigt vorherige Textsegmente stärker beim nächsten Segment
    )

    with txt_file.open("w", encoding="utf-8") as f:
        for segment in segments:
            text = segment.text.strip()
            if text:
                f.write(text + "\n")

    return txt_file


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def main() -> None:
    rows = read_csv()
    if not rows:
        return
    
    asr_model: WhisperModel | None = None

    print(f"Smotrim.ru – Audio-Download")
    print(f"Episoden: {len(rows)}")
    print(f"Audio:    {AUDIO_DIR}\n")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=HEADLESS)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
            locale="de-DE",
        )

        for index, row in enumerate(rows, start=1):
            video_id   = row.get("video_id", "").strip()
            seiten_url = row.get("seiten_url", "").strip()
            jahr       = row.get("jahr", "").strip()
            datum_text = row.get("datum_text", "").strip()

            if not video_id or not seiten_url:
                continue

            datum           = parse_datum(datum_text, jahr)
            stem            = f"{datum}_{video_id}"
            

            print(f"\n[{index}/{len(rows)}] Video {video_id} – {datum}")

            if transkript_existiert(stem, datum):
                print(f"    Transkript für {datum} existiert bereits, überspringe.")
                continue
            
            wav = None
            try:
                m3u8_url = find_m3u8(context, seiten_url)

                if not m3u8_url:
                    raise RuntimeError("Keine m3u8-URL gefunden")

                wav = download_audio(m3u8_url, seiten_url, stem)
                
                if asr_model is None:
                    asr_model = lade_asr_model()

                txt = transcribe(wav, asr_model)
            
                print(f"    ✓ Fertig: {txt.name}")

                write_log({
                    "timestamp":     datetime.now().isoformat(timespec="seconds"),
                    "video_id":      video_id,
                    "seiten_url":    seiten_url,                    
                    "status":        "ok",
                    "meldung":       "",
                    "ausgabe_datei": str(txt),
                })

            except Exception as e:
                print(f"    Fehler: {e}")
                write_log({
                    "timestamp":     datetime.now().isoformat(timespec="seconds"),
                    "video_id":      video_id,
                    "seiten_url":    seiten_url,                    
                    "status":        "fehler",
                    "meldung":       str(e),
                    "ausgabe_datei": "",
                })
            
            finally:
                if WAV_NACH_TRANSKRIPTION_LOESCHEN and wav is not None and wav.exists():
                    wav.unlink()
                    print(f"    WAV gelöscht: {wav.name}")

            # Pause zwischen Episoden, um Server nicht zu überlasten
            time.sleep(PAUSE_ZWISCHEN_EPISODEN)

        context.close()
        browser.close()

    print("\nAlle Episoden verarbeitet.")


if __name__ == "__main__":
    main()