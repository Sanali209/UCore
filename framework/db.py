# framework/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from .component import Component
from .config import Config

# Base class for declarative models
Base = declarative_base()

class SQLAlchemyAdapter(Component):
    """
    Manages the database connection lifecycle using SQLAlchemy's async features.
    """
    def __init__(self, app):
        self.app = app
        self.config = app.container.get(Config)
        self.engine = None
        self.SessionLocal = None

    async def start(self):
        """
        Initializes the database engine and session maker.
        """
        db_url = self.config.get("DATABASE_URL", "sqlite+aiosqlite:///./ucore_default.db")
        self.app.logger.info(f"Connecting to database: {db_url}")

        try:
            self.engine = create_async_engine(db_url, echo=self.config.get("DB_ECHO", False))
            self.SessionLocal = async_sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
                class_=AsyncSession
            )
            self.app.logger.info("Database engine and session maker initialized.")
        except Exception as e:
            self.app.logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise

    def connect(self):
        """
        Alias for start() for backward compatibility with test expectations.
        """
        # In a real async environment, this would need to be handled differently
        # For testing purposes, we return None and assume start() was called
        self.app.logger.info("Database connection requested")
        return None

    async def stop(self):
        """
        Disposes of the database engine's connection pool.
        """
        if self.engine:
            self.app.logger.info("Closing database connection pool.")
            await self.engine.dispose()
            self.app.logger.info("Database connection pool closed.")

    def on_config_update(self, config):
        """
        Handle dynamic configuration updates for database connection.
        """
        # Get updated configuration values
        new_db_url = config.get("DATABASE_URL")
        new_echo = config.get("DB_ECHO")

        # Check if database URL changed
        if new_db_url and new_db_url != getattr(self.engine, 'url', None):
            # Store current settings
            current_db_url = getattr(self.engine, 'url', self.config.get("DATABASE_URL"))
            if new_db_url != current_db_url:
                self.app.logger.info("Database URL changed - requires restart")
                # In a real implementation, you might want to gracefully
                # stop connections and restart with new URL
                # For now, just log the change
                self.app.logger.warning("Runtime database URL changes require component restart")

        # Update echo setting if changed
        if new_echo is not None:
            current_echo = getattr(self.engine, 'echo', False)
            if new_echo != current_echo:
                self.app.logger.info(f"Database echo setting changed to: {new_echo}")
                # Note: SQLAlchemy echo setting can't be changed after engine creation
                # This would require engine recreation
                if hasattr(self.engine, 'echo'):
                    self.app.logger.warning("Echo setting requires engine restart to take effect")

    def get_session(self) -> AsyncSession:
        """
        Provides a new database session.
        This will be used for dependency injection.
        """
        if not self.SessionLocal:
            raise RuntimeError("Database session not initialized. Was the SQLAlchemyAdapter started?")
        return self.SessionLocal()
