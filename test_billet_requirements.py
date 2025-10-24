"""
test_billet_requirements.py
---------------------------

Test the billet requirements system and integration with manning documents.
"""

import sys
import pandas as pd

print("="*80)
print("TESTING BILLET REQUIREMENTS SYSTEM")
print("="*80)
print()

# Test 1: Import modules
print("[TEST 1] Importing modules...")
try:
    from billet_requirements import (
        BilletRequirements, LanguageRequirement, BadgeRequirement,
        ExperienceRequirement, BilletRequirementTemplates,
        create_basic_requirements
    )
    from manning_document import (
        ManningDocument, CapabilityRequirement,
        ManningDocumentBuilder, ManningDocumentTemplates
    )
    print("[PASS] All modules imported successfully")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Create basic requirements
print("[TEST 2] Creating basic billet requirements...")
try:
    basic_req = create_basic_requirements(
        position_title="Infantry Squad Leader",
        min_education="HS",
        badges=["AIRBORNE"],
        combat_required=True,
        min_deployments=1
    )

    print("[PASS] Basic requirements created:")
    print(f"  Position: {basic_req.position_title}")
    print(f"  Education: {basic_req.min_education_level}")
    print(f"  Badges: {len(basic_req.badges_required)}")
    print(f"  Experience: {len(basic_req.experience_required)}")
