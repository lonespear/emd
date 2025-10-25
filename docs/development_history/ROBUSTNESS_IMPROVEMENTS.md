# Geographic Optimization - Robustness Improvements

## Status: IN PROGRESS

### ✅ Completed

1. **error_handling.py** - Created centralized error handling module
   - GeoConfig with all constants and limits
   - Custom exception classes
   - Validation functions for all data types
   - Safe conversion wrappers
   - Error recovery utilities
   - User-friendly error messages

2. **geolocation.py** - Partial enhancement
   - Added error handling imports
   - Added GeoLocation.is_valid() method
   - Enhanced LocationDatabase.get() with fuzzy matching fallback
   - Added LocationDatabase.get_safe() method with defaults
   - Added try-catch blocks to search() and list_by_aor()
   - Added validation in _add() method

### 🔄 In Progress

3. **geolocation.py** - Remaining work
   - Need to enhance Distance Calculator.haversine() with error handling
   - Need to enhance DistanceCalculator.calculate() with validation
   - Need to enhance TravelCostEstimator methods with validation

4. **advanced_profiles.py** - Not started
   - Need to add profile validation
   - Need to add safe defaults
   - Need to add try-catch in ProfileRegistry

5. **emd_agent.py** - Not started
   - Need to enhance apply_geographic_penalties() with comprehensive error handling
   - Need to add detailed logging
   - Need to add counters for success/failure

6. **dashboard.py** - Not started
   - Need to add user-friendly error messages
   - Need to add data validation before operations
   - Need to add fallback visualizations
   - Need to add session state validation

7. **test_error_handling.py** - Not started
   - Need to create comprehensive test suite for edge cases

## Remaining Work

### geolocation.py Enhancements

```python
# In DistanceCalculator.haversine()
@staticmethod
def haversine(lat1: float, lon1: float, lat2: float, lon2: float, unit: str = "miles") -> float:
    """Calculate great-circle distance with error handling."""
    try:
        # Validate inputs
        if ERROR_HANDLING_AVAILABLE:
            for lat, name in [(lat1, "lat1"), (lat2, "lat2")]:
                is_valid, msg = validate_coordinates(lat, 0, name)
                if not is_valid:
                    logger.warning(msg)
                    return GeoConfig.DEFAULT_DISTANCE

        # Convert to radians with safe conversion
        lat1_rad = math.radians(safe_float_conversion(lat1, 0, "lat1"))
        lon1_rad = math.radians(safe_float_conversion(lon1, 0, "lon1"))
        lat2_rad = math.radians(safe_float_conversion(lat2, 0, "lat2"))
        lon2_rad = math.radians(safe_float_conversion(lon2, 0, "lon2"))

        # Haversine formula with error handling
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2

        # Check for domain errors
        if a < 0 or a > 1:
            logger.warning(f"Invalid haversine value a={a}, using default distance")
            return GeoConfig.DEFAULT_DISTANCE

        c = 2 * math.asin(math.sqrt(a))

        # Calculate distance
        if unit == "km":
            distance = c * DistanceCalculator.EARTH_RADIUS_KM
        else:
            distance = c * DistanceCalculator.EARTH_RADIUS_MILES

        # Validate result
        if ERROR_HANDLING_AVAILABLE:
            is_valid, msg = validate_distance(distance)
            if not is_valid:
                logger.warning(f"Invalid calculated distance: {msg}")
                return GeoConfig.DEFAULT_DISTANCE

        return distance

    except (ValueError, TypeError, ZeroDivisionError) as e:
        logger.error(f"Error in haversine calculation: {e}")
        return GeoConfig.DEFAULT_DISTANCE
    except Exception as e:
        logger.error(f"Unexpected error in haversine: {e}")
        return GeoConfig.DEFAULT_DISTANCE
```

