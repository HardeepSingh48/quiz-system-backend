"""Quiz repository for database operations"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from app.db.base import Quiz, Question
from app.domain.enums import UserRole


class QuizRepository:
    """Repository for Quiz entity operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        title: str,
        description: str,
        duration_minutes: int,
        passing_score: int,
        randomize_questions: bool,
        randomize_options: bool,
        max_attempts: Optional[int],
        created_by: UUID
    ) -> Quiz:
        """Create a new quiz"""
        quiz = Quiz(
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            passing_score=passing_score,
            randomize_questions=randomize_questions,
            randomize_options=randomize_options,
            max_attempts=max_attempts,
            created_by=created_by
        )
        self.session.add(quiz)
        await self.session.commit()
        await self.session.refresh(quiz)
        return quiz
    
    async def create_question(
        self,
        quiz_id: UUID,
        question_text: str,
        question_type: str,
        options: List[str],
        correct_answer: str,
        points: int,
        order: int
    ) -> Question:
        """Create a question for a quiz"""
        question = Question(
            quiz_id=quiz_id,
            question_text=question_text,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer,
            points=points,
            order=order
        )
        self.session.add(question)
        await self.session.commit()
        await self.session.refresh(question)
        return question
    
    async def get_by_id(self, quiz_id: UUID, include_questions: bool = True) -> Optional[Quiz]:
        """Get quiz by ID with optional questions"""
        query = select(Quiz).where(Quiz.id == quiz_id)
        
        if include_questions:
            query = query.options(selectinload(Quiz.questions))
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_published_quizzes(self, skip: int = 0, limit: int = 100) -> List[Quiz]:
        """Get all published quizzes"""
        result = await self.session.execute(
            select(Quiz)
            .where(Quiz.is_published == True)
            .options(selectinload(Quiz.questions))
            .offset(skip)
            .limit(limit)
            .order_by(Quiz.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_all_quizzes(self, skip: int = 0, limit: int = 100) -> List[Quiz]:
        """Get all quizzes (admin only)"""
        result = await self.session.execute(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .offset(skip)
            .limit(limit)
            .order_by(Quiz.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update(self, quiz: Quiz) -> Quiz:
        """Update quiz"""
        quiz.updated_at = datetime.utcnow()
        self.session.add(quiz)
        await self.session.commit()
        await self.session.refresh(quiz)
        return quiz
    
    async def publish(self, quiz_id: UUID) -> Optional[Quiz]:
        """Publish a quiz"""
        # Load quiz WITH questions to avoid lazy loading issues
        quiz = await self.get_by_id(quiz_id, include_questions=True)
        if quiz:
            quiz.is_published = True
            quiz.updated_at = datetime.utcnow()
            self.session.add(quiz)
            await self.session.commit()
            await self.session.refresh(quiz)
        return quiz
    
    async def delete(self, quiz_id: UUID) -> bool:
        """Delete a quiz"""
        quiz = await self.get_by_id(quiz_id, include_questions=False)
        if quiz:
            await self.session.delete(quiz)
            await self.session.commit()
            return True
        return False
    
    async def get_questions(self, quiz_id: UUID) -> List[Question]:
        """Get all questions for a quiz"""
        result = await self.session.execute(
            select(Question)
            .where(Question.quiz_id == quiz_id)
            .order_by(Question.order)
        )
        return list(result.scalars().all())
    
    # Quiz Assignment Methods
    
    async def assign_quiz(
        self,
        quiz_id: UUID,
        user_id: UUID,
        assigned_by: UUID,
        due_date: Optional[datetime] = None
    ):
        """Assign quiz to a user"""
        from app.db.base import QuizAssignment
        
        # Normalize due_date to naive datetime (database expects TIMESTAMP WITHOUT TIME ZONE)
        if due_date and due_date.tzinfo is not None:
            # Convert to UTC and remove timezone info
            due_date = due_date.replace(tzinfo=None)
        
        # Check if assignment already exists
        result = await self.session.execute(
            select(QuizAssignment).where(
                and_(
                    QuizAssignment.quiz_id == quiz_id,
                    QuizAssignment.user_id == user_id
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing assignment
            existing.is_active = True
            existing.due_date = due_date
            existing.assigned_at = datetime.utcnow()
            self.session.add(existing)
        else:
            # Create new assignment
            assignment = QuizAssignment(
                quiz_id=quiz_id,
                user_id=user_id,
                assigned_by=assigned_by,
                due_date=due_date
            )
            self.session.add(assignment)
        
        await self.session.commit()
        return True
    
    async def get_quiz_assignments(self, quiz_id: UUID):
        """Get all assignments for a quiz"""
        from app.db.base import QuizAssignment, User
        
        result = await self.session.execute(
            select(QuizAssignment, User)
            .join(User, QuizAssignment.user_id == User.id)
            .where(QuizAssignment.quiz_id == quiz_id)
        )
        return result.all()
    
    async def revoke_assignment(self, quiz_id: UUID, user_id: UUID) -> bool:
        """Revoke quiz assignment from a user"""
        from app.db.base import QuizAssignment
        
        result = await self.session.execute(
            select(QuizAssignment).where(
                and_(
                    QuizAssignment.quiz_id == quiz_id,
                    QuizAssignment.user_id == user_id
                )
            )
        )
        assignment = result.scalar_one_or_none()
        
        if assignment:
            assignment.is_active = False
            self.session.add(assignment)
            await self.session.commit()
            return True
        return False
    
    async def get_user_assignment(self, quiz_id: UUID, user_id: UUID):
        """Get specific user's assignment for a quiz"""
        from app.db.base import QuizAssignment
        
        result = await self.session.execute(
            select(QuizAssignment).where(
                and_(
                    QuizAssignment.quiz_id == quiz_id,
                    QuizAssignment.user_id == user_id,
                    QuizAssignment.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_quizzes(self, user_id: UUID) -> List[Quiz]:
        """Get all quizzes assigned to a user or public quizzes"""
        from app.db.base import QuizAssignment
        
        # Get assigned quizzes
        result = await self.session.execute(
            select(Quiz)
            .join(QuizAssignment, Quiz.id == QuizAssignment.quiz_id)
            .where(
                and_(
                    QuizAssignment.user_id == user_id,
                    QuizAssignment.is_active == True,
                    Quiz.is_published == True
                )
            )
            .options(selectinload(Quiz.questions))
        )
        assigned_quizzes = list(result.scalars().all())
        
        # Get public quizzes
        result = await self.session.execute(
            select(Quiz)
            .where(
                and_(
                    Quiz.is_published == True,
                    Quiz.is_public == True
                )
            )
            .options(selectinload(Quiz.questions))
        )
        public_quizzes = list(result.scalars().all())
        
        # Combine and deduplicate
        all_quizzes = {q.id: q for q in assigned_quizzes + public_quizzes}
        return list(all_quizzes.values())
