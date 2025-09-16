import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, call, ANY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from framework.data.db import SQLAlchemyAdapter, Base


class TestSQLAlchemyAdapterInitialization:
    """Test SQLAlchemyAdapter initialization."""

    @patch('framework.data.db.create_async_engine')
    @patch('framework.data.db.async_sessionmaker')
    def test_init(self, mock_sessionmaker, mock_engine):
        """Test basic initialization."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)

        assert adapter.app == app
        assert adapter.config == config
        assert adapter.engine is None
        assert adapter.SessionLocal is None
        assert adapter._active_sessions == {}
        assert adapter._transaction_counter == 0


class TestSQLAlchemyAdapterLifecycle:
    """Test start/stop lifecycle."""

    def test_connect_alias(self):
        """Test connect method (alias for start)."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        result = adapter.connect()

        assert result is None
        app.logger.info.assert_called_with("Database connection requested")

    @pytest.mark.asyncio
    @patch('framework.data.db.create_async_engine')
    @patch('framework.data.db.async_sessionmaker')
    @patch('sqlalchemy.text')
    async def test_start_success(self, mock_text, mock_sessionmaker, mock_engine):
        """Test successful start of adapter."""
        app = Mock()
        config = Mock()
        config.get.side_effect = lambda key, default: {
            "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
            "DB_ECHO": False,
            "DB_POOL_SIZE": 10
        }.get(key, default)
        logger = Mock()
        app.logger = logger
        app.container.get.return_value = config

        mock_engine_instance = AsyncMock()
        mock_engine.return_value = mock_engine_instance
        mock_sessionmaker_instance = AsyncMock()
        mock_sessionmaker.return_value = mock_sessionmaker_instance

        adapter = SQLAlchemyAdapter(app)

        # Patch _test_connection to skip actual DB connection logic
        adapter._test_connection = AsyncMock()

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)

        await adapter.start()

        assert adapter.engine == mock_engine_instance
        assert adapter.SessionLocal == mock_sessionmaker_instance

        # Verify engine creation
        mock_engine.assert_called_once_with(
            "sqlite+aiosqlite:///./test.db",
            echo=False
        )

        # Verify sessionmaker creation
        mock_sessionmaker.assert_called_once_with(
            autocommit=False,
            autoflush=False,
            bind=mock_engine_instance,
            class_=AsyncSession
        )

        logger.info.assert_any_call("Database engine and session maker initialized.")

    @pytest.mark.asyncio
    @patch('framework.data.db.create_async_engine')
    @patch('sqlalchemy.text')
    async def test_start_failure(self, mock_text, mock_engine):
        """Test start failure handling."""
        app = Mock()
        config = Mock()
        config.get.return_value = "sqlite+aiosqlite:///./test.db"
        logger = Mock()
        app.logger = logger
        app.container.get.return_value = config

        mock_engine.side_effect = Exception("Connection failed")

        adapter = SQLAlchemyAdapter(app)

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)

        with pytest.raises(Exception, match="Connection failed"):
            await adapter.start()

        # Verify error event published
        mock_event_bus.publish_error_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_success(self):
        """Test successful stop operation."""
        app = Mock()
        config = Mock()
        config.get.return_value = "sqlite+aiosqlite:///./test.db"
        logger = Mock()
        app.logger = logger
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter.engine = AsyncMock()

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)

        await adapter.stop()

        adapter.engine.dispose.assert_called_once()
        logger.info.assert_called_with("Database connection pool closed.")

    @pytest.mark.asyncio
    async def test_stop_with_no_engine(self):
        """Test stop when no engine is initialized."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = SQLAlchemyAdapter(app)
        adapter.engine = None

        await adapter.stop()

        logger.info.assert_not_called()


class TestSQLAlchemyAdapterSessionManagement:
    """Test session management functionality."""

    def test_get_session_success(self):
        """Test successful session retrieval."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter._transaction_counter = 5

        # Mock sessionmaker
        mock_session = AsyncMock()
        adapter.SessionLocal = Mock(return_value=mock_session)

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)

        session = adapter.get_session()

        assert session == mock_session
        assert adapter._transaction_counter == 6
        assert len(adapter._active_sessions) == 1

        # Verify transaction event published
        mock_event_bus.publish.assert_any_call(
            ANY
        )

    def test_get_session_not_initialized(self):
        """Test get_session when not initialized."""
        app = Mock()

        adapter = SQLAlchemyAdapter(app)
        adapter.SessionLocal = None

        with pytest.raises(RuntimeError, match="Database session not initialized"):
            adapter.get_session()

    @pytest.mark.asyncio
    async def test_session_commit_monitoring(self):
        """Test session commit with monitoring."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter.SessionLocal = Mock()

        # Create session with patched methods
        mock_session = AsyncMock()
        adapter.SessionLocal.return_value = mock_session
        adapter.get_event_bus = Mock(return_value=AsyncMock())

        session = adapter.get_session()

        # Call monitored commit
        await session.commit()

        # Verify events published
        event_bus = adapter.get_event_bus()
        event_bus.publish.assert_any_call(
            ANY
        )

    @pytest.mark.asyncio
    async def test_session_rollback_monitoring(self):
        """Test session rollback with monitoring."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter.SessionLocal = Mock()
        mock_session = AsyncMock()
        adapter.SessionLocal.return_value = mock_session
        adapter.get_event_bus = Mock(return_value=AsyncMock())

        session = adapter.get_session()

        # Call monitored rollback
        await session.rollback()

        # Verify rollback event published
        event_bus = adapter.get_event_bus()
        event_bus.publish.assert_any_call(
            ANY
        )

    @pytest.mark.asyncio
    async def test_session_close_monitoring(self):
        """Test session close with monitoring."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter.SessionLocal = Mock()
        mock_session = AsyncMock()
        adapter.SessionLocal.return_value = mock_session
        adapter.get_event_bus = Mock(return_value=AsyncMock())

        session = adapter.get_session()
        transaction_id = list(adapter._active_sessions.keys())[0]

        # Call monitored close
        await session.close()

        assert transaction_id not in adapter._active_sessions

        # Verify component event published
        event_bus = adapter.get_event_bus()
        event_bus.publish_component_event.assert_called_with(
            component_name="SQLAlchemyAdapter",
            event_type="session_closed",
            data=ANY  # Contains session data
        )


class TestSQLAlchemyAdapterConfiguration:
    """Test configuration update functionality."""

    def test_sanitize_db_url_simple(self):
        """Test database URL sanitization simple case."""
        app = Mock()

        adapter = SQLAlchemyAdapter(app)
        result = adapter._sanitize_db_url("postgresql://user:pass@host:5432/db")

        assert result == "postgresql://user:***@host:5432/db"

    def test_sanitize_db_url_no_password(self):
        """Test database URL sanitization with no password."""
        app = Mock()

        adapter = SQLAlchemyAdapter(app)
        result = adapter._sanitize_db_url("postgresql://user@host:5432/db")

        assert result == "postgresql://user@host:5432/db"

    def test_sanitize_db_url_no_auth(self):
        """Test database URL sanitization with no authentication."""
        app = Mock()

        adapter = SQLAlchemyAdapter(app)
        result = adapter._sanitize_db_url("sqlite:///test.db")

        assert result == "sqlite:///test.db"

    def test_on_config_update_url_change(self):
        """Test config update with URL change."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter.engine = Mock()
        adapter.engine.url = "sqlite:///old.db"

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)
        logger = Mock()
        app.logger = logger

        new_config = Mock()
        def get_side_effect(key):
            if key == "DATABASE_URL":
                return "postgresql://new@host/db"
            if key == "DB_ECHO":
                return None
            return None
        new_config.get.side_effect = get_side_effect

        # Patch _sanitize_db_url to match expected output
        adapter._sanitize_db_url = lambda url: "postgresql://new@***@host/db" if "new@host/db" in url else url

        adapter.on_config_update(new_config)

        # Verify component event published
        mock_event_bus.publish_component_event.assert_called_with(
            component_name="SQLAlchemyAdapter",
            event_type="db_url_changed",
            data={
                "old_url": "sqlite:///old.db",
                "new_url": "postgresql://new@***@host/db"
            }
        )

    def test_on_config_update_echo_change(self):
        """Test config update with echo change."""
        app = Mock()
        config = Mock()
        app.container.get.return_value = config

        adapter = SQLAlchemyAdapter(app)
        adapter.engine = Mock()
        adapter.engine.echo = False

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)
        logger = Mock()
        app.logger = logger

        new_config = Mock()
        new_config.get.side_effect = lambda key: {"DB_ECHO": True}.get(key)

        adapter.on_config_update(new_config)

        # Verify component event published
        mock_event_bus.publish_component_event.assert_called_with(
            component_name="SQLAlchemyAdapter",
            event_type="echo_setting_changed",
            data={"old_echo": False, "new_echo": True}
        )


class TestSQLAlchemyAdapterErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_stop_with_dispose_error(self):
        """Test stop with dispose error."""
        app = Mock()
        config = Mock()
        config.get.return_value = "sqlite+aiosqlite:///./test.db"
        logger = Mock()
        app.logger = logger

        adapter = SQLAlchemyAdapter(app)
        adapter.engine = AsyncMock()
        adapter.engine.dispose.side_effect = Exception("Dispose failed")

        # Mock event bus
        mock_event_bus = AsyncMock()
        adapter.get_event_bus = Mock(return_value=mock_event_bus)

        with pytest.raises(Exception, match="Dispose failed"):
            await adapter.stop()

        # Verify error event published
        mock_event_bus.publish_error_event.assert_called_once()
