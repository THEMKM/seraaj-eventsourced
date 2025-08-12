"""
PostgreSQL connection management for Seraaj event store
"""
import os
import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
try:
    import asyncpg  # type: ignore
    ASYNCPG_AVAILABLE = True
except Exception:
    asyncpg = None  # type: ignore
    ASYNCPG_AVAILABLE = False
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.pool_overflow = int(os.getenv('DB_POOL_OVERFLOW', '20'))
        self.connection_timeout = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
        self.pool_pre_ping = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from environment"""
        if url := os.getenv('DATABASE_URL'):
            return url
        
        # Build from individual components
        host = os.getenv('DB_HOST', 'localhost')
        port = int(os.getenv('DB_PORT', '5432'))
        name = os.getenv('DB_NAME', 'seraaj')
        user = os.getenv('DB_USER', 'seraaj')
        password = os.getenv('DB_PASSWORD', 'seraaj')
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
    
    @property
    def is_configured(self) -> bool:
        """Check if database is configured"""
        return self.database_url is not None

class DatabaseConnection:
    """Manages PostgreSQL connection and session factory"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection"""
        if not self.config.is_configured:
            raise ValueError("Database not configured. Set DATABASE_URL or DB_* environment variables.")
        
        if self._initialized:
            return
        
        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.pool_overflow,
                pool_timeout=self.config.connection_timeout,
                pool_pre_ping=self.config.pool_pre_ping,
                echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            await self.health_check()
            self._initialized = True
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if not self._initialized:
            await self.initialize()
        
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def health_check(self) -> dict:
        """Check database connectivity and basic health"""
        if not self._initialized:
            await self.initialize()
        
        try:
            async with self.get_session() as session:
                # Test basic connectivity
                result = await session.execute("SELECT 1")
                result.scalar()
                
                # Get database info
                result = await session.execute("SELECT version()")
                db_version = result.scalar()
                
                # Get connection pool info
                pool_info = {
                    'pool_size': self.engine.pool.size(),
                    'checked_in': self.engine.pool.checkedin(),
                    'checked_out': self.engine.pool.checkedout(),
                    'overflow': self.engine.pool.overflow(),
                }
                
                return {
                    'status': 'healthy',
                    'database_version': db_version,
                    'pool_info': pool_info,
                    'config': {
                        'pool_size': self.config.pool_size,
                        'pool_overflow': self.config.pool_overflow,
                        'connection_timeout': self.config.connection_timeout
                    }
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Global database connection instance
db_connection = DatabaseConnection()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database session"""
    async with db_connection.get_session() as session:
        yield session

async def init_database():
    """Initialize database connection (call at startup)"""
    await db_connection.initialize()

async def close_database():
    """Close database connection (call at shutdown)"""
    await db_connection.close()

class ConnectionRetry:
    """Retry logic for database operations"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0):
        self.max_retries = max_retries
        self.delay = delay
    
    async def execute(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except self._db_errors() as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"Database operation failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                    await asyncio.sleep(self.delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Database operation failed after {self.max_retries + 1} attempts: {e}")
        
        raise last_exception

    @staticmethod
    def _db_errors():
        """Return a tuple of database-related exceptions to catch.

        If asyncpg is not installed, only ConnectionError is returned.
        """
        if ASYNCPG_AVAILABLE and hasattr(asyncpg, "PostgresError"):
            return (asyncpg.PostgresError, ConnectionError)  # type: ignore[attr-defined]
        return (ConnectionError,)

# Default retry instance
default_retry = ConnectionRetry()