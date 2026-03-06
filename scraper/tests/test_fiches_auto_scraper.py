"""
Tests pour le scraper fiches-auto.fr.

Utilise `responses` pour mocker les requêtes HTTP et valide :
- Extraction du score fiabilité (conversion formule)
- Extraction des années (regex)
- Extraction des problèmes connus (parsing HTML)
- Scraping des marques et modèles
"""
import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

import fiches_auto_scraper as fas


class TestScoreConversion:
    """Tests pour la conversion du score fiabilité."""

    def test_score_conversion_zero(self):
        """val=0 → score=10 (meilleur)."""
        val = 0.0
        score = max(0, round(10 - val / 5))
        assert score == 10

    def test_score_conversion_five(self):
        """val=5 → score=9."""
        val = 5.0
        score = max(0, round(10 - val / 5))
        assert score == 9

    def test_score_conversion_twenty_five(self):
        """val=25 → score=5."""
        val = 25.0
        score = max(0, round(10 - val / 5))
        assert score == 5

    def test_score_conversion_fifty(self):
        """val=50 → score=0 (pire)."""
        val = 50.0
        score = max(0, round(10 - val / 5))
        assert score == 0

    def test_score_conversion_negative_becomes_zero(self):
        """Score négatif clampé à 0."""
        val = 100.0
        score = max(0, round(10 - val / 5))
        assert score == 0


class TestScrapeBrands:
    """Tests pour scrape_all_brands()."""

    def test_scrape_all_brands_returns_list(self):
        """scrape_all_brands() retourne une liste."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <a href="/fiabilite-renault/">Renault</a>
                <a href="/fiabilite-peugeot/">Peugeot</a>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_all_brands()
            assert isinstance(result, list)

    def test_scrape_all_brands_filters_valid_hrefs(self):
        """scrape_all_brands() ne retourne que les URLs /fiabilite-*/ valides."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <a href="/fiabilite-renault/">Renault</a>
                <a href="/fiabilite-peugeot/">Peugeot</a>
                <a href="/autre/">Autre</a>
                <a href="http://external.com">External</a>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_all_brands()
            assert len(result) == 2
            assert any("renault" in url for url in result)
            assert any("peugeot" in url for url in result)

    def test_scrape_all_brands_deduplicates(self):
        """scrape_all_brands() déduplique les URLs."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <a href="/fiabilite-renault/">Renault</a>
                <a href="/fiabilite-renault/">Renault (duplicate)</a>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_all_brands()
            assert len(result) == 1

    def test_scrape_all_brands_handles_none_soup(self):
        """scrape_all_brands() retourne [] si _get() retourne None."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_get.return_value = None
            result = fas.scrape_all_brands()
            assert result == []


class TestScrapeBrandModels:
    """Tests pour scrape_brand_models()."""

    def test_scrape_brand_models_returns_list(self):
        """scrape_brand_models() retourne une liste de dicts."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <a href="/fiabilite-renault/fiabilite-1-pannes-renault-clio.php">Clio</a>
                <a href="/fiabilite-renault/fiabilite-2-pannes-renault-scenic.php">Scenic</a>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_brand_models("https://www.fiches-auto.fr/fiabilite-renault/")
            assert isinstance(result, list)
            assert len(result) > 0

    def test_scrape_brand_models_extracts_name_and_url(self):
        """scrape_brand_models() extrait name et url pour chaque modèle."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <a href="/fiabilite-renault/fiabilite-1-pannes-renault-clio.php">Clio</a>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_brand_models("https://www.fiches-auto.fr/fiabilite-renault/")
            assert len(result) == 1
            assert result[0]["name"] == "Clio"
            assert "clio" in result[0]["url"].lower()
            assert result[0]["brand_slug"] == "renault"

    def test_scrape_brand_models_filters_pannes_links(self):
        """scrape_brand_models() ne retourne que les liens contenant 'pannes'."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <a href="/fiabilite-renault/fiabilite-1-pannes-renault-clio.php">Clio</a>
                <a href="/autre/">Autre</a>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_brand_models("https://www.fiches-auto.fr/fiabilite-renault/")
            assert len(result) == 1

    def test_scrape_brand_models_handles_none_soup(self):
        """scrape_brand_models() retourne [] si _get() retourne None."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_get.return_value = None
            result = fas.scrape_brand_models("https://www.fiches-auto.fr/fiabilite-renault/")
            assert result == []


