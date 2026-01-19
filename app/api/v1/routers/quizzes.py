"""Quiz router"""

from fastapi import APIRouter, Depends, status
from typing import List
from uuid import UUID
from app.schemas.quiz import QuizCreate, QuizUpdate, QuizResponse, QuizAdminResponse, QuizListItem
from app.schemas.assignment import QuizAssignmentCreate, QuizAssignmentResponse, QuizAssignmentWithUser
from app.services.quiz_service import QuizService
from app.api.v1.deps import get_quiz_service, require_admin, get_current_user
from app.db.base import User

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])


@router.post("/", response_model=QuizAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz_data: QuizCreate,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Create a new quiz (Admin only)
    
    Args:
        quiz_data: Quiz creation data
        current_admin: Current admin user
        quiz_service: Quiz service
        
    Returns:
        Created quiz
    """
    quiz = await quiz_service.create_quiz(
        title=quiz_data.title,
        description=quiz_data.description,
        duration_minutes=quiz_data.duration_minutes,
        passing_score=quiz_data.passing_score,
        randomize_questions=quiz_data.randomize_questions,
        randomize_options=quiz_data.randomize_options,
        max_attempts=quiz_data.max_attempts,
        questions=quiz_data.questions,
        created_by=current_admin.id
    )
    return quiz


@router.get("/", response_model=List[QuizResponse])
async def list_published_quizzes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    List all published quizzes
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user: Current user
        quiz_service: Quiz service
        
    Returns:
        List of published quizzes
    """
    quizzes = await quiz_service.get_published_quizzes(skip, limit)
    return quizzes


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Get quiz details
    
    Args:
        quiz_id: Quiz ID
        current_user: Current user
        quiz_service: Quiz service
        
    Returns:
        Quiz details
    """
    quiz = await quiz_service.get_quiz(quiz_id)
    return quiz


@router.put("/{quiz_id}", response_model=QuizAdminResponse)
async def update_quiz(
    quiz_id: UUID,
    quiz_update: QuizUpdate,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Update quiz (Admin only)
    
    Args:
        quiz_id: Quiz ID
        quiz_update: Quiz update data
        current_admin: Current admin user
        quiz_service: Quiz service
        
    Returns:
        Updated quiz
    """
    quiz = await quiz_service.update_quiz(
        quiz_id=quiz_id,
        title=quiz_update.title,
        description=quiz_update.description,
        duration_minutes=quiz_update.duration_minutes,
        passing_score=quiz_update.passing_score,
        randomize_questions=quiz_update.randomize_questions,
        randomize_options=quiz_update.randomize_options,
        max_attempts=quiz_update.max_attempts
    )
    return quiz


@router.post("/{quiz_id}/publish", response_model=QuizAdminResponse)
async def publish_quiz(
    quiz_id: UUID,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Publish a quiz (Admin only)
    
    Args:
        quiz_id: Quiz ID
        current_admin: Current admin user
        quiz_service: Quiz service
        
    Returns:
        Published quiz
    """
    quiz = await quiz_service.publish_quiz(quiz_id)
    return quiz


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: UUID,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Delete a quiz (Admin only)
    
    Args:
        quiz_id: Quiz ID
        current_admin: Current admin user
        quiz_service: Quiz service
    """
    await quiz_service.delete_quiz(quiz_id)
    return None


# Quiz Assignment Endpoints (NEW)

@router.post("/{quiz_id}/assign", status_code=status.HTTP_201_CREATED)
async def assign_quiz_to_users(
    quiz_id: UUID,
    assignment_data: QuizAssignmentCreate,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Admin assigns quiz to specific users
    
    Body:
    {
        "user_ids": ["uuid1", "uuid2", "uuid3"],
        "due_date": "2024-02-01T23:59:59Z"  // optional
    }
    """
    result = await quiz_service.assign_quiz(
        quiz_id=quiz_id,
        user_ids=assignment_data.user_ids,
        assigned_by=current_admin.id,
        due_date=assignment_data.due_date
    )
    return result


@router.delete("/{quiz_id}/assignments/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_quiz_assignment(
    quiz_id: UUID,
    user_id: UUID,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """Admin revokes quiz assignment from a user"""
    await quiz_service.revoke_assignment(quiz_id, user_id)
    return None


@router.get("/{quiz_id}/assignments")
async def get_quiz_assignments(
    quiz_id: UUID,
    current_admin: User = Depends(require_admin),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """Get all users assigned to this quiz"""
    assignments = await quiz_service.get_quiz_assignments(quiz_id)
    
    # Format response
    result = []
    for assignment, user in assignments:
        result.append(QuizAssignmentWithUser(
            id=assignment.id,
            quiz_id=assignment.quiz_id,
            user_id=assignment.user_id,
            user_email=user.email,
            user_username=user.username,
            assigned_at=assignment.assigned_at,
            due_date=assignment.due_date,
            is_active=assignment.is_active
        ))
    
    return result


@router.get("/my-quizzes", response_model=List[QuizResponse])
async def get_my_assigned_quizzes(
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service)
):
    """
    Get all quizzes assigned to current user
    Includes both public quizzes and specifically assigned ones
    """
    quizzes = await quiz_service.get_user_quizzes(current_user.id)
    return quizzes
