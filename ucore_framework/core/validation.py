"""
Validation utilities for UCore Framework.

This module provides:
- Pydantic models for configuration and web input validation
- Query sanitization helpers for MongoDB
- Example request models for API endpoints

Classes:
    ConfigModel: Pydantic model for application configuration.
    QueryValidator: MongoDB query sanitizer.
    CreateUserRequest: Example web input validation model.
"""

from pydantic import BaseModel, validator, AnyUrl
from typing import Dict, Any, Optional

try:
    from pydantic import EmailStr
except ImportError:
    # Fallback to str if email-validator is not installed
    EmailStr = str

# --- Configuration Validation ---

class ConfigModel(BaseModel):
    """
    Pydantic model for application configuration validation.

    Attributes:
        database_url: Database connection URL (optional).
        redis_url: Redis connection URL (optional).
        secret_key: Application secret key (optional, but must be strong if provided).
        app_name: Application name (optional).
        version: Application version (optional).
    """
    database_url: Optional[AnyUrl] = None
    redis_url: Optional[AnyUrl] = None
    secret_key: Optional[str] = None
    app_name: Optional[str] = None
    version: Optional[str] = None
    
    # Allow any additional fields for flexibility
    class Config:
        extra = "allow"

    @validator('secret_key')
    def secret_key_must_be_strong(cls, v):
        if v is not None and len(v) < 32:
            raise ValueError('secret_key must be at least 32 characters long')
        return v

# --- MongoDB Query Sanitization ---

ALLOWED_OPERATORS = {'$in', '$nin', '$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$exists', '$regex'}

class QueryValidator:
    """
    MongoDB query sanitizer for UCore.

    Provides static methods to recursively sanitize MongoDB queries
    by removing disallowed operators for security.
    """
    @staticmethod
    def sanitize_mongo_query(query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitizes a MongoDB query by removing disallowed operators.

        Args:
            query: The MongoDB query dictionary.

        Returns:
            Sanitized query dictionary with only allowed operators.
        """
        sanitized_query = {}
        for key, value in query.items():
            if key.startswith('$') and key not in ALLOWED_OPERATORS:
                # Optionally log this attempt for security monitoring
                continue
            if isinstance(value, dict):
                sanitized_query[key] = QueryValidator.sanitize_mongo_query(value)
            else:
                sanitized_query[key] = value
        return sanitized_query

# --- Example Web Input Validation Model ---

def get_create_user_request_model():
    """
    Factory function for CreateUserRequest model.
    This avoids the email-validator import issue at module level.
    """
    class CreateUserRequest(BaseModel):
        """
        Example Pydantic model for validating user creation requests.

        Attributes:
            username: Username string.
            email: Email address (validated).
            password: User password.
        """
        username: str
        email: EmailStr
        password: str
    
    return CreateUserRequest

# For backward compatibility, create the class conditionally
try:
    CreateUserRequest = get_create_user_request_model()
except ImportError:
    # If email-validator is not available, create a simplified version
    class CreateUserRequest(BaseModel):
        username: str
        email: str  # Fallback to basic string validation
        password: str
