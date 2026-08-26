"""
Configuration management for data seeding framework.

Loads environment variables and provides configuration classes
for database connections, logging, and seeding options.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    
    url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://erp:password@localhost:5432/erp_test"
        ),
        description="PostgreSQL connection URL"
    )
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = Field(default=False, description="Enable SQL logging")
    
    
class SeedingConfig(BaseModel):
    """Seeding operation configuration."""
    
    batch_size: int = Field(default=100, ge=1, le=10000)
    commit_interval: int = Field(default=500, ge=10, le=10000)
    dry_run: bool = Field(default=False, description="Preview without committing")
    verbose: bool = Field(default=True, description="Enable verbose output")
    stop_on_error: bool = Field(default=True, description="Stop on first error")
    
    
class ImporterConfig(BaseModel):
    """Data importer configuration."""
    
    csv_encoding: str = Field(default="utf-8")
    csv_delimiter: str = Field(default=",")
    excel_sheet_index: int = Field(default=0)
    chunk_size: int = Field(default=1000, ge=100, le=50000)
    validate_before_import: bool = Field(default=True)
    skip_invalid_rows: bool = Field(default=False)
    
    
class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    log_file: Optional[Path] = Field(default=None)
    structured_logging: bool = Field(default=True)
    
    
class Config(BaseModel):
    """Main configuration container."""
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    seeding: SeedingConfig = Field(default_factory=SeedingConfig)
    importer: ImporterConfig = Field(default_factory=ImporterConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    class Config:
        arbitrary_types_allowed = True


def get_config() -> Config:
    """
    Create an application configuration instance using environment-derived settings.
    
    Returns:
    	Config: A new application configuration instance.
    """
    return Config()


# Global config instance
config = get_config()
