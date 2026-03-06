"""
Tests pour les endpoints FastAPI du scraper.

Utilise TestClient de FastAPI pour tester :
- GET /health
- POST /scrape (avec filtres et patterns)
- POST /scrape/vehicles-catalog
- GET /scrape/vehicles-status
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import dynamique pour éviter les problèmes d'imports dans tests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from main import app, ScrapeRequest


client = TestClient(app)


class TestHealthEndpoint:
    """Tests pour GET /health."""

    def test_health_returns_200(self):
        """GET /health retourne 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self):
        """GET /health retourne {status: 'ok'}."""
        response = client.get("/health")
        assert response.json()["status"] == "ok"

    def test_health_returns_sync_status(self):
        """GET /health inclut sync_status."""
        response = client.get("/health")
        assert "sync_status" in response.json()
        assert "running" in response.json()["sync_status"]


class TestScrapeEndpoint:
    """Tests pour POST /scrape."""

    @patch("main._lbc.search")
    def test_scrape_returns_200(self, mock_search):
        """POST /scrape retourne 200."""
        mock_search.return_value = []
        response = client.post(
            "/scrape",
            json={
                "brand": "Renault",
                "model": "Clio",
                "price_min": 1000,
                "price_max": 5000,
            },
        )
        assert response.status_code == 200

    @patch("main._lbc.search")
    def test_scrape_returns_listings_and_count(self, mock_search):
        """POST /scrape retourne {listings, count}."""
        mock_listing = {
            "lbc_id": "123",
            "title": "Test",
            "price": 3000,
            "year": 2015,
            "mileage": 90000,
            "horsepower": 110,
            "gearbox": "manual",
            "location": "Paris",
            "description": "Test",
            "url": "https://lbc.fr/123",
            "matched_keywords": ["CT valide"],
            "brand": "Renault",
            "model": "Clio",
        }
        mock_search.return_value = [mock_listing]
        response = client.post("/scrape", json={"brand": "Renault"})
        data = response.json()
        assert "listings" in data
        assert "count" in data
        assert data["count"] == 1
        assert len(data["listings"]) == 1

    @patch("main._lbc.search")
    def test_scrape_passes_filters_to_lbc(self, mock_search):
        """POST /scrape passe les filtres au LBCScraper."""
        mock_search.return_value = []
        client.post(
            "/scrape",
            json={
                "brand": "Renault",
                "model": "Clio",
                "price_min": 1000,
                "price_max": 5000,
                "mileage_max": 150000,
                "year_min": 2010,
                "gearbox": "manual",
                "horsepower_min": 100,
                "horsepower_max": 150,
            },
        )
        # Vérifie que search() a été appelée avec SearchFilters
        assert mock_search.called
        call_args = mock_search.call_args
        filters = call_args[0][0]  # Premier argument positional
        assert filters.brand == "Renault"
        assert filters.model == "Clio"
        assert filters.price_min == 1000
        assert filters.price_max == 5000

    @patch("main._lbc.search")
    def test_scrape_with_patterns(self, mock_search):
        """POST /scrape accepte des patterns."""
        mock_search.return_value = []
        response = client.post(
            "/scrape",
            json={
                "brand": "Renault",
                "patterns": [{"name": "CT valide", "pattern": r"\bct\b"}],
            },
        )
        assert response.status_code == 200
        # Vérifie que patterns ont été passés
        call_args = mock_search.call_args
        filters = call_args[0][0]
        assert len(filters.extra_patterns) > 0

    @patch("main._lbc.search")
    def test_scrape_with_custom_regex(self, mock_search):
        """POST /scrape accepte un regex custom."""
        mock_search.return_value = []
        response = client.post(
            "/scrape",
            json={
                "brand": "Renault",
                "custom_regex": r"\bclient\s+satisfait\b",
            },
        )
        assert response.status_code == 200

    @patch("main._lbc.search")
    def test_scrape_rejects_invalid_custom_regex(self, mock_search):
        """POST /scrape rejette un regex invalid."""
        response = client.post(
            "/scrape",
            json={
                "brand": "Renault",
                "custom_regex": "[invalid(",  # Invalid regex
            },
        )
        assert response.status_code == 422

    @patch("main._lbc.search")
    def test_scrape_returns_empty_list_when_no_results(self, mock_search):
        """POST /scrape retourne [] si aucun résultat."""
        mock_search.return_value = []
        response = client.post("/scrape", json={"brand": "NonExistentBrand"})
        data = response.json()
        assert data["count"] == 0
        assert data["listings"] == []

    @patch("main._lbc.search")
    def test_scrape_returns_multiple_listings(self, mock_search):
        """POST /scrape peut retourner plusieurs listings."""
        listings = [
            {
                "lbc_id": str(i),
                "title": f"Listing {i}",
                "price": 3000 + i * 100,
                "year": 2015,
                "mileage": 90000,
                "horsepower": 110,
                "gearbox": "manual",
                "location": "Paris",
                "description": "Test",
                "url": f"https://lbc.fr/{i}",
                "matched_keywords": [],
                "brand": "Renault",
                "model": "Clio",
            }
            for i in range(5)
        ]
        mock_search.return_value = listings
        response = client.post("/scrape", json={"brand": "Renault"})
        data = response.json()
        assert data["count"] == 5
        assert len(data["listings"]) == 5


