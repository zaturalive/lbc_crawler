import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CACHE_DIR = Path(os.getenv("FICHES_AUTO_CACHE_DIR", "/app/cache"))
CACHE_TTL_DAYS = int(os.getenv("FICHES_AUTO_CACHE_TTL_DAYS", "7"))
RATE_LIMIT_SECONDS = float(os.getenv("FICHES_AUTO_RATE_LIMIT", "2.0"))
BASE_URL = "https://www.fiches-auto.fr"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class FichesAutoScraper:
    def __init__(self):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._cache_file = CACHE_DIR / "fiches_auto_cache.json"
        self._cache = self._load_cache()

    def get_vehicle_data(self, brand: str, model: str) -> Optional[dict]:
        cache_key = f"{brand.lower()}_{model.lower()}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            data = self._scrape(brand, model)
            self._set_cache(cache_key, data)
            return data
        except Exception as exc:
            logger.warning("fiches-auto scraping failed for %s %s: %s", brand, model, exc)
            self._set_cache(cache_key, None)
            return None

    def _scrape(self, brand: str, model: str) -> Optional[dict]:
        search_url = f"{BASE_URL}/recherche/?q={quote_plus(f'{brand} {model}')}"
        resp = requests.get(search_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        time.sleep(RATE_LIMIT_SECONDS)

        soup = BeautifulSoup(resp.text, "html.parser")
        result_link = soup.select_one("a.result-title, a[href*='/voiture/']")
        if not result_link:
            return None

        sheet_url = result_link.get("href", "")
        if not sheet_url.startswith("http"):
            sheet_url = BASE_URL + sheet_url

        resp2 = requests.get(sheet_url, headers=HEADERS, timeout=15)
        resp2.raise_for_status()
        soup2 = BeautifulSoup(resp2.text, "html.parser")

        reliability_score = self._extract_reliability(soup2)
        common_issues = self._extract_common_issues(soup2)

        return {
            "reliability_score": reliability_score,
            "common_issues": common_issues,
        }

    def _extract_reliability(self, soup: BeautifulSoup) -> Optional[int]:
        selectors = [
            "span.note", "div.fiabilite span", ".rating-value", "span[class*='note']",
        ]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                try:
                    raw = el.get_text(strip=True).replace(",", ".").split("/")[0]
                    score = float(raw)
                    return min(10, max(0, round(score)))
                except ValueError:
                    continue
        return None

    def _extract_common_issues(self, soup: BeautifulSoup) -> list[str]:
        issues = []
        selectors = [
            "ul.problemes li", "div.pannes li", ".defauts li", "li[class*='panne']",
        ]
        for sel in selectors:
            items = soup.select(sel)
            if items:
                issues = [el.get_text(strip=True) for el in items[:5] if el.get_text(strip=True)]
                break
        return issues

    def _load_cache(self) -> dict:
        if self._cache_file.exists():
            try:
                return json.loads(self._cache_file.read_text())
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self):
        try:
            self._cache_file.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2))
        except IOError as exc:
            logger.warning("Could not save fiches-auto cache: %s", exc)

    def _get_from_cache(self, key: str) -> Optional[dict]:
        entry = self._cache.get(key)
        if not entry:
            return None
        cached_at = datetime.fromisoformat(entry["cached_at"])
        if datetime.now() - cached_at > timedelta(days=CACHE_TTL_DAYS):
            return None
        return entry.get("data")

    def _set_cache(self, key: str, data: Optional[dict]):
        self._cache[key] = {"data": data, "cached_at": datetime.now().isoformat()}
        self._save_cache()
