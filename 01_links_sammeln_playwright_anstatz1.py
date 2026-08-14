"""
01_links_sammeln_playwright_anstatz1.py
--------------------------------
Sammelt alle Episoden-Links von smotrim.ru/brand/60851 ("60 минут")
direkt aus dem HTML, da die GraphQL-API keine brauchbare publicId
für ältere Episoden liefert.

Strategie:
1. Seite öffnen
2. Für jedes Jahr (linke Sidebar) klicken
3. "Показать все выпуски" wiederholt klicken bis alle geladen sind
4. Alle <a href="/video/XXXXX"> Links samt Titel/Datum extrahieren

Ausgabe: links.csv mit Spalten:
    video_id, jahr, datum_text, titel, seiten_url
"""

import csv
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

# ── Konfiguration ─────────────────────────────────────────────────────────────

START_URL  = "https://smotrim.ru/brand/60851"
OUTPUT_CSV = Path(__file__).resolve().parent / "links.csv"

HEADLESS = False  # zum Testen sichtbar lassen

# Jahre die gesammelt werden sollen (laut Sidebar: 16 bis 26 sichtbar -> 2016-2026)
YEARS = list(range(2019, 2026))

# Zum Testen: nur 1 Jahr. Danach auf None setzen für alle.
MAX_YEARS = 1


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def click_all_years_button(page, year_index: int) -> bool:
    """Klickt auf die Jahres-Schaltfläche in der linken Sidebar."""
    year_short = str(year_index)[-2:]
 
    try:
        btn = page.get_by_text(year_short, exact=True)
        if btn.count() > 0:
            btn.first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            btn.first.click(timeout=8000)
            page.wait_for_timeout(2000)
            return True
    except Exception as e:
        print(f"    Konnte Jahr {year_index} nicht klicken: {e}")
 
    return False


def load_all_episodes(page, max_scrolls: int = 100) -> None:
    """
    Klickt EINMAL auf 'Показать все выпуски', dann scrollt wiederholt
    nach unten bis keine neuen Episoden mehr nachgeladen werden.
    """
    # Button einmal klicken
    try:
        btn = page.get_by_text("Показать все выпуски", exact=False)
        if btn.count() > 0:
            btn.first.click(timeout=5000)
            print("    'Показать все выпуски' geklickt.")
            page.wait_for_timeout(2000)
    except Exception as e:
        print(f"    Button nicht gefunden oder nicht klickbar: {e}")

    # Danach wiederholt scrollen bis sich die Anzahl nicht mehr ändert
    last_count = -1
    stable_rounds = 0

    for i in range(max_scrolls):
        current_count = page.locator('a[href*="/video/"]').count()
        print(f"      Scroll {i}: {current_count} Links sichtbar")

        if current_count == last_count:
            stable_rounds += 1
            if stable_rounds >= 3:
                print("      Anzahl stabil über 3 Runden, stoppe.")
                break
        else:
            stable_rounds = 0

        last_count = current_count

        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(1200)

    print(f"    Finale Episoden-Links: {page.locator('a[href*=\"/video/\"]').count()}")


def extract_episodes(page, year: int) -> list[dict]:
    """Extrahiert alle Episode-Links samt Titel/Datum aus der aktuellen Seite."""
    items = page.locator('a[href*="/video/"]').evaluate_all(
        """
        elements => elements.map(a => {
            const card = a.closest('.card-episode') || a.closest('div');
            return {
                href: a.getAttribute('href') || '',
                title: a.innerText || '',
                cardText: card ? card.innerText : ''
            };
        })
        """
    )

    rows = []
    for item in items:
        href = item["href"]
        match = re.search(r"/video/(\d+)", href)
        if not match:
            continue

        video_id = match.group(1)
        full_url = urljoin(START_URL, href)

        rows.append({
            "video_id":   video_id,
            "jahr":       year,
            "datum_text": clean_text(item["cardText"])[:100],
            "titel":      clean_text(item["title"]),
            "seiten_url": full_url,
        })

    return rows


def main() -> None:
    years = YEARS if MAX_YEARS is None else YEARS[-MAX_YEARS:]  # neueste Jahre zuerst testen
    print(f"Zu sammelnde Jahre: {years}")

    all_rows = []
    seen_ids = set()

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=HEADLESS)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()

        print(f"\nÖffne: {START_URL}")
        page.goto(START_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        for year in years:
            print(f"\n── Jahr {year} ──")

            clicked = click_all_years_button(page, year)
            if not clicked:
                print(f"    Jahr-Button nicht gefunden, überspringe.")
                continue

            page.wait_for_timeout(2000)
            load_all_episodes(page)

            rows = extract_episodes(page, year)
            print(f"    Gefundene Episoden: {len(rows)}")

            for row in rows:
                if row["video_id"] in seen_ids:
                    continue
                seen_ids.add(row["video_id"])
                all_rows.append(row)

        context.close()
        browser.close()

    if not all_rows:
        print("\nKeine Episoden gefunden.")
        return

    fieldnames = ["video_id", "jahr", "datum_text", "titel", "seiten_url"]
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n✓ {len(all_rows)} Episoden gespeichert → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()