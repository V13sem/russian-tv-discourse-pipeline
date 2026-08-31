# python pre_processing_all_txt.py


from pathlib import Path
import ru_core_news_md

nlp = ru_core_news_md.load()

input_dir = Path("C:/Users/PeppermintButler/Desktop/Bachelorarbeit/Audio/transkripte")
output_dir = Path("C:/Users/PeppermintButler/Desktop/Bachelorarbeit/Audio/lemmatisiert")

anzahl_verarbeitet = 0
anzahl_uebersprungen = 0

for input_file in input_dir.glob("*.txt"):
    output_file = output_dir / input_file.name

    if output_file.exists():
        print((f"Überspringe: {output_file.name}"))
        anzahl_uebersprungen += 1
        continue

    print(f"Bearbeite: {input_file.name}")

    text = input_file.read_text(encoding = "utf-8")

    doc = nlp(text)


    lemmas = [
        token.lemma_.lower()
        for token in doc
        if token.is_alpha 
    ]

    output_file.write_text(" ".join(lemmas), encoding = "utf-8")

    print(f"Fertig: {output_file.name}")
    anzahl_verarbeitet += 1

print("Alle Datein verarbeitet")


