# tests/test_db_integration.py
import sys
import pytest
import pytest_asyncio
import asyncio
from aiohttp import ClientSession
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

# Add the UCore directory to the Python path so framework modules can be imported
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.web.http import HttpServer
from framework.data.db import SQLAlchemyAdapter, Base
from framework.core.di import Depends

# Test model
TestModel = None  # Will define inside test

# Dependency provider
def get_db_session(adapter):
    return adapter.get_session()

@pytest_asyncio.fixture
async def test_app():
    """Test fixture that provides a complete app with DB and HTTP server."""
    # Define the test model inside the fixture to avoid collection issues
    class TestModel(Base):
        __tablename__ = "test_model"
        id = Column(Integer, primary_key=True, index=True)
        name = Column(String, index=True)

    app = App(name="TestDBApp")
    http_server = HttpServer(app, port=8081)
    db_adapter = SQLAlchemyAdapter(app)
    app.register_component(lambda: http_server)
    app.register_component(lambda: db_adapter)

    # Override the database URL for testing
    db_adapter.config.set("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    # Simple test endpoint
    @http_server.route("/test", "POST")
    async def create_test_item(db: AsyncSession = Depends(lambda: get_db_session(db_adapter))):
        item = TestModel(name="test_item")
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return {"id": item.id, "name": item.name}

    @http_server.route("/test", "GET")
    async def get_test_items(db: AsyncSession = Depends(lambda: get_db_session(db_adapter))):
        result = await db.execute(select(TestModel))
        items = result.scalars().all()
        return [item.name for item in items]

    yield app
    await app.stop()

@pytest.mark.asyncio
async def test_sqlalchemy_adapter_initialization():
    """Test that the SQLAlchemy adapter initializes correctly."""
    app = App(name="TestDBApp")
    db_adapter = SQLAlchemyAdapter(app)
    app.register_component(lambda: db_adapter)

    # Override database URL
    db_adapter.config.set("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    await db_adapter.start()

    assert db_adapter is not None
    assert db_adapter.engine is not None
    assert db_adapter.SessionLocal is not None

    await db_adapter.stop()

@pytest.mark.asyncio
async def test_session_dependency_injection():
    """Test that session dependency injection works at request-time."""
    app = App(name="TestSessionApp")
    db_adapter = SQLAlchemyAdapter(app)
    app.register_component(lambda: db_adapter)

    # Override database URL
    db_adapter.config.set("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    await db_adapter.start()

    # Test session creation
    session = get_db_session(db_adapter)
    assert isinstance(session, AsyncSession)

    # Clean up
    await db_adapter.stop()
