import math
import os
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests

import lbc
import lbc.model.enums

from regex_engine import RegexEngine

logger = logging.getLogger(__name__)

MAX_PAGES = int(os.getenv("LBC_MAX_PAGES", "5"))
RATE_LIMIT_MIN = float(os.getenv("LBC_RATE_MIN", "1.0"))
RATE_LIMIT_MAX = float(os.getenv("LBC_RATE_MAX", "2.0"))

FUEL_LBC_MAP = {
    "essence": "1",
    "diesel": "2",
    "gpl": "3",
    "electrique": "4",
    "hybride": "5",
}


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
    fuel: Optional[str] = None
    city: Optional[str] = None
    radius: Optional[int] = None  # km, default 30
    extra_patterns: list[dict] = field(default_factory=list)


def _extract_attribute(ad, key: str, default=None):
    try:
        for attr in (getattr(ad, "attributes", []) or []):
            if getattr(attr, "key", None) == key:
                return getattr(attr, "value", default)
    except Exception:
        pass
    return default


def _extract_attribute_label(ad, key: str, default=None):
    """Extract attribute using value_label (human-readable label in French)."""
    try:
        for attr in (getattr(ad, "attributes", []) or []):
            if getattr(attr, "key", None) == key:
                # Prefer value_label, fallback to value
                return getattr(attr, "value_label", None) or getattr(attr, "value", default)
    except Exception:
        pass
    return default


def _gearbox_label(raw: str) -> Optional[str]:
    if not raw:
        return None
    raw = str(raw).lower()
    if raw in ("1", "manuelle", "manual") or "manuelle" in raw:
        return "manual"
    if raw in ("2", "automatique", "automatic") or "automatique" in raw:
        return "automatic"
    return None


