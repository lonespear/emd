"""
test_error_handling.py
----------------------

Comprehensive test suite for error handling and robustness in the
EMD geographic optimization system.

Tests edge cases, invalid inputs, and error recovery mechanisms.
"""

import pytest
import pandas as pd
import numpy as np
from geolocation import LocationDatabase, DistanceCalculator, TravelCostEstimator, GeoLocation
from advanced_profiles import ProfileRegistry, AdvancedReadinessProfile, get_recommended_profile
from error_handling import GeoConfig, validate_coordinates, validate_distance, validate_duration, validate_cost


def test_invalid_coordinates():
    """Test handling of invalid coordinates."""
    print("\n[TEST] Invalid coordinates handling...")

    # Test 1: Latitude too high
    result = DistanceCalculator.haversine(200, 0, 0, 0)
    assert result == GeoConfig.DEFAULT_DISTANCE, f"Expected {GeoConfig.DEFAULT_DISTANCE}, got {result}"
    print("  [OK] Invalid latitude handled correctly")

    # Test 2: Longitude too low
    result = DistanceCalculator.haversine(0, -200, 0, 0)
    assert result == GeoConfig.DEFAULT_DISTANCE
    print("  [OK] Invalid longitude handled correctly")

    # Test 3: Non-numeric coordinates
    result = DistanceCalculator.haversine("bad", 0, 0, 0)
    assert result == GeoConfig.DEFAULT_DISTANCE
    print("  [OK] Non-numeric coordinates handled correctly")

    print("[PASS] Invalid coordinates test complete\n")


def test_missing_location():
    """Test handling of missing location."""
    print("\n[TEST] Missing location handling...")

    db = LocationDatabase()

    # Test exact match fails gracefully
    result = db.get("NonExistentLocation")
    assert result is None, "Missing location should return None"
    print("  [OK] Missing location returns None")

    # Test get_safe returns default
    jblm = db.get("JBLM")  # Get a valid location to use as default
    result_safe = db.get_safe("NonExistentLocation", default_location=jblm)
    assert result_safe is not None, "get_safe should return default"
    assert result_safe == jblm, "Should return the default location"
    print(f"  [OK] get_safe returns fallback: {result_safe.name}")

    print("[PASS] Missing location test complete\n")


def test_negative_distance():
    """Test handling of negative distance in cost estimation."""
    print("\n[TEST] Negative distance handling...")

    # Should use default distance internally
    result = TravelCostEstimator.estimate_travel_cost(-100, 14, False)
    assert result > 0, "Should return positive cost even with negative distance"
    assert result == TravelCostEstimator.estimate_travel_cost(GeoConfig.DEFAULT_DISTANCE, 14, False)
    print(f"  [OK] Negative distance handled: ${result:,.0f}")

    print("[PASS] Negative distance test complete\n")


def test_zero_duration():
    """Test handling of zero duration."""
    print("\n[TEST] Zero duration handling...")

    result = TravelCostEstimator.estimate_travel_cost(1000, 0, False)
    assert result > 0, "Should return valid cost even with zero duration"
    # Should use default duration
    expected = TravelCostEstimator.estimate_travel_cost(1000, GeoConfig.DEFAULT_DURATION, False)
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  [OK] Zero duration handled: ${result:,.0f}")

    print("[PASS] Zero duration test complete\n")


def test_extreme_distance():
    """Test handling of extremely large distance."""
    print("\n[TEST] Extreme distance handling...")

    # Test with distance larger than max allowed
    extreme_distance = GeoConfig.MAX_DISTANCE + 1000
    result = TravelCostEstimator.estimate_travel_cost(extreme_distance, 14, False)
    # Should use default distance
    expected = TravelCostEstimator.estimate_travel_cost(GeoConfig.DEFAULT_DISTANCE, 14, False)
    assert result == expected, f"Extreme distance should be capped to default"
    print(f"  [OK] Extreme distance handled: {extreme_distance:,.0f} mi -> ${result:,.0f}")

    print("[PASS] Extreme distance test complete\n")


def test_profile_validation():
    """Test profile validation."""
    print("\n[TEST] Profile validation...")

    # Test 1: Get valid profile
    profile = ProfileRegistry.get_profile_safe("NTC Rotation")
    assert profile is not None
    is_valid, errors = profile.validate()
    assert is_valid, f"Valid profile failed validation: {errors}"
    print(f"  [OK] Valid profile passes validation: {profile.profile_name}")

    # Test 2: Get missing profile (should return default)
    fallback = ProfileRegistry.get_profile_safe("NonExistentProfile")
    assert fallback is not None
    assert fallback.profile_name == "Home_Station_Exercise"
    print(f"  [OK] Missing profile returns fallback: {fallback.profile_name}")

    # Test 3: Create invalid profile and validate
    invalid_profile = AdvancedReadinessProfile(
        profile_name="",  # Empty name
        required_training=[],
        min_dwell_months=-5,  # Invalid negative
        typical_duration_days=0,  # Invalid zero
        max_med_cat=10,  # Invalid (should be 1-4)
        max_dental_cat=0  # Invalid (should be 1-4)
    )
    is_valid, errors = invalid_profile.validate()
    assert not is_valid, "Invalid profile should fail validation"
    assert len(errors) > 0, "Should have error messages"
    print(f"  [OK] Invalid profile detected: {len(errors)} errors found")

    print("[PASS] Profile validation test complete\n")


