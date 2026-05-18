"""Black-box test case generators implementing ISO 29119-4 techniques."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, TestCase


class BaseBlackBoxGenerator(ABC):
    """Abstract base class for black-box test case generators.
    
    All generators must implement the generate method to produce
    test cases according to ISO 29119-4 standards.
    """
    
    @property
    @abstractmethod
    def technique(self) -> BlackBoxTechnique:
        """Return the testing technique this generator implements."""
        pass
    
    @abstractmethod
    def generate(
        self,
        requirement: StructuredRequirement,
        coverage_items: Optional[list[str]] = None
    ) -> list[TestCase]:
        """Generate test cases based on the given requirement.
        
        Args:
            requirement: The structured requirement to analyze
            coverage_items: Optional list of specific coverage items to address
            
        Returns:
            List of generated test cases
        """
        pass
    
    def _generate_test_id(self, requirement_id: str, index: int) -> str:
        """Generate a unique test case ID.
        
        Args:
            requirement_id: Source requirement ID
            index: Sequential index for this technique
            
        Returns:
            Formatted test case ID (e.g., REQ001_EP_001)
        """
        return f"{requirement_id}_{self.technique.value}_{index:03d}"
