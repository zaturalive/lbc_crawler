import logging
import re
import time
import unicodedata
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.fiches-auto.fr"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
RATE_LIMIT = 1


def _get(url: str) -> Optional[BeautifulSoup]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        time.sleep(RATE_LIMIT)
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        logger.warning("GET %s failed: %s", url, exc)
        return None


def scrape_all_brands() -> list[str]:
    """Return list of brand page URLs from /fiabilite-auto/."""
    soup = _get(f"{BASE_URL}/fiabilite-auto/")
    if not soup:
        return []
    links = [
        urljoin(BASE_URL, a.get("href", ""))
        for a in soup.find_all("a", href=True)
        if re.match(r"^/fiabilite-[a-z\-]+/$", a.get("href", ""))
    ]
    return list(dict.fromkeys(links))


def _parse_model_link(link_text: str, href: str, brand_slug: str) -> dict:
    """Extract model name and year range from link text like 'Clio 42012-2019'."""
    # Extract years: "2012-2019" or "2012 - 2019" or just "2012"
    year_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})?', link_text)
    year_start = int(year_match.group(1)) if year_match else None
    year_end_raw = year_match.group(2) if year_match else None
    year_end = int(year_end_raw) if year_end_raw else None
    
    # Model name = everything before the year
    if year_match:
        model_name = link_text[:year_match.start()].strip()
    else:
        # No year found, try to strip trailing 4-digit number
        model_name = re.sub(r'\d{4}.*$', '', link_text).strip()
    
    # Clean model name
    model_name = re.sub(r'\s+', ' ', model_name).strip()
    if not model_name:
        # Fallback: parse from URL
        slug = href.split("/")[-1].replace(".php", "")
        # fiabilite-84-pannes-renault-clio-4 -> extract after brand_slug
        parts = slug.split(f"-{brand_slug}-", 1)
        model_name = parts[1].replace("-", " ").title() if len(parts) > 1 else slug
    
    brand_name = brand_slug.replace("-", " ").title()
    
    return {
        "name": model_name,
        "brand": brand_name,
        "url": urljoin(BASE_URL, href),
        "brand_slug": brand_slug,
        "year_start": year_start,
        "year_end": year_end,
    }


def scrape_brand_models(brand_url: str) -> list[dict]:
    """Return list of model info dicts for all models of a brand."""
    soup = _get(brand_url)
    if not soup:
        return []

    brand_slug = brand_url.rstrip("/").split("/")[-1].replace("fiabilite-", "")
    models = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "pannes" in href and href.startswith(f"/fiabilite-{brand_slug}/"):
            link_text = a.get_text(strip=True)
            model_info = _parse_model_link(link_text, href, brand_slug)
            models.append(model_info)
    return models


