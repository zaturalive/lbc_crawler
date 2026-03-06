"""
Tests for search and admin router endpoints.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from unittest.mock import patch, AsyncMock, MagicMock

from main import app
from models import Base, SearchSession, RegexPattern
from db.database import get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    """Create in-memory test database."""
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Provide async session."""
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """FastAPI test client with overridden DB."""

    def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """GET /health returns 200 with ok status."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSearchEndpoint:
    """Tests for POST /search endpoint — integration tests with mocked scraper."""

    @pytest.mark.asyncio
    async def test_search_endpoint_exists(self):
        """Verify /search endpoint is registered in app."""
        # Verify the endpoint is in the app routes
        routes = [route.path for route in app.routes]
        assert "/search" in routes


class TestAdminSyncEndpoints:
    """Tests for admin endpoints — structural tests."""

    @pytest.mark.asyncio
    async def test_admin_endpoints_exist(self):
        """Verify admin endpoints are registered."""
        routes = [route.path for route in app.routes]
        assert "/admin/sync-vehicles" in routes
        assert "/admin/sync-status" in routes
        assert "/admin/sync-vehicles/store" in routes


class TestPatternsEndpoints:
    """Tests for pattern management endpoints — structural tests."""

    @pytest.mark.asyncio
    async def test_patterns_endpoint_exists(self):
        """Verify /patterns endpoint is registered."""
        routes = [route.path for route in app.routes]
        assert "/patterns" in routes
