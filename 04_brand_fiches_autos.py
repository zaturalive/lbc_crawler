#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import unicodedata
import re
import logging
import time

# -----------------------
# CONFIG
# -----------------------
MARQUES = [
    "Alfa-Romeo"
]
BASE_URL = "https://www.fiches-auto.fr/articles-auto/fiabilite/"
DELAY = 1.5
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.google.com/",
}

logging.basicConfig(filename="scrap_errors.log", level=logging.WARNING, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# -----------------------
# UTILITAIRES
# -----------------------
def normalize_text(s):
    if not s:
        return ""
    s = s.lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_avis(soup):
    """Récupère la synthèse des avis"""
    avis = {}
    div = soup.find("div", text=re.compile("Synthèse de vos"))
    if not div:
        div = soup.find("div")  # fallback
    text = div.get_text(" ", strip=True) if div else ""
    
    # Regex pour récupérer les "aiment" et "n'aiment pas"
    pattern = re.compile(r"([\w\s\(\)/]+)\s*:\s*(?:<.*?>)?(\d+)?\s*aiment\s*(?:<.*?>)?(?:,?\s*(\d+)?\s*n'?aiment pas)?", re.I)
    
    for line in text.split("\n"):
        match = re.findall(r"([\w\s\(\)/]+)\s*:\s*(\d+)?\s*aiment\s*(\d+)?\s*n'?aiment pas", line, re.I)
        if match:
            for m in match:
                key = normalize_text(m[0])
                avis[key] = {"aiment": int(m[1]), "naiment_pas": int(m[2])}
    return avis

def parse_fiabilite_tables(soup):
    fiab = {}
    tables = soup.find_all("table", class_="tab_fiabili")
    for table in tables:
        headers = [normalize_text(td.get_text(strip=True)) for td in table.find_all("td", class_="intiu_fiabilite")]
        values = [int(td.get_text(strip=True)) for td in table.find_all("td", class_="donnee_fiabilite")]
        for h, v in zip(headers, values):
            fiab[h] = v
    return fiab

def scrap_modele_fiches(h2):
    """Scrap les fiches d'un modèle"""
    fiches = {}
    links = h2.find_next("ul").find_all("a") if h2.find_next("ul") else []
    for a in links:
        titre = normalize_text(a.get_text())
        href = a.get("href")
        url = f"https://www.fiches-auto.fr{href}" if href else ""
        if url:
            try:
                r = requests.get(url, headers=HEADERS, timeout=15)
                soup = BeautifulSoup(r.text, "html.parser")
                avis = extract_avis(soup)
                fiab = parse_fiabilite_tables(soup)
                fiches[titre] = {"url": url, "avis": avis, "fiabilite_tables": fiab}
            except Exception as e:
                logging.warning(f"Erreur scrap {url} - {e}")
            time.sleep(DELAY)
    return fiches

def scrap_marque(marque):
    data = {}
    url = f"{BASE_URL}{normalize_text(marque)}.php"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            logging.warning(f"{url} - Status {r.status_code}")
            return data
        soup = BeautifulSoup(r.text, "html.parser")
        h2s = soup.find_all("h2")
        for h2 in h2s:
            modele = normalize_text(h2.get_text())
            fiches = scrap_modele_fiches(h2)
            if fiches:
                data[modele] = fiches
    except Exception as e:
        logging.warning(f"Erreur scrap {url} - {e}")
    return data

# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    fiabilite_json = {}
    for marque in MARQUES:
        print(f"Scrap marque: {marque}")
        fiabilite_json[normalize_text(marque)] = scrap_marque(marque)
        time.sleep(DELAY)

    with open("fiabilite_voitures.json", "w", encoding="utf-8") as f:
        json.dump(fiabilite_json, f, indent=2, ensure_ascii=False)

    print("✅ Scrap terminé, JSON créé : fiabilite_voitures.json")