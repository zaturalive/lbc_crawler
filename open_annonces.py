#!/usr/bin/env python3
"""
Ouvre les annonces LeBonCoin dans Chrome par plage (ex: 2 à 15)
Utilise : python open_annonces.py
"""

import csv
import subprocess
import sys
import os

CSV_FILE = "leboncoin_ct_ok.csv"

# Chemin Chrome — ajuste si nécessaire
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def charger_urls():
    if not os.path.exists(CSV_FILE):
        print(f"❌ Fichier {CSV_FILE} introuvable. Lance d'abord leboncoin_ct_search.py")
        sys.exit(1)

    urls = []
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("URL") and row["URL"] != "?":
                urls.append((row["Titre"], row["Prix"], row["URL"]))
    return urls

def afficher_liste(urls):
    print(f"\n{'N°':<5} {'Prix':<12} {'Titre'}")
    print("-" * 70)
    for i, (titre, prix, url) in enumerate(urls, 1):
        print(f"{i:<5} {prix:<12} {titre[:55]}")

def ouvrir_dans_chrome(urls, debut, fin):
    liens = [url for _, _, url in urls[debut-1:fin]]
    print(f"\n🚀 Ouverture de {len(liens)} annonces dans Chrome...\n")
    for url in liens:
        subprocess.Popen([CHROME_PATH, url])
    print("✅ Fait !")

if __name__ == "__main__":
    urls = charger_urls()
    afficher_liste(urls)

    print(f"\nTotal : {len(urls)} annonces disponibles")
    print("Entrez la plage à ouvrir (ex: 2 15 pour ouvrir les annonces 2 à 15)")

    try:
        entree = input("Plage (début fin) : ").strip().split()
        debut = int(entree[0])
        fin   = int(entree[1])

        if debut < 1 or fin > len(urls) or debut > fin:
            print(f"❌ Plage invalide. Doit être entre 1 et {len(urls)}")
            sys.exit(1)

        if fin - debut + 1 > 20:
            confirm = input(f"⚠️  Tu vas ouvrir {fin - debut + 1} onglets. Confirmer ? (o/n) : ")
            if confirm.lower() != "o":
                print("Annulé.")
                sys.exit(0)

        ouvrir_dans_chrome(urls, debut, fin)

    except (ValueError, IndexError):
        print("❌ Format invalide. Exemple : 2 15")
