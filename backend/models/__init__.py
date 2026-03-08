from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, relationship





class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    __tablename__ = "vehicles"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    brand             = Column(String(100), nullable=False)
    model             = Column(String(100), nullable=False)
    year_start        = Column(Integer)
    year_end          = Column(Integer)
    reliability_score = Column(Integer)
    total_testimonials= Column(Integer, default=0)
    common_issues     = Column(JSON)
    known_issues_text = Column(JSON)
    source_url        = Column(String(500))
    reliability_rank  = Column(String(20), nullable=True)
    fuel_type         = Column(String(50))
    scraped_at        = Column(DateTime, server_default=func.now())
    category          = Column(String(50), nullable=True)
    rank_in_category  = Column(Integer, nullable=True)
    total_in_category = Column(Integer, nullable=True)

    listings = relationship("Listing", back_populates="vehicle")

    __table_args__ = (Index("idx_brand_model", "brand", "model"),)


class Listing(Base):
    __tablename__ = "listings"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    lbc_id           = Column(String(50), unique=True, nullable=False)
    title            = Column(String(255))
    price            = Column(Integer)
    year             = Column(Integer)
    mileage          = Column(Integer)
    horsepower       = Column(Integer)
    gearbox          = Column(Enum("manual", "automatic"))
    fuel_type        = Column(String(50))
    doors            = Column(Integer)
    seats            = Column(Integer)
    color            = Column(String(50))
    location         = Column(String(100))
    description      = Column(Text)
    url              = Column(String(500))
    matched_keywords = Column(JSON)
    images           = Column(JSON, nullable=True)  # list of image URLs from LBC
    vehicle_id       = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"))
    scraped_at       = Column(DateTime, server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="listings")
    likes = relationship("Like", back_populates="listing", cascade="all, delete-orphan")


class RegexPattern(Base):
    __tablename__ = "regex_patterns"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False)
    pattern     = Column(String(500), nullable=False)
    description = Column(String(255))
    is_default  = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id                 = Column(Integer, primary_key=True, autoincrement=True)
    email              = Column(String(255), unique=True, nullable=False)
    hashed_password    = Column(String(255), nullable=False)
    is_verified        = Column(Boolean, default=False)
    verification_token = Column(String(100), nullable=True)
    created_at         = Column(DateTime, server_default=func.now())


class Like(Base):
    __tablename__ = "likes"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, nullable=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    listing = relationship("Listing", back_populates="likes")

    __table_args__ = (
        Index("idx_likes_user", "user_id"),
        Index("idx_likes_listing", "listing_id"),
        Index("uk_user_listing", "user_id", "listing_id", unique=True),
    )


class SearchHistory(Base):
    __tablename__ = "search_history"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, default=1, nullable=False)
    params       = Column(JSON, nullable=False)
    listing_ids  = Column(JSON, nullable=True)
    patterns     = Column(JSON, nullable=True)
    result_count = Column(Integer, default=0)
    created_at   = Column(DateTime, default=func.now())


class ViewedListing(Base):
    __tablename__ = "viewed_listings"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, default=1, nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    viewed_at  = Column(DateTime, default=func.now())

    listing = relationship("Listing", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "listing_id", name="uk_vl_user_listing"),
    )


class ListingAnalysisUser(Base):
    """Join table: tracks which users have consumed a credit for which listing analysis."""
    __tablename__ = "listing_analysis_users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    used_cache = Column(Boolean, default=False)   # True = cache hit (no real AI call was made)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("listing_id", "user_id", name="uk_lau_listing_user"),
    )


class RequeteIA(Base):
    __tablename__ = "requete_ia"

    id          = Column(Integer, primary_key=True)
    listing_id  = Column(Integer, ForeignKey("listings.id"), nullable=False)
    user_id     = Column(Integer, nullable=True)
    prompt_text = Column(Text, nullable=True)        # prompt complet envoyé au LLM
    model       = Column(String(100), nullable=False)  # ex: "gpt-4o-mini"
    status      = Column(String(20), default="pending")  # pending | done | error
    created_at  = Column(DateTime, default=func.now())

    listing  = relationship("Listing", backref="requetes_ia", lazy="selectin")
    reponse  = relationship("ReponseIA", back_populates="requete", uselist=False, lazy="selectin")


