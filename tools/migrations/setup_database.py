#!/usr/bin/env python3
"""
Setup PostgreSQL database for Seraaj event store.

Usage:
    python tools/migrations/setup_database.py [--create-db] [--drop-existing]
    
Arguments:
    --create-db: Create the database if it doesn't exist
    --drop-existing: Drop existing tables before creating new ones
"""

import argparse
import asyncio
import os
from pathlib import Path
from typing import Optional
import asyncpg
import logging

# Add the project root to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infrastructure.db.connection import DatabaseConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Handles database setup and schema creation"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self.schema_file = Path(__file__).parent.parent.parent / "infrastructure" / "db" / "schema.sql"
    
    async def create_database_if_not_exists(self, database_name: str):
        """Create database if it doesn't exist"""
        logger.info(f"Checking if database '{database_name}' exists...")
        
        # Parse connection URL to get connection details without database
        if not self.config.database_url:
            raise ValueError("Database URL not configured")
        
        # Extract connection components
        url_parts = self.config.database_url.replace("postgresql+asyncpg://", "").split("/")
        auth_and_host = url_parts[0]
        
        # Split auth and host
        if "@" in auth_and_host:
            auth, host = auth_and_host.split("@")
            user, password = auth.split(":")
        else:
            user = "postgres"
            password = ""
            host = auth_and_host
        
        # Extract host and port
        if ":" in host:
            host, port = host.split(":")
            port = int(port)
        else:
            port = 5432
        
        # Connect to postgres database to check if target database exists
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database='postgres'  # Connect to default postgres database
            )
            
            # Check if database exists
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", 
                database_name
            )
            
            if not result:
                logger.info(f"Creating database '{database_name}'...")
                await conn.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(f"Database '{database_name}' created successfully")
            else:
                logger.info(f"Database '{database_name}' already exists")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    async def drop_existing_tables(self):
        """Drop existing tables"""
        logger.info("Dropping existing tables...")
        
        try:
            conn = await asyncpg.connect(self.config.database_url.replace("+asyncpg", ""))
            
            # Drop tables in reverse dependency order
            drop_statements = [
                "DROP VIEW IF EXISTS match_suggestion_stats CASCADE;",
                "DROP VIEW IF EXISTS application_stats CASCADE;",
                "DROP VIEW IF EXISTS event_store_stats CASCADE;",
                "DROP TABLE IF EXISTS match_suggestions CASCADE;",
                "DROP TABLE IF EXISTS applications CASCADE;",
                "DROP TABLE IF EXISTS events CASCADE;"
            ]
            
            for statement in drop_statements:
                await conn.execute(statement)
                logger.info(f"Executed: {statement}")
            
            await conn.close()
            logger.info("Existing tables dropped successfully")
            
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise
    
    async def create_schema(self):
        """Create database schema from SQL file"""
        logger.info("Creating database schema...")
        
        if not self.schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_file}")
        
        # Read schema SQL
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        try:
            # Connect and execute schema
            conn = await asyncpg.connect(self.config.database_url.replace("+asyncpg", ""))
            
            # Split statements and execute them one by one
            statements = [
                stmt.strip() for stmt in schema_sql.split(';') 
                if stmt.strip() and not stmt.strip().startswith('--')
            ]
            
            for statement in statements:
                if statement:
                    try:
                        await conn.execute(statement)
                        logger.debug(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        logger.error(f"Error executing statement: {statement[:100]}...")
                        logger.error(f"Error: {e}")
                        raise
            
            await conn.close()
            logger.info("Database schema created successfully")
            
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            raise
    
    async def verify_schema(self):
        """Verify that all tables and views were created"""
        logger.info("Verifying database schema...")
        
        expected_tables = ['events', 'applications', 'match_suggestions']
        expected_views = ['event_store_stats', 'application_stats', 'match_suggestion_stats']
        
        try:
            conn = await asyncpg.connect(self.config.database_url.replace("+asyncpg", ""))
            
            # Check tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            
            table_names = [row['table_name'] for row in tables]
            
            for table in expected_tables:
                if table in table_names:
                    logger.info(f"✓ Table '{table}' exists")
                else:
                    logger.error(f"✗ Table '{table}' missing")
            
            # Check views
            views = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
            """)
            
            view_names = [row['table_name'] for row in views]
            
            for view in expected_views:
                if view in view_names:
                    logger.info(f"✓ View '{view}' exists")
                else:
                    logger.error(f"✗ View '{view}' missing")
            
            # Check indexes
            indexes = await conn.fetch("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
            """)
            
            logger.info(f"Created {len(indexes)} indexes")
            
            await conn.close()
            logger.info("Schema verification completed")
            
        except Exception as e:
            logger.error(f"Error verifying schema: {e}")
            raise

async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup PostgreSQL database for Seraaj")
    parser.add_argument('--create-db', action='store_true', help='Create database if it does not exist')
    parser.add_argument('--drop-existing', action='store_true', help='Drop existing tables before creating')
    parser.add_argument('--verify-only', action='store_true', help='Only verify the existing schema')
    
    args = parser.parse_args()
    
    try:
        setup = DatabaseSetup()
        
        if not setup.config.is_configured:
            logger.error("Database not configured. Set DATABASE_URL or DB_* environment variables.")
            return
        
        logger.info(f"Using database URL: {setup.config.database_url}")
        
        if args.verify_only:
            await setup.verify_schema()
            return
        
        # Extract database name from URL
        database_name = setup.config.database_url.split('/')[-1]
        
        if args.create_db:
            await setup.create_database_if_not_exists(database_name)
        
        if args.drop_existing:
            await setup.drop_existing_tables()
        
        # Create schema
        await setup.create_schema()
        
        # Verify schema
        await setup.verify_schema()
        
        logger.info("Database setup completed successfully")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())