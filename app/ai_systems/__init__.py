"""
AI Systems for 0BullshitIntelligence
"""

from .coordinator import AICoordinator

# Create singleton instance
ai_coordinator = AICoordinator()

__all__ = ["ai_coordinator", "AICoordinator"]