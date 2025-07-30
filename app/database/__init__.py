"""
Database management for 0BullshitIntelligence
"""

from .manager import DatabaseManager

# Create singleton instance
database_manager = DatabaseManager()

__all__ = ["database_manager", "DatabaseManager"]