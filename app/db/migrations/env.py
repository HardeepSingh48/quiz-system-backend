"""Alembic migration environment configuration"""

import sys
from pathlib import Path

# CRITICAL: Add project root to Python path so we can import from 'app'
# This resolves: app/db/migrations/env.py -> app/db -> app -> project_root
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from sqlmodel import SQLModel

# NOW we can import from app module
from app.core.config import settings

# Import ALL models so Alembic can detect schema changes
# These imports register the models with SQLModel.metadata
from app.db.base import (
    User,
    Quiz,
    Question,
    Attempt,
    Answer,
    Result,
    RefreshToken,
    QuizAssignment,  # Don't forget the new assignment model!
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use SQLModel.metadata as target for autogenerate
target_metadata = SQLModel.metadata

# Override sqlalchemy.url from settings (not from alembic.ini)
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get alembic config section
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        configuration = {}
    
    # Override DB URL from settings
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect default value changes
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine which mode to run
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
