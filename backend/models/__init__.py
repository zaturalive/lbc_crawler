from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, func
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


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filters      = Column(JSON)
    patterns     = Column(JSON)
    result_count = Column(Integer, default=0)
    created_at   = Column(DateTime, server_default=func.now())


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


class ListingAnalysis(Base):
    __tablename__ = "listing_analyses"

    id                   = Column(Integer, primary_key=True)
    listing_id           = Column(Integer, ForeignKey("listings.id"), nullable=False, unique=True)
    model_used           = Column(String(100))
    repairs_found        = Column(JSON)
    upcoming_maintenance = Column(JSON)
    condition_summary    = Column(Text)
    risk_level           = Column(String(20))
    raw_response         = Column(Text)
    created_at           = Column(DateTime, default=func.now())

    listing = relationship("Listing", backref="analysis", lazy="selectin")
