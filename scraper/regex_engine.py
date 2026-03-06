import re
from typing import Optional


DEFAULT_PATTERNS = [
    {"name": "CT valide",            "pattern": r"(?:\bct\b|\bcontr[oô]le\s+technique\b)"},
    {"name": "Carte grise",          "pattern": r"\bcarte\s+grise\b"},
    {"name": "Premier propriétaire", "pattern": r"\bpremier\s+propri[eé]taire\b|\b1[eè]re?\s+main\b"},
    {"name": "Carnet entretien",     "pattern": r"\bcarnet\s+d'?entretien\b"},
    {"name": "Factures garage",      "pattern": r"\bfacture[s]?\s+(?:garage|entretien|réparation)\b"},
    {"name": "Non fumeur",           "pattern": r"\bnon[- ]fumeur\b|\bsans\s+odeur\b"},
    {"name": "Révision récente",     "pattern": r"\br[eé]vision\s+(?:r[eé]cente|faite|effectu[eé]e)\b"},
]


class RegexEngine:
    def __init__(self, patterns: Optional[list[dict]] = None):
        self._patterns = patterns if patterns is not None else DEFAULT_PATTERNS
        self._compiled = [
            {"name": p["name"], "regex": re.compile(p["pattern"], re.IGNORECASE)}
            for p in self._patterns
        ]

    def match(self, description: str, extra_patterns: Optional[list[dict]] = None) -> list[str]:
        compiled = list(self._compiled)
        if extra_patterns:
            for p in extra_patterns:
                compiled.append({
                    "name": p["name"],
                    "regex": re.compile(p["pattern"], re.IGNORECASE),
                })
        return [c["name"] for c in compiled if c["regex"].search(description)]

    @staticmethod
    def validate_pattern(pattern: str) -> bool:
        try:
            re.compile(pattern)
            return True
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc


if __name__ == "__main__":
    engine = RegexEngine()
    samples = [
        "Voiture en bon état, CT valide jusqu'en 2026.",
        "Contrôle technique OK, carte grise disponible.",
        "Premier propriétaire, carnet d'entretien complet.",
        "Factures garage sur demande, non-fumeur.",
        "Aucun document particulier.",
    ]
    for s in samples:
        matched = engine.match(s)
        print(f"  [{', '.join(matched) if matched else 'aucun'}] — {s[:60]}")
