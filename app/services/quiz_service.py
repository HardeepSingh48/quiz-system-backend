"""Quiz service for quiz management"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.repositories.quiz_repo import QuizRepository
from app.db.base import Quiz, Question
from app.core.exceptions import QuizNotFoundException, InvalidOperationException
from app.schemas.quiz import QuestionCreate


class QuizService:
    """Service for quiz operations"""
    
    def __init__(self, quiz_repo: QuizRepository):
        self.quiz_repo = quiz_repo
    
    async def create_quiz(
        self,
        title: str,
        description: str,
        duration_minutes: int,
        passing_score: int,
        randomize_questions: bool,
        randomize_options: bool,
        max_attempts: Optional[int],
        questions: List[QuestionCreate],
        created_by: UUID
    ) -> Quiz:
        """
        Create a new quiz with questions
        
        Args:
            title: Quiz title
            description: Quiz description
            duration_minutes: Quiz duration
            passing_score: Passing percentage
            randomize_questions: Randomize question order
            randomize_options: Randomize option order
            max_attempts: Maximum attempts allowed
            questions: List of questions
            created_by: Creator user ID
            
        Returns:
            Created quiz
        """
        # Create quiz
        quiz = await self.quiz_repo.create(
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            passing_score=passing_score,
            randomize_questions=randomize_questions,
            randomize_options=randomize_options,
            max_attempts=max_attempts,
            created_by=created_by
        )
        
        # Create questions
        for q_data in questions:
            await self.quiz_repo.create_question(
                quiz_id=quiz.id,
                question_text=q_data.question_text,
                question_type=q_data.question_type,
                options=q_data.options,
                correct_answer=q_data.correct_answer,
                points=q_data.points,
                order=q_data.order
            )
        
        # Reload quiz with questions
        quiz = await self.quiz_repo.get_by_id(quiz.id, include_questions=True)
        return quiz
    
    async def get_quiz(self, quiz_id: UUID) -> Quiz:
        """
        Get quiz by ID
        
        Args:
            quiz_id: Quiz ID
            
        Returns:
            Quiz
            
        Raises:
            QuizNotFoundException: If quiz not found
        """
        quiz = await self.quiz_repo.get_by_id(quiz_id, include_questions=True)
        if not quiz:
            raise QuizNotFoundException(details={"quiz_id": str(quiz_id)})
        return quiz
    
    async def get_published_quizzes(self, skip: int = 0, limit: int = 100) -> List[Quiz]:
        """Get all published quizzes"""
        return await self.quiz_repo.get_published_quizzes(skip, limit)
    
    async def get_all_quizzes(self, skip: int = 0, limit: int = 100) -> List[Quiz]:
        """Get all quizzes (admin only)"""
        return await self.quiz_repo.get_all_quizzes(skip, limit)
    
    async def update_quiz(
        self,
        quiz_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        passing_score: Optional[int] = None,
        randomize_questions: Optional[bool] = None,
        randomize_options: Optional[bool] = None,
        max_attempts: Optional[int] = None
    ) -> Quiz:
        """
        Update quiz
        
        Args:
            quiz_id: Quiz ID
            title: New title
            description: New description
            duration_minutes: New duration
            passing_score: New passing score
            randomize_questions: Randomize questions
            randomize_options: Randomize options
            max_attempts: Max attempts
            
        Returns:
            Updated quiz
            
        Raises:
            QuizNotFoundException: If quiz not found
            InvalidOperationException: If quiz is already published
        """
        quiz = await self.get_quiz(quiz_id)
        
        # Prevent updating published quizzes
        if quiz.is_published:
            raise InvalidOperationException(
                message="Cannot update published quiz",
                details={"quiz_id": str(quiz_id)}
            )
        
        # Update fields
        if title is not None:
            quiz.title = title
        if description is not None:
            quiz.description = description
        if duration_minutes is not None:
            quiz.duration_minutes = duration_minutes
        if passing_score is not None:
            quiz.passing_score = passing_score
        if randomize_questions is not None:
            quiz.randomize_questions = randomize_questions
        if randomize_options is not None:
            quiz.randomize_options = randomize_options
        if max_attempts is not None:
            quiz.max_attempts = max_attempts
        
        return await self.quiz_repo.update(quiz)
    
    async def publish_quiz(self, quiz_id: UUID) -> Quiz:
        """
        Publish a quiz
        
        Args:
            quiz_id: Quiz ID
            
        Returns:
            Published quiz
            
        Raises:
            QuizNotFoundException: If quiz not found
        """
        quiz = await self.quiz_repo.publish(quiz_id)
        if not quiz:
            raise QuizNotFoundException(details={"quiz_id": str(quiz_id)})
        
        # TODO: Trigger notification to users (Celery task)
        # celery.send_task('notifications.quiz_published', args=[quiz_id])
        
        return quiz
    
    async def delete_quiz(self, quiz_id: UUID) -> bool:
        """
        Delete a quiz
        
        Args:
            quiz_id: Quiz ID
            
        Returns:
            True if deleted
            
        Raises:
            QuizNotFoundException: If quiz not found
        """
        deleted = await self.quiz_repo.delete(quiz_id)
        if not deleted:
            raise QuizNotFoundException(details={"quiz_id": str(quiz_id)})
        return True
    
    # Quiz Assignment Methods
    
    async def assign_quiz(
        self,
        quiz_id: UUID,
        user_ids: List[UUID],
        assigned_by: UUID,
        due_date: Optional[datetime] = None
    ) -> dict:
        """
        Assign quiz to multiple users
        
        Args:
            quiz_id: Quiz ID
            user_ids: List of user IDs to assign
            assigned_by: Admin user ID
            due_date: Optional deadline
            
        Returns:
            Assignment summary
        """
        # Verify quiz exists
        await self.get_quiz(quiz_id)
        
        # Assign to each user
        for user_id in user_ids:
            await self.quiz_repo.assign_quiz(
                quiz_id=quiz_id,
                user_id=user_id,
                assigned_by=assigned_by,
                due_date=due_date
            )
        
        return {
            "quiz_id": quiz_id,
            "assigned_users": len(user_ids),
            "message": f"Quiz assigned to {len(user_ids)} user(s)"
        }
    
    async def revoke_assignment(self, quiz_id: UUID, user_id: UUID) -> bool:
        """
        Revoke quiz assignment from a user
        
        Args:
            quiz_id: Quiz ID
            user_id: User ID
            
        Returns:
            True if revoked
        """
        return await self.quiz_repo.revoke_assignment(quiz_id, user_id)
    
    async def get_quiz_assignments(self, quiz_id: UUID):
        """Get all assignments for a quiz"""
        return await self.quiz_repo.get_quiz_assignments(quiz_id)
    
    async def get_user_quizzes(self, user_id: UUID) -> List[Quiz]:
        """Get quizzes assigned to a user or public quizzes"""
        return await self.quiz_repo.get_user_quizzes(user_id)
