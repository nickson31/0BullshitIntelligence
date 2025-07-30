"""
Search router - Endpoints for investor and company searches
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from app.core.logging import get_logger
from app.models import (
    ResponseModel, InvestorSearchRequest, InvestorSearchResponse,
    CompanySearchRequest, CompanySearchResponse, UserContext
)
from app.search.investor_search import investor_search_engine
from app.search.company_search import company_search_engine
from app.services.search_storage_service import search_storage_service
from app.api.middleware import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.post("/investors", response_model=InvestorSearchResponse)
async def search_investors(
    search_request: InvestorSearchRequest,
    background_tasks: BackgroundTasks,
    user_context: UserContext = Depends(get_current_user)
):
    """
    Search for relevant investors (Angels + Funds)
    
    This endpoint:
    1. Validates user has sufficient completeness (50% minimum)
    2. Executes hybrid search combining Angels and Funds
    3. Applies scoring and filtering
    4. Returns structured results
    5. Saves results to database for outreach campaigns
    """
    try:
        logger.info("Processing investor search", 
                   user_id=user_context.user_id,
                   project_id=search_request.project_id,
                   keywords_count=len(search_request.keywords) if search_request.keywords else 0)
        
        # Execute investor search
        search_results = await investor_search_engine.search_investors(
            keywords=search_request.keywords,
            stage_keywords=search_request.stage_keywords,
            categories=search_request.categories,
            project_id=search_request.project_id,
            user_context=user_context,
            limit=search_request.limit or 15
        )
        
        # Save results to database in background for CTO outreach campaigns
        background_tasks.add_task(
            search_storage_service.save_investor_search_results,
            search_results,
            user_context.user_id,
            search_request.project_id
        )
        
        return InvestorSearchResponse(
            success=True,
            message="Investor search completed successfully",
            data=search_results
        )
        
    except ValueError as e:
        logger.warning(f"Invalid search request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Investor search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Investor search failed")


@router.post("/companies", response_model=CompanySearchResponse)
async def search_companies(
    search_request: CompanySearchRequest,
    background_tasks: BackgroundTasks,
    user_context: UserContext = Depends(get_current_user)
):
    """
    Search for relevant B2B service companies
    
    This endpoint searches for companies that can help with specific services
    based on user needs and project context.
    """
    try:
        logger.info("Processing company search",
                   user_id=user_context.user_id,
                   project_id=search_request.project_id,
                   service_type=search_request.service_type)
        
        # Execute company search
        search_results = await company_search_engine.search_companies(
            service_keywords=search_request.service_keywords,
            service_type=search_request.service_type,
            location_preference=search_request.location_preference,
            project_id=search_request.project_id,
            user_context=user_context,
            limit=search_request.limit or 10
        )
        
        # Save results to database in background
        background_tasks.add_task(
            search_storage_service.save_company_search_results,
            search_results,
            user_context.user_id,
            search_request.project_id
        )
        
        return CompanySearchResponse(
            success=True,
            message="Company search completed successfully",
            data=search_results
        )
        
    except ValueError as e:
        logger.warning(f"Invalid company search request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Company search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Company search failed")


@router.get("/investors/saved", response_model=ResponseModel)
async def get_saved_investor_searches(
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user_context: UserContext = Depends(get_current_user)
):
    """Get user's saved investor search results"""
    try:
        saved_searches = await search_storage_service.get_saved_investor_searches(
            user_id=user_context.user_id,
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        return ResponseModel(
            success=True,
            message="Saved investor searches retrieved",
            data={
                "searches": saved_searches,
                "total_count": len(saved_searches),
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve saved investor searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve saved searches")


@router.get("/companies/saved", response_model=ResponseModel)
async def get_saved_company_searches(
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    user_context: UserContext = Depends(get_current_user)
):
    """Get user's saved company search results"""
    try:
        saved_searches = await search_storage_service.get_saved_company_searches(
            user_id=user_context.user_id,
            project_id=project_id,
            limit=limit,
            offset=offset
        )
        
        return ResponseModel(
            success=True,
            message="Saved company searches retrieved",
            data={
                "searches": saved_searches,
                "total_count": len(saved_searches),
                "limit": limit,
                "offset": offset
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve saved company searches: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve saved searches")


@router.get("/investors/{investor_id}/employees", response_model=ResponseModel)
async def get_fund_employees(
    investor_id: str,
    user_context: UserContext = Depends(get_current_user)
):
    """Get employees of a specific investment fund"""
    try:
        employees = await investor_search_engine.get_fund_employees(
            fund_id=investor_id,
            min_score=5.9  # From config
        )
        
        return ResponseModel(
            success=True,
            message="Fund employees retrieved successfully",
            data={
                "fund_id": investor_id,
                "employees": employees,
                "count": len(employees)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve fund employees: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve fund employees")


@router.post("/test", response_model=ResponseModel)
async def test_search_engines(
    test_data: Dict[str, Any],
    user_context: UserContext = Depends(get_current_user)
):
    """Test search engines with sample data (only in debug mode)"""
    from app.core.config import features
    
    if not features.is_debug_mode():
        raise HTTPException(status_code=404, detail="Endpoint not available")
    
    try:
        test_type = test_data.get("type", "investors")
        
        if test_type == "investors":
            results = await investor_search_engine.test_search(
                keywords=test_data.get("keywords", ["fintech", "saas"]),
                stage=test_data.get("stage", "seed")
            )
        elif test_type == "companies":
            results = await company_search_engine.test_search(
                service_keywords=test_data.get("keywords", ["marketing", "digital"])
            )
        else:
            raise ValueError("Invalid test type. Use 'investors' or 'companies'")
        
        return ResponseModel(
            success=True,
            message=f"Test {test_type} search completed",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Test search failed: {e}")
        raise HTTPException(status_code=500, detail="Test search failed")


@router.get("/health", response_model=ResponseModel)
async def search_health_check():
    """Health check for search engines"""
    try:
        investor_health = await investor_search_engine.health_check()
        company_health = await company_search_engine.health_check()
        
        overall_healthy = investor_health and company_health
        
        return ResponseModel(
            success=overall_healthy,
            message="Search engines health check",
            data={
                "investor_search": "healthy" if investor_health else "unhealthy",
                "company_search": "healthy" if company_health else "unhealthy",
                "overall_status": "healthy" if overall_healthy else "degraded"
            }
        )
        
    except Exception as e:
        logger.error(f"Search health check failed: {e}")
        raise HTTPException(status_code=500, detail="Search health check failed")