```python
# In DistanceCalculator.calculate()
@staticmethod
def calculate(loc1: str | GeoLocation, loc2: str | GeoLocation, db: Optional[LocationDatabase] = None) -> float:
    """Calculate distance with comprehensive error handling."""
    try:
        if db is None:
            db = LocationDatabase()

        # Resolve locations with error handling
        if isinstance(loc1, str):
            geo1 = db.get(loc1)
            if geo1 is None:
                logger.warning(f"Location not found: {loc1}, using default distance")
                return GeoConfig.DEFAULT_DISTANCE
        else:
            geo1 = loc1

        if isinstance(loc2, str):
            geo2 = db.get(loc2)
            if geo2 is None:
                logger.warning(f"Location not found: {loc2}, using default distance")
                return GeoConfig.DEFAULT_DISTANCE
        else:
            geo2 = loc2

        # Validate locations have valid coordinates
        if ERROR_HANDLING_AVAILABLE:
            if not geo1.is_valid() or not geo2.is_valid():
                logger.warning(f"Invalid coordinates for {geo1.name} or {geo2.name}")
                return GeoConfig.DEFAULT_DISTANCE

        return DistanceCalculator.haversine(geo1.lat, geo1.lon, geo2.lat, geo2.lon)

    except Exception as e:
        logger.error(f"Error calculating distance between {loc1} and {loc2}: {e}")
        return GeoConfig.DEFAULT_DISTANCE
```

```python
# In TravelCostEstimator.estimate_travel_cost()
@staticmethod
def estimate_travel_cost(distance_miles: float, duration_days: int, is_oconus: bool = False) -> float:
    """Estimate travel cost with validation."""
    try:
        # Validate inputs
        if ERROR_HANDLING_AVAILABLE:
            is_valid_dist, msg_dist = validate_distance(distance_miles)
            is_valid_dur, msg_dur = validate_duration(duration_days)

            if not is_valid_dist:
                logger.warning(msg_dist)
                distance_miles = GeoConfig.DEFAULT_DISTANCE

            if not is_valid_dur:
                logger.warning(msg_dur)
                duration_days = GeoConfig.DEFAULT_DURATION

        # Safe conversions
        distance_miles = safe_float_conversion(distance_miles, GeoConfig.DEFAULT_DISTANCE, "distance")
        duration_days = safe_int_conversion(duration_days, GeoConfig.DEFAULT_DURATION, "duration")

        # Calculate costs (existing logic with error handling)
        if distance_miles < 500:
            transport_cost = 150 + (distance_miles * 0.67)
        elif distance_miles < 3000:
            transport_cost = 400 + (distance_miles * 0.15)
        else:
            transport_cost = 1200 + (distance_miles * 0.20)

        per_diem_rate = 200 if is_oconus else 150
        per_diem_cost = duration_days * per_diem_rate

        total_cost = transport_cost + per_diem_cost

        # Validate result
        if ERROR_HANDLING_AVAILABLE:
            is_valid_cost, msg_cost = validate_cost(total_cost)
            if not is_valid_cost:
                logger.warning(msg_cost)
                return GeoConfig.DEFAULT_COST

        return total_cost

    except Exception as e:
        logger.error(f"Error estimating travel cost: {e}")
        return GeoConfig.DEFAULT_COST
```

### advanced_profiles.py Enhancements

```python
# Add to AdvancedReadinessProfile class
def validate(self) -> Tuple[bool, list[str]]:
    """
    Validate profile configuration.

    Returns:
        (is_valid, list of error messages)
    """
    errors = []

    try:
        # Validate required_training is a list
        if not isinstance(self.required_training, list):
            errors.append("required_training must be a list")

        # Validate min_dwell_months
        if self.min_dwell_months < 0:
            errors.append(f"min_dwell_months must be >= 0, got {self.min_dwell_months}")

        # Validate typical_duration_days
        if self.typical_duration_days <= 0:
            errors.append(f"typical_duration_days must be > 0, got {self.typical_duration_days}")

        # Validate medical categories
        if not (1 <= self.max_med_cat <= 4):
            errors.append(f"max_med_cat must be 1-4, got {self.max_med_cat}")

        if not (1 <= self.max_dental_cat <= 4):
            errors.append(f"max_dental_cat must be 1-4, got {self.max_dental_cat}")

    except Exception as e:
        errors.append(f"Validation error: {e}")

    return (len(errors) == 0, errors)
```

