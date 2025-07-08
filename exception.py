from typing import Optional, Dict, Any

class BaseAPIException(Exception):
    """Base exception class for all API exceptions"""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization Exceptions
class AuthenticationError(BaseAPIException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, "AUTH_ERROR", details)


class TokenExpiredError(BaseAPIException):
    """Raised when OAuth token has expired"""
    def __init__(self, message: str = "Access token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, "TOKEN_EXPIRED", details)


class InvalidTokenError(BaseAPIException):
    """Raised when OAuth token is invalid"""
    def __init__(self, message: str = "Invalid access token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, "INVALID_TOKEN", details)


class AuthorizationError(BaseAPIException):
    """Raised when user lacks required permissions"""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 403, "AUTHORIZATION_ERROR", details)


# User-related Exceptions
class UserNotFoundError(BaseAPIException):
    """Raised when user is not found"""
    def __init__(self, email: str, details: Optional[Dict[str, Any]] = None):
        message = f"User with email '{email}' not found"
        super().__init__(message, 404, "USER_NOT_FOUND", details)


class UserAlreadyExistsError(BaseAPIException):
    """Raised when trying to create a user that already exists"""
    def __init__(self, email: str, details: Optional[Dict[str, Any]] = None):
        message = f"User with email '{email}' already exists"
        super().__init__(message, 409, "USER_ALREADY_EXISTS", details)


# Email-related Exceptions
class EmailNotFoundError(BaseAPIException):
    """Raised when email is not found"""
    def __init__(self, email_id: int, details: Optional[Dict[str, Any]] = None):
        message = f"Email with ID '{email_id}' not found"
        super().__init__(message, 404, "EMAIL_NOT_FOUND", details)


class EmailSendError(BaseAPIException):
    """Raised when email sending fails"""
    def __init__(self, message: str = "Failed to send email", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "EMAIL_SEND_ERROR", details)


class EmailSyncError(BaseAPIException):
    """Raised when email synchronization fails"""
    def __init__(self, message: str = "Failed to sync emails", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "EMAIL_SYNC_ERROR", details)


class InvalidEmailFormatError(BaseAPIException):
    """Raised when email format is invalid"""
    def __init__(self, email: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid email format: '{email}'"
        super().__init__(message, 400, "INVALID_EMAIL_FORMAT", details)


# Draft-related Exceptions
class DraftNotFoundError(BaseAPIException):
    """Raised when draft is not found"""
    def __init__(self, draft_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Draft with ID '{draft_id}' not found"
        super().__init__(message, 404, "DRAFT_NOT_FOUND", details)


class DraftCreateError(BaseAPIException):
    """Raised when draft creation fails"""
    def __init__(self, message: str = "Failed to create draft", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "DRAFT_CREATE_ERROR", details)


class DraftUpdateError(BaseAPIException):
    """Raised when draft update fails"""
    def __init__(self, message: str = "Failed to update draft", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "DRAFT_UPDATE_ERROR", details)


class DraftDeleteError(BaseAPIException):
    """Raised when draft deletion fails"""
    def __init__(self, message: str = "Failed to delete draft", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "DRAFT_DELETE_ERROR", details)


# Calendar-related Exceptions
class CalendarEventNotFoundError(BaseAPIException):
    """Raised when calendar event is not found"""
    def __init__(self, event_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Calendar event with ID '{event_id}' not found"
        super().__init__(message, 404, "CALENDAR_EVENT_NOT_FOUND", details)


class CalendarEventCreateError(BaseAPIException):
    """Raised when calendar event creation fails"""
    def __init__(self, message: str = "Failed to create calendar event", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "CALENDAR_EVENT_CREATE_ERROR", details)


class CalendarEventUpdateError(BaseAPIException):
    """Raised when calendar event update fails"""
    def __init__(self, message: str = "Failed to update calendar event", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "CALENDAR_EVENT_UPDATE_ERROR", details)


class CalendarEventDeleteError(BaseAPIException):
    """Raised when calendar event deletion fails"""
    def __init__(self, message: str = "Failed to delete calendar event", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "CALENDAR_EVENT_DELETE_ERROR", details)


class InvalidDateTimeError(BaseAPIException):
    """Raised when datetime format is invalid"""
    def __init__(self, datetime_str: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid datetime format: '{datetime_str}'"
        super().__init__(message, 400, "INVALID_DATETIME_FORMAT", details)


# Gmail API Exceptions
class GmailAPIError(BaseAPIException):
    """Raised when Gmail API call fails"""
    def __init__(self, message: str = "Gmail API error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "GMAIL_API_ERROR", details)


class GmailQuotaExceededError(BaseAPIException):
    """Raised when Gmail API quota is exceeded"""
    def __init__(self, message: str = "Gmail API quota exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 429, "GMAIL_QUOTA_EXCEEDED", details)


class GmailServiceBuildError(BaseAPIException):
    """Raised when Gmail service building fails"""
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to build {service_name} service"
        super().__init__(message, 500, "GMAIL_SERVICE_BUILD_ERROR", details)


# Database Exceptions
class DatabaseError(BaseAPIException):
    """Raised when database operation fails"""
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "DATABASE_ERROR", details)


class DatabaseConnectionError(BaseAPIException):
    """Raised when database connection fails"""
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "DATABASE_CONNECTION_ERROR", details)


# Validation Exceptions
class ValidationError(BaseAPIException):
    """Raised when input validation fails"""
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)


class MissingRequiredFieldError(BaseAPIException):
    """Raised when required field is missing"""
    def __init__(self, field_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Required field '{field_name}' is missing"
        super().__init__(message, 400, "MISSING_REQUIRED_FIELD", details)


class InvalidFieldValueError(BaseAPIException):
    """Raised when field value is invalid"""
    def __init__(self, field_name: str, value: str, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid value '{value}' for field '{field_name}'"
        super().__init__(message, 400, "INVALID_FIELD_VALUE", details)


# Rate Limiting Exceptions
class RateLimitExceededError(BaseAPIException):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED", details)


# External Service Exceptions
class ExternalServiceError(BaseAPIException):
    """Raised when external service call fails"""
    def __init__(self, service_name: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        message = message or f"External service '{service_name}' error"
        super().__init__(message, 503, "EXTERNAL_SERVICE_ERROR", details)


class ExternalServiceTimeoutError(BaseAPIException):
    """Raised when external service times out"""
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"External service '{service_name}' timeout"
        super().__init__(message, 504, "EXTERNAL_SERVICE_TIMEOUT", details)


# Configuration Exceptions
class ConfigurationError(BaseAPIException):
    """Raised when configuration is invalid"""
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 500, "CONFIGURATION_ERROR", details)


class MissingConfigurationError(BaseAPIException):
    """Raised when required configuration is missing"""
    def __init__(self, config_key: str, details: Optional[Dict[str, Any]] = None):
        message = f"Missing required configuration: '{config_key}'"
        super().__init__(message, 500, "MISSING_CONFIGURATION", details)