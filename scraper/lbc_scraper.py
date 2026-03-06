import os
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import lbc

from regex_engine import RegexEngine

logger = logging.getLogger(__name__)

LBC_USER_AGENT = os.getenv("LBC_USER_AGENT", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
MAX_PAGES = int(os.getenv("LBC_MAX_PAGES", "5"))
RATE_LIMIT_MIN = float(os.getenv("LBC_RATE_MIN", "1.0"))
RATE_LIMIT_MAX = float(os.getenv("LBC_RATE_MAX", "2.0"))


@dataclass
class SearchFilters:
    brand: Optional[str] = None
    model: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    mileage_max: Optional[int] = None
    year_min: Optional[int] = None
    horsepower_min: Optional[int] = None
    horsepower_max: Optional[int] = None
    gearbox: Optional[str] = None
    extra_patterns: list[dict] = field(default_factory=list)


def _build_search_url(filters: SearchFilters) -> str:
    base = "https://www.leboncoin.fr/recherche?category=2"
    params = []
    if filters.price_min or filters.price_max:
        lo = filters.price_min or ""
        hi = filters.price_max or ""
        params.append(f"price={lo}-{hi}")
    if filters.year_min:
        params.append(f"regdate={filters.year_min}-max")
    if filters.mileage_max:
        params.append(f"mileage=0-{filters.mileage_max}")
    if filters.gearbox == "manual":
        params.append("gearbox=1")
    elif filters.gearbox == "automatic":
        params.append("gearbox=2")
    params.append("owner_type=private")
    params.append("sort=time&order=desc")
    url = base + ("&" + "&".join(params) if params else "")
    return url


def _extract_attribute(ad, key: str, default=None):
    try:
        attrs = getattr(ad, "attributes", {}) or {}
        if isinstance(attrs, dict):
            return attrs.get(key, default)
        for attr in attrs:
            if getattr(attr, "key", None) == key:
                return getattr(attr, "value", default)
    except Exception:
        pass
    return default


def _gearbox_label(raw: str) -> Optional[str]:
    if not raw:
        return None
    raw = str(raw).lower()
    if "1" in raw or "manuelle" in raw or "manual" in raw:
        return "manual"
    if "2" in raw or "automatique" in raw or "automatic" in raw:
        return "automatic"
    return None


class LBCScraper:
    def __init__(self):
        self._client = lbc.Client()
        self._regex_engine = RegexEngine()

    def search(self, filters: SearchFilters) -> list[dict]:
        url = _build_search_url(filters)
        results = []
        for page in range(1, MAX_PAGES + 1):
            try:
                ads = self._client.search(url, page=page)
            except Exception as exc:
                logger.warning("LBC search failed on page %d: %s", page, exc)
                break
            if not ads:
                break
            for ad in ads:
                try:
                    listing = self._parse_ad(ad, filters)
                    if listing:
                        results.append(listing)
                except Exception as exc:
                    logger.warning("Failed to parse ad %s: %s", getattr(ad, "id", "?"), exc)
            time.sleep(random.uniform(RATE_LIMIT_MIN, RATE_LIMIT_MAX))
        return results

    def _parse_ad(self, ad, filters: SearchFilters) -> Optional[dict]:
        description = getattr(ad, "body", "") or ""
        matched_keywords = self._regex_engine.match(description, filters.extra_patterns)

        brand = filters.brand or _extract_attribute(ad, "brand") or ""
        model = filters.model or _extract_attribute(ad, "model") or ""

        raw_gearbox = _extract_attribute(ad, "gearbox")
        gearbox = _gearbox_label(str(raw_gearbox) if raw_gearbox else "")

        raw_hp = _extract_attribute(ad, "horse_power_din") or _extract_attribute(ad, "horse_power")
        try:
            horsepower = int(str(raw_hp).split()[0]) if raw_hp else None
        except (ValueError, IndexError):
            horsepower = None

        raw_km = _extract_attribute(ad, "mileage")
        try:
            mileage = int(str(raw_km).replace(" ", "").replace("km", "")) if raw_km else None
        except ValueError:
            mileage = None

        raw_year = _extract_attribute(ad, "regdate") or _extract_attribute(ad, "vehicle_damage")
        try:
            year = int(str(raw_year)[:4]) if raw_year and str(raw_year)[:4].isdigit() else None
        except (ValueError, TypeError):
            year = None

        price = None
        try:
            price_obj = getattr(ad, "price", None)
            if price_obj:
                price = int(str(price_obj).replace(" ", "").replace("€", ""))
        except (ValueError, TypeError):
            pass

        return {
            "lbc_id": str(getattr(ad, "id", "")),
            "title": str(getattr(ad, "subject", "") or ""),
            "price": price,
            "year": year,
            "mileage": mileage,
            "horsepower": horsepower,
            "gearbox": gearbox,
            "location": str(getattr(ad, "location", {}).get("city", "") if isinstance(getattr(ad, "location", None), dict) else ""),
            "description": description,
            "url": str(getattr(ad, "url", "") or ""),
            "matched_keywords": matched_keywords,
            "brand": brand,
            "model": model,
        }
