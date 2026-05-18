"""API routes for black-box test case generation."""

from typing import Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from app.engines.blackbox_generator import BlackBoxTestGenerator
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, CoverageItem, TestCase

router = APIRouter(
    prefix="/blackbox",
    tags=["Black-Box Testing"],
    responses={404: {"description": "Not found"}},
)

# Initialize the generator engine
generator_engine = BlackBoxTestGenerator()


class GenerateWithCoverageRequest(BaseModel):
    """Request model for generate_with_coverage endpoint."""
    requirement: StructuredRequirement
    selected_techniques: Optional[list[str]] = None


@router.get("/techniques")
async def get_available_techniques():
    """Get information about available black-box testing techniques.
    
    Returns details about EP, BVA, and DT techniques including their
    purpose and best use cases according to ISO 29119-4.
    """
    return generator_engine.get_technique_info()


@router.post("/generate/all", response_model=list[TestCase])
async def generate_all_techniques(requirement: StructuredRequirement):
    """Generate test cases using all three black-box techniques (EP, BVA, DT).
    
    This endpoint applies all ISO 29119-4 techniques to the given requirement
    and returns a comprehensive set of test cases.
    
    Args:
        requirement: The structured requirement to test
        
    Returns:
        List of generated test cases from all techniques
    """
    try:
        test_cases = generator_engine.generate_all_techniques(requirement)
        return test_cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/generate/with-coverage")
async def generate_with_coverage(
    requirement: StructuredRequirement,
    selected_techniques: Optional[list[str]] = None
):
    """Generate test cases with full coverage tracking and reporting.
    
    This is the most comprehensive endpoint that provides:
    - Identified coverage items
    - Generated test cases
    - Coverage statistics and metrics
    
    Args:
        requirement: The structured requirement to test
        selected_techniques: Optional list of techniques to use (default: all)
        
    Returns:
        Dictionary containing coverage_items, test_cases, and coverage_report
    """
    try:
        # Convert string techniques to enums if provided
        technique_enums = None
        if selected_techniques:
            technique_enums = [
                BlackBoxTechnique(t.upper()) for t in selected_techniques
            ]
        
        result = generator_engine.generate_with_coverage_tracking(
            requirement, technique_enums
        )
        
        # Convert CoverageItem objects to dicts for JSON serialization
        result['coverage_items'] = [
            item.model_dump() for item in result['coverage_items']
        ]
        
        # Also convert TestCase objects to dicts
        result['test_cases'] = [
            tc.model_dump() for tc in result['test_cases']
        ]
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/generate/{technique}", response_model=list[TestCase])
async def generate_specific_technique(
    requirement: StructuredRequirement,
    technique: str
):
    """Generate test cases using a specific black-box technique.
    
    Args:
        requirement: The structured requirement to test
        technique: Technique to use (EP, BVA, or DT)
        
    Returns:
        List of generated test cases
    """
    try:
        # Convert string to enum
        technique_enum = BlackBoxTechnique(technique.upper())
        test_cases = generator_engine.generate_specific_technique(
            requirement, technique_enum
        )
        return test_cases
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid technique: {technique}. Must be one of: EP, BVA, DT"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/coverage/identify", response_model=list[CoverageItem])
async def identify_coverage_items(requirement: StructuredRequirement):
    """Identify coverage items from a structured requirement.
    
    Analyzes input fields, data ranges, and conditions to create
    coverage items that need to be tested.
    
    Args:
        requirement: The structured requirement to analyze
        
    Returns:
        List of identified coverage items
    """
    try:
        coverage_manager = generator_engine.coverage_manager
        coverage_items = coverage_manager.identify_coverage_items(requirement)
        return coverage_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coverage identification failed: {str(e)}")


@router.post("/coverage/select-techniques")
async def select_techniques_for_coverage_item(
    coverage_item: CoverageItem,
    techniques: list[str]
):
    """Select testing techniques for a specific coverage item.
    
    Args:
        coverage_item: The coverage item to update
        techniques: List of technique names (EP, BVA, DT)
        
    Returns:
        Updated coverage item
    """
    try:
        coverage_manager = generator_engine.coverage_manager
        technique_enums = [BlackBoxTechnique(t.upper()) for t in techniques]
        updated_item = coverage_manager.select_techniques_for_item(
            coverage_item, technique_enums
        )
        return updated_item
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid technique. Must be one of: EP, BVA, DT"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Technique selection failed: {str(e)}")


@router.get("/coverage/report-template")
async def get_coverage_report_template():
    """Get a template/example of coverage report structure.
    
    Returns example structure showing what coverage metrics are available.
    """
    return {
        'total_coverage_items': 0,
        'covered_items': 0,
        'uncovered_items': 0,
        'coverage_percentage': 0.0,
        'type_distribution': {},
        'technique_usage': {},
        'uncovered_item_details': []
    }