class ReponseIA(Base):
    __tablename__ = "reponse_ia"

    id                   = Column(Integer, primary_key=True)
    requete_id           = Column(Integer, ForeignKey("requete_ia.id"), nullable=False, unique=True)
    repairs_found        = Column(JSON)           # list[str]
    upcoming_maintenance = Column(JSON)           # list[str]
    condition_summary    = Column(Text)
    risk_level           = Column(String(20))     # "low" | "medium" | "high"
    raw_response         = Column(Text)           # réponse brute LLM
    created_at           = Column(DateTime, default=func.now())

    requete = relationship("RequeteIA", back_populates="reponse")


class AnalyseRecherche(Base):
    __tablename__ = "analyse_recherche"

    id          = Column(Integer, primary_key=True)
    search_id   = Column(Integer, ForeignKey("search_history.id", ondelete="CASCADE"), nullable=False, unique=True)
    user_id     = Column(Integer, nullable=True)
    listing_ids = Column(JSON, nullable=False)   # list[int] des listings analyses
    prompt_text = Column(Text, nullable=True)
    model       = Column(String(100), nullable=False)
    status      = Column(String(20), default="pending")  # pending | done | error
    created_at  = Column(DateTime, default=func.now())

    reponse = relationship("ReponseRechercheIA", back_populates="analyse", uselist=False, lazy="selectin")


class ReponseRechercheIA(Base):
    __tablename__ = "reponse_recherche_ia"

    id                     = Column(Integer, primary_key=True)
    analyse_id             = Column(Integer, ForeignKey("analyse_recherche.id"), nullable=False, unique=True)
    synthese_globale       = Column(Text)
    themes_mentionnes      = Column(JSON)    # list[str]
    themes_absents         = Column(JSON)    # list[str]
    prochaines_reparations = Column(JSON)    # list[str]
    risk_level             = Column(String(20))   # "low" | "medium" | "high"
    raw_response           = Column(Text)
    created_at             = Column(DateTime, default=func.now())

    analyse = relationship("AnalyseRecherche", back_populates="reponse")


# ─────────────────────────────────────────────────────────────────────────────
# Système de crédits & paiements
# ─────────────────────────────────────────────────────────────────────────────

PACK_TYPES = ("search", "analysis")

class CreditPack(Base):
    """Packs de crédits achetables (configurés en DB ou en code)."""
    __tablename__ = "credit_packs"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False)
    pack_type   = Column(Enum(*PACK_TYPES, name="pack_type_enum"), nullable=False)
    credits     = Column(Integer, nullable=False)
    price_cents = Column(Integer, nullable=False)  # prix en centimes EUR
    active      = Column(Boolean, default=True)

    transactions = relationship("CreditTransaction", back_populates="pack")


class UserCredits(Base):
    """Solde de crédits par utilisateur + compteurs quotidiens."""
    __tablename__ = "user_credits"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    user_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    search_credits      = Column(Integer, default=0, nullable=False)
    analysis_credits    = Column(Integer, default=0, nullable=False)
    daily_searches_used = Column(Integer, default=0, nullable=False)
    daily_results_used  = Column(Integer, default=0, nullable=False)
    daily_reset_date    = Column(Date, nullable=True)

    user = relationship("User", backref="credits")

    __table_args__ = (Index("idx_uc_user", "user_id"),)


class CreditTransaction(Base):
    """Historique des achats de crédits."""
    __tablename__ = "credit_transactions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pack_id          = Column(Integer, ForeignKey("credit_packs.id", ondelete="SET NULL"), nullable=True)
    credits_added    = Column(Integer, nullable=False)
    pack_type        = Column(Enum(*PACK_TYPES, name="pack_type_enum"), nullable=False)
    stripe_session_id = Column(String(200), nullable=True, unique=True)
    stripe_payment_id = Column(String(200), nullable=True)
    status           = Column(String(20), default="pending")  # pending | completed | failed
    created_at       = Column(DateTime, default=func.now())

    pack = relationship("CreditPack", back_populates="transactions")

    __table_args__ = (Index("idx_ct_user", "user_id"),)
