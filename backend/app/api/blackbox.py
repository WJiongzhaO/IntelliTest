"""API routes for black-box test case generation."""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.engines.blackbox_generator import BlackBoxTestGenerator
from app.models.requirement import StructuredRequirement
from app.models.test_case import BlackBoxTechnique, CoverageItem, TestCase, TestSuite
from app.services.artifact_store import persist_suite

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
    requirement_id: Optional[str] = None
    use_llm: bool = True


class GenerateAllRequest(BaseModel):
    """Request for all-technique generation with optional LLM toggle."""
    requirement: StructuredRequirement
    use_llm: bool = True


@router.get("/techniques")
async def get_available_techniques():
    """Get information about available black-box testing techniques.
    
    Returns details about EP, BVA, and DT techniques including their
    purpose and best use cases according to ISO 29119-4.
    """
    return generator_engine.get_technique_info()


@router.post("/generate/all", response_model=list[TestCase])
async def generate_all_techniques(body: GenerateAllRequest):
    """Generate test cases using all three black-box techniques (EP, BVA, DT)."""
    try:
        test_cases = generator_engine.generate_all_techniques(
            body.requirement, use_llm=body.use_llm
        )
        return test_cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.post("/generate/with-coverage")
async def generate_with_coverage(
    body: GenerateWithCoverageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate test cases with full coverage tracking and reporting."""
    try:
        technique_enums = None
        if body.selected_techniques:
            technique_enums = [BlackBoxTechnique(t.upper()) for t in body.selected_techniques]

        result = generator_engine.generate_with_coverage_tracking(
            body.requirement, technique_enums, use_llm=body.use_llm
        )

        coverage_items = result["coverage_items"]
        test_cases = result["test_cases"]

        if body.requirement_id:
            suite = TestSuite(
                id=f"bb-suite-{body.requirement_id}",
                name=f"Blackbox design for {body.requirement.id}",
                description="Blackbox generation output",
                test_cases=test_cases,
            )
            await persist_suite(
                db,
                requirement_id=body.requirement_id,
                suite=suite,
                source_type="blackbox",
                coverage_items=coverage_items,
            )

        result["coverage_items"] = [item.model_dump() for item in coverage_items]
        result["test_cases"] = [tc.model_dump() for tc in test_cases]
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}") from e


class GenerateTechniqueRequest(BaseModel):
    requirement: StructuredRequirement
    use_llm: bool = True


@router.post("/generate/{technique}", response_model=list[TestCase])
async def generate_specific_technique(
    technique: str,
    body: GenerateTechniqueRequest,
):
    """Generate test cases using a specific black-box technique."""
    try:
        technique_enum = BlackBoxTechnique(technique.upper())
        test_cases = generator_engine.generate_specific_technique(
            body.requirement, technique_enum, use_llm=body.use_llm
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
