import logging
import re
import time
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


def bulk_scrape_vehicles(progress_callback=None) -> list[dict]:
    """Scrape all brands and models. Returns list of vehicle dicts."""
    vehicles = []
    brand_urls = scrape_all_brands()
    logger.info("Found %d brands to scrape", len(brand_urls))

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
                vehicles.append(vehicle)
                if progress_callback:
                    progress_callback(vehicle)
                logger.info("Scraped: %s %s", vehicle["brand"], vehicle["model"])

    return vehicles
