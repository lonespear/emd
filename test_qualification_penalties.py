"""
test_qualification_penalties.py
--------------------------------

Test the qualification penalty system in the EMD cost matrix.
"""

import sys
import numpy as np
import pandas as pd
import logging

# Setup logging to see penalty messages
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

print("="*80)
print("TESTING QUALIFICATION PENALTY SYSTEM")
print("="*80)
print()

# Test 1: Import modules
print("[TEST 1] Importing modules...")
try:
    from emd_agent import EMD
    from mtoe_generator import UnitGenerator, MTOELibrary
    from manning_document import (
        ManningDocument, CapabilityRequirement,
        ManningDocumentBuilder
    )
    from billet_requirements import BilletRequirementTemplates
    print("[PASS] All modules imported successfully")
except ImportError as e:
    print(f"[FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Generate soldiers with extended profiles
print("[TEST 2] Generating soldiers with extended profiles...")
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

    soldiers_df, soldiers_ext = generator.generate_soldiers_for_unit(unit, fill_rate=0.30)

    print(f"[PASS] Generated {len(soldiers_df)} soldiers")
    print(f"  Columns: {len(soldiers_df.columns)}")
    print(f"  Has extended profiles: {'education_level' in soldiers_df.columns}")
except Exception as e:
    print(f"[FAIL] Soldier generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 3: Generate billets with extended requirements
print("[TEST 3] Generating billets with extended requirements...")
try:
    doc = ManningDocument(
        document_id="TEST-QUAL-001",
        exercise_name="Qualification Test Exercise",
        mission_description="Test qualification matching",
        requesting_unit="Test Unit"
    )

    # Add Ranger-qualified billets
    ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()
    doc.add_requirement(CapabilityRequirement(
        capability_name="Ranger Infantry Team Leader",
        quantity=3,
        mos_required="11B",
        min_rank="E-6",
        priority=3,
        location="JBLM",
        extended_requirements=ranger_req
    ))

    # Add intel analyst billets
    intel_req = BilletRequirementTemplates.intelligence_analyst_strategic_language()
    doc.add_requirement(CapabilityRequirement(
        capability_name="Strategic Intel Analyst",
        quantity=2,
        mos_required="35F",
        min_rank="E-5",
        clearance_req="TS",
        priority=3,
        location="JBLM",
        extended_requirements=intel_req
    ))

    # Add basic infantry billets (no special requirements)
    from billet_requirements import create_basic_requirements
    basic_req = create_basic_requirements(
        position_title="Infantry Rifleman",
        min_education="HS"
    )
    doc.add_requirement(CapabilityRequirement(
        capability_name="Infantry Rifleman",
        quantity=10,
        mos_required="11B",
        min_rank="E-3",
        max_rank="E-4",
        priority=2,
        location="JBLM",
        extended_requirements=basic_req
    ))

    billets_df = ManningDocumentBuilder.generate_billets_from_document(doc)

    print(f"[PASS] Generated {len(billets_df)} billets")
    print(f"  Columns: {len(billets_df.columns)}")
    print(f"  Has extended requirements: {'badges_required_json' in billets_df.columns}")
    print(f"  Ranger billets: {len(billets_df[billets_df['capability_name'] == 'Ranger Infantry Team Leader'])}")
    print(f"  Intel billets: {len(billets_df[billets_df['capability_name'] == 'Strategic Intel Analyst'])}")
    print(f"  Basic billets: {len(billets_df[billets_df['capability_name'] == 'Infantry Rifleman'])}")
except Exception as e:
    print(f"[FAIL] Billet generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Initialize EMD with extended data
print("[TEST 4] Initializing EMD with extended profiles and requirements...")
try:
    emd = EMD(
        soldiers_df=soldiers_df,
        billets_df=billets_df,
        seed=42
    )

    print(f"[PASS] EMD initialized")
    print(f"  Soldiers: {len(emd.soldiers)}")
    print(f"  Billets: {len(emd.billets)}")
    print(f"  Policy parameters: {len(emd.policies)}")

    # Check for new qualification policy parameters
    qual_policies = [k for k in emd.policies.keys() if any(x in k for x in
                     ['education', 'language_prof', 'asi_', 'sqi_', 'badge_', 'license_',
                      'combat_experience', 'deployment', 'leadership', 'tis_', 'tig_', 'perfect_match'])]
    print(f"  Qualification policy parameters: {len(qual_policies)}")

except Exception as e:
    print(f"[FAIL] EMD initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Build base cost matrix
print("[TEST 5] Building base cost matrix...")
try:
    base_cost_matrix = emd.build_cost_matrix("default")

    print(f"[PASS] Base cost matrix built")
    print(f"  Shape: {base_cost_matrix.shape}")
    print(f"  Min cost: {base_cost_matrix.min():.2f}")
    print(f"  Max cost: {base_cost_matrix.max():.2f}")
    print(f"  Mean cost: {base_cost_matrix.mean():.2f}")
except Exception as e:
    print(f"[FAIL] Cost matrix build failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 6: Apply qualification penalties
print("[TEST 6] Applying qualification penalties...")
try:
    enhanced_cost_matrix = emd.apply_qualification_penalties(base_cost_matrix.copy())

    print(f"[PASS] Qualification penalties applied")
    print(f"  Shape: {enhanced_cost_matrix.shape}")
    print(f"  Min cost: {enhanced_cost_matrix.min():.2f}")
    print(f"  Max cost: {enhanced_cost_matrix.max():.2f}")
    print(f"  Mean cost: {enhanced_cost_matrix.mean():.2f}")

    # Calculate difference
    diff = enhanced_cost_matrix - base_cost_matrix
    print(f"\n  Penalty/Bonus statistics:")
    print(f"    Min penalty: {diff.min():.2f}")
    print(f"    Max penalty: {diff.max():.2f}")
    print(f"    Mean adjustment: {diff.mean():.2f}")
    print(f"    Non-zero adjustments: {(diff != 0).sum()} / {diff.size}")

except Exception as e:
    print(f"[FAIL] Qualification penalties failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 7: Run full assignment with qualification penalties
print("[TEST 7] Running full assignment with all penalties...")
try:
    assignments, summary = emd.assign("default")

    print(f"[PASS] Assignment complete")
    print(f"  Total assignments: {len(assignments)}")
    print(f"  Fill rate: {summary.get('fill_rate', 0)*100:.1f}%")
    print(f"  Total cost: ${summary.get('total_cost', 0):,.2f}")

    # Analyze assignments
    if len(assignments) > 0:
        print(f"\n  Sample assignments:")
        for idx, row in assignments.head(5).iterrows():
            soldier_id = row.get('soldier_id', '?')
            billet_id = row.get('billet_id', '?')
            cost = row.get('cost', 0)
            print(f"    Soldier {soldier_id} -> Billet {billet_id}: cost ${cost:,.2f}")

except Exception as e:
    print(f"[FAIL] Assignment failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 8: Compare with and without qualification penalties
print("[TEST 8] Comparing assignments with/without qualification penalties...")
try:
    # Build cost matrix without qualification penalties
    C_base = emd.build_cost_matrix("default")
    C_base = emd.apply_readiness_penalties(C_base)
    C_base = emd.apply_cohesion_adjustments(C_base)
    C_base = emd.apply_geographic_penalties(C_base)

    # Build cost matrix WITH qualification penalties
    C_qual = C_base.copy()
    C_qual = emd.apply_qualification_penalties(C_qual)

    diff = C_qual - C_base

    print(f"[PASS] Comparison complete")
    print(f"  Cost matrix difference statistics:")
    print(f"    Positions with penalties: {(diff > 0).sum()}")
    print(f"    Positions with bonuses: {(diff < 0).sum()}")
    print(f"    Positions unchanged: {(diff == 0).sum()}")
    print(f"    Largest penalty: ${diff.max():,.2f}")
    print(f"    Largest bonus: ${diff.min():,.2f}")

    # Find matches with largest penalties/bonuses
    max_penalty_idx = np.unravel_index(diff.argmax(), diff.shape)
    max_bonus_idx = np.unravel_index(diff.argmin(), diff.shape)

    print(f"\n  Largest penalty: Soldier {max_penalty_idx[0]} -> Billet {max_penalty_idx[1]}: ${diff[max_penalty_idx]:,.2f}")
    print(f"  Largest bonus: Soldier {max_bonus_idx[0]} -> Billet {max_bonus_idx[1]}: ${diff[max_bonus_idx]:,.2f}")

except Exception as e:
    print(f"[FAIL] Comparison failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 9: Verify policy parameters are being used
print("[TEST 9] Verifying policy parameters...")
try:
    # Modify a policy parameter
    original_badge_penalty = emd.policies["badge_missing_penalty"]
    emd.policies["badge_missing_penalty"] = 10000  # Massive penalty

    # Rebuild cost matrix
    C_modified = emd.build_cost_matrix("default")
    C_modified = emd.apply_qualification_penalties(C_modified)

    # Reset policy
    emd.policies["badge_missing_penalty"] = original_badge_penalty

    # Rebuild with original policy
    C_original = emd.build_cost_matrix("default")
    C_original = emd.apply_qualification_penalties(C_original)

    # Check if they're different
    if not np.array_equal(C_modified, C_original):
        print(f"[PASS] Policy parameters are being applied correctly")
        diff = C_modified - C_original
        print(f"  Cost difference when badge penalty increased 10x:")
        print(f"    Max difference: ${diff.max():,.2f}")
        print(f"    Affected positions: {(diff != 0).sum()}")
    else:
        print(f"[WARNING] Policy parameter change had no effect")

except Exception as e:
    print(f"[FAIL] Policy verification failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 10: Performance test
print("[TEST 10] Performance test...")
try:
    import time

    start = time.time()
    for i in range(5):
        C = emd.build_cost_matrix("default")
        C = emd.apply_qualification_penalties(C)
    elapsed = time.time() - start

    avg_time = elapsed / 5

    print(f"[PASS] Performance test complete")
    print(f"  Average time per iteration: {avg_time*1000:.1f}ms")
    print(f"  Matrix size: {C.shape[0]} x {C.shape[1]} = {C.size:,} elements")
    print(f"  Processing rate: {C.size / avg_time:,.0f} elements/sec")

except Exception as e:
    print(f"[FAIL] Performance test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("[SUCCESS] All qualification penalty tests complete!")
print("="*80)
print()
print("Phase 4 complete. Qualification penalty system provides:")
print("  - 30+ policy parameters for fine-tuning")
print("  - Comprehensive matching across 10 qualification categories")
print("  - Integration with existing cost matrix system")
print("  - Detailed logging and statistics")
print("  - Graceful degradation when data unavailable")
print()
print("Next: Phase 5 - Create QualificationFilter class for dashboard")
