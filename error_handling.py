"""
error_handling.py
-----------------

Centralized error handling, validation, and logging utilities for the
EMD geographic optimization system.

Features:
- Input validation for coordinates, distances, costs
- Custom exception classes
- Logging configuration
- Error recovery strategies
- User-friendly error messages
"""

import logging
from typing import Optional, Any, Tuple
from dataclasses import dataclass


# ====================
# CONFIGURATION
# ====================

class GeoConfig:
    """Configuration constants for geographic calculations."""

    # Coordinate validation
    MIN_LATITUDE = -90.0
    MAX_LATITUDE = 90.0
    MIN_LONGITUDE = -180.0
    MAX_LONGITUDE = 180.0

    # Distance limits (miles)
    MIN_DISTANCE = 0.0
    MAX_DISTANCE = 15000.0  # Roughly half earth's circumference
    DEFAULT_DISTANCE = 1000.0  # Fallback if calculation fails

    # Duration limits (days)
    MIN_DURATION = 1
    MAX_DURATION = 365
    DEFAULT_DURATION = 14

    # Cost limits (USD)
    MIN_COST = 0.0
    MAX_COST = 50000.0  # Per soldier
    DEFAULT_COST = 3000.0  # Reasonable default

    # Dwell time limits (months)
    MIN_DWELL_MONTHS = 0
    MAX_DWELL_MONTHS = 60

    # Medical/Dental categories
    MIN_MED_CAT = 1
    MAX_MED_CAT = 4

    # Logging
    LOG_LEVEL = logging.WARNING  # Change to DEBUG for verbose output
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


# ====================
# CUSTOM EXCEPTIONS
# ====================

class GeoOptimizationError(Exception):
    """Base exception for geographic optimization errors."""
    pass


class InvalidCoordinateError(GeoOptimizationError):
    """Raised when coordinates are invalid."""
    pass


class InvalidDistanceError(GeoOptimizationError):
    """Raised when distance is invalid."""
    pass


class LocationNotFoundError(GeoOptimizationError):
    """Raised when a location cannot be found."""
    pass


class CalculationError(GeoOptimizationError):
    """Raised when a calculation fails."""
    pass


class ValidationError(GeoOptimizationError):
    """Raised when validation fails."""
    pass


# ====================
# LOGGING SETUP
# ====================

def setup_logging(name: str = "geo_optimization", level: int = None) -> logging.Logger:
    """
    Setup logging for geographic optimization modules.

    Args:
        name: Logger name
        level: Logging level (defaults to GeoConfig.LOG_LEVEL)

    Returns:
        Configured logger
    """
    if level is None:
        level = GeoConfig.LOG_LEVEL

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(GeoConfig.LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ====================
# VALIDATION FUNCTIONS
# ====================

def validate_coordinates(lat: float, lon: float, location_name: str = "Unknown") -> Tuple[bool, Optional[str]]:
    """
    Validate latitude and longitude coordinates.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        location_name: Name for error messages

    Returns:
        (is_valid, error_message)
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError) as e:
        return False, f"Coordinates for {location_name} must be numeric: {e}"

    if not (GeoConfig.MIN_LATITUDE <= lat <= GeoConfig.MAX_LATITUDE):
        return False, f"Latitude for {location_name} must be between {GeoConfig.MIN_LATITUDE} and {GeoConfig.MAX_LATITUDE}, got {lat}"

    if not (GeoConfig.MIN_LONGITUDE <= lon <= GeoConfig.MAX_LONGITUDE):
        return False, f"Longitude for {location_name} must be between {GeoConfig.MIN_LONGITUDE} and {GeoConfig.MAX_LONGITUDE}, got {lon}"

    return True, None


def validate_distance(distance: float) -> Tuple[bool, Optional[str]]:
    """
    Validate a distance value.

    Args:
        distance: Distance in miles

    Returns:
        (is_valid, error_message)
    """
    try:
        distance = float(distance)
    except (TypeError, ValueError) as e:
        return False, f"Distance must be numeric: {e}"

    if distance < GeoConfig.MIN_DISTANCE:
        return False, f"Distance must be >= {GeoConfig.MIN_DISTANCE}, got {distance}"

    if distance > GeoConfig.MAX_DISTANCE:
        return False, f"Distance exceeds maximum ({GeoConfig.MAX_DISTANCE} miles), got {distance}"

    return True, None


def validate_duration(duration: int) -> Tuple[bool, Optional[str]]:
    """
    Validate a duration value.

    Args:
        duration: Duration in days

    Returns:
        (is_valid, error_message)
    """
    try:
        duration = int(duration)
    except (TypeError, ValueError) as e:
        return False, f"Duration must be an integer: {e}"

    if duration < GeoConfig.MIN_DURATION:
        return False, f"Duration must be >= {GeoConfig.MIN_DURATION}, got {duration}"

    if duration > GeoConfig.MAX_DURATION:
        return False, f"Duration exceeds maximum ({GeoConfig.MAX_DURATION} days), got {duration}"

    return True, None


def validate_cost(cost: float) -> Tuple[bool, Optional[str]]:
    """
    Validate a cost value.

    Args:
        cost: Cost in USD

    Returns:
        (is_valid, error_message)
    """
    try:
        cost = float(cost)
    except (TypeError, ValueError) as e:
        return False, f"Cost must be numeric: {e}"

    if cost < GeoConfig.MIN_COST:
        return False, f"Cost must be >= ${GeoConfig.MIN_COST}, got ${cost}"

    if cost > GeoConfig.MAX_COST:
        return False, f"Cost exceeds maximum (${GeoConfig.MAX_COST}), got ${cost}"

    return True, None


def validate_medical_category(category: int, category_name: str = "medical") -> Tuple[bool, Optional[str]]:
    """
    Validate medical/dental category.

    Args:
        category: Category value (1-4)
        category_name: Name for error messages

    Returns:
        (is_valid, error_message)
    """
    try:
        category = int(category)
    except (TypeError, ValueError) as e:
        return False, f"{category_name} category must be an integer: {e}"

    if not (GeoConfig.MIN_MED_CAT <= category <= GeoConfig.MAX_MED_CAT):
        return False, f"{category_name} category must be between {GeoConfig.MIN_MED_CAT} and {GeoConfig.MAX_MED_CAT}, got {category}"

    return True, None


# ====================
# SAFE WRAPPERS
# ====================

def safe_float_conversion(value: Any, default: float, name: str = "value") -> float:
    """
    Safely convert value to float with fallback.

    Args:
        value: Value to convert
        default: Default if conversion fails
        name: Name for logging

    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (TypeError, ValueError, AttributeError):
        logger = setup_logging()
        logger.warning(f"Could not convert {name} to float: {value}, using default {default}")
        return default


def safe_int_conversion(value: Any, default: int, name: str = "value") -> int:
    """
    Safely convert value to int with fallback.

    Args:
        value: Value to convert
        default: Default if conversion fails
        name: Name for logging

    Returns:
        Int value or default
    """
    try:
        return int(value)
    except (TypeError, ValueError, AttributeError):
        logger = setup_logging()
        logger.warning(f"Could not convert {name} to int: {value}, using default {default}")
        return default


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely perform division with zero-check.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default if division fails

    Returns:
        Result or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError, ZeroDivisionError):
        return default


