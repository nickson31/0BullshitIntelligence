"""
Search engines for 0BullshitIntelligence
"""

from .coordinator import SearchCoordinator

# Create singleton instance
search_coordinator = SearchCoordinator()

__all__ = ["search_coordinator", "SearchCoordinator"]