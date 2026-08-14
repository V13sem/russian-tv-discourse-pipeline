import subprocess
import os

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
gdrive =BASE_DIR / "roh"
yt_dlp = "yt-dlp"

while True:
    url = input("Video URL (ENTER zum Beenden): ").strip()
    if not url:
        break

    datum = input("Datum (YYYY-MM-DD): ").strip()

    output = os.path.join(gdrive, f"{datum}_60_minut.%(ext)s")

    command = [
        yt_dlp,
        "-f", "bestaudio/best",
        "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--concurrent-fragments", "8",
        "--no-keep-video",
        "--cookies-from-browser", "firefox",
        "--hls-use-mpegts",
        "--postprocessor-args", "ffmpeg:-ar 16000 -ac 1 -c:a pcm_s16le",
        "-o", output,
        url
    ]

    print("\nDownload läuft...\n")

    try:
        subprocess.run(command, check=True)
        print("\nDownload fertig! Starte Whisper-Transkription...\n")

        # Whisper-Transkription starten
        audio_file = os.path.join(gdrive, f"{datum}_60_minut.wav")
        
        #pfrüfen, ob Pfad zu Datei existiert
        if not os.path.exists(audio_file):
            print(f"\nAudiodatei nicht gefunden: {audio_file}\n")
            continue

        whisper_command = [
            sys.executable,
            "-m",
            "whisper",
            audio_file,
            "--language", "Russian",  # Sprache erzwingen 
            "--model", "small",  # Modell wählen (tiny/base/small/medium/large)
            "--output_dir", gdrive  # Speicherort für die Transkription
        ]
        subprocess.run(whisper_command, check=True)
        print(f"\nTranskription fertig! Ergebnis: {datum}_60_minut.txt\n")

    except subprocess.CalledProcessError as e:
        print(f"\nFehler beim Download oder der Transkription: {e}\n")