class TestVehiclesCatalogEndpoint:
    """Tests pour POST /scrape/vehicles-catalog."""

    @patch("main.bulk_scrape_vehicles")
    def test_vehicles_catalog_returns_200(self, mock_bulk):
        """POST /scrape/vehicles-catalog retourne 200 si pas en cours."""
        response = client.post("/scrape/vehicles-catalog")
        assert response.status_code == 200

    @patch("main.bulk_scrape_vehicles")
    def test_vehicles_catalog_returns_started_status(self, mock_bulk):
        """POST /scrape/vehicles-catalog retourne {status: 'started'}."""
        response = client.post("/scrape/vehicles-catalog")
        data = response.json()
        assert data["status"] == "started"

    @patch("main.bulk_scrape_vehicles")
    def test_vehicles_catalog_rejects_concurrent_sync(self, mock_bulk):
        """POST /scrape/vehicles-catalog rejette si sync en cours."""
        # Simuler une première requête
        client.post("/scrape/vehicles-catalog")
        # Manuellement set running = True
        from main import _sync_status
        _sync_status["running"] = True

        try:
            response = client.post("/scrape/vehicles-catalog")
            assert response.status_code == 409
        finally:
            _sync_status["running"] = False


class TestVehiclesStatusEndpoint:
    """Tests pour GET /scrape/vehicles-status."""

    def test_vehicles_status_returns_200(self):
        """GET /scrape/vehicles-status retourne 200."""
        response = client.get("/scrape/vehicles-status")
        assert response.status_code == 200

    def test_vehicles_status_running(self):
        """GET /scrape/vehicles-status retourne {status: 'running'} si en cours."""
        from main import _sync_status

        _sync_status["running"] = True
        try:
            response = client.get("/scrape/vehicles-status")
            data = response.json()
            assert data["status"] == "running"
        finally:
            _sync_status["running"] = False

    def test_vehicles_status_error(self):
        """GET /scrape/vehicles-status retourne {status: 'error'} en cas d'erreur."""
        from main import _sync_status

        _sync_status["running"] = False
        _sync_status["last_error"] = "Test error"
        try:
            response = client.get("/scrape/vehicles-status")
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data
        finally:
            _sync_status["last_error"] = None


class TestScrapeRequestModel:
    """Tests pour ScrapeRequest Pydantic model."""

    def test_scrape_request_all_fields_optional(self):
        """ScrapeRequest a tous les champs optionnels."""
        req = ScrapeRequest()
        assert req.brand is None
        assert req.model is None
        assert req.price_min is None
        assert req.price_max is None
        assert req.mileage_max is None
        assert req.year_min is None
        assert req.horsepower_min is None
        assert req.horsepower_max is None
        assert req.gearbox is None
        assert req.patterns == []
        assert req.custom_regex is None

    def test_scrape_request_accepts_values(self):
        """ScrapeRequest accepte des valeurs."""
        req = ScrapeRequest(
            brand="Renault",
            model="Clio",
            price_min=1000,
            price_max=5000,
        )
        assert req.brand == "Renault"
        assert req.model == "Clio"
        assert req.price_min == 1000
        assert req.price_max == 5000

    def test_scrape_request_accepts_patterns(self):
        """ScrapeRequest accepte une liste de patterns."""
        patterns = [
            {"name": "CT valide", "pattern": r"\bct\b"},
            {"name": "Carte grise", "pattern": r"\bcarte\b"},
        ]
        req = ScrapeRequest(patterns=patterns)
        assert len(req.patterns) == 2
        assert req.patterns[0]["name"] == "CT valide"
