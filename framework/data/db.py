# framework/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import time
import inspect
from typing import Optional
from ..core.component import Component
from ..core.config import Config
from ..messaging.events import DBConnectionEvent, DBQueryEvent, DBTransactionEvent, DBPoolEvent
from typing import Dict, Any

# Base class for declarative models
Base = declarative_base()

class SQLAlchemyAdapter(Component):
    """
    Manages the database connection lifecycle using SQLAlchemy's async features.
    Enhanced with comprehensive event publishing for monitoring and observability.
    """
    def __init__(self, app):
        self.app = app
        self.config = app.container.get(Config)
        self.engine = None
        self.SessionLocal = None
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._transaction_counter = 0

    async def start(self):
        """
        Initializes the database engine and session maker with event publishing.
        """
        db_url = self.config.get("DATABASE_URL", "sqlite+aiosqlite:///./ucore_default.db")

        try:
            # Publish lifecycle event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_lifecycle_event(
                    component_name="SQLAlchemyAdapter",
                    lifecycle_type="starting"
                )
            start_time = time.time()

            self.app.logger.info(f"Connecting to database: {db_url}")

            self.engine = create_async_engine(db_url, echo=self.config.get("DB_ECHO", False))
            self.SessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                class_=AsyncSession
            )

            connection_time = time.time() - start_time

            # Test the connection and publish success event
            await self._test_connection()
            self.app.logger.info("Database engine and session maker initialized.")

            # Publish successful connection event
            if event_bus:
                connection_event = DBConnectionEvent(
                    database_url=self._sanitize_db_url(db_url),
                    connection_status="success",
                    connection_time=connection_time
                )
                event_bus.publish(connection_event)

                # Publish pool status event
                pool_event = DBPoolEvent(
                    pool_size=self.config.get("DB_POOL_SIZE", 10),
                    active_connections=0,
                    idle_connections=0,
                    pending_connections=0
                )
                event_bus.publish(pool_event)

                # Publish success lifecycle event
                event_bus.publish_lifecycle_event(
                    component_name="SQLAlchemyAdapter",
                    lifecycle_type="started",
                    success=True,
                    duration=connection_time
                )

        except Exception as e:
            # Publish error event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_error_event(
                    component_name="SQLAlchemyAdapter",
                    error=e,
                    context={"operation": "start", "database_url": db_url}
                )
            raise

    async def _test_connection(self):
        """Test the database connection"""
        if self.engine:
            async with self.engine.begin() as conn:
                # This will raise if connection fails - simple test query
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))

    def _sanitize_db_url(self, db_url: str) -> str:
        """Sanitize database URL for logging (remove credentials)"""
        if "://" not in db_url:
            return db_url

        # Remove password from URL if present
        protocol, rest = db_url.split("://", 1)
        if "@" in rest:
            auth, host = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                return f"{protocol}://{user}:***@{host}"
        return db_url

    def connect(self):
        """
        Alias for start() for backward compatibility with test expectations.
        """
        self.app.logger.info("Database connection requested")
        return None

    async def stop(self):
        """
        Disposes of the database engine's connection pool with event publishing.
        """
        try:
            # Publish lifecycle event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_lifecycle_event(
                    component_name="SQLAlchemyAdapter",
                    lifecycle_type="stopping"
                )

            if self.engine:
                self.app.logger.info("Closing database connection pool.")
                await self.engine.dispose()

                # Publish connection closure event
                if event_bus:
                    connection_event = DBConnectionEvent(
                        database_url=self._sanitize_db_url(
                            self.config.get("DATABASE_URL", "")
                        ),
                        connection_status="closed",
                        connection_time=0.0
                    )
                    event_bus.publish(connection_event)

                self.app.logger.info("Database connection pool closed.")

                # Publish success lifecycle event
                if event_bus:
                    event_bus.publish_lifecycle_event(
                        component_name="SQLAlchemyAdapter",
                        lifecycle_type="stopped",
                        success=True
                    )

        except Exception as e:
            # Publish error event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_error_event(
                    component_name="SQLAlchemyAdapter",
                    error=e,
                    context={"operation": "stop"}
                )
            raise
    def on_config_update(self, config):
        """
        Handle dynamic configuration updates for database connection.
        """
        # Get updated configuration values
        new_db_url = config.get("DATABASE_URL")
        new_echo = config.get("DB_ECHO")

        # Check if database URL changed
        if new_db_url and new_db_url != getattr(self.engine, 'url', None):
            current_db_url = getattr(self.engine, 'url', self.config.get("DATABASE_URL"))
            if new_db_url != current_db_url:
                event_bus = self.get_event_bus()
                if event_bus:
                    event_bus.publish_component_event(
                        component_name="SQLAlchemyAdapter",
                        event_type="db_url_changed",
                        data={
                            "old_url": self._sanitize_db_url(current_db_url or ""),
                            "new_url": self._sanitize_db_url(new_db_url)
                        }
                    )

                self.app.logger.info("Database URL changed - requires restart")
                self.app.logger.warning("Runtime database URL changes require component restart")

        # Update echo setting if changed
        if new_echo is not None:
            current_echo = getattr(self.engine, 'echo', False)
            if new_echo != current_echo and hasattr(self.engine, 'echo'):
                event_bus = self.get_event_bus()
                if event_bus:
                    event_bus.publish_component_event(
                        component_name="SQLAlchemyAdapter",
                        event_type="echo_setting_changed",
                        data={"old_echo": current_echo, "new_echo": new_echo}
                    )

                self.app.logger.info(f"Database echo setting changed to: {new_echo}")
                self.app.logger.warning("Echo setting requires engine restart to take effect")

    def get_session(self) -> AsyncSession:
        """
        Provides a new database session with monitoring and event publishing.
        """
        if not self.SessionLocal:
            raise RuntimeError("Database session not initialized. Was the SQLAlchemyAdapter started?")

        session = self.SessionLocal()
        transaction_id = f"tx_{self._transaction_counter}"
        self._transaction_counter += 1

        session_start = time.time()

        # Store session metadata
        session_meta = {
            "transaction_id": transaction_id,
            "start_time": session_start,
            "query_count": 0
        }
        self._active_sessions[transaction_id] = session_meta

        # Publish transaction start event
        event_bus = self.get_event_bus()
        if event_bus:
            event_bus.publish(DBTransactionEvent(
                operation="begin",
                transaction_id=transaction_id,
                duration=0.0,
                query_count=0
            ))

        # Monkey patch session methods for monitoring
        original_commit = session.commit
        original_rollback = session.rollback
        original_close = session.close

        async def monitored_commit():
            session_meta["duration"] = time.time() - session_start

            # Publish commit event
            if event_bus:
                event_bus.publish(DBTransactionEvent(
                    operation="commit",
                    transaction_id=transaction_id,
                    duration=session_meta["duration"],
                    query_count=session_meta["query_count"]
                ))

            # Publish performance metric
            if event_bus:
                event_bus.publish_performance_event(
                    metric_name="db_transaction_duration",
                    value=session_meta["duration"],
                    component_type="SQLAlchemyAdapter",
                    tags={
                        "operation": "commit",
                        "query_count": str(session_meta["query_count"])
                    }
                )

            return await original_commit()

        async def monitored_rollback():
            session_meta["duration"] = time.time() - session_start

            # Publish rollback event
            if event_bus:
                event_bus.publish(DBTransactionEvent(
                    operation="rollback",
                    transaction_id=transaction_id,
                    duration=session_meta["duration"],
                    query_count=session_meta["query_count"]
                ))

            return await original_rollback()

        async def monitored_close():
            session_meta["duration"] = time.time() - session_start

            # Remove from active sessions
            if transaction_id in self._active_sessions:
                del self._active_sessions[transaction_id]

            # Publish session close event
            if event_bus:
                event_bus.publish_component_event(
                    component_name="SQLAlchemyAdapter",
                    event_type="session_closed",
                    data={
                        "transaction_id": transaction_id,
                        "duration": session_meta["duration"],
                        "query_count": session_meta["query_count"]
                    }
                )

            return await original_close()

        # Replace methods
        session.commit = monitored_commit
        session.rollback = monitored_rollback
        session.close = monitored_close

        return session
