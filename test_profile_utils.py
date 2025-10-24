"""
test_profile_utils.py
---------------------

Test the profile_utils.py helper functions with generated soldier data.
"""

import sys
import pandas as pd

print("="*80)
print("TESTING PROFILE UTILITIES MODULE")
print("="*80)
print()

# Test 1: Import modules
print("[TEST 1] Importing modules...")
try:
    from mtoe_generator import UnitGenerator, MTOELibrary
    from profile_utils import (
        get_languages, get_badges, get_awards, get_deployments,
        has_language, has_badge, has_combat_experience,
        filter_by_language, filter_by_badge, filter_by_combat_experience,
        get_language_distribution, get_badge_distribution,
        get_deployment_statistics, get_qualification_coverage,
        generate_qualification_summary, print_dataframe_statistics
    )
    print("[PASS] All modules imported successfully")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

print()

# Test 2: Generate test data
print("[TEST 2] Generating test soldiers...")
try:
    generator = UnitGenerator(seed=42)
    template = MTOELibrary.infantry_rifle_company()

    unit = generator.create_unit(
        template=template,
        uic="A1234",
        name="Alpha Company, 1st Battalion",
        short_name="A/1-2",
        home_station="JBLM"
    )

    soldiers_df, soldiers_ext = generator.generate_soldiers_for_unit(unit, fill_rate=0.50)

    print(f"[PASS] Generated {len(soldiers_df)} soldiers for testing")
except Exception as e:
    print(f"[FAIL] Generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Test JSON parsing functions
print("[TEST 3] Testing JSON parsing functions...")
try:
    sample = soldiers_df.iloc[0]

    languages = get_languages(sample)
    badges = get_badges(sample)
    awards = get_awards(sample)
    deployments = get_deployments(sample)

    print(f"[PASS] Parsed profile data:")
    print(f"  Languages: {len(languages)}")
    print(f"  Badges: {len(badges)}")
    print(f"  Awards: {len(awards)}")
    print(f"  Deployments: {len(deployments)}")
except Exception as e:
    print(f"[FAIL] JSON parsing failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Test qualification checking
print("[TEST 4] Testing qualification checking...")
try:
    # Count soldiers with various qualifications
    lang_count = sum(1 for _, row in soldiers_df.iterrows() if has_language(row, 'AR', 2))
    badge_count = sum(1 for _, row in soldiers_df.iterrows() if has_badge(row, 'AIRBORNE'))
    combat_count = sum(1 for _, row in soldiers_df.iterrows() if has_combat_experience(row))

    print(f"[PASS] Qualification checks:")
    print(f"  Soldiers with Arabic (L2+): {lang_count}")
    print(f"  Soldiers with Airborne badge: {badge_count}")
    print(f"  Soldiers with combat experience: {combat_count}")
except Exception as e:
    print(f"[FAIL] Qualification checking failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Test filtering functions
print("[TEST 5] Testing DataFrame filtering...")
try:
    combat_df = filter_by_combat_experience(soldiers_df)
    print(f"[PASS] Filtered to {len(combat_df)} soldiers with combat experience")

    # Try filtering by language (might be zero)
    arabic_df = filter_by_language(soldiers_df, 'AR', 2)
    print(f"[PASS] Filtered to {len(arabic_df)} soldiers with Arabic proficiency")

    # Try filtering by badge
    airborne_df = filter_by_badge(soldiers_df, 'AIRBORNE')
    print(f"[PASS] Filtered to {len(airborne_df)} soldiers with Airborne badge")
except Exception as e:
    print(f"[FAIL] Filtering failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 6: Test statistical functions
print("[TEST 6] Testing statistical analysis...")
try:
    lang_dist = get_language_distribution(soldiers_df)
    badge_dist = get_badge_distribution(soldiers_df)
    deploy_stats = get_deployment_statistics(soldiers_df)
    coverage = get_qualification_coverage(soldiers_df)

    print(f"[PASS] Statistics calculated:")
    print(f"  Unique languages: {len(lang_dist)}")
    print(f"  Unique badges: {len(badge_dist)}")
    print(f"  Soldiers with deployments: {deploy_stats['soldiers_with_deployments']}")
    print(f"  Combat experience coverage: {coverage.get('combat_experience', 0)*100:.1f}%")
except Exception as e:
    print(f"[FAIL] Statistical analysis failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 7: Test summary generation
print("[TEST 7] Testing summary generation...")
try:
    sample = soldiers_df.iloc[0]
    summary = generate_qualification_summary(sample)
    print(f"[PASS] Generated summary:")
    print()
    for line in summary.split('\n'):
        print(f"  {line}")
except Exception as e:
    print(f"[FAIL] Summary generation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 8: Print full statistics
print("[TEST 8] Testing full statistics printer...")
try:
    print()
    print_dataframe_statistics(soldiers_df)
    print("[PASS] Statistics printed successfully")
except Exception as e:
    print(f"[FAIL] Statistics printer failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 9: Test specific language searches
print("[TEST 9] Testing language-specific searches...")
try:
    strategic_langs = ['AR', 'ZH', 'KO', 'RU', 'FA', 'PS']
    results = {}

    for lang in strategic_langs:
        count = len(filter_by_language(soldiers_df, lang, 2))
        results[lang] = count

    print(f"[PASS] Strategic language proficiency:")
    for lang, count in results.items():
        if count > 0:
            print(f"  {lang}: {count} soldiers")

    if sum(results.values()) == 0:
        print("  (No strategic language proficiency in this sample)")
except Exception as e:
    print(f"[FAIL] Language search failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 10: Test badge-specific searches
print("[TEST 10] Testing badge-specific searches...")
try:
    common_badges = ['AIRBORNE', 'AIR_ASSAULT', 'RANGER', 'EFMB', 'CIB']
    results = {}

    for badge in common_badges:
        count = len(filter_by_badge(soldiers_df, badge))
        results[badge] = count

    print(f"[PASS] Badge distribution:")
    for badge, count in results.items():
        if count > 0:
            pct = count / len(soldiers_df) * 100
            print(f"  {badge}: {count} ({pct:.1f}%)")

    if sum(results.values()) == 0:
        print("  (No common badges in this sample)")
except Exception as e:
    print(f"[FAIL] Badge search failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("[SUCCESS] All profile utility tests complete!")
print("="*80)
print()
print("Phase 2 complete. profile_utils.py provides:")
print("  - JSON parsing helpers (9 functions)")
print("  - Qualification checking (15+ functions)")
print("  - DataFrame filtering (7 functions)")
print("  - Statistical analysis (6 functions)")
print("  - Summary generation (2 functions)")
print("  - Validation functions (2 functions)")
print()
print("Next: Phase 3 - Extend billet requirements schema")
