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
    r"(?:\bct\b|\bcontr[oô]le\s+technique\b)",
    re.IGNORECASE
)

def extract_vehicle_data(ad):
    car = {
        "marque": "",
        "modele": "",
        "annee": "",
        "mise_en_circulation": "",
        "km": "",
        "carburant": "",
        "boite": "",
        "puissance_fiscale": "",
        "puissance_din": "",
        "portes": "",
        "places": "",
        "couleur": "",
        "critair": "",
        "norme_euro": "",
        "finition": "",
        "version": "",
        "date_fin_ct": "",
        "etat": "",
        "type_vehicule": "",
    }

    if not hasattr(ad, "attributes"):
        return car

    for attr in ad.attributes:
        key = (attr.key or "").lower()
        val = attr.value_label if attr.value_label else attr.value

        if not val:
            continue

        val = str(val).strip()

        if key == "brand":
            car["marque"] = val

        elif key == "model":
            car["modele"] = val

        elif key == "regdate":
            car["annee"] = val

        elif key == "issuance_date":
            car["mise_en_circulation"] = val

        elif key == "mileage":
            car["km"] = val.replace(" km", "")

        elif key == "fuel":
            car["carburant"] = val

        elif key == "gearbox":
            car["boite"] = val

        elif key == "horsepower":
            car["puissance_fiscale"] = val

        elif key == "horse_power_din":
            car["puissance_din"] = val

        elif key == "doors":
            car["portes"] = val

        elif key == "seats":
            car["places"] = val

        elif key == "vehicule_color":
            car["couleur"] = val

        elif key == "critair":
            car["critair"] = val

        elif key == "vehicle_euro_emissions_standard":
            car["norme_euro"] = val

        elif key == "u_car_finition":
            car["finition"] = val

        elif key == "u_car_version":
            car["version"] = val

        elif key == "vehicle_technical_inspection_a":
            car["date_fin_ct"] = val

        elif key == "vehicle_damage":
            car["etat"] = val

        elif key == "vehicle_type":
            car["type_vehicule"] = val

    return car
def search_with_ct(max_pages=5):
    results = []

    for page in range(1, max_pages + 1):
        print(f"\n=== PAGE {page} ===")

        result = client.search(url=SEARCH_URL, page=page, limit=100, limit_alu=0)

        if not result.ads:
            break

        for ad in result.ads:
            text = f"{ad.subject or ''} {ad.body or ''}"
            if not CT_PATTERN.search(text):
                continue

            car = extract_vehicle_data(ad)

            results.append({
                "Titre": ad.subject,
                "Description": (ad.body or "").replace("\n", " ").strip(),
                "Prix": f"{ad.price} €" if ad.price else "?",
                "Ville": ad.location.city if ad.location else "?",
                "URL": ad.url,
                **car
            })

            print(f"✅ {car['marque']} {car['modele']} ({car['annee']})")

        time.sleep(2)

    return results


if __name__ == "__main__":
    print(f"Démarrage — {datetime.now()}")
    annonces = search_with_ct()

    if annonces:
        with open("leboncoin_ct_details.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=annonces[0].keys())
            writer.writeheader()
            writer.writerows(annonces)

        print("\n📁 Exporté : leboncoin_ct_details.csv")
    else:
        print("❌ Aucune annonce trouvée.")