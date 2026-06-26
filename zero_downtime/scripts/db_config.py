#!/usr/bin/env python3
"""
Database configuration for the zero-downtime migration project.
Centralized configuration for all scripts.
"""

import os
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @property
    def connection_string(self):
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"
    
    @property
    def url(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

# Source database configuration (using port 5434)
SOURCE_CONFIG = DatabaseConfig(
    host=os.getenv('SOURCE_DB_HOST', 'localhost'),
    port=int(os.getenv('SOURCE_DB_PORT', '5434')),
    database=os.getenv('SOURCE_DB_NAME', 'sales'),
    user=os.getenv('SOURCE_DB_USER', 'postgres'),
    password=os.getenv('SOURCE_DB_PASSWORD', 'postgres')
)

# Target database configuration (using port 5435)
TARGET_CONFIG = DatabaseConfig(
    host=os.getenv('TARGET_DB_HOST', 'localhost'),
    port=int(os.getenv('TARGET_DB_PORT', '5435')),
    database=os.getenv('TARGET_DB_NAME', 'sales'),
    user=os.getenv('TARGET_DB_USER', 'postgres'),
    password=os.getenv('TARGET_DB_PASSWORD', 'postgres')
)

# Redis configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'db': 0
}

def get_connection(config: DatabaseConfig):
    """Get a psycopg2 connection"""
    import psycopg2
    return psycopg2.connect(**{
        'host': config.host,
        'port': config.port,
        'dbname': config.database,
        'user': config.user,
        'password': config.password
    })