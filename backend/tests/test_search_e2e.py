"""
Backend integration tests — mocked scraper, in-memory SQLite.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from main import app
from models import Base
from db.database import get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_patterns_empty(client):
    resp = await client.get("/patterns")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_pattern(client):
    resp = await client.post("/patterns", json={
        "name": "Test pattern",
        "pattern": r"\btest\b",
        "description": "Test",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test pattern"
    assert data["is_default"] is False


@pytest.mark.asyncio
async def test_create_invalid_pattern(client):
    resp = await client.post("/patterns", json={
        "name": "Bad",
        "pattern": "[invalid(",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_delete_default_pattern_forbidden(client, db_session):
    from models import RegexPattern
    pattern = RegexPattern(name="Default", pattern=r"\btest\b", is_default=True)
    db_session.add(pattern)
    await db_session.commit()
    await db_session.refresh(pattern)

    resp = await client.delete(f"/patterns/{pattern.id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_custom_pattern(client, db_session):
    from models import RegexPattern
    pattern = RegexPattern(name="Custom", pattern=r"\btest\b", is_default=False)
    db_session.add(pattern)
    await db_session.commit()
    await db_session.refresh(pattern)

    resp = await client.delete(f"/patterns/{pattern.id}")
    assert resp.status_code == 204