def test_empty_assignments():
    """Test handling of empty assignments DataFrame."""
    print("\n[TEST] Empty assignments handling...")

    # Create empty DataFrame
    empty_df = pd.DataFrame()

    # Test calculate_geographic_metrics with empty DF
    try:
        from dashboard import calculate_geographic_metrics
        result = calculate_geographic_metrics(empty_df, "JBLM")
        assert result is None, "Empty assignments should return None"
        print("  [OK] Empty assignments handled gracefully")
    except Exception as e:
        print(f"  [X] Error with empty assignments: {e}")
        raise

    print("[PASS] Empty assignments test complete\n")


def test_coordinate_validation():
    """Test coordinate validation function."""
    print("\n[TEST] Coordinate validation...")

    # Valid coordinates
    is_valid, msg = validate_coordinates(47.6, -122.3, "Test Location")
    assert is_valid, f"Valid coordinates rejected: {msg}"
    print("  [OK] Valid coordinates accepted")

    # Invalid latitude
    is_valid, msg = validate_coordinates(100, -122.3, "Test Location")
    assert not is_valid, "Invalid latitude should be rejected"
    print(f"  [OK] Invalid latitude rejected: {msg}")

    # Invalid longitude
    is_valid, msg = validate_coordinates(47.6, -200, "Test Location")
    assert not is_valid, "Invalid longitude should be rejected"
    print(f"  [OK] Invalid longitude rejected: {msg}")

    print("[PASS] Coordinate validation test complete\n")


def test_distance_validation():
    """Test distance validation function."""
    print("\n[TEST] Distance validation...")

    # Valid distance
    is_valid, msg = validate_distance(1000.0)
    assert is_valid, f"Valid distance rejected: {msg}"
    print("  [OK] Valid distance accepted")

    # Negative distance
    is_valid, msg = validate_distance(-100)
    assert not is_valid, "Negative distance should be rejected"
    print(f"  [OK] Negative distance rejected: {msg}")

    # Extreme distance
    is_valid, msg = validate_distance(20000)
    assert not is_valid, "Extreme distance should be rejected"
    print(f"  [OK] Extreme distance rejected: {msg}")

    print("[PASS] Distance validation test complete\n")


def test_location_is_valid():
    """Test GeoLocation.is_valid() method."""
    print("\n[TEST] GeoLocation.is_valid()...")

    # Valid location
    valid_loc = GeoLocation(
        name="Test Base",
        lat=47.6,
        lon=-122.3,
        country="USA",
        aor="NORTHCOM",
        installation_type="Base"
    )
    assert valid_loc.is_valid(), "Valid location should pass is_valid()"
    print("  [OK] Valid location passes is_valid()")

    # Invalid location
    invalid_loc = GeoLocation(
        name="Bad Location",
        lat=200,  # Invalid
        lon=-122.3,
        country="USA",
        aor="NORTHCOM",
        installation_type="Base"
    )
    assert not invalid_loc.is_valid(), "Invalid location should fail is_valid()"
    print("  [OK] Invalid location fails is_valid()")

    print("[PASS] GeoLocation.is_valid() test complete\n")


def test_fuzzy_location_matching():
    """Test fuzzy location name matching."""
    print("\n[TEST] Fuzzy location matching...")

    db = LocationDatabase()

    # Test partial match
    result = db.get("Fort Lewis")  # Should match "JBLM" or similar
    if result:
        print(f"  [OK] Fuzzy match found: 'Fort Lewis' -> {result.name}")
    else:
        print("  [INFO] No fuzzy match for 'Fort Lewis'")

    # Test search function
    results = db.search("Lewis")
    assert len(results) > 0, "Search should find JBLM"
    print(f"  [OK] Search found {len(results)} results for 'Lewis'")

    print("[PASS] Fuzzy matching test complete\n")


def test_recommended_profile_errors():
    """Test get_recommended_profile with invalid inputs."""
    print("\n[TEST] Recommended profile error handling...")

    # Test with None location
    profile = get_recommended_profile(None, 14)
    assert profile is not None, "Should return fallback for None location"
    assert profile.profile_name == "TDY_Exercise", f"Expected TDY_Exercise, got {profile.profile_name}"
    print(f"  [OK] None location handled: {profile.profile_name}")

    # Test with empty string
    profile = get_recommended_profile("", 14)
    assert profile is not None
    print(f"  [OK] Empty string handled: {profile.profile_name}")

    # Test with invalid duration
    profile = get_recommended_profile("Korea", "bad_duration")
    assert profile is not None, "Should handle invalid duration"
    print(f"  [OK] Invalid duration handled: {profile.profile_name}")

    print("[PASS] Recommended profile error handling complete\n")


def run_all_tests():
    """Run all error handling tests."""
    print("\n" + "="*80)
    print("ERROR HANDLING AND ROBUSTNESS TEST SUITE")
    print("="*80)

    try:
        test_invalid_coordinates()
        test_missing_location()
        test_negative_distance()
        test_zero_duration()
        test_extreme_distance()
        test_profile_validation()
        test_coordinate_validation()
        test_distance_validation()
        test_location_is_valid()
        test_fuzzy_location_matching()
        test_recommended_profile_errors()

        # Try dashboard test if available
        try:
            test_empty_assignments()
        except ImportError:
            print("[SKIP] Dashboard tests skipped (streamlit not in test environment)\n")

        print("="*80)
        print("[SUCCESS] ALL ERROR HANDLING TESTS PASSED")
        print("="*80)
        return True

    except Exception as e:
        print("\n" + "="*80)
        print(f"[FAIL] TEST FAILED: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
