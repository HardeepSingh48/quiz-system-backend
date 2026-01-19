"""Results router"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.result import ResultResponse
from app.repositories.result_repo import ResultRepository
from app.api.v1.deps import get_result_repo, get_current_user
from app.db.base import User

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("/attempts/{attempt_id}", response_model=ResultResponse)
async def get_result_by_attempt(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    result_repo: ResultRepository = Depends(get_result_repo)
):
    """
    Get result by attempt ID
    
    Args:
        attempt_id: Attempt ID
        current_user: Current user
        result_repo: Result repository
        
    Returns:
        Result details
    """
    result = await result_repo.get_by_attempt_id(attempt_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    # Verify user owns this result
    if result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this result"
        )
    
    return result


@router.get("/my-results", response_model=List[ResultResponse])
async def get_my_results(
    current_user: User = Depends(get_current_user),
    result_repo: ResultRepository = Depends(get_result_repo)
):
    """
    Get all results for current user
    
    Args:
        current_user: Current user
        result_repo: Result repository
        
    Returns:
        List of user's results
    """
    results = await result_repo.get_user_results(current_user.id)
    return results
