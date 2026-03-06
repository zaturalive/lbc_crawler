"""
Tests pour les filtres LBC — BUG-01 (corrigé).

Ces tests valident que tous les filtres (price, mileage, year, gearbox, horsepower)
fonctionnent correctement dans le post-filtering du scraper LBC.
"""
from unittest.mock import MagicMock, patch
import pytest

from lbc_scraper import LBCScraper, SearchFilters, _extract_attribute, _gearbox_label


def make_mock_ad(
    ad_id="123",
    price=5000,
    mileage="90000",
    year="2015",
    gearbox="1",
    brand="Renault",
    model="Clio",
    horsepower="110",
    subject="Test Ad",
    body="Annonce test",
    url="https://lbc.fr/ad/123",
):
    """Fabrique une mock annonce LBC avec attributs standards."""
    ad = MagicMock()
    ad.id = ad_id
    ad.subject = subject
    ad.body = body
    ad.price = float(price)
    ad.url = url
    ad.location = MagicMock(city=f"City_{ad_id}", city_label=f"City_{ad_id}")

    # Mock attributes comme une liste
    attrs_dict = {
        "brand": brand,
        "model": model,
        "regdate": year,
        "mileage": mileage,
        "gearbox": gearbox,
        "horse_power_din": horsepower,
    }
    ad.attributes = [
        MagicMock(key=k, value=v) for k, v in attrs_dict.items()
    ]

    return ad


