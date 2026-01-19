"""Attempt service for quiz attempt management with timed quizzes"""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID
import random
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.quiz_repo import QuizRepository
from app.repositories.result_repo import ResultRepository
from app.services.scoring_service import ScoringService
from app.db.base import Attempt, Answer, Question
from app.domain.enums import AttemptStatus
from app.core.exceptions import (
    QuizNotFoundException,
    QuizNotPublishedException,
    ActiveAttemptExistsException,
    MaxAttemptsReachedException,
    AttemptNotFoundException,
    QuizExpiredException,
    AlreadySubmittedException,
    InvalidOperationException
)


class AttemptService:
    """Service for quiz attempt operations"""
    
    def __init__(
        self,
        attempt_repo: AttemptRepository,
        quiz_repo: QuizRepository,
        result_repo: ResultRepository,
        scoring_service: ScoringService
    ):
        self.attempt_repo = attempt_repo
        self.quiz_repo = quiz_repo
        self.result_repo = result_repo
        self.scoring_service = scoring_service
    
    async def can_user_access_quiz(self, user_id: UUID, quiz_id: UUID) -> bool:
        """
        Check if user has permission to access quiz
        
        Rules:
        1. If quiz.is_public = True → Anyone can access
        2. If quiz.is_public = False → Only assigned users can access
        
        Args:
            user_id: User ID
            quiz_id: Quiz ID
            
        Returns:
            True if user has access, False otherwise
        """
        quiz = await self.quiz_repo.get_by_id(quiz_id, include_questions=False)
        
        # Public quizzes - anyone can access
        if quiz.is_public:
            return True
        
        # Check if user is assigned
        assignment = await self.quiz_repo.get_user_assignment(quiz_id, user_id)
        if assignment and assignment.is_active:
            # Check due date if exists
            if assignment.due_date and datetime.utcnow() > assignment.due_date:
                return False
            return True
        
        return False
    
    async def start_attempt(self, quiz_id: UUID, user_id: UUID) -> Attempt:
        """
        Start a new quiz attempt
        
        Args:
            quiz_id: Quiz ID
            user_id: User ID
            
        Returns:
            Created attempt
            
        Raises:
            QuizNotFoundException: If quiz not found
            QuizNotPublishedException: If quiz not published
            QuizAccessDeniedException: If user doesn't have access
            ActiveAttemptExistsException: If active attempt exists
            MaxAttemptsReachedException: If max attempts reached
        """
        # Get quiz
        quiz = await self.quiz_repo.get_by_id(quiz_id, include_questions=True)
        if not quiz:
            raise QuizNotFoundException(details={"quiz_id": str(quiz_id)})
        
        # Check if quiz is published
        if not quiz.is_published:
            raise QuizNotPublishedException(details={"quiz_id": str(quiz_id)})
        
        # CHECK ACCESS PERMISSION (NEW)
        has_access = await self.can_user_access_quiz(user_id, quiz_id)
        if not has_access:
            from app.core.exceptions import QuizAccessDeniedException
            raise QuizAccessDeniedException(
                message="You are not assigned to this quiz or it has expired",
                details={"quiz_id": str(quiz_id), "user_id": str(user_id)}
            )
        
        # Check for active attempt
        active_attempt = await self.attempt_repo.get_active_attempt(user_id, quiz_id)
        if active_attempt:
            raise ActiveAttemptExistsException(
                details={"attempt_id": str(active_attempt.id)}
            )
        
        # Check max attempts
        if quiz.max_attempts:
            attempt_count = await self.attempt_repo.count_user_attempts(user_id, quiz_id)
            if attempt_count >= quiz.max_attempts:
                raise MaxAttemptsReachedException(
                    details={"max_attempts": quiz.max_attempts, "current": attempt_count}
                )
        
        # Calculate expiry time
        expires_at = datetime.utcnow() + timedelta(minutes=quiz.duration_minutes)
        
        # Create attempt
        attempt = await self.attempt_repo.create(quiz_id, user_id, expires_at)
        
        # TODO: Store expiry in Redis for faster checking
        # redis.setex(f"attempt:{attempt.id}:expires", quiz.duration_minutes * 60, expires_at.isoformat())
        
        return attempt
    
    async def submit_answer(
        self,
        attempt_id: UUID,
        question_id: UUID,
        selected_answer: str
    ) -> Answer:
        """
        Submit an answer for a question
        
        Args:
            attempt_id: Attempt ID
            question_id: Question ID
            selected_answer: Selected answer
            
        Returns:
            Created/updated answer
            
        Raises:
            AttemptNotFoundException: If attempt not found
            QuizExpiredException: If quiz has expired
            AlreadySubmittedException: If quiz already submitted
        """
        # Get attempt
        attempt = await self.attempt_repo.get_by_id(attempt_id, include_answers=False)
        if not attempt:
            raise AttemptNotFoundException(details={"attempt_id": str(attempt_id)})
        
        # Check if already submitted
        if attempt.is_submitted:
            raise AlreadySubmittedException(
                details={"attempt_id": str(attempt_id)}
            )
        
        # Check if expired
        if datetime.utcnow() > attempt.expires_at:
            # Auto-submit expired attempt
            await self.submit_attempt(attempt_id)
            raise QuizExpiredException(
                details={
                    "attempt_id": str(attempt_id),
                    "expired_at": attempt.expires_at.isoformat()
                }
            )
        
        # Create/update answer
        answer = await self.attempt_repo.create_answer(
            attempt_id, question_id, selected_answer
        )
        
        return answer
    
    async def submit_attempt(self, attempt_id: UUID) -> dict:
        """
        Submit quiz attempt (atomic operation)
        
        Args:
            attempt_id: Attempt ID
            
        Returns:
            Result details
            
        Raises:
            AttemptNotFoundException: If attempt not found
            AlreadySubmittedException: If already submitted
        """
        # Start transaction - lock attempt row
        attempt = await self.attempt_repo.get_for_update(attempt_id)
        if not attempt:
            raise AttemptNotFoundException(details={"attempt_id": str(attempt_id)})
        
        # Check if already submitted
        if attempt.is_submitted:
            raise AlreadySubmittedException(
                details={"attempt_id": str(attempt_id)}
            )
        
        # Calculate time taken
        time_taken_seconds = int((datetime.utcnow() - attempt.started_at).total_seconds())
        
        # Calculate score
        score_data = await self.scoring_service.calculate_score(attempt_id)
        
        # Create result
        result = await self.result_repo.create(
            attempt_id=attempt_id,
            user_id=attempt.user_id,
            quiz_id=attempt.quiz_id,
            score=score_data["score"],
            total_points=score_data["total_points"],
            percentage=score_data["percentage"],
            passed=score_data["passed"]
        )
        
        # Update attempt
        attempt.is_submitted = True
        attempt.submitted_at = datetime.utcnow()
        attempt.time_taken_seconds = time_taken_seconds
        attempt.status = AttemptStatus.SUBMITTED
        await self.attempt_repo.update(attempt)
        
        # Queue background tasks
        from app.workers.celery_app import celery_app
        
        # Send result notification
        celery_app.send_task(
            "notifications.send_result_notification",
            args=[
                str(attempt.user_id),
                str(attempt.quiz_id),
                str(result.id),  # Added result_id
                score_data["score"],
                score_data["percentage"],
                score_data["passed"]
            ]
        )
        
        # Update leaderboard (if leaderboard worker exists)
        # celery_app.send_task("leaderboard.update_rankings", args=[str(result.id)])
        
        return {
            "result_id": result.id,
            "score": score_data["score"],
            "total_points": score_data["total_points"],
            "percentage": score_data["percentage"],
            "passed": score_data["passed"]
        }
    
    async def get_attempt(self, attempt_id: UUID) -> Attempt:
        """
        Get attempt by ID
        
        Args:
            attempt_id: Attempt ID
            
        Returns:
            Attempt
            
        Raises:
            AttemptNotFoundException: If attempt not found
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id, include_answers=True)
        if not attempt:
            raise AttemptNotFoundException(details={"attempt_id": str(attempt_id)})
        return attempt
    
    def randomize_questions(self, questions: List[Question]) -> List[Question]:
        """Randomize question order"""
        shuffled = questions.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def randomize_options(self, question: Question) -> Question:
        """Randomize option order for a question"""
        shuffled_options = question.options.copy()
        random.shuffle(shuffled_options)
        question.options = shuffled_options
        return question
