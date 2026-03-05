#!/usr/bin/env python3
import requests
import csv
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import quote

# ─────────────────────────────
# CONFIG
# ─────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.google.com/",
}

DELAY = 2  # secondes entre requêtes


# ─────────────────────────────
# 1) Trouver l'URL Fiches-Auto
# ─────────────────────────────
def find_fiches_url(marque, modele):
    query = quote(f"{marque} {modele}")
    url = f"https://www.fiches-auto.fr/recherche-fiches-auto.php?q={query}"
    print(f"   🔎 Recherche fiches-auto: {query}")

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
    except Exception as e:
        print("   ❌ Erreur requête Fiches-Auto:", e)
        return ""
    print(f"   ↳ Status: {r.status_code}")

    if r.status_code != 200:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "/avis-" in a["href"] or "/essai-" in a["href"]:
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.fiches-auto.fr" + link
            return link
    return ""


# ─────────────────────────────
# 2) Scraper Fiches-Auto
# ─────────────────────────────
def scrape_fiches(url):
    """Récupère les avis et critères de fiabilité sur Fiches-Auto"""
    data = {
        "Nb avis": "",
        "Note moyenne /20": "",
        "Fiabilité": "",
        "Consommation": "",
        "Entretien (coût)": "",
        "Agrément": "",
        "Puissance moteur": "",
        "Bruit moteur": "",
        "Plaintes": "",
    }
    if not url:
        return data

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return data
        soup = BeautifulSoup(r.text, "html.parser")

        # Nombre d'avis
        h1 = soup.find("h1") or soup.find("h2")
        if h1:
            m = re.search(r"(\d+)\s+avis", h1.get_text())
            if m:
                data["Nb avis"] = int(m.group(1))

        # Notes /20 → moyenne approx
        notes = []
        for td in soup.find_all(string=re.compile(r"\d{1,2}/20")):
            m = re.search(r"(\d{1,2}(?:\.\d)?)/20", td)
            if m:
                try:
                    notes.append(float(m.group(1)))
                except ValueError:
                    pass
        if notes:
            data["Note moyenne /20"] = round(sum(notes)/len(notes), 1)

        # Critères (like / dislike)
        full_text = soup.get_text("\n")
        for line in full_text.splitlines():
            if "aiment" not in line.lower():
                continue
            lower = line.lower()
            if "fiabilit" in lower: data["Fiabilité"] = line.strip()
            if "consommation" in lower: data["Consommation"] = line.strip()
            if "entretien" in lower: data["Entretien (coût)"] = line.strip()
            if "agrément" in lower: data["Agrément"] = line.strip()
            if "puissance moteur" in lower: data["Puissance moteur"] = line.strip()
            if "bruit moteur" in lower: data["Bruit moteur"] = line.strip()

        # Plaintes : avis <12/20 avec description >20 chars
        plaintes = []
        for row in soup.select("tr"):
            cells = row.find_all("td")
            if len(cells) < 2: continue
            note_txt = cells[0].get_text(strip=True)
            desc = cells[1].get_text(strip=True)
            m = re.match(r"(\d{1,2}(?:\.\d)?)/20", note_txt)
            if not m: continue
            try:
                note = float(m.group(1))
            except ValueError:
                continue
            if note < 12 and len(desc) > 20:
                plaintes.append(f"[{note_txt}] {desc[:120]}")
        data["Plaintes"] = " | ".join(plaintes[:5])

    except Exception as e:
        print("   ❌ Erreur scraping Fiches-Auto:", e)

    return data


# ─────────────────────────────
# 3) Pipeline CSV → CSV enrichi
# ─────────────────────────────
if __name__ == "__main__":
    input_csv = "leboncoin_ct_details.csv"  # CSV LBC existant
    output_csv = "leboncoin_ct_fiabilite.csv"

    with open(input_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    enriched = []
    for i, row in enumerate(rows, 1):
        print(f"\n[{i}/{len(rows)}] {row.get('marque')} {row.get('modele')}")

        # 1) trouver fiches-auto
        try:
            fiches_url = find_fiches_url(row.get("marque",""), row.get("modele",""))
            row["Fiches URL"] = fiches_url
        except Exception as e:
            print("   ❌ Erreur recherche Fiches-Auto:", e)
            row["Fiches URL"] = ""

        # 2) scraper Fiches-Auto
        if fiches_url:
            fiab = scrape_fiches(fiches_url)
            row.update(fiab)

        enriched.append(row)
        time.sleep(DELAY)

    # Champs du CSV final = union de toutes les clés
    fieldnames = []
    for r in enriched:
        for k in r.keys():
            if k not in fieldnames:
                fieldnames.append(k)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)

    print(f"\n✅ CSV enrichi exporté : {output_csv} ({len(enriched)} lignes)")