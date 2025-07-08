"""
Error Handlers and Middleware for Gmail-like API
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from google.auth.exceptions import RefreshError, GoogleAuthError
from googleapiclient.errors import HttpError
from requests.exceptions import RequestException, Timeout, ConnectionError
from pydantic import ValidationError as PydanticValidationError

from exception import (
    AuthorizationError, BaseAPIException, AuthenticationError, TokenExpiredError, 
    InvalidTokenError, UserNotFoundError, EmailNotFoundError,
    DraftNotFoundError, CalendarEventNotFoundError, GmailAPIError,
    GmailQuotaExceededError, DatabaseError, ValidationError,
    RateLimitExceededError, ExternalServiceError, ExternalServiceTimeoutError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format"""
    
    @staticmethod
    def create_error_response(
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a standardized error response"""
        error_response = {
            "success": False,
            "error": {
                "message": message,
                "code": error_code,
                "status_code": status_code,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        if details:
            error_response["error"]["details"] = details
            
        if request_id:
            error_response["error"]["request_id"] = request_id
            
        return error_response


def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app"""
    
    # Custom API Exception Handler
    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(request: Request, exc: BaseAPIException):
        """Handle custom API exceptions"""
        logger.error(f"API Exception: {exc.message} | Path: {request.url.path} | Code: {exc.error_code}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.create_error_response(
                message=exc.message,
                status_code=exc.status_code,
                error_code=exc.error_code,
                details=exc.details,
                request_id=str(id(request))
            )
        )
    
    # FastAPI HTTPException Handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions"""
        logger.error(f"HTTP Exception: {exc.detail} | Status: {exc.status_code} | Path: {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.create_error_response(
                message=str(exc.detail),
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
                request_id=str(id(request))
            )
        )
    
    # Starlette HTTPException Handler
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.error(f"Starlette Exception: {exc.detail} | Status: {exc.status_code} | Path: {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse.create_error_response(
                message=str(exc.detail),
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
                request_id=str(id(request))
            )
        )
    
    # Request Validation Error Handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle FastAPI request validation errors"""
        logger.error(f"Validation Error: {exc.errors()} | Path: {request.url.path}")
        
        # Extract validation error details
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse.create_error_response(
                message="Request validation failed",
                status_code=422,
                error_code="VALIDATION_ERROR",
                details={"validation_errors": error_details},
                request_id=str(id(request))
            )
        )
    
    # Pydantic Validation Error Handler
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
        """Handle Pydantic validation errors"""
        logger.error(f"Pydantic Validation Error: {exc.errors()} | Path: {request.url.path}")
        
        error_details = []
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content=ErrorResponse.create_error_response(
                message="Data validation failed",
                status_code=422,
                error_code="PYDANTIC_VALIDATION_ERROR",
                details={"validation_errors": error_details},
                request_id=str(id(request))
            )
        )
    
    # SQLAlchemy Database Error Handler
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """Handle SQLAlchemy database errors"""
        logger.error(f"Database Error: {str(exc)} | Path: {request.url.path}")
        
        # Handle specific database errors
        if isinstance(exc, IntegrityError):
            return JSONResponse(
                status_code=409,
                content=ErrorResponse.create_error_response(
                    message="Database integrity constraint violation",
                    status_code=409,
                    error_code="INTEGRITY_ERROR",
                    details={"original_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)},
                    request_id=str(id(request))
                )
            )
        elif isinstance(exc, OperationalError):
            return JSONResponse(
                status_code=503,
                content=ErrorResponse.create_error_response(
                    message="Database operational error",
                    status_code=503,
                    error_code="DATABASE_OPERATIONAL_ERROR",
                    details={"original_error": str(exc.orig) if hasattr(exc, 'orig') else str(exc)},
                    request_id=str(id(request))
                )
            )
        else:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse.create_error_response(
                    message="Database error occurred",
                    status_code=500,
                    error_code="DATABASE_ERROR",
                    details={"original_error": str(exc)},
                    request_id=str(id(request))
                )
            )
    
    # Google Auth Error Handler
    @app.exception_handler(GoogleAuthError)
    async def google_auth_exception_handler(request: Request, exc: GoogleAuthError):
        """Handle Google authentication errors"""
        logger.error(f"Google Auth Error: {str(exc)} | Path: {request.url.path}")
        
        if isinstance(exc, RefreshError):
            return JSONResponse(
                status_code=401,
                content=ErrorResponse.create_error_response(
                    message="Google token refresh failed",
                    status_code=401,
                    error_code="TOKEN_REFRESH_ERROR",
                    details={"original_error": str(exc)},
                    request_id=str(id(request))
                )
            )
        else:
            return JSONResponse(
                status_code=401,
                content=ErrorResponse.create_error_response(
                    message="Google authentication failed",
                    status_code=401,
                    error_code="GOOGLE_AUTH_ERROR",
                    details={"original_error": str(exc)},
                    request_id=str(id(request))
                )
            )
    
    # Google API HttpError Handler
    @app.exception_handler(HttpError)
    async def google_api_exception_handler(request: Request, exc: HttpError):
        """Handle Google API HTTP errors"""
        logger.error(f"Google API Error: {str(exc)} | Path: {request.url.path}")
        
        # Parse Google API error details
        error_details = {
            "status_code": exc.resp.status,
            "reason": exc.resp.reason,
            "original_error": str(exc)
        }
        
        # Handle specific Google API errors
        if exc.resp.status == 401:
            return JSONResponse(
                status_code=401,
                content=ErrorResponse.create_error_response(
                    message="Google API authentication failed",
                    status_code=401,
                    error_code="GOOGLE_API_AUTH_ERROR",
                    details=error_details,
                    request_id=str(id(request))
                )
            )
        elif exc.resp.status == 403:
            return JSONResponse(
                status_code=403,
                content=ErrorResponse.create_error_response(
                    message="Google API access forbidden",
                    status_code=403,
                    error_code="GOOGLE_API_FORBIDDEN",
                    details=error_details,
                    request_id=str(id(request))
                )
            )
        elif exc.resp.status == 429:
            return JSONResponse(
                status_code=429,
                content=ErrorResponse.create_error_response(
                    message="Google API quota exceeded",
                    status_code=429,
                    error_code="GOOGLE_API_QUOTA_EXCEEDED",
                    details=error_details,
                    request_id=str(id(request))
                )
            )
        elif exc.resp.status == 404:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse.create_error_response(
                    message="Google API resource not found",
                    status_code=404,
                    error_code="GOOGLE_API_NOT_FOUND",
                    details=error_details,
                    request_id=str(id(request))
                )
            )
        else:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse.create_error_response(
                    message="Google API error occurred",
                    status_code=500,
                    error_code="GOOGLE_API_ERROR",
                    details=error_details,
                    request_id=str(id(request))
                )
            )
    
    # Request Exception Handler (for external API calls)
    @app.exception_handler(RequestException)
    async def request_exception_handler(request: Request, exc: RequestException):
        """Handle requests library exceptions"""
        logger.error(f"Request Exception: {str(exc)} | Path: {request.url.path}")
        
        if isinstance(exc, Timeout):
            return JSONResponse(
                status_code=504,
                content=ErrorResponse.create_error_response(
                    message="External service timeout",
                    status_code=504,
                    error_code="EXTERNAL_SERVICE_TIMEOUT",
                    details={"original_error": str(exc)},
                    request_id=str(id(request))
                )
            )
        elif isinstance(exc, ConnectionError):
            return JSONResponse(
                status_code=503,
                content=ErrorResponse.create_error_response(
                    message="External service connection error",
                    status_code=503,
                    error_code="EXTERNAL_SERVICE_CONNECTION_ERROR",
                    details={"original_error": str(exc)},
                    request_id=str(id(request))
                )
            )
        else:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse.create_error_response(
                    message="External service error",
                    status_code=500,
                    error_code="EXTERNAL_SERVICE_ERROR",
                    details={"original_error": str(exc)},
                    request_id=str(id(request))
                )
            )
    
    # Generic Exception Handler (catch-all)
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions"""
        logger.error(f"Unhandled Exception: {str(exc)} | Path: {request.url.path}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse.create_error_response(
                message="An unexpected error occurred",
                status_code=500,
                error_code="INTERNAL_SERVER_ERROR",
                details={"original_error": str(exc)} if app.debug else None,
                request_id=str(id(request))
            )
        )


# Utility functions for error handling
def handle_database_error(exc: SQLAlchemyError, operation: str = "database operation"):
    """Convert SQLAlchemy errors to custom exceptions"""
    if isinstance(exc, IntegrityError):
        raise DatabaseError(f"Database integrity error during {operation}", details={"original_error": str(exc)})
    elif isinstance(exc, OperationalError):
        raise DatabaseError(f"Database operational error during {operation}", details={"original_error": str(exc)})
    else:
        raise DatabaseError(f"Database error during {operation}", details={"original_error": str(exc)})


def handle_google_api_error(exc: HttpError, operation: str = "Google API operation"):
    """Convert Google API errors to custom exceptions"""
    if exc.resp.status == 401:
        raise InvalidTokenError("Google API authentication failed")
    elif exc.resp.status == 403:
        raise AuthorizationError("Google API access forbidden")
    elif exc.resp.status == 429:
        raise GmailQuotaExceededError("Google API quota exceeded")
    elif exc.resp.status == 404:
        raise GmailAPIError(f"Google API resource not found during {operation}")
    else:
        raise GmailAPIError(f"Google API error during {operation}", details={"status_code": exc.resp.status})


def handle_google_auth_error(exc: GoogleAuthError, operation: str = "Google authentication"):
    """Convert Google Auth errors to custom exceptions"""
    if isinstance(exc, RefreshError):
        raise TokenExpiredError("Google token refresh failed")
    else:
        raise AuthenticationError(f"Google authentication failed during {operation}")


def handle_request_error(exc: RequestException, service_name: str = "external service"):
    """Convert requests errors to custom exceptions"""
    if isinstance(exc, Timeout):
        raise ExternalServiceTimeoutError(service_name)
    elif isinstance(exc, ConnectionError):
        raise ExternalServiceError(service_name, "Connection error")
    else:
        raise ExternalServiceError(service_name, str(exc))