# ====================
# ERROR RECOVERY
# ====================

@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    location: Optional[str] = None
    soldier_id: Optional[str] = None
    details: Optional[str] = None


def handle_calculation_error(context: ErrorContext, fallback_value: Any, logger: logging.Logger) -> Any:
    """
    Handle a calculation error with logging and fallback.

    Args:
        context: Error context information
        fallback_value: Value to return on error
        logger: Logger instance

    Returns:
        Fallback value
    """
    msg = f"Error in {context.operation}"
    if context.location:
        msg += f" for location {context.location}"
    if context.soldier_id:
        msg += f" for soldier {context.soldier_id}"
    if context.details:
        msg += f": {context.details}"

    logger.warning(msg + f", using fallback value {fallback_value}")
    return fallback_value


# ====================
# USER-FRIENDLY MESSAGES
# ====================

class ErrorMessages:
    """User-friendly error messages for common issues."""

    LOCATION_NOT_FOUND = """
    Location not found in database.

    Possible solutions:
    - Check spelling of location name
    - Try an alternative name (e.g., "Fort Irwin" instead of "NTC")
    - Contact support to add this location to the database
    """

    INVALID_COORDINATES = """
    Invalid geographic coordinates provided.

    Requirements:
    - Latitude must be between -90 and 90 degrees
    - Longitude must be between -180 and 180 degrees
    - Both must be numeric values
    """

    CALCULATION_FAILED = """
    Geographic calculation failed.

    The system will use default values to continue. Check:
    - Location data quality
    - Network connectivity (if using external geocoding)
    - Error logs for details
    """

    NO_ASSIGNMENTS = """
    No valid assignments could be made.

    Possible reasons:
    - All soldiers filtered out by readiness requirements
    - No soldiers meet MOS/rank requirements
    - Policy penalties too high

    Try:
    - Relaxing readiness requirements
    - Adjusting policy penalties
    - Adding more soldiers to the pool
    """

    MAP_NOT_AVAILABLE = """
    Interactive map visualization not available.

    To enable maps, install:
    pip install folium streamlit-folium

    The system will continue with text-based analysis.
    """


# ====================
# VALIDATION HELPERS
# ====================

def validate_dataframe_columns(df, required_columns: list, df_name: str = "DataFrame") -> Tuple[bool, Optional[str]]:
    """
    Validate that a DataFrame has required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        df_name: Name for error messages

    Returns:
        (is_valid, error_message)
    """
    if df is None or len(df) == 0:
        return False, f"{df_name} is empty"

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        return False, f"{df_name} missing required columns: {', '.join(missing_columns)}"

    return True, None


def validate_non_empty(value: Any, name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a value is not None or empty.

    Args:
        value: Value to check
        name: Name for error messages

    Returns:
        (is_valid, error_message)
    """
    if value is None:
        return False, f"{name} is None"

    if hasattr(value, '__len__') and len(value) == 0:
        return False, f"{name} is empty"

    return True, None
