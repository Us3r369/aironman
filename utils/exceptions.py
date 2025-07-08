"""
Custom exception classes for AIronman app.
Provides domain-specific exceptions for better error handling and categorization.
"""

from typing import Optional, Dict, Any


class AIronmanException(Exception):
    """Base exception class for AIronman application."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class DatabaseException(AIronmanException):
    """Exception raised for database-related errors."""
    pass


class DatabaseConnectionException(DatabaseException):
    """Exception raised when database connection fails."""
    pass


class DatabaseQueryException(DatabaseException):
    """Exception raised when database query fails."""
    pass


class GarminException(AIronmanException):
    """Exception raised for Garmin API-related errors."""
    pass


class GarminAuthenticationException(GarminException):
    """Exception raised when Garmin authentication fails."""
    pass


class GarminConnectionException(GarminException):
    """Exception raised when Garmin connection fails."""
    pass


class GarminDataException(GarminException):
    """Exception raised when Garmin data processing fails."""
    pass


class FileProcessingException(AIronmanException):
    """Exception raised for file processing errors."""
    pass


class FileNotFoundException(FileProcessingException):
    """Exception raised when a required file is not found."""
    pass


class FileParseException(FileProcessingException):
    """Exception raised when file parsing fails."""
    pass


class ValidationException(AIronmanException):
    """Exception raised for data validation errors."""
    pass


class ConfigurationException(AIronmanException):
    """Exception raised for configuration errors."""
    pass


class SyncException(AIronmanException):
    """Exception raised for data synchronization errors."""
    pass


class ProfileException(AIronmanException):
    """Exception raised for profile-related errors."""
    pass


class ProfileNotFoundException(ProfileException):
    """Exception raised when a profile is not found."""
    pass


class ProfileValidationException(ProfileException):
    """Exception raised when profile validation fails."""
    pass


class WorkoutException(AIronmanException):
    """Exception raised for workout-related errors."""
    pass


class WorkoutProcessingException(WorkoutException):
    """Exception raised when workout processing fails."""
    pass


class HealthMetricException(AIronmanException):
    """Exception raised for health metric-related errors."""
    pass


class HealthMetricProcessingException(HealthMetricException):
    """Exception raised when health metric processing fails."""
    pass 