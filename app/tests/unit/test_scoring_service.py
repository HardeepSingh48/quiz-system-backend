"""Unit tests for scoring service"""

import pytest
from uuid import uuid4
from app.services.scoring_service import ScoringService


class TestScoringService:
    """Test cases for ScoringService"""
    
    def test_check_answer_mcq_correct(self):
        """Test correct MCQ answer"""
        service = ScoringService(None, None)
        result = service._check_answer(
            selected_answer="Option A",
            correct_answer="Option A",
            question_type="mcq"
        )
        assert result is True
    
    def test_check_answer_mcq_incorrect(self):
        """Test incorrect MCQ answer"""
        service = ScoringService(None, None)
        result = service._check_answer(
            selected_answer="Option B",
            correct_answer="Option A",
            question_type="mcq"
        )
        assert result is False
    
    def test_check_answer_case_insensitive(self):
        """Test case-insensitive answer checking"""
        service = ScoringService(None, None)
        result = service._check_answer(
            selected_answer="option a",
            correct_answer="Option A",
            question_type="mcq"
        )
        assert result is True
    
    def test_check_answer_true_false(self):
        """Test true/false question"""
        service = ScoringService(None, None)
        
        # Correct
        result = service._check_answer(
            selected_answer="true",
            correct_answer="true",
            question_type="true_false"
        )
        assert result is True
        
        # Incorrect
        result = service._check_answer(
            selected_answer="false",
            correct_answer="true",
            question_type="true_false"
        )
        assert result is False