```python
# Add to ProfileRegistry
@staticmethod
def get_profile_safe(profile_name: str) -> AdvancedReadinessProfile:
    """
    Get profile with fallback to default.

    Args:
        profile_name: Name of profile to retrieve

    Returns:
        Profile or default home station profile
    """
    try:
        profile = ProfileRegistry.get_profile(profile_name)
        if profile is None:
            logger.warning(f"Profile {profile_name} not found, using Home Station Exercise")
            return StandardCONUSProfiles.home_station_exercise()
        return profile
    except Exception as e:
        logger.error(f"Error retrieving profile {profile_name}: {e}")
        return StandardCONUSProfiles.home_station_exercise()
```

### dashboard.py Enhancements

```python
# Add at top of show_geographic_analysis()
def show_geographic_analysis(assignments, exercise_location):
    """Display geographic analysis with comprehensive error handling."""
    try:
        if not GEOGRAPHIC_AVAILABLE:
            st.warning("⚠️ " + ErrorMessages.MAP_NOT_AVAILABLE)
            return

        # Validate inputs
        if assignments is None or len(assignments) == 0:
            st.info("No assignments to analyze. Please run optimization first.")
            return

        if not exercise_location:
            st.warning("Exercise location not specified. Please select a location in Manning Document page.")
            return

        st.markdown("---")
        st.subheader("🌍 Geographic & Travel Analysis")

        # Calculate metrics with error handling
        try:
            geo_metrics = calculate_geographic_metrics(assignments, exercise_location)
        except Exception as e:
            st.error(f"Error calculating geographic metrics: {e}")
            st.info("Showing partial analysis...")
            geo_metrics = None

        if geo_metrics is None:
            st.info("Geographic data not available for this assignment. This may be due to missing location data.")
            return

        # Rest of implementation with try-catch around each section...

    except Exception as e:
        st.error(f"Error in geographic analysis: {e}")
        st.info("Geographic analysis unavailable. Please check error logs.")
        logger.error(f"Geographic analysis error: {e}", exc_info=True)
```

### emd_agent.py Enhancements

```python
# Enhanced apply_geographic_penalties()
def apply_geographic_penalties(self, cost_matrix: np.ndarray) -> np.ndarray:
    """Apply geographic penalties with comprehensive error handling and logging."""
    if self.exercise_location is None:
        logger.info("No exercise location specified, skipping geographic penalties")
        return cost_matrix

    try:
        from geolocation import LocationDatabase, DistanceCalculator, TravelCostEstimator
        from advanced_profiles import AdvancedReadinessProfile
        from error_handling import ErrorContext, handle_calculation_error

        P = self.policies
        db = LocationDatabase()

        # Get exercise location with error handling
        exercise_loc = db.get(self.exercise_location)
        if exercise_loc is None:
            logger.warning(f"Exercise location not found: {self.exercise_location}")
            return cost_matrix

        # Validate exercise location
        if not exercise_loc.is_valid():
            logger.warning(f"Exercise location has invalid coordinates: {exercise_loc}")
            return cost_matrix

        # Determine OCONUS and duration
        is_oconus = self.readiness_profile.is_oconus() if (
            self.readiness_profile and
            isinstance(self.readiness_profile, AdvancedReadinessProfile)
        ) else False

        duration_days = self.readiness_profile.typical_duration_days if (
            self.readiness_profile and
            isinstance(self.readiness_profile, AdvancedReadinessProfile)
        ) else 14

        # Track success/failure
        success_count = 0
        failure_count = 0
        soldiers_missing_base = []

        S = self.soldiers.reset_index(drop=True)

        for i, soldier_row in S.iterrows():
            try:
                # Get soldier's home station
                home_station = soldier_row.get("base", None)

                if not home_station:
                    failure_count += 1
                    soldier_id = soldier_row.get("soldier_id", f"index_{i}")
                    soldiers_missing_base.append(soldier_id)
                    continue

                home_loc = db.get(home_station)

                if home_loc is None:
                    failure_count += 1
                    logger.debug(f"Home station not found: {home_station} for soldier {i}")
                    continue

                # Validate home location
                if not home_loc.is_valid():
                    failure_count += 1
                    logger.debug(f"Invalid home station coordinates: {home_station}")
                    continue

                # Calculate distance with error handling
                distance_miles = DistanceCalculator.calculate(home_loc, exercise_loc, db)

                # Calculate costs with validation
                travel_cost = TravelCostEstimator.estimate_travel_cost(
                    distance_miles,
                    duration_days,
                    is_oconus
                )

                # Apply penalties
                weighted_travel_cost = travel_cost * P["geographic_cost_weight"]
                cost_matrix[i, :] += weighted_travel_cost

                if is_oconus:
                    cost_matrix[i, :] += P["lead_time_penalty_oconus"]

                if home_loc.aor == exercise_loc.aor and home_loc.aor != "NORTHCOM":
                    cost_matrix[i, :] += P["same_theater_bonus"]

                distance_penalty = (distance_miles / 1000.0) * P["distance_penalty_per_1000mi"]
                cost_matrix[i, :] += distance_penalty

                success_count += 1

            except Exception as soldier_error:
                failure_count += 1
                logger.debug(f"Error processing soldier {i}: {soldier_error}")
                continue

        # Log summary
        total_soldiers = len(S)
        logger.info(f"Geographic penalties applied: {success_count}/{total_soldiers} soldiers processed successfully")

        if failure_count > 0:
            logger.warning(f"{failure_count} soldiers failed geographic processing")

        if soldiers_missing_base:
            logger.warning(f"{len(soldiers_missing_base)} soldiers missing base information: {soldiers_missing_base[:5]}")

        return cost_matrix

    except ImportError as e:
        logger.warning(f"Geographic optimization modules not available: {e}")
        return cost_matrix
    except Exception as e:
        logger.error(f"Critical error in geographic penalties: {e}", exc_info=True)
        return cost_matrix  # Return original matrix on critical error
```

