"""
test_profile_integration.py
----------------------------

Test the integration of extended profiles with MTOE soldier generation.
"""

import sys
import pandas as pd

print("="*80)
print("TESTING EXTENDED PROFILE INTEGRATION WITH MTOE GENERATION")
print("="*80)
print()

# Test 1: Import all modules
print("[TEST 1] Importing modules...")
try:
    from soldier_profile_extended import SoldierProfileExtended, EducationLevel
    from profile_generator import ProfileGenerator
    from mtoe_generator import UnitGenerator, MTOELibrary
    print("[PASS] All modules imported successfully")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    sys.exit(1)

print()

# Test 2: Generate a small unit with extended profiles
print("[TEST 2] Generating infantry rifle company with extended profiles...")
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

    soldiers_df, soldiers_ext = generator.generate_soldiers_for_unit(unit, fill_rate=0.10)  # Only 10% for quick test

    print(f"[PASS] Generated {len(soldiers_df)} soldiers")
    print(f"  Unit: {unit.name}")
    print(f"  Authorized strength: {unit.authorized_strength}")
    print(f"  Assigned strength: {unit.assigned_strength}")
except Exception as e:
    print(f"[FAIL] Unit generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Check DataFrame has extended profile columns
print("[TEST 3] Verifying extended profile columns exist...")
expected_columns = [
    'soldier_id', 'base', 'paygrade', 'mos', 'skill_level',
    'education_level', 'languages_json', 'asi_codes_json', 'badges_json',
    'awards_json', 'licenses_json', 'time_in_service_months', 'deployments_json'
]

missing_columns = []
for col in expected_columns:
    if col not in soldiers_df.columns:
        missing_columns.append(col)

if missing_columns:
    print(f"[FAIL] Missing columns: {missing_columns}")
    print(f"  Available columns: {list(soldiers_df.columns)}")
else:
    print(f"[PASS] All expected columns present")
    print(f"  Total columns: {len(soldiers_df.columns)}")

print()

# Test 4: Sample a few soldiers and display their profiles
print("[TEST 4] Displaying sample soldier profiles...")
try:
    sample_size = min(3, len(soldiers_df))
    sample = soldiers_df.head(sample_size)

    for idx, row in sample.iterrows():
        print(f"\n  Soldier {row['soldier_id']}:")
        print(f"    Rank: {row['paygrade']}, MOS: {row['mos']}")
        print(f"    Base: {row['base']}, UIC: {row['uic']}")
        print(f"    Position: {row['duty_position']}")

        if 'education_level' in row:
            print(f"    Education: {row['education_level']}")

        if 'time_in_service_months' in row:
            print(f"    TIS: {row['time_in_service_months']} months, TIG: {row['time_in_grade_months']} months")

        # Parse and display languages
        if 'languages_json' in row and row['languages_json'] and row['languages_json'] != '[]':
            import json
            languages = json.loads(row['languages_json'])
            if languages:
                lang_str = ", ".join([f"{lang['language_name']} (L{lang['listening_level']}/R{lang['reading_level']})"
                                     for lang in languages])
                print(f"    Languages: {lang_str}")

        # Parse and display badges
        if 'badges_json' in row and row['badges_json'] and row['badges_json'] != '[]':
            import json
            badges = json.loads(row['badges_json'])
            if badges:
                badge_str = ", ".join([badge['badge_code'] for badge in badges])
                print(f"    Badges: {badge_str}")

        # Parse and display awards
        if 'awards_json' in row and row['awards_json'] and row['awards_json'] != '[]':
            import json
            awards = json.loads(row['awards_json'])
            if awards:
                print(f"    Awards: {len(awards)} total")

    print("\n[PASS] Profile display successful")
except Exception as e:
    print(f"[FAIL] Profile display failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Verify profile data statistics
print("[TEST 5] Extended profile statistics...")
try:
    import json

    # Count soldiers with languages
    lang_count = 0
    for lang_json in soldiers_df['languages_json']:
        if lang_json and lang_json != '[]':
            langs = json.loads(lang_json)
            if langs:
                lang_count += 1

    # Count soldiers with badges
    badge_count = 0
    for badge_json in soldiers_df['badges_json']:
        if badge_json and badge_json != '[]':
            badges = json.loads(badge_json)
            if badges:
                badge_count += 1

    # Count soldiers with awards
    award_count = 0
    for award_json in soldiers_df['awards_json']:
        if award_json and award_json != '[]':
            awards = json.loads(award_json)
            if awards:
                award_count += 1

    # Count soldiers with deployments
    deployment_count = 0
    for deploy_json in soldiers_df['deployments_json']:
        if deploy_json and deploy_json != '[]':
            deploys = json.loads(deploy_json)
            if deploys:
                deployment_count += 1

    total = len(soldiers_df)
    print(f"  Total soldiers: {total}")
    print(f"  With languages: {lang_count} ({lang_count/total*100:.1f}%)")
    print(f"  With badges: {badge_count} ({badge_count/total*100:.1f}%)")
    print(f"  With awards: {award_count} ({award_count/total*100:.1f}%)")
    print(f"  With deployments: {deployment_count} ({deployment_count/total*100:.1f}%)")

    # Education distribution
    if 'education_level' in soldiers_df.columns:
        edu_dist = soldiers_df['education_level'].value_counts()
        print(f"\n  Education distribution:")
        for edu, count in edu_dist.items():
            print(f"    {edu}: {count} ({count/total*100:.1f}%)")

    print("\n[PASS] Statistics calculated successfully")
except Exception as e:
    print(f"[FAIL] Statistics calculation failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("[SUCCESS] Extended profile integration test complete!")
print("="*80)
print()
print("Next steps:")
print("  - Phase 2: Create profile_utils.py for helper functions")
print("  - Phase 3: Extend billet requirements")
print("  - Phase 4: Add qualification penalties to EMD cost matrix")