class TestPostFilter:
    """Tests pour _post_filter() qui applique les filtres post-scraping."""

    def test_price_min_filter(self):
        """Annonce à 500€ exclue si price_min=1000."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 500,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(price_min=1000)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce à 500€ doit être exclue si price_min=1000"

    def test_price_max_filter(self):
        """Annonce à 8000€ exclue si price_max=5000."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 8000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(price_max=5000)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce à 8000€ doit être exclue si price_max=5000"

    def test_price_in_range_passes(self):
        """Annonce à 3000€ incluse si price_min=1000 et price_max=5000."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 3000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(price_min=1000, price_max=5000)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 1, "Annonce à 3000€ doit passer le filtre"

    def test_mileage_max_filter(self):
        """Annonce à 200k km exclue si mileage_max=150000."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 200000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(mileage_max=150000)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce à 200k km doit être exclue"

    def test_mileage_in_range_passes(self):
        """Annonce à 120k km incluse si mileage_max=150000."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 120000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(mileage_max=150000)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 1, "Annonce à 120k km doit passer le filtre"

    def test_year_min_filter(self):
        """Annonce de 2008 exclue si year_min=2010."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2008,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(year_min=2010)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce de 2008 doit être exclue"

    def test_year_min_passes(self):
        """Annonce de 2015 incluse si year_min=2010."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(year_min=2010)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 1, "Annonce de 2015 doit passer le filtre"

    def test_gearbox_manual_filter(self):
        """Annonce avec boîte auto (gearbox=automatic) exclue si gearbox='manual'."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "automatic",
            "horsepower": 100,
        }
        filters = SearchFilters(gearbox="manual")
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce auto doit être exclue si on cherche manual"

    def test_gearbox_automatic_filter(self):
        """Annonce avec boîte manual exclue si gearbox='automatic'."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(gearbox="automatic")
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce manual doit être exclue si on cherche auto"

    def test_gearbox_manual_passes(self):
        """Annonce manual incluse si gearbox='manual'."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 100,
        }
        filters = SearchFilters(gearbox="manual")
        result = scraper._post_filter([listing], filters)
        assert len(result) == 1, "Annonce manual doit passer le filtre"

    def test_horsepower_min_filter(self):
        """Annonce à 80ch exclue si horsepower_min=100."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 80,
        }
        filters = SearchFilters(horsepower_min=100)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce à 80ch doit être exclue"

    def test_horsepower_max_filter(self):
        """Annonce à 200ch exclue si horsepower_max=150."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 200,
        }
        filters = SearchFilters(horsepower_max=150)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce à 200ch doit être exclue"

    def test_horsepower_in_range_passes(self):
        """Annonce à 120ch incluse si horsepower_min=100 et horsepower_max=150."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 5000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 120,
        }
        filters = SearchFilters(horsepower_min=100, horsepower_max=150)
        result = scraper._post_filter([listing], filters)
        assert len(result) == 1, "Annonce à 120ch doit passer le filtre"

    def test_all_filters_combined(self):
        """Annonce qui passe tous les filtres retournée."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 3000,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": 110,
        }
        filters = SearchFilters(
            price_min=1000,
            price_max=5000,
            mileage_max=150000,
            year_min=2010,
            gearbox="manual",
            horsepower_min=100,
            horsepower_max=150,
        )
        result = scraper._post_filter([listing], filters)
        assert len(result) == 1, "Annonce valide doit passer tous les filtres"

    def test_all_filters_combined_fails_one(self):
        """Annonce qui échoue un seul filtre exclue."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": 3000,  # OK
            "mileage": 100000,  # OK
            "year": 2005,  # FAIL: < 2010
            "gearbox": "manual",  # OK
            "horsepower": 110,  # OK
        }
        filters = SearchFilters(
            price_min=1000,
            price_max=5000,
            mileage_max=150000,
            year_min=2010,
            gearbox="manual",
            horsepower_min=100,
            horsepower_max=150,
        )
        result = scraper._post_filter([listing], filters)
        assert len(result) == 0, "Annonce échouant year_min doit être exclue"

    def test_no_filters_returns_all(self):
        """Sans filtres, toutes les annonces retournées."""
        scraper = LBCScraper()
        listings = [
            {
                "lbc_id": "1",
                "price": 500,
                "mileage": 200000,
                "year": 2000,
                "gearbox": "automatic",
                "horsepower": 50,
            },
            {
                "lbc_id": "2",
                "price": 10000,
                "mileage": 10000,
                "year": 2023,
                "gearbox": "manual",
                "horsepower": 200,
            },
        ]
        filters = SearchFilters()  # Tous None
        result = scraper._post_filter(listings, filters)
        assert len(result) == 2, "Sans filtres, toutes les annonces doivent être retournées"

    def test_filter_with_none_values_in_listing(self):
        """Annonce avec valeurs None ne bloque pas les filtres."""
        scraper = LBCScraper()
        listing = {
            "lbc_id": "1",
            "price": None,
            "mileage": 100000,
            "year": 2015,
            "gearbox": "manual",
            "horsepower": None,
        }
        filters = SearchFilters(price_min=1000, horsepower_min=100)
        result = scraper._post_filter([listing], filters)
        # L'annonce passe car les filtres ne s'appliquent que si la valeur existe
        assert len(result) == 1


class TestParseAd:
    """Tests pour _parse_ad() qui convertit une annonce LBC en dict."""

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_extracts_all_fields(self, mock_lbc_client):
        """_parse_ad extrait tous les champs requis."""
        scraper = LBCScraper()
        ad = make_mock_ad(
            price=3000,
            brand="Renault",
            model="Clio",
            year="2015",
            mileage="90000",
            horsepower="110",
            gearbox="1",  # manual
        )
        listing = scraper._parse_ad(ad, SearchFilters())

        assert listing["lbc_id"] == "123"
        assert listing["price"] == 3000
        assert listing["brand"] == "Renault"
        assert listing["model"] == "Clio"
        assert listing["year"] == 2015
        assert listing["mileage"] == 90000
        assert listing["horsepower"] == 110
        assert listing["gearbox"] == "manual"

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_gearbox_conversion_manual(self, mock_lbc_client):
        """_gearbox_label() convertit '1' en 'manual'."""
        raw = "1"
        result = _gearbox_label(raw)
        assert result == "manual"

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_gearbox_conversion_automatic(self, mock_lbc_client):
        """_gearbox_label() convertit '2' en 'automatic'."""
        raw = "2"
        result = _gearbox_label(raw)
        assert result == "automatic"

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_gearbox_conversion_text_manual(self, mock_lbc_client):
        """_gearbox_label() convertit 'manuelle' en 'manual'."""
        raw = "manuelle"
        result = _gearbox_label(raw)
        assert result == "manual"

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_gearbox_conversion_text_automatic(self, mock_lbc_client):
        """_gearbox_label() convertit 'automatique' en 'automatic'."""
        raw = "automatique"
        result = _gearbox_label(raw)
        assert result == "automatic"

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_horsepower_with_unit(self, mock_lbc_client):
        """_parse_ad extrait les chevaux même avec unité (ex: '110 ch')."""
        scraper = LBCScraper()
        ad = make_mock_ad(horsepower="110 ch")
        listing = scraper._parse_ad(ad, SearchFilters())
        assert listing["horsepower"] == 110

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_mileage_with_km(self, mock_lbc_client):
        """_parse_ad extrait le kilométrage avec unité (ex: '90000 km')."""
        scraper = LBCScraper()
        ad = make_mock_ad(mileage="90000 km")
        listing = scraper._parse_ad(ad, SearchFilters())
        assert listing["mileage"] == 90000

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_regex_matching(self, mock_lbc_client):
        """_parse_ad applique les patterns regex sur la description."""
        scraper = LBCScraper()
        ad = make_mock_ad(body="CT valide, carte grise fournie.")
        listing = scraper._parse_ad(ad, SearchFilters())
        assert "CT valide" in listing["matched_keywords"]
        assert "Carte grise" in listing["matched_keywords"]

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_invalid_price_becomes_none(self, mock_lbc_client):
        """_parse_ad gère les prix invalides."""
        scraper = LBCScraper()
        ad = MagicMock()
        ad.id = "123"
        ad.subject = "Test"
        ad.body = "Description"
        ad.url = "https://lbc.fr/123"
        ad.price = "invalid"  # String that can't be converted
        ad.location = MagicMock(city="Paris")
        ad.attributes = []
        
        listing = scraper._parse_ad(ad, SearchFilters())
        assert listing["price"] is None

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_invalid_mileage_becomes_none(self, mock_lbc_client):
        """_parse_ad gère les kilométrages invalides."""
        scraper = LBCScraper()
        ad = make_mock_ad(mileage="invalid")
        listing = scraper._parse_ad(ad, SearchFilters())
        assert listing["mileage"] is None

    @patch("lbc_scraper.lbc.Client")
    def test_parse_ad_invalid_year_becomes_none(self, mock_lbc_client):
        """_parse_ad gère les années invalides."""
        scraper = LBCScraper()
        ad = make_mock_ad(year="invalid")
        listing = scraper._parse_ad(ad, SearchFilters())
        assert listing["year"] is None

    @patch("lbc_scraper.lbc.Client")
    def test_extract_attribute_returns_value(self, mock_lbc_client):
        """_extract_attribute retourne la valeur si la clé existe."""
        ad = make_mock_ad()
        result = _extract_attribute(ad, "brand")
        assert result == "Renault"

    @patch("lbc_scraper.lbc.Client")
    def test_extract_attribute_returns_default(self, mock_lbc_client):
        """_extract_attribute retourne le default si la clé n'existe pas."""
        ad = make_mock_ad()
        result = _extract_attribute(ad, "nonexistent", default="N/A")
        assert result == "N/A"


class TestSearchFilters:
    """Tests pour SearchFilters dataclass."""

    def test_filters_all_none_by_default(self):
        """SearchFilters initialise tous les champs à None."""
        filters = SearchFilters()
        assert filters.brand is None
        assert filters.model is None
        assert filters.price_min is None
        assert filters.price_max is None
        assert filters.mileage_max is None
        assert filters.year_min is None
        assert filters.horsepower_min is None
        assert filters.horsepower_max is None
        assert filters.gearbox is None
        assert filters.extra_patterns == []

    def test_filters_can_be_set(self):
        """SearchFilters accepte des valeurs."""
        filters = SearchFilters(
            brand="Renault",
            price_min=1000,
            price_max=5000,
        )
        assert filters.brand == "Renault"
        assert filters.price_min == 1000
        assert filters.price_max == 5000
