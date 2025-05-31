import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

class TestMigrations:
    
    def test_migration_up_and_down(self):
        """Test migration up and down operations"""
        alembic_cfg = Config("alembic.ini")
        
        # Test upgrade
        command.upgrade(alembic_cfg, "head")
        
        # Test downgrade
        command.downgrade(alembic_cfg, "base")
        
        # Test upgrade again
        command.upgrade(alembic_cfg, "head")
