"""
Scraper unit tests with mocked lbc.Client.
"""
from dataclasses import dataclass
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from lbc_scraper import LBCScraper, SearchFilters


@dataclass
class FakeAd:
    id: str = "abc123"
    subject: str = "Peugeot 308 2015"
    body: str = "CT valide, carte grise fournie."
    url: str = "https://www.leboncoin.fr/voitures/abc123"
    price: int = 5000
    location: dict = None
    attributes: list = None

    def __post_init__(self):
        if self.location is None:
            self.location = MagicMock(city="Paris", city_label="Paris")
        if self.attributes is None:
            # Create proper attribute objects
            self.attributes = [
                MagicMock(key="brand", value="Peugeot"),
                MagicMock(key="model", value="308"),
                MagicMock(key="regdate", value="2015"),
                MagicMock(key="mileage", value="90000"),
                MagicMock(key="horse_power_din", value="110"),
                MagicMock(key="gearbox", value="1"),
                MagicMock(key="fuel", value="2", value_label="Diesel"),
                MagicMock(key="doors", value="5"),
                MagicMock(key="seats", value="5"),
                MagicMock(key="color", value="blanc", value_label="Blanc"),
                MagicMock(key="vehicle_damage", value="Bon état"),
            ]


def create_mock_lbc_client(num_pages=1):
    """Helper to create mock LBC client with configurable pagination."""
    client = MagicMock()
    
    # Create initial search result
    search_results = MagicMock()
    search_results.ads = [FakeAd()]
    
    # Create empty result to stop pagination
    empty_result = MagicMock()
    empty_result.ads = []
    
    # Build side_effect list: num_pages of results, then empty
    side_effects = [search_results] * num_pages + [empty_result]
    client.search.side_effect = side_effects
    
    return client


@pytest.fixture
def mock_lbc_client():
    with patch("lbc_scraper.lbc") as mock_lbc:
        client = create_mock_lbc_client(num_pages=1)
        mock_lbc.Client.return_value = client
        yield client


def test_search_returns_data_contract(mock_lbc_client):
    scraper = LBCScraper()
    filters = SearchFilters(brand="Peugeot", model="308")
    results = scraper.search(filters)

    assert len(results) == 1
    listing = results[0]
    required_keys = ["lbc_id", "title", "price", "year", "mileage", "horsepower",
                     "gearbox", "fuel_type", "doors", "seats", "color", "vehicle_damage",
                     "location", "description", "url", "matched_keywords", "brand", "model"]
    for key in required_keys:
        assert key in listing, f"Missing key: {key}"


def test_search_applies_regex(mock_lbc_client):
    scraper = LBCScraper()
    filters = SearchFilters()
    results = scraper.search(filters)

    assert "CT valide" in results[0]["matched_keywords"]
    assert "Carte grise" in results[0]["matched_keywords"]


def test_search_handles_empty_results():
    """Test that search handles empty results."""
    with patch("lbc_scraper.lbc"):
        scraper = LBCScraper()
        # Mock the _client directly
        empty_result = MagicMock()
        empty_result.ads = []
        scraper._client.search.return_value = empty_result
        
        results = scraper.search(SearchFilters())
        assert results == []


def test_search_handles_ad_parse_error(mock_lbc_client):
    bad_ad = MagicMock(spec=[])
    mock_lbc_client.search.side_effect = [Exception("network error")]
    scraper = LBCScraper()
    results = scraper.search(SearchFilters())
    assert results == []
