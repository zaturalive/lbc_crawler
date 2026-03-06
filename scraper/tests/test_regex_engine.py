import pytest
from regex_engine import DEFAULT_PATTERNS, RegexEngine


@pytest.fixture
def engine():
    return RegexEngine()


def test_ct_valide_short(engine):
    assert "CT valide" in engine.match("Voiture avec CT ok, prête à rouler.")


def test_ct_valide_full(engine):
    assert "CT valide" in engine.match("Contrôle technique valide jusqu'en 2026.")


def test_ct_valide_accent(engine):
    assert "CT valide" in engine.match("Contrôle technique fait en janvier.")


def test_carte_grise(engine):
    assert "Carte grise" in engine.match("Carte grise au nom du vendeur.")


def test_premier_proprietaire(engine):
    assert "Premier propriétaire" in engine.match("Premier propriétaire, non fumeur.")


def test_premier_proprietaire_first_main(engine):
    assert "Premier propriétaire" in engine.match("1ère main, carnet complet.")


def test_no_match(engine):
    assert engine.match("Belle voiture, bon état.") == []


def test_multiple_matches(engine):
    result = engine.match("CT valide, carte grise dispo, 1ère main.")
    assert "CT valide" in result
    assert "Carte grise" in result
    assert "Premier propriétaire" in result


def test_custom_pattern(engine):
    extra = [{"name": "Sans rouille", "pattern": r"sans\s+rouille"}]
    assert "Sans rouille" in engine.match("Carrosserie impeccable, sans rouille.", extra)


def test_invalid_pattern_raises():
    with pytest.raises(ValueError):
        RegexEngine.validate_pattern("[invalid(")


def test_valid_pattern_returns_true():
    assert RegexEngine.validate_pattern(r"\btest\b") is True


def test_case_insensitive(engine):
    assert "CT valide" in engine.match("CT VALIDE, VOITURE EN BON ÉTAT.")