def scrape_vehicle_page(url: str, brand_slug: str, model_name: str = None, year_start: int = None, year_end: int = None) -> Optional[dict]:
    """Scrape a single model reliability page. Returns dict or None."""
    soup = _get(url)
    if not soup:
        return None

    brand_name = brand_slug.replace("-", " ").title()

    # If model_name not provided, try to extract from title
    if not model_name:
        title = soup.title.get_text(strip=True) if soup.title else ""
        # Title format: "Tous les problèmes sur {Brand} {Model} {year}-{year}"
        title_match = re.search(r'sur\s+\S+\s+(.+?)\s+\d{4}', title, re.IGNORECASE)
        model_name = title_match.group(1).strip() if title_match else "Inconnu"
    
    # If years not provided, try to extract from page title
    if not year_start:
        title = soup.title.get_text(strip=True) if soup.title else ""
        year_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4})?', title)
        year_start = int(year_match.group(1)) if year_match else None
        year_end_raw = year_match.group(2) if year_match else None
        year_end = int(year_end_raw) if year_end_raw else None

    # Extract issues from tab_fiabili tables
    # Each table has: row1 = intiu_fiabilite (names), row2 = donnee_fiabilite (counts)
    issues_dict = {}  # {name: count}
    total_issues = 0
    fiabili_tables = soup.find_all("table", class_="tab_fiabili")

    for table in fiabili_tables:
        names = [td.get_text(strip=True) for td in table.find_all("td", class_="intiu_fiabilite")]
        counts_raw = [td.get_text(strip=True) for td in table.find_all("td", class_="donnee_fiabilite")]
        
        for name, count_str in zip(names, counts_raw):
            try:
                count = int(count_str)
                total_issues += count
                if count > 0 and name:
                    # Accumulate counts for same issue name across motor variants
                    issues_dict[name] = issues_dict.get(name, 0) + count
            except ValueError:
                continue

    # Build common_issues list: only issues with count > 0, sorted by count desc
    common_issues = []
    for name, count in sorted(issues_dict.items(), key=lambda x: -x[1]):
        common_issues.append(f"{name}: {count} témoignage{'s' if count > 1 else ''}")

    # Reliability score: 0-10, 10 = very reliable (0 issues), 0 = many issues
    # None if no data tables found at all (page has no stats).
    # Normalize: most cars have 0-100 total issues, cap at 50 for scale.
    if not fiabili_tables:
        reliability_score = None
    elif total_issues == 0:
        reliability_score = 10
    else:
        reliability_score = max(0, round(10 - (total_issues / 5)))

    # Extract narrative "Problèmes les plus connus" section.
    # fiches-auto.fr has a qualitative text block (per engine variant) in addition
    # to the stats tables. We look for a heading containing "connu" or "problème"
    # and collect the paragraphs that follow it.
    known_issues_text: list[str] = []
    known_section = None

    # Strategy 1: find heading tag containing the section title
    for tag in soup.find_all(re.compile(r'^h[2-4]$')):
        text = tag.get_text(strip=True).lower()
        if 'connu' in text or ('probl' in text and 'plus' in text):
            known_section = tag
            break

    # Strategy 2: fallback — look for a bold/strong span with that keyword
    if not known_section:
        for tag in soup.find_all(['strong', 'b', 'span']):
            text = tag.get_text(strip=True).lower()
            if 'connu' in text or ('probl' in text and 'plus' in text):
                known_section = tag
                break

    if known_section:
        # Collect sibling/following paragraphs until the next heading
        for sibling in known_section.find_next_siblings():
            if sibling.name and re.match(r'^h[2-4]$', sibling.name):
                break  # stop at next section
            if sibling.name in ('p', 'div'):
                raw = sibling.get_text(separator=' ', strip=True)
                if raw and len(raw) > 15:
                    known_issues_text.append(raw)

    return {
        "brand": brand_name,
        "model": model_name,
        "year_start": year_start,
        "year_end": year_end,
        "reliability_score": reliability_score,
        "total_testimonials": total_issues,
        "common_issues": common_issues,
        "known_issues_text": known_issues_text,
        "source_url": url,
    }


def _normalize(text: str) -> str:
    """Lowercase, remove accents, collapse spaces."""
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_str.lower()).strip()


RANKING_PAGES = [
    ("mini-citadines", "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/mini-citadines.php"),
    ("citadines",      "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/citadines.php"),
    ("compactes",      "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/compactes.php"),
    ("berlines",       "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/berlines.php"),
    ("monospaces-compacts", "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/monospaces-compacts.php"),
    ("monospaces",     "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/monospaces.php"),
    ("4x4-suv",        "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/4x4.php"),
    ("coupes",         "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/coupes.php"),
    ("cabriolets",     "https://www.fiches-auto.fr/articles-auto/classement-comparatif-fiabilite/cabriolets.php"),
]