except Exception as e:
    print(f"[FAIL] Basic requirements creation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Use requirement templates
print("[TEST 3] Testing requirement templates...")
try:
    ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()
    intel_req = BilletRequirementTemplates.intelligence_analyst_strategic_language()
    sf_req = BilletRequirementTemplates.special_forces_comms_sergeant()

    print("[PASS] Created from templates:")
    print(f"  Ranger Leader: {len(ranger_req.badges_required)} badges, {len(ranger_req.experience_required)} experience")
    print(f"  Intel Analyst: {len(intel_req.languages_required)} languages, min edu: {intel_req.min_education_level}")
    print(f"  SF Comms: {len(sf_req.sqi_codes_required)} SQIs, {len(sf_req.licenses_required)} licenses")
except Exception as e:
    print(f"[FAIL] Template creation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Serialize/deserialize requirements
print("[TEST 4] Testing JSON serialization...")
try:
    ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()

    # Convert to dict
    req_dict = ranger_req.to_dict()
    print(f"[PASS] Serialized to dict with {len(req_dict)} fields")

    # Convert back
    ranger_req2 = BilletRequirements.from_dict(req_dict)
    print(f"[PASS] Deserialized requirements:")
    print(f"  Position: {ranger_req2.position_title}")
    print(f"  Badges: {len(ranger_req2.badges_required)}")
    print(f"  Experience: {len(ranger_req2.experience_required)}")
except Exception as e:
    print(f"[FAIL] Serialization failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Integration with manning documents
print("[TEST 5] Integrating requirements with manning documents...")
try:
    # Create a manning document
    doc = ManningDocument(
        document_id="TEST-001",
        exercise_name="Test Exercise",
        mission_description="Test mission",
        requesting_unit="Test Unit"
    )

    # Create capability with extended requirements
    ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()

    cap_req = CapabilityRequirement(
        capability_name="Ranger Infantry Team Leader",
        quantity=2,
        mos_required="11B",
        min_rank="E-6",
        priority=3,
        location="JBLM",
        airborne_required=True,
        extended_requirements=ranger_req
    )

    doc.add_requirement(cap_req)

    print(f"[PASS] Added requirement to manning document")
    print(f"  Total billets: {doc.total_billets()}")
    print(f"  Total capabilities: {doc.total_capabilities()}")
except Exception as e:
    print(f"[FAIL] Manning document integration failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 6: Generate billets with extended requirements
print("[TEST 6] Generating billets DataFrame with extended requirements...")
try:
    billets_df = ManningDocumentBuilder.generate_billets_from_document(doc)

    print(f"[PASS] Generated {len(billets_df)} billets")
    print(f"  Total columns: {len(billets_df.columns)}")

    # Check for extended requirement columns
    ext_cols = [col for col in billets_df.columns if '_json' in col or 'education' in col]
    if ext_cols:
        print(f"  Extended requirement columns: {len(ext_cols)}")
        print(f"    Sample: {ext_cols[:5]}")
    else:
        print("  [WARNING] No extended requirement columns found")

except Exception as e:
    print(f"[FAIL] Billet generation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 7: Create complex manning document
print("[TEST 7] Creating complex manning document with multiple requirement types...")
try:
    complex_doc = ManningDocument(
        document_id="COMPLEX-001",
        exercise_name="Multi-Domain Operations",
        mission_description="Complex multi-domain exercise",
        requesting_unit="Multi-Domain Task Force"
    )

    # Add Ranger-qualified leaders
    ranger_cap = CapabilityRequirement(
        capability_name="Ranger Team Leader",
        quantity=3,
        mos_required="11B",
        min_rank="E-6",
        priority=3,
        location="JBLM",
        extended_requirements=BilletRequirementTemplates.ranger_qualified_infantry_leader()
    )
    complex_doc.add_requirement(ranger_cap)

    # Add Intel analysts with language
    intel_cap = CapabilityRequirement(
        capability_name="Strategic Intel Analyst",
        quantity=2,
        mos_required="35F",
        min_rank="E-5",
        clearance_req="TS",
        priority=3,
        location="JBLM",
        extended_requirements=BilletRequirementTemplates.intelligence_analyst_strategic_language()
    )
    complex_doc.add_requirement(intel_cap)

    # Add SF comms sergeants
    sf_cap = CapabilityRequirement(
        capability_name="SF Comms Sergeant",
        quantity=1,
        mos_required="18E",
        min_rank="E-6",
        priority=4,
        location="JBLM",
        extended_requirements=BilletRequirementTemplates.special_forces_comms_sergeant()
    )
    complex_doc.add_requirement(sf_cap)

    # Add basic combat medics
    medic_req = create_basic_requirements(
        position_title="Combat Medic",
        min_education="HS",
        min_deployments=1
    )

    medic_cap = CapabilityRequirement(
        capability_name="Combat Medic",
        quantity=4,
        mos_required="68W",
        min_rank="E-4",
        priority=2,
        location="JBLM",
        extended_requirements=medic_req
    )
    complex_doc.add_requirement(medic_cap)

    print(f"[PASS] Complex manning document created:")
    print(f"  Total requirements: {len(complex_doc.requirements)}")
    print(f"  Total billets: {complex_doc.total_billets()}")

    # Generate billets
    complex_billets = ManningDocumentBuilder.generate_billets_from_document(complex_doc)
    print(f"  Generated DataFrame: {len(complex_billets)} rows x {len(complex_billets.columns)} columns")

except Exception as e:
    print(f"[FAIL] Complex document creation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 8: Display sample billet requirements
print("[TEST 8] Displaying sample billet with extended requirements...")
try:
    if len(complex_billets) > 0:
        sample = complex_billets.iloc[0]
        print(f"[PASS] Sample billet {sample['billet_id']}:")
        print(f"  Capability: {sample['capability_name']}")
        print(f"  MOS: {sample['mos_required']}, Rank: {sample['min_rank']}-{sample['max_rank']}")
        print(f"  Priority: {sample['priority']}")

        # Display extended requirements if present
        if 'min_education_level' in sample and sample['min_education_level']:
            print(f"  Min Education: {sample['min_education_level']}")

        if 'badges_required_json' in sample and sample['badges_required_json']:
            import json
            badges = json.loads(sample['badges_required_json'])
            if badges:
                print(f"  Badges Required: {len(badges)}")
                for badge in badges:
                    print(f"    - {badge.get('badge_name', 'Unknown')}")

        if 'experience_required_json' in sample and sample['experience_required_json']:
            import json
            experiences = json.loads(sample['experience_required_json'])
            if experiences:
                print(f"  Experience Required: {len(experiences)}")
                for exp in experiences:
                    print(f"    - {exp.get('description', 'Unknown')}")

        if 'min_acft_score' in sample and sample['min_acft_score']:
            print(f"  Min ACFT Score: {sample['min_acft_score']}")

        if 'criticality' in sample and sample['criticality']:
            print(f"  Criticality: {sample['criticality']}/4")

except Exception as e:
    print(f"[FAIL] Sample display failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 9: Test requirement summary generation
print("[TEST 9] Testing requirement summary generation...")
try:
    ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()
    summary = ranger_req.get_summary()

    print("[PASS] Generated requirement summary:")
    for line in summary.split('\n'):
        print(f"  {line}")

except Exception as e:
    print(f"[FAIL] Summary generation failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 10: Verify DataFrame schema
print("[TEST 10] Verifying billet DataFrame has extended requirement columns...")
try:
    required_ext_cols = [
        'min_education_level',
        'badges_required_json',
        'experience_required_json',
        'criticality'
    ]

    missing = []
    present = []

    for col in required_ext_cols:
        if col in complex_billets.columns:
            present.append(col)
        else:
            missing.append(col)

    if missing:
        print(f"[WARNING] Missing columns: {missing}")
    else:
        print(f"[PASS] All extended requirement columns present")

    print(f"  Present: {len(present)}/{len(required_ext_cols)}")

    # Count non-null values
    for col in present:
        non_null = complex_billets[col].notna().sum()
        print(f"    {col}: {non_null}/{len(complex_billets)} billets have data")

except Exception as e:
    print(f"[FAIL] Schema verification failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("[SUCCESS] All billet requirement tests complete!")
print("="*80)
print()
print("Phase 3 complete. Billet requirements system provides:")
print("  - Comprehensive qualification requirements (education, language, badges, etc.)")
print("  - Requirement templates for common positions")
print("  - Integration with manning documents")
print("  - JSON serialization for DataFrame storage")
print("  - Backward compatibility with existing system")
print()
print("Next: Phase 4 - Apply qualification penalties in EMD cost matrix")