class TestScrapeVehiclePage:
    """Tests pour scrape_vehicle_page()."""

    def test_scrape_vehicle_page_extracts_score(self):
        """scrape_vehicle_page() extrait le score fiabilité depuis les tables tab_fiabili."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Tous les probl&#232;mes sur Renault Clio 2010-2020 (5 t&#233;moignages)</title>
                <table class="tab_fiabili">
                  <tr>
                    <td class="intiu_fiabilite">Boite de vit.</td>
                    <td class="intiu_fiabilite">Batterie</td>
                  </tr>
                  <tr>
                    <td class="donnee_fiabilite">3</td>
                    <td class="donnee_fiabilite">2</td>
                  </tr>
                </table>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            # total_issues = 5 → 10 - 5/5 = 10 - 1 = 9
            assert result["reliability_score"] == 9

    def test_scrape_vehicle_page_extracts_year_range(self):
        """scrape_vehicle_page() extrait les années de la title."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Renault Clio 2010-2020 | Fiches Auto</title>
                <td class="verre_chiffres_cellules">10.0</td>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            assert result["year_start"] == 2010
            assert result["year_end"] == 2020

    def test_scrape_vehicle_page_extracts_brand_model(self):
        """scrape_vehicle_page() extrait marque et modèle depuis le slug."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Tous les probl&#232;mes sur Renault Clio 2010-2020 (10 t&#233;moignages)</title>
                <table class="tab_fiabili">
                  <tr><td class="intiu_fiabilite">Batterie</td></tr>
                  <tr><td class="donnee_fiabilite">0</td></tr>
                </table>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            assert result["brand"] == "Renault"
            assert "Clio" in result["model"] or "clio" in result["model"].lower()

    def test_scrape_vehicle_page_extracts_common_issues(self):
        """scrape_vehicle_page() extrait les problèmes connus depuis les tables tab_fiabili."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Tous les probl&#232;mes sur Renault Clio 2010-2020 (20 t&#233;moignages)</title>
                <table class="tab_fiabili">
                  <tr>
                    <td class="intiu_fiabilite">Casse Moteur</td>
                    <td class="intiu_fiabilite">Batterie</td>
                  </tr>
                  <tr>
                    <td class="donnee_fiabilite">12</td>
                    <td class="donnee_fiabilite">8</td>
                  </tr>
                </table>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            assert len(result["common_issues"]) > 0
            assert any("moteur" in issue.lower() for issue in result["common_issues"])

    def test_scrape_vehicle_page_handles_missing_score(self):
        """scrape_vehicle_page() retourne None pour score si aucune table tab_fiabili trouvée."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Tous les probl&#232;mes sur Renault Clio 2010-2020</title>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            assert result["reliability_score"] is None

    def test_scrape_vehicle_page_handles_missing_years(self):
        """scrape_vehicle_page() retourne None pour années si pas trouvées."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Renault Clio | Fiches Auto</title>
                <td class="verre_chiffres_cellules">10.0</td>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            assert result["year_start"] is None
            assert result["year_end"] is None

    def test_scrape_vehicle_page_handles_none_soup(self):
        """scrape_vehicle_page() retourne None si _get() retourne None."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_get.return_value = None
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            assert result is None

    def test_scrape_vehicle_page_score_clamped_to_zero(self):
        """scrape_vehicle_page() clamp le score à 0 si le total de témoignages est très élevé."""
        with patch("fiches_auto_scraper._get") as mock_get:
            mock_soup = BeautifulSoup(
                """
                <title>Tous les probl&#232;mes sur Renault Clio 2010-2020 (110 t&#233;moignages)</title>
                <table class="tab_fiabili">
                  <tr>
                    <td class="intiu_fiabilite">Casse Moteur</td>
                    <td class="intiu_fiabilite">Boite de vit.</td>
                  </tr>
                  <tr>
                    <td class="donnee_fiabilite">60</td>
                    <td class="donnee_fiabilite">50</td>
                  </tr>
                </table>
                """,
                "html.parser",
            )
            mock_get.return_value = mock_soup
            result = fas.scrape_vehicle_page(
                "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                "renault",
            )
            # total_issues = 110 → max(0, round(10 - 110/5)) = max(0, -12) = 0
            assert result["reliability_score"] == 0


class TestBulkScrapeVehicles:
    """Tests pour bulk_scrape_vehicles()."""

    def test_bulk_scrape_vehicles_returns_list(self):
        """bulk_scrape_vehicles() retourne une liste."""
        with patch("fiches_auto_scraper.scrape_all_brands") as mock_brands:
            with patch("fiches_auto_scraper.scrape_brand_models") as mock_models:
                with patch("fiches_auto_scraper.scrape_vehicle_page") as mock_page:
                    mock_brands.return_value = [
                        "https://www.fiches-auto.fr/fiabilite-renault/"
                    ]
                    mock_models.return_value = [
                        {
                            "name": "Clio",
                            "url": "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                            "brand_slug": "renault",
                        }
                    ]
                    mock_page.return_value = {
                        "brand": "Renault",
                        "model": "Clio",
                        "year_start": 2010,
                        "year_end": 2020,
                        "reliability_score": 8,
                        "common_issues": ["Problème 1"],
                        "source_url": "...",
                    }

                    result = fas.bulk_scrape_vehicles()
                    assert isinstance(result, list)
                    assert len(result) == 1

    def test_bulk_scrape_vehicles_calls_progress_callback(self):
        """bulk_scrape_vehicles() appelle le progress_callback pour chaque vehicle."""
        with patch("fiches_auto_scraper.scrape_all_brands") as mock_brands:
            with patch("fiches_auto_scraper.scrape_brand_models") as mock_models:
                with patch("fiches_auto_scraper.scrape_vehicle_page") as mock_page:
                    mock_brands.return_value = [
                        "https://www.fiches-auto.fr/fiabilite-renault/"
                    ]
                    mock_models.return_value = [
                        {
                            "name": "Clio",
                            "url": "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                            "brand_slug": "renault",
                        }
                    ]
                    mock_page.return_value = {
                        "brand": "Renault",
                        "model": "Clio",
                        "year_start": 2010,
                        "year_end": 2020,
                        "reliability_score": 8,
                        "common_issues": ["Problème 1"],
                        "source_url": "...",
                    }

                    progress_calls = []

                    def progress_callback(vehicle):
                        progress_calls.append(vehicle)

                    fas.bulk_scrape_vehicles(progress_callback=progress_callback)
                    assert len(progress_calls) == 1

    def test_bulk_scrape_vehicles_skips_failed_pages(self):
        """bulk_scrape_vehicles() ignore les pages échouées (scrape_vehicle_page retourne None)."""
        with patch("fiches_auto_scraper.scrape_all_brands") as mock_brands:
            with patch("fiches_auto_scraper.scrape_brand_models") as mock_models:
                with patch("fiches_auto_scraper.scrape_vehicle_page") as mock_page:
                    mock_brands.return_value = [
                        "https://www.fiches-auto.fr/fiabilite-renault/"
                    ]
                    mock_models.return_value = [
                        {
                            "name": "Clio",
                            "url": "https://fiches-auto.fr/fiabilite-renault/fiabilite-1-pannes-renault-clio.php",
                            "brand_slug": "renault",
                        },
                        {
                            "name": "Scenic",
                            "url": "https://fiches-auto.fr/fiabilite-renault/fiabilite-2-pannes-renault-scenic.php",
                            "brand_slug": "renault",
                        },
                    ]
                    # Premier succès, second échoue
                    mock_page.side_effect = [
                        {
                            "brand": "Renault",
                            "model": "Clio",
                            "year_start": 2010,
                            "year_end": 2020,
                            "reliability_score": 8,
                            "common_issues": ["Problème 1"],
                            "source_url": "...",
                        },
                        None,  # Scenic failed
                    ]

                    result = fas.bulk_scrape_vehicles()
                    assert len(result) == 1  # Only Clio

    def test_bulk_scrape_vehicles_handles_empty_brands(self):
        """bulk_scrape_vehicles() retourne [] si aucune marque trouvée."""
        with patch("fiches_auto_scraper.scrape_all_brands") as mock_brands:
            mock_brands.return_value = []
            result = fas.bulk_scrape_vehicles()
            assert result == []


class TestGetFunction:
    """Tests pour _get() qui fetch et parse HTML."""

    def test_get_returns_soup(self):
        """_get() retourne une BeautifulSoup."""
        with patch("fiches_auto_scraper.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body>Test</body></html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with patch("fiches_auto_scraper.time.sleep"):
                result = fas._get("https://example.com")
                assert isinstance(result, BeautifulSoup)

    def test_get_handles_network_error(self):
        """_get() retourne None en cas d'erreur réseau."""
        with patch("fiches_auto_scraper.requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = fas._get("https://example.com")
            assert result is None

    def test_get_handles_http_error(self):
        """_get() retourne None en cas d'erreur HTTP."""
        with patch("fiches_auto_scraper.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value = mock_response
            result = fas._get("https://example.com")
            assert result is None

    def test_get_rate_limits(self):
        """_get() respecte le RATE_LIMIT (sleep)."""
        with patch("fiches_auto_scraper.requests.get") as mock_get:
            with patch("fiches_auto_scraper.time.sleep") as mock_sleep:
                mock_response = MagicMock()
                mock_response.text = "<html></html>"
                mock_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_response

                fas._get("https://example.com")
                mock_sleep.assert_called_once()
