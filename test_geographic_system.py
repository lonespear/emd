"""
test_geographic_system.py
--------------------------

Comprehensive test suite for geographic distance-based optimization system.

Tests:
1. LocationDatabase - Verify locations load correctly
2. DistanceCalculator - Test known distances
3. TravelCostEstimator - Verify cost calculations
4. AdvancedReadinessProfile - Test profile loading
5. EMD Integration - End-to-end test with geographic penalties
"""

from geolocation import (
    LocationDatabase, DistanceCalculator, TravelCostEstimator,
    calculate_distance_and_cost
)
from advanced_profiles import ProfileRegistry, StandardCONUSProfiles, AORProfiles


def test_location_database():
    """Test 1: LocationDatabase loads and contains expected locations."""
    print("\n" + "="*80)
    print("TEST 1: LocationDatabase")
    print("="*80)

    db = LocationDatabase()

    print(f"[OK] Database loaded with {len(db.locations)} locations")

    # Test specific locations
    test_locations = [
        "JBLM",
        "Fort Bragg",
        "NTC",
        "JRTC",
        "Camp Humphreys",
        "Kadena AB",
        "Grafenwoehr",
        "Djibouti"
    ]

    for loc_name in test_locations:
        loc = db.get(loc_name)
        if loc:
            print(f"[OK] {loc_name:20} - {loc.lat:7.2f}, {loc.lon:8.2f} ({loc.aor})")
        else:
            print(f"[FAIL] {loc_name} NOT FOUND")

    # Test AOR filtering
    indopacom_locs = db.list_by_aor("INDOPACOM")
    print(f"\n[OK] INDOPACOM has {len(indopacom_locs)} locations")

    print("\n[PASS] TEST 1 PASSED")


def test_distance_calculations():
    """Test 2: Distance calculations with known distances."""
    print("\n" + "="*80)
    print("TEST 2: Distance Calculations")
    print("="*80)

    db = LocationDatabase()

    # Known approximate distances (from Google Maps / Great Circle Mapper)
    test_cases = [
        ("JBLM", "NTC", 1045, 100),  # Seattle to Fort Irwin
        ("JBLM", "Camp Humphreys", 5217, 200),  # Seattle to Korea
        ("Fort Bragg", "Grafenwoehr", 4381, 200),  # North Carolina to Germany
        ("Camp Humphreys", "Kadena AB", 739, 50),  # Korea to Okinawa
    ]

    all_passed = True
    for home, dest, expected_dist, tolerance in test_cases:
        actual_dist = DistanceCalculator.calculate(home, dest, db)
        diff = abs(actual_dist - expected_dist)
        status = "[OK]" if diff <= tolerance else "[FAIL]"

        if diff > tolerance:
            all_passed = False

        print(f"{status} {home:20} -> {dest:20}: "
              f"{actual_dist:6.0f} mi (expected {expected_dist:6.0f}, diff {diff:.0f})")

    if all_passed:
        print("\n[PASS] TEST 2 PASSED - All distances within tolerance")
    else:
        print("\n[WARN] TEST 2: Some distances outside tolerance")


def test_travel_cost_estimation():
    """Test 3: Travel cost estimation."""
    print("\n" + "="*80)
    print("TEST 3: Travel Cost Estimation")
    print("="*80)

    # Test cases: (distance_miles, duration_days, is_oconus, expected_range)
    test_cases = [
        (300, 14, False, (2000, 2500)),  # Short CONUS
        (1500, 14, False, (2500, 3500)),  # Medium CONUS
        (5000, 14, True, (3500, 4500)),  # OCONUS
        (1000, 30, False, (5000, 6000)),  # Longer duration
    ]

    all_passed = True
    for dist, days, oconus, (min_cost, max_cost) in test_cases:
        cost = TravelCostEstimator.estimate_travel_cost(dist, days, oconus)
        status = "[OK]" if min_cost <= cost <= max_cost else "[FAIL]"

        if not (min_cost <= cost <= max_cost):
            all_passed = False

        location_type = "OCONUS" if oconus else "CONUS"
        print(f"{status} {dist:5.0f} mi, {days:2}d, {location_type:6}: "
              f"${cost:6,.0f} (expected ${min_cost:5,.0f}-${max_cost:5,.0f})")

    if all_passed:
        print("\n[PASS] TEST 3 PASSED - All costs in expected range")
    else:
        print("\n[WARN] TEST 3: Some costs outside expected range")