def _geocode_city(city_name: str) -> Optional[tuple[float, float]]:
    """Geocode city name to (lat, lng) using Nominatim OSM. Returns None on failure."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city_name, "format": "json", "limit": 1, "countrycodes": "fr"},
            headers={"User-Agent": "find_my_car/1.0 (dev)"},
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as exc:
        logger.warning("Geocoding failed for '%s': %s", city_name, exc)
    return None


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcule la distance orthodromique entre deux points GPS en km."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


class LBCScraper:
    def __init__(self):
        self._client = lbc.Client()
        self._regex_engine = RegexEngine()

    def search(self, filters: SearchFilters) -> list[dict]:
        text = " ".join(filter(None, [filters.brand, filters.model]))
        results = []

        # Geocode city ONCE before the page loop to avoid rate-limiting Nominatim.
        # Raises ValueError if geocoding fails so the caller can return a 422 instead
        # of silently falling back to a nationwide search.
        city_coords: Optional[tuple[float, float]] = None
        if filters.city:
            city_coords = _geocode_city(filters.city)
            if city_coords is None:
                raise ValueError(
                    f"Impossible de géocoder la ville '{filters.city}'. "
                    "Vérifie l'orthographe ou réessaie dans quelques secondes."
                )
            logger.info(
                "Searching near %s (%.4f,%.4f) radius=%dkm",
                filters.city, city_coords[0], city_coords[1], filters.radius or 30,
            )

        for page in range(1, MAX_PAGES + 1):
            try:
                search_kwargs: dict = {
                    "text": text or None,
                    "category": lbc.model.enums.Category.VEHICULES_VOITURES,
                    "page": page,
                    "limit": 35,
                    "owner_type": lbc.model.enums.OwnerType.PRIVATE,
                }
                
                # Add native LBC filter kwargs if supported
                if filters.price_min is not None or filters.price_max is not None:
                    price_min = filters.price_min or 0
                    price_max = filters.price_max or 10000000
                    search_kwargs["price"] = (price_min, price_max)
                
                if filters.mileage_max is not None:
                    search_kwargs["mileage"] = (0, filters.mileage_max)
                
                if filters.year_min is not None:
                    # regdate must be a tuple (min_year, max_year)
                    search_kwargs["regdate"] = (filters.year_min, 2100)
                
                if filters.fuel is not None and filters.fuel in FUEL_LBC_MAP:
                    search_kwargs["fuel"] = [FUEL_LBC_MAP[filters.fuel]]

                if city_coords is not None:
                    lat, lng = city_coords
                    radius_m = (filters.radius or 30) * 1000
                    search_kwargs["locations"] = [lbc.City(lat=lat, lng=lng, radius=radius_m, city=filters.city)]
                
                ads = self._client.search(**{k: v for k, v in search_kwargs.items() if v is not None})
            except ValueError:
                raise
            except Exception as exc:
                logger.warning("LBC search failed on page %d: %s", page, exc)
                break

            if not ads or not ads.ads:
                break

            for ad in ads.ads:
                try:
                    listing = self._parse_ad(ad, filters)
                    if listing:
                        results.append(listing)
                except Exception as exc:
                    logger.warning("Failed to parse ad %s: %s", getattr(ad, "id", "?"), exc)

            time.sleep(random.uniform(RATE_LIMIT_MIN, RATE_LIMIT_MAX))
        
        # Apply post-filter to ensure filters are correctly applied
        results = self._post_filter(results, filters, city_coords)
        return results

    def _post_filter(
        self,
        listings: list[dict],
        filters: SearchFilters,
        city_coords: Optional[tuple[float, float]] = None,
    ) -> list[dict]:
        """Apply post-filter to ensure all filters are correctly applied.
        
        This is a safety net for filters that may not be fully supported by the lbc library,
        and ensures consistent filtering behavior.
        """
        result = []
        for listing in listings:
            # Filter by price
            if filters.price_min is not None and listing.get("price"):
                if listing["price"] < filters.price_min:
                    continue
            if filters.price_max is not None and listing.get("price"):
                if listing["price"] > filters.price_max:
                    continue
            
            # Filter by mileage
            if filters.mileage_max is not None and listing.get("mileage"):
                if listing["mileage"] > filters.mileage_max:
                    continue
            
            # Filter by year (using regdate)
            if filters.year_min is not None and listing.get("year"):
                if listing["year"] < filters.year_min:
                    continue
            
            # Filter by gearbox
            if filters.gearbox is not None and listing.get("gearbox"):
                if listing["gearbox"] != filters.gearbox:
                    continue
            
            # Filter by fuel
            if filters.fuel is not None and listing.get("fuel_type"):
                fuel_label = listing["fuel_type"].lower()
                filter_label = filters.fuel.lower()
                if filter_label not in fuel_label:
                    continue
            
            # Filter by horsepower
            if filters.horsepower_min is not None and listing.get("horsepower"):
                if listing["horsepower"] < filters.horsepower_min:
                    continue
            if filters.horsepower_max is not None and listing.get("horsepower"):
                if listing["horsepower"] > filters.horsepower_max:
                    continue

            # Filter by geographic distance (Haversine) — safety net against LBC API imprecision
            if city_coords and filters.radius and listing.get("lat") and listing.get("lng"):
                city_lat, city_lng = city_coords
                dist_km = _haversine_km(city_lat, city_lng, listing["lat"], listing["lng"])
                if dist_km > filters.radius:
                    logger.debug(
                        "Excluded out-of-range listing %s (%.1fkm from %s)",
                        listing.get("lbc_id"), dist_km, filters.city,
                    )
                    continue
            
            result.append(listing)
        
        return result

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
            price_raw = getattr(ad, "price", None)
            if price_raw is not None:
                price = int(float(price_raw))
        except (ValueError, TypeError):
            pass

        loc = getattr(ad, "location", None)
        if loc is not None and not isinstance(loc, dict):
            location_str = getattr(loc, "city", "") or getattr(loc, "city_label", "") or ""
            ad_lat = getattr(loc, "lat", None)
            ad_lng = getattr(loc, "lng", None)
        elif isinstance(loc, dict):
            location_str = loc.get("city", "")
            ad_lat = loc.get("lat")
            ad_lng = loc.get("lng")
        else:
            location_str = ""
            ad_lat = None
            ad_lng = None

        # Extract fuel using value_label (human-readable label)
        fuel_type = _extract_attribute_label(ad, "fuel")

        # Extract other enriched attributes
        doors = _extract_attribute(ad, "doors")
        seats = _extract_attribute(ad, "seats")
        color = _extract_attribute_label(ad, "color")
        vehicle_damage = _extract_attribute(ad, "vehicle_damage")

        return {
            "lbc_id": str(getattr(ad, "id", "")),
            "title": str(getattr(ad, "subject", "") or ""),
            "price": price,
            "year": year,
            "mileage": mileage,
            "horsepower": horsepower,
            "gearbox": gearbox,
            "fuel_type": fuel_type,
            "doors": doors,
            "seats": seats,
            "color": color,
            "vehicle_damage": vehicle_damage,
            "location": location_str,
            "lat": ad_lat,
            "lng": ad_lng,
            "description": description,
            "url": str(getattr(ad, "url", "") or ""),
            "matched_keywords": matched_keywords,
            "brand": brand,
            "model": model,
        }
