"""Scoring service for quiz evaluation"""

from typing import List
from uuid import UUID
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.quiz_repo import QuizRepository
from app.db.base import Answer


class ScoringService:
    """Service for scoring quiz attempts"""
    
    def __init__(self, attempt_repo: AttemptRepository, quiz_repo: QuizRepository):
        self.attempt_repo = attempt_repo
        self.quiz_repo = quiz_repo
    
    async def calculate_score(self, attempt_id: UUID) -> dict:
        """
        Calculate score for a quiz attempt
        
        Args:
            attempt_id: Attempt ID
            
        Returns:
            Dictionary with scoring details:
            - score: Points earned
            - total_points: Total possible points
            - percentage: Percentage score
            - passed: Whether user passed
        """
        # Get attempt with answers
        attempt = await self.attempt_repo.get_by_id(attempt_id, include_answers=True)
        if not attempt:
            raise ValueError("Attempt not found")
        
        # Get quiz questions
        questions = await self.quiz_repo.get_questions(attempt.quiz_id)
        question_dict = {q.id: q for q in questions}
        
        # Calculate score
        score = 0
        total_points = sum(q.points for q in questions)
        
        for answer in attempt.answers:
            question = question_dict.get(answer.question_id)
            if not question:
                continue
            
            # Check if answer is correct
            is_correct = self._check_answer(
                answer.selected_answer,
                question.correct_answer,
                question.question_type
            )
            
            # Update answer correctness
            answer.is_correct = is_correct
            
            # Add points if correct
            if is_correct:
                score += question.points
        
        # Calculate percentage
        percentage = (score / total_points * 100) if total_points > 0 else 0
        
        # Get quiz for passing score
        quiz = await self.quiz_repo.get_by_id(attempt.quiz_id, include_questions=False)
        passed = percentage >= quiz.passing_score
        
        return {
            "score": score,
            "total_points": total_points,
            "percentage": round(percentage, 2),
            "passed": passed
        }
    
    def _check_answer(
        self,
        selected_answer: str,
        correct_answer: str,
        question_type: str
    ) -> bool:
        """
        Check if selected answer is correct
        
        Args:
            selected_answer: User's selected answer
            correct_answer: Correct answer
            question_type: Type of question
            
        Returns:
            True if correct, False otherwise
        """
        # Normalize answers for comparison (case-insensitive, trimmed)
        selected = selected_answer.strip().lower()
        correct = correct_answer.strip().lower()
        
        return selected == correct