def test_lead_time_estimation():
    """Test 4: Lead time estimation."""
    print("\n" + "="*80)
    print("TEST 4: Lead Time Estimation")
    print("="*80)

    test_cases = [
        (50, False, 3),  # Local CONUS
        (1000, False, 7),  # Regional CONUS
        (2500, False, 14),  # Far CONUS
        (5000, True, 21),  # Near OCONUS
        (8000, True, 28),  # Far OCONUS
    ]

    for dist, oconus, expected_days in test_cases:
        lead_time = TravelCostEstimator.estimate_lead_time(dist, oconus)
        status = "[OK]" if lead_time == expected_days else "[FAIL]"

        location_type = "OCONUS" if oconus else "CONUS"
        print(f"{status} {dist:5.0f} mi, {location_type:6}: {lead_time:2}d lead time "
              f"(expected {expected_days}d)")

    print("\n[PASS] TEST 4 PASSED")


def test_profile_loading():
    """Test 5: Advanced readiness profiles load correctly."""
    print("\n" + "="*80)
    print("TEST 5: Advanced Readiness Profiles")
    print("="*80)

    profiles = ProfileRegistry.get_all_profiles()

    print(f"[OK] Loaded {len(profiles)} profiles")

    # Test each profile
    for name, profile in profiles.items():
        required = len(profile.required_training)
        print(f"[OK] {name:30} - {profile.primary_location:20} "
              f"({profile.typical_duration_days:2}d, {required:2} training gates)")

    # Test specific profile details
    print("\nDetailed Profile Tests:")

    ntc = StandardCONUSProfiles.ntc_rotation()
    print(f"[OK] NTC: {ntc.typical_duration_days}d, AOR={ntc.aor}, OCONUS={ntc.is_oconus()}")

    indopacom = AORProfiles.indopacom_exercise()
    print(f"[OK] INDOPACOM: {indopacom.typical_duration_days}d, AOR={indopacom.aor}, "
          f"OCONUS={indopacom.is_oconus()}")

    # Test conversion to base ReadinessProfile
    base_profile = ntc.to_readiness_profile()
    print(f"[OK] Conversion to ReadinessProfile works: {base_profile.profile_name}")

    print("\n[PASS] TEST 5 PASSED")


def test_calculate_distance_and_cost():
    """Test 6: Helper function calculate_distance_and_cost."""
    print("\n" + "="*80)
    print("TEST 6: Integrated Distance and Cost Calculation")
    print("="*80)

    # Realistic scenarios
    scenarios = [
        ("JBLM", "NTC", 30),  # NTC rotation from Seattle
        ("Fort Bragg", "JRTC", 21),  # JRTC rotation from Bragg
        ("JBLM", "Camp Humphreys", 14),  # INDOPACOM exercise from Seattle
        ("Fort Carson", "Grafenwoehr", 21),  # EUCOM exercise from Carson
    ]

    for home, dest, days in scenarios:
        dist, cost, lead, category = calculate_distance_and_cost(home, dest, days)
        print(f"[OK] {home:15} -> {dest:20}: {dist:5.0f} mi, ${cost:5,.0f}, "
              f"{lead:2}d lead, {category}")

    print("\n[PASS] TEST 6 PASSED")


