"""Quiz attempt router"""

from fastapi import APIRouter, Depends, status
from uuid import UUID
from datetime import datetime
from app.schemas.attempt import AttemptStart, AnswerSubmit, AttemptResponse, AnswerResponse
from app.services.attempt_service import AttemptService
from app.api.v1.deps import get_attempt_service, get_current_user
from app.db.base import User

router = APIRouter(prefix="/attempts", tags=["Attempts"])


@router.post("/quizzes/{quiz_id}/start", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
async def start_quiz_attempt(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    attempt_service: AttemptService = Depends(get_attempt_service)
):
    """
    Start a new quiz attempt
    
    Args:
        quiz_id: Quiz ID
        current_user: Current user
        attempt_service: Attempt service
        
    Returns:
        Created attempt with timer information
    """
    attempt = await attempt_service.start_attempt(quiz_id, current_user.id)
    
    # Calculate time remaining
    time_remaining = int((attempt.expires_at - datetime.utcnow()).total_seconds())
    
    return AttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        submitted_at=attempt.submitted_at,
        is_submitted=attempt.is_submitted,
        status=attempt.status,
        time_remaining_seconds=max(0, time_remaining),
        answers=[]
    )


@router.get("/{attempt_id}", response_model=AttemptResponse)
async def get_attempt(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    attempt_service: AttemptService = Depends(get_attempt_service)
):
    """
    Get quiz attempt details
    
    Args:
        attempt_id: Attempt ID
        current_user: Current user
        attempt_service: Attempt service
        
    Returns:
        Attempt details with answers
    """
    attempt = await attempt_service.get_attempt(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this attempt"
        )
    
    # Calculate time remaining
    time_remaining = int((attempt.expires_at - datetime.utcnow()).total_seconds())
    
    return AttemptResponse(
        id=attempt.id,
        quiz_id=attempt.quiz_id,
        user_id=attempt.user_id,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        submitted_at=attempt.submitted_at,
        is_submitted=attempt.is_submitted,
        status=attempt.status,
        time_remaining_seconds=max(0, time_remaining),
        answers=[
            AnswerResponse(
                id=a.id,
                question_id=a.question_id,
                selected_answer=a.selected_answer,
                answered_at=a.answered_at
            ) for a in attempt.answers
        ]
    )


@router.post("/{attempt_id}/answers", response_model=AnswerResponse)
async def submit_answer(
    attempt_id: UUID,
    answer_data: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    attempt_service: AttemptService = Depends(get_attempt_service)
):
    """
    Submit an answer for a question
    
    Args:
        attempt_id: Attempt ID
        answer_data: Answer data
        current_user: Current user
        attempt_service: Attempt service
        
    Returns:
        Submitted answer
    """
    # Verify user owns the attempt
    attempt = await attempt_service.get_attempt(attempt_id)
    if attempt.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this attempt"
        )
    
    # Submit answer
    answer = await attempt_service.submit_answer(
        attempt_id=attempt_id,
        question_id=answer_data.question_id,
        selected_answer=answer_data.selected_answer
    )
    
    return AnswerResponse(
        id=answer.id,
        question_id=answer.question_id,
        selected_answer=answer.selected_answer,
        answered_at=answer.answered_at
    )


@router.post("/{attempt_id}/submit")
async def submit_quiz(
    attempt_id: UUID,
    current_user: User = Depends(get_current_user),
    attempt_service: AttemptService = Depends(get_attempt_service)
):
    """
    Submit quiz attempt for grading
    
    Args:
        attempt_id: Attempt ID
        current_user: Current user
        attempt_service: Attempt service
        
    Returns:
        Result summary
    """
    # Verify user owns the attempt
    attempt = await attempt_service.get_attempt(attempt_id)
    if attempt.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this attempt"
        )
    
    # Submit attempt
    result = await attempt_service.submit_attempt(attempt_id)
    
    return {
        "message": "Quiz submitted successfully",
        "result": result
    }
