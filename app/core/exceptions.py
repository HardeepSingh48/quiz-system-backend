"""Custom exceptions for the application"""

from typing import Any, Optional, Dict


class CustomException(Exception):
    """Base exception class for custom exceptions"""
    
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "An internal server error occurred"
    
    def __init__(self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


# Authentication Exceptions
class InvalidCredentialsException(CustomException):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"


class TokenExpiredException(CustomException):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "Token has expired"


class InvalidTokenException(CustomException):
    status_code = 401
    error_code = "INVALID_TOKEN"
    message = "Invalid or malformed token"


class InsufficientPermissionsException(CustomException):
    status_code = 403
    error_code = "INSUFFICIENT_PERMISSIONS"
    message = "You do not have permission to perform this action"


# Resource Exceptions
class ResourceNotFoundException(CustomException):
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found"


class UserNotFoundException(ResourceNotFoundException):
    error_code = "USER_NOT_FOUND"
    message = "User not found"


class QuizNotFoundException(ResourceNotFoundException):
    error_code = "QUIZ_NOT_FOUND"
    message = "Quiz not found"


class AttemptNotFoundException(ResourceNotFoundException):
    error_code = "ATTEMPT_NOT_FOUND"
    message = "Quiz attempt not found"


class ResultNotFoundException(ResourceNotFoundException):
    error_code = "RESULT_NOT_FOUND"
    message = "Result not found"


# Validation Exceptions
class ValidationException(CustomException):
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Validation error"


class DuplicateResourceException(CustomException):
    status_code = 409
    error_code = "DUPLICATE_RESOURCE"
    message = "Resource already exists"


class UserAlreadyExistsException(DuplicateResourceException):
    error_code = "USER_ALREADY_EXISTS"
    message = "User with this email or username already exists"


# Quiz Attempt Exceptions
class QuizAccessDeniedException(CustomException):
    status_code = 403
    error_code = "QUIZ_ACCESS_DENIED"
    message = "You don't have access to this quiz"


class QuizExpiredException(CustomException):
    status_code = 400
    error_code = "QUIZ_EXPIRED"
    message = "Quiz attempt has expired"


class AlreadySubmittedException(CustomException):
    status_code = 409
    error_code = "ALREADY_SUBMITTED"
    message = "Quiz attempt has already been submitted"


class ActiveAttemptExistsException(CustomException):
    status_code = 409
    error_code = "ACTIVE_ATTEMPT_EXISTS"
    message = "An active attempt already exists for this quiz"


class MaxAttemptsReachedException(CustomException):
    status_code = 403
    error_code = "MAX_ATTEMPTS_REACHED"
    message = "Maximum number of attempts reached for this quiz"


class QuizNotPublishedException(CustomException):
    status_code = 403
    error_code = "QUIZ_NOT_PUBLISHED"
    message = "Quiz is not published"


# Business Logic Exceptions
class InvalidOperationException(CustomException):
    status_code = 400
    error_code = "INVALID_OPERATION"
    message = "Invalid operation"