def scrape_reliability_ranking() -> dict:
    """
    Scrape the 9 fiches-auto.fr reliability ranking sub-pages.

    Returns a dict keyed by (brand_normalized, model_normalized) with value
    (score_int, category_str) where score_int = round(float(X.X) * 10) (scale 0-100).

    Example: { ("suzuki", "swift 4"): (90, "citadines") }
    Scores are decimal (e.g. 8.9/10 -> 89, 9/10 -> 90).
    """
    ranking: dict = {}

    for category, url in RANKING_PAGES:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser", from_encoding="iso-8859-1")
        except Exception as exc:
            logger.warning("scrape_reliability_ranking [%s] failed: %s", category, exc)
            time.sleep(RATE_LIMIT)
            continue

        # Strategy: find all <td> with background-color in style that contain X/10 or X.X/10.
        # Each such TD is the score cell; its parent <tr> also contains the vehicle TD.
        entries_found = 0
        for score_td in soup.find_all("td", style=True):
            style = score_td.get("style", "")
            if "background-color" not in style:
                continue
            score_text = score_td.get_text(separator=" ", strip=True)
            score_match = re.search(r"(\d+(?:\.\d+)?)/10", score_text)
            if not score_match:
                continue

            # Get parent <tr> and find vehicle <td> (the sibling with a "Fiabilite" link)
            tr = score_td.parent
            if not tr or tr.name != "tr":
                continue

            vehicle_link = None
            for td in tr.find_all("td"):
                link = td.find("a", href=True)
                if link and "fiabilit" in link.get_text().lower():
                    vehicle_link = link
                    break

            if not vehicle_link:
                continue

            link_text = vehicle_link.get_text(separator=" ", strip=True)
            # Parse: "Fiabilite Brand Model (+)" -> brand + model
            cleaned = re.sub(r"fiabilit[eé]\s+", "", link_text, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r"\s*\([+-]\)\s*$", "", cleaned).strip()
            parts = cleaned.split(None, 1)
            if not parts:
                continue
            brand_n = _normalize(parts[0])
            model_n = _normalize(parts[1]) if len(parts) > 1 else ""
            if not brand_n:
                continue

            score_int = round(float(score_match.group(1)) * 10)
            ranking[(brand_n, model_n)] = (score_int, category)
            entries_found += 1

        logger.info("scrape_reliability_ranking [%s]: %d entries found", category, entries_found)
        time.sleep(RATE_LIMIT)

    logger.info("scrape_reliability_ranking: %d total entries parsed", len(ranking))
    return ranking


def bulk_scrape_vehicles(progress_callback=None) -> list[dict]:
    """Scrape all brands and models. Returns list of vehicle dicts."""
    vehicles = []
    brand_urls = scrape_all_brands()
    logger.info("Found %d brands to scrape", len(brand_urls))

    # Pre-fetch reliability ranking once for all vehicles
    reliability_map = scrape_reliability_ranking()
    logger.info("Reliability ranking loaded: %d entries", len(reliability_map))

    for brand_url in brand_urls:
        models = scrape_brand_models(brand_url)
        logger.info("Brand %s: %d models", brand_url, len(models))

        for m in models:
            vehicle = scrape_vehicle_page(
                url=m["url"],
                brand_slug=m["brand_slug"],
                model_name=m["name"],
                year_start=m.get("year_start"),
                year_end=m.get("year_end"),
            )
            if vehicle:
                # Enrich with reliability score and rank if available
                brand_n = _normalize(vehicle["brand"])
                model_n = _normalize(vehicle["model"])

                # Try exact match first
                rank_info = reliability_map.get((brand_n, model_n))

                # Fallback: partial match on first word of model
                if not rank_info:
                    model_short = model_n.split()[0] if model_n else ""
                    for (b, m_key), info in reliability_map.items():
                        if b == brand_n and model_short and (
                            m_key.startswith(model_short) or model_short.startswith(m_key)
                        ):
                            rank_info = info
                            break

                if rank_info:
                    score, category = rank_info
                    vehicle["reliability_score"] = score    # 0-100 (e.g. 90 for 9/10)
                    vehicle["reliability_rank"] = category  # e.g. "citadines"
                else:
                    vehicle["reliability_rank"] = None

                vehicles.append(vehicle)
                if progress_callback:
                    progress_callback(vehicle)
                logger.info(
                    "Scraped: %s %s (score: %s, rank: %s)",
                    vehicle["brand"], vehicle["model"],
                    vehicle.get("reliability_score"), vehicle.get("reliability_rank"),
                )

    return vehicles
