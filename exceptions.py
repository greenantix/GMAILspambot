"""
Custom Exception Classes for Gmail Intelligent Cleaner

This module defines custom exception classes to provide more specific error
handling and better context for debugging and recovery suggestions.
"""

import logging
from typing import Optional, Dict, Any


class GmailCleanerException(Exception):
    """Base exception class for Gmail Cleaner application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, 
                 recovery_suggestion: Optional[str] = None):
        self.message = message
        self.details = details or {}
        self.recovery_suggestion = recovery_suggestion
        super().__init__(self.message)
    
    def log_error(self, logger: logging.Logger):
        """Log this exception with appropriate details."""
        logger.error(f"{self.__class__.__name__}: {self.message}")
        if self.details:
            logger.error(f"Details: {self.details}")
        if self.recovery_suggestion:
            logger.info(f"Recovery suggestion: {self.recovery_suggestion}")


class GmailAPIError(GmailCleanerException):
    """Exception raised when Gmail API operations fail."""
    
    def __init__(self, message: str, api_error: Optional[Exception] = None, 
                 operation: Optional[str] = None, email_id: Optional[str] = None):
        details = {}
        if api_error:
            details['api_error'] = str(api_error)
        if operation:
            details['operation'] = operation
        if email_id:
            details['email_id'] = email_id
        
        recovery_suggestion = self._get_recovery_suggestion(api_error)
        
        super().__init__(message, details, recovery_suggestion)
        self.api_error = api_error
        self.operation = operation
        self.email_id = email_id
    
    def _get_recovery_suggestion(self, api_error: Optional[Exception]) -> str:
        """Provide specific recovery suggestions based on the API error."""
        if not api_error:
            return "Check Gmail API connectivity and authentication"
        
        error_str = str(api_error).lower()
        
        if "429" in error_str or "quota" in error_str:
            return "Wait and retry with exponential backoff, or reduce batch size"
        elif "403" in error_str or "permission" in error_str:
            return "Check OAuth scopes and re-authenticate if necessary"
        elif "401" in error_str or "unauthorized" in error_str:
            return "Re-authenticate with Gmail API (delete token.json)"
        elif "404" in error_str or "not found" in error_str:
            return "Verify the email/label/filter ID exists"
        elif "network" in error_str or "connection" in error_str:
            return "Check internet connectivity and retry"
        else:
            return "Check Gmail API status and retry the operation"


class EmailProcessingError(GmailCleanerException):
    """Exception raised when email processing fails."""
    
    def __init__(self, message: str, email_id: Optional[str] = None, 
                 email_subject: Optional[str] = None, processing_step: Optional[str] = None):
        details = {}
        if email_id:
            details['email_id'] = email_id
        if email_subject:
            details['email_subject'] = email_subject[:100]  # Truncate long subjects
        if processing_step:
            details['processing_step'] = processing_step
        
        recovery_suggestion = "Skip this email and continue processing, or retry with different parameters"
        
        super().__init__(message, details, recovery_suggestion)
        self.email_id = email_id
        self.email_subject = email_subject
        self.processing_step = processing_step


class LLMConnectionError(GmailCleanerException):
    """Exception raised when LLM service (LM Studio/Gemini) is unavailable."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 endpoint: Optional[str] = None):
        details = {}
        if service_name:
            details['service_name'] = service_name
        if endpoint:
            details['endpoint'] = endpoint
        
        recovery_suggestion = self._get_llm_recovery_suggestion(service_name)
        
        super().__init__(message, details, recovery_suggestion)
        self.service_name = service_name
        self.endpoint = endpoint
    
    def _get_llm_recovery_suggestion(self, service_name: Optional[str]) -> str:
        """Provide specific recovery suggestions for LLM connection issues."""
        if service_name == "LM Studio":
            return "Ensure LM Studio is running on localhost:1234 with a model loaded"
        elif service_name == "Gemini":
            return "Check GEMINI_API_KEY environment variable and API quota"
        else:
            return "Check LLM service configuration and connectivity"


class FilterProcessingError(GmailCleanerException):
    """Exception raised when Gmail filter operations fail."""
    
    def __init__(self, message: str, filter_id: Optional[str] = None, 
                 filter_criteria: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if filter_id:
            details['filter_id'] = filter_id
        if filter_criteria:
            details['filter_criteria'] = filter_criteria
        if operation:
            details['operation'] = operation
        
        recovery_suggestion = "Check filter syntax and Gmail API permissions for filter management"
        
        super().__init__(message, details, recovery_suggestion)
        self.filter_id = filter_id
        self.filter_criteria = filter_criteria
        self.operation = operation


class AuthenticationError(GmailCleanerException):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None):
        details = {}
        if auth_type:
            details['auth_type'] = auth_type
        
        recovery_suggestion = self._get_auth_recovery_suggestion(auth_type)
        
        super().__init__(message, details, recovery_suggestion)
        self.auth_type = auth_type
    
    def _get_auth_recovery_suggestion(self, auth_type: Optional[str]) -> str:
        """Provide specific recovery suggestions for authentication issues."""
        if auth_type == "gmail":
            return "Delete token.json and re-authenticate, check credentials.json file"
        elif auth_type == "gemini":
            return "Verify GEMINI_API_KEY in .env file"
        else:
            return "Check authentication credentials and re-authenticate"


class ConfigurationError(GmailCleanerException):
    """Exception raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_file: Optional[str] = None, 
                 config_key: Optional[str] = None):
        details = {}
        if config_file:
            details['config_file'] = config_file
        if config_key:
            details['config_key'] = config_key
        
        recovery_suggestion = "Check configuration file format and required fields"
        
        super().__init__(message, details, recovery_suggestion)
        self.config_file = config_file
        self.config_key = config_key


class ValidationError(GmailCleanerException):
    """Exception raised when data validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 field_value: Optional[Any] = None, expected_type: Optional[str] = None):
        details = {}
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = str(field_value)[:100]  # Truncate long values
        if expected_type:
            details['expected_type'] = expected_type
        
        recovery_suggestion = "Check input data format and required fields"
        
        super().__init__(message, details, recovery_suggestion)
        self.field_name = field_name
        self.field_value = field_value
        self.expected_type = expected_type


def handle_exception_with_logging(exception: Exception, logger: logging.Logger, 
                                operation: str = "Unknown operation") -> bool:
    """
    Handle any exception with appropriate logging and return whether to continue.
    
    Args:
        exception: The exception that occurred
        logger: Logger instance to use
        operation: Description of the operation that failed
    
    Returns:
        bool: True if operation should continue, False if it should stop
    """
    if isinstance(exception, GmailCleanerException):
        exception.log_error(logger)
        # Most custom exceptions are recoverable
        return True
    else:
        # Log unexpected exceptions with full traceback
        logger.exception(f"Unexpected error during {operation}: {exception}")
        # Unexpected exceptions might be critical
        return False


def wrap_gmail_api_call(func, *args, operation: str = "Gmail API call", 
                       email_id: Optional[str] = None, **kwargs):
    """
    Wrapper function to handle Gmail API calls with proper exception handling.
    
    Args:
        func: The Gmail API function to call
        *args: Positional arguments for the function
        operation: Description of the API operation
        email_id: Optional email ID for context
        **kwargs: Keyword arguments for the function
    
    Returns:
        The result of the API call
    
    Raises:
        GmailAPIError: If the API call fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise GmailAPIError(
            f"Gmail API operation failed: {operation}",
            api_error=e,
            operation=operation,
            email_id=email_id
        ) from e