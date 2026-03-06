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
    common_issues     = Column(JSON)
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
    location         = Column(String(100))
    description      = Column(Text)
    url              = Column(String(500))
    matched_keywords = Column(JSON)
    vehicle_id       = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"))
    scraped_at       = Column(DateTime, server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="listings")


class RegexPattern(Base):
    __tablename__ = "regex_patterns"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(100), nullable=False)
    pattern     = Column(String(500), nullable=False)
    description = Column(String(255))
    is_default  = Column(Boolean, default=False)
    created_at  = Column(DateTime, server_default=func.now())


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    filters      = Column(JSON)
    patterns     = Column(JSON)
    result_count = Column(Integer, default=0)
    created_at   = Column(DateTime, server_default=func.now())
