"""
Database connection management for PostgreSQL
"""
import os
import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import text

# Base class for SQLAlchemy models
Base = declarative_base()


class DatabaseConfig:
    """Database configuration from environment variables"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            # Build URL from individual components
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            name = os.getenv('DB_NAME', 'seraaj')
            user = os.getenv('DB_USER', 'postgres')
            password = os.getenv('DB_PASSWORD', 'postgres')
            self.database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
        
        # Connection pool settings
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_POOL_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # 1 hour


class DatabaseManager:
    """Database connection manager with connection pooling"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        self.session_maker = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database engine and session maker"""
        if self._initialized:
            return
        
        self.engine = create_async_engine(
            self.config.database_url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',  # SQL logging
            future=True
        )
        
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        self._initialized = True
        print(f"[INFO] Database initialized with URL: {self._mask_password(self.config.database_url)}")
    
    def _mask_password(self, url: str) -> str:
        """Mask password in database URL for logging"""
        if '://' in url and '@' in url:
            parts = url.split('://')
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                if '@' in rest:
                    auth_part, host_part = rest.split('@', 1)
                    if ':' in auth_part:
                        user, _ = auth_part.split(':', 1)
                        return f"{protocol}://{user}:***@{host_part}"
        return url
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
        if not self._initialized:
            self.initialize()
        
        async with self.session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> dict:
        """Check database connection health"""
        if not self._initialized:
            self.initialize()
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1 as healthy"))
                row = result.fetchone()
                return {
                    "healthy": row[0] == 1 if row else False,
                    "database": "postgresql",
                    "status": "connected"
                }
        except Exception as e:
            return {
                "healthy": False,
                "database": "postgresql", 
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            print("[INFO] Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI"""
    async with db_manager.get_session() as session:
        yield session


def is_database_available() -> bool:
    """Check if PostgreSQL is configured and available"""
    return bool(os.getenv('DATABASE_URL') or os.getenv('DB_HOST'))


async def init_database():
    """Initialize database for application startup"""
    if is_database_available():
        db_manager.initialize()
        health = await db_manager.health_check()
        if not health["healthy"]:
            print(f"[WARNING] Database health check failed: {health.get('error', 'Unknown error')}")
        else:
            print("[INFO] Database connection healthy")
    else:
        print("[INFO] No database configuration found, skipping PostgreSQL initialization")