## Testing Strategy

### Create test_error_handling.py

```python
"""Test error handling and robustness."""

import pytest
from geolocation import LocationDatabase, DistanceCalculator, TravelCostEstimator
from advanced_profiles import ProfileRegistry
from error_handling import GeoConfig


def test_invalid_coordinates():
    """Test handling of invalid coordinates."""
    # Should not crash
    result = DistanceCalculator.haversine(200, 0, 0, 0)  # Invalid lat
    assert result == GeoConfig.DEFAULT_DISTANCE


def test_missing_location():
    """Test handling of missing location."""
    db = LocationDatabase()
    result = db.get("NonExistentLocation")
    assert result is None  # Should return None, not crash


def test_negative_distance():
    """Test handling of negative distance in cost estimation."""
    # Should use default
    result = TravelCostEstimator.estimate_travel_cost(-100, 14, False)
    assert result > 0  # Should return valid cost


def test_zero_duration():
    """Test handling of zero duration."""
    result = TravelCostEstimator.estimate_travel_cost(1000, 0, False)
    assert result > 0  # Should use default duration


def test_extreme_distance():
    """Test handling of extremely large distance."""
    result = TravelCostEstimator.estimate_travel_cost(100000, 14, False)
    # Should handle gracefully


def test_profile_validation():
    """Test profile validation."""
    profile = ProfileRegistry.get_profile_safe("NonExistent")
    assert profile is not None  # Should return default


def test_empty_assignments():
    """Test handling of empty assignments DataFrame."""
    import pandas as pd
    from dashboard import calculate_geographic_metrics

    empty_df = pd.DataFrame()
    result = calculate_geographic_metrics(empty_df, "JBLM")
    # Should return None or empty metrics, not crash


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Benefits of These Improvements

1. **No Crashes**: System never crashes, always degrades gracefully
2. **Clear Logging**: All errors logged with context
3. **User Friendly**: Helpful error messages guide users
4. **Debuggable**: Easy to trace issues with detailed logs
5. **Production Ready**: Handles real-world data quality issues
6. **Maintainable**: Centralized error handling
7. **Tested**: Comprehensive test coverage for edge cases

## Next Steps

1. Complete geolocation.py enhancements (Distance Calculator, TravelCostEstimator)
2. Complete advanced_profiles.py enhancements
3. Complete emd_agent.py enhancements
4. Complete dashboard.py enhancements
5. Create test_error_handling.py
6. Run all tests
7. Document error handling guide for users

---

**Status**: 30% Complete
**Priority**: High
**Timeline**: 2-3 hours to complete all remaining work
