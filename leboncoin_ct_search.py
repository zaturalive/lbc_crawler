#!/usr/bin/env python3
import lbc
import re
import time
import csv
from datetime import datetime

client = lbc.Client()

SEARCH_URL = (
    "https://www.leboncoin.fr/recherche?category=2"
    "&price=1400-3000&regdate=2000-max&mileage=50000-200000"
    "&gearbox=1&vehicle_vsp=avecpermis&owner_type=private"
    "&sort=time&order=desc"
)

CT_PATTERN = re.compile(
    r"(?:"
    r"\bct\s*(?:ok|bon|valide|neuf|frais|fait|pass[eé]|r[eé]cent|à jour|a jour|en cours)\b"
    r"|\bct\s*[-–]?\s*(?:moins\s+de\s+)?\d+\s*(?:mois|ans?)\b"
    r"|\bct\s+jusqu[''e]\w*"
    r"|\bcontr[oô]le\s+technique\s*(?:ok|bon|valide|neuf|frais|fait|pass[eé]|r[eé]cent|à jour|a jour|en cours)?\b"
    r"|\bct\b"
    r")",
    re.IGNORECASE
)

def search_with_ct(max_pages=5):
    results = []
    offset = 0

    for page in range(1, max_pages + 1):
        try:
            result = client.search(url=SEARCH_URL, page=page, limit=100, limit_alu=0)
        except Exception as e:
            print(f"[Erreur page {page}] {e}")
            break

        ads = result.ads
        if not ads:
            print(f"Plus d'annonces à la page {page}.")
            break

        print(f"Page {page} — {len(ads)} annonces récupérées")

        for ad in ads:
            title = ad.subject or ""
            body  = ad.body or ""
            text  = f"{title} {body}"
            match = CT_PATTERN.search(text)

            if match:
                price = ad.price if ad.price else None
                url   = ad.url or "?"
                city  = ad.location.city if ad.location else "?"

                results.append({
                    "Titre":    title,
                    "Prix":     f"{price} €" if price else "?",
                    "Ville":    city,
                    "CT match": match.group(0),
                    "URL":      url,
                })
                print(f"  ✅ [{results[-1]['Prix']}] {title} — CT: \"{match.group(0)}\"")
                print(f"      🔗 {url}")

        time.sleep(2)

    return results

if __name__ == "__main__":
    print(f"Démarrage — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    annonces = search_with_ct(max_pages=5)

    if annonces:
        print(f"\n✅ {len(annonces)} annonces avec CT trouvées\n")
        with open("leboncoin_ct_ok.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=annonces[0].keys())
            writer.writeheader()
            writer.writerows(annonces)
        print("📁 Exporté : leboncoin_ct_ok.csv")
    else:
        print("❌ Aucune annonce trouvée.")