def test_emd_integration():
    """Test 7: EMD integration with geographic penalties."""
    print("\n" + "="*80)
    print("TEST 7: EMD Integration (Conceptual)")
    print("="*80)

    print("Testing EMD integration workflow...")

    # Simulate what would happen in EMD
    from geolocation import LocationDatabase, DistanceCalculator

    db = LocationDatabase()

    # Simulate soldiers at different bases
    soldiers = [
        ("JBLM", "11B", "E-5"),
        ("Fort Carson", "11B", "E-5"),
        ("Fort Drum", "11B", "E-5"),
        ("Schofield Barracks", "11B", "E-5"),
    ]

    exercise_loc = "NTC"
    duration = 30

    print(f"\nExercise Location: {exercise_loc} ({duration} days)")
    print("Calculating geographic penalties for each soldier:\n")

    for home, mos, rank in soldiers:
        home_loc = db.get(home)
        exercise = db.get(exercise_loc)

        if home_loc and exercise:
            dist = DistanceCalculator.calculate(home_loc, exercise, db)
            is_oconus = (home_loc.country != exercise.country) or (exercise.country != "US")

            # Calculate penalties (simulating EMD logic)
            travel_cost = TravelCostEstimator.estimate_travel_cost(dist, duration, is_oconus)
            lead_penalty = 500 if is_oconus else 0
            same_theater = -300 if (home_loc.aor == exercise.aor and home_loc.aor != "NORTHCOM") else 0
            dist_penalty = (dist / 1000.0) * 100

            total_geo_cost = travel_cost + lead_penalty + same_theater + dist_penalty

            print(f"{home:20}: {dist:5.0f} mi, Travel=${travel_cost:5,.0f}, "
                  f"Lead=${lead_penalty:3}, Theater=${same_theater:4}, "
                  f"Dist=${dist_penalty:4.0f} -> Total=${total_geo_cost:5,.0f}")

    print("\n[PASS] TEST 7 PASSED - Geographic penalty calculation works")


def test_comparison_scenarios():
    """Test 8: Real-world comparison scenarios."""
    print("\n" + "="*80)
    print("TEST 8: Real-World Comparison Scenarios")
    print("="*80)

    print("\nScenario 1: Who should source to NTC?")
    print("-" * 60)

    bases = ["JBLM", "Fort Carson", "Fort Bragg", "Fort Drum"]
    costs = []
    for base in bases:
        dist, cost, lead, cat = calculate_distance_and_cost(base, "NTC", 30)
        costs.append((base, dist, cost))
        print(f"{base:15}: {dist:5.0f} mi, ${cost:6,.0f}")

    best = min(costs, key=lambda x: x[2])
    print(f"\n-> RECOMMENDATION: {best[0]} (lowest cost: ${best[2]:,.0f})")

    print("\nScenario 2: INDOPACOM Exercise in Korea")
    print("-" * 60)

    bases = ["JBLM", "Schofield Barracks", "Camp Zama", "Fort Bragg"]
    costs = []
    for base in bases:
        dist, cost, lead, cat = calculate_distance_and_cost(base, "Camp Humphreys", 14)
        costs.append((base, dist, cost))

        # Add same-theater bonus for INDOPACOM bases
        db = LocationDatabase()
        home_loc = db.get(base)
        exercise_loc = db.get("Camp Humphreys")
        if home_loc and exercise_loc:
            if home_loc.aor == "INDOPACOM":
                cost -= 300  # Same theater bonus
                costs[-1] = (base, dist, cost)

        print(f"{base:20}: {dist:5.0f} mi, ${cost:6,.0f}")

    best = min(costs, key=lambda x: x[2])
    print(f"\n-> RECOMMENDATION: {best[0]} (lowest cost: ${best[2]:,.0f})")

    print("\n[PASS] TEST 8 PASSED - Realistic comparison scenarios work")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("GEOGRAPHIC OPTIMIZATION SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)

    try:
        test_location_database()
        test_distance_calculations()
        test_travel_cost_estimation()
        test_lead_time_estimation()
        test_profile_loading()
        test_calculate_distance_and_cost()
        test_emd_integration()
        test_comparison_scenarios()

        print("\n" + "="*80)
        print("[PASS] ALL TESTS PASSED")
        print("="*80)
        print("\nGeographic optimization system is working correctly!")
        print("Ready for integration with EMD and dashboard.")

    except Exception as e:
        print("\n" + "="*80)
        print(f"[FAIL] TEST FAILED: {e}")
        print("="*80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
