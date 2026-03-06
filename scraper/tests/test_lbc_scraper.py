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
    attributes: dict = None

    def __post_init__(self):
        if self.location is None:
            self.location = {"city": "Paris"}
        if self.attributes is None:
            self.attributes = {
                "brand": "Peugeot",
                "model": "308",
                "regdate": "2015",
                "mileage": "90000",
                "horse_power_din": "110",
                "gearbox": "1",
            }


@pytest.fixture
def mock_lbc_client():
    with patch("lbc_scraper.lbc") as mock_lbc:
        client = MagicMock()
        client.search.return_value = [FakeAd()]
        mock_lbc.Client.return_value = client
        yield client


def test_search_returns_data_contract(mock_lbc_client):
    scraper = LBCScraper()
    filters = SearchFilters(brand="Peugeot", model="308")
    results = scraper.search(filters)

    assert len(results) == 1
    listing = results[0]
    required_keys = ["lbc_id", "title", "price", "year", "mileage", "horsepower",
                     "gearbox", "location", "description", "url", "matched_keywords", "brand", "model"]
    for key in required_keys:
        assert key in listing, f"Missing key: {key}"


def test_search_applies_regex(mock_lbc_client):
    scraper = LBCScraper()
    filters = SearchFilters()
    results = scraper.search(filters)

    assert "CT valide" in results[0]["matched_keywords"]
    assert "Carte grise" in results[0]["matched_keywords"]


def test_search_handles_empty_results(mock_lbc_client):
    mock_lbc_client.search.return_value = []
    scraper = LBCScraper()
    results = scraper.search(SearchFilters())
    assert results == []


def test_search_handles_ad_parse_error(mock_lbc_client):
    bad_ad = MagicMock(spec=[])
    mock_lbc_client.search.side_effect = [Exception("network error")]
    scraper = LBCScraper()
    results = scraper.search(SearchFilters())
    assert results == []
