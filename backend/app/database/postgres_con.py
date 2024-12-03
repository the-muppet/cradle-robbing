import os
from typing import AsyncGenerator, Optional, Type
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.exc import SQLAlchemyError

class DatabaseError(Exception):
    """Base exception for database-related errors"""
    pass

class DatabaseSession:
    """
    Manages async database sessions with proper resource handling and error management.
    Provides both context manager and direct session access patterns.
    """
    def __init__(self, database_url: Optional[str] = None):
        if not database_url:
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                raise DatabaseError("DATABASE_URL not configured")
                
        # Ensure we're using the async dialect
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
            
        try:
            self.engine: AsyncEngine = create_async_engine(
                database_url,
                pool_size=5,
                max_overflow=10
            )
            
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False  # Prevent implicit flushes for better control
            )
            
            self._session: Optional[AsyncSession] = None
            self.model: Optional[Type[DeclarativeMeta]] = None
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database connection: {str(e)}")

    async def __aenter__(self) -> AsyncSession:
        """Async context manager entry"""
        try:
            self._session = self.session_factory()
            return self._session
        except Exception as e:
            raise DatabaseError(f"Failed to create database session: {str(e)}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper error handling"""
        if self._session:
            try:
                if exc_type is not None:
                    # An error occurred, rollback
                    await self._session.rollback()
                await self._session.close()
            except SQLAlchemyError as e:
                raise DatabaseError(f"Error closing database session: {str(e)}")
            finally:
                self._session = None

    async def get_session(self) -> AsyncSession:
        """
        Get the current session or create a new one.
        Use this method when you need more control over the session lifecycle.
        """
        if not self._session:
            self._session = self.session_factory()
        return self._session

    async def cleanup(self):
        """Cleanup database resources"""
        if self._session:
            await self._session.close()
        if self.engine:
            await self.engine.dispose()

@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[DatabaseSession, None]:
    """
    Async context manager for database connections.
    Ensures proper resource cleanup even if errors occur.
    
    Usage:
        async with get_db_connection() as db:
            async with db.get_session() as session:
                # Use session here
    """
    db = DatabaseSession()
    try:
        yield db
    finally:
        await db.cleanup()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get a new database session.
    This is a convenience function for FastAPI dependency injection.
    
    Usage:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            # Use session here
    """
    async with DatabaseSession() as session:
        try:
            yield session
        finally:
            await session.close()