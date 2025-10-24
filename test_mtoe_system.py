"""
test_mtoe_system.py
-------------------

Comprehensive test and demonstration of the enhanced MTOE-based manning system.

This demonstrates the full workflow:
1. Generate units from MTOE templates
2. Create manning document with capability requirements
3. Apply readiness filters
4. Run optimization with unit cohesion preferences
5. Analyze results

Run this to validate the entire system works end-to-end.
"""

import sys
import pandas as pd
import numpy as np
from datetime import date, timedelta

# Import all new components
from mtoe_generator import quick_generate_force, UnitGenerator, MTOELibrary
from manning_document import (
    ManningDocumentTemplates,
    ManningDocumentBuilder,
    create_custom_manning_document
)
from readiness_tracker import (
    StandardProfiles,
    ReadinessAnalyzer,
    filter_ready_soldiers
)
from task_organizer import TaskOrganizer
from emd_agent import EMD
from unit_types import Unit


def test_1_basic_mtoe_generation():
    """Test 1: Generate units from MTOE templates."""
    print("\n" + "="*80)
    print("TEST 1: MTOE Unit Generation")
    print("="*80)

    generator, soldiers_df, soldiers_ext = quick_generate_force(
        n_battalions=2,
        companies_per_bn=3,
        seed=42,
        fill_rate=0.92
    )

    print(f"\n✓ Generated {len(generator.units)} companies")
    print(f"✓ Total soldiers: {len(soldiers_df):,}")
    print(f"✓ Extended records: {len(soldiers_ext):,}")

    # Show unit breakdown
    print("\nUnit Breakdown:")
    for uic, unit in generator.units.items():
        print(f"  {unit.short_name:20s} | {unit.unit_type:20s} | "
              f"{unit.assigned_strength:3d}/{unit.authorized_strength:3d} "
              f"({unit.get_fill_rate():.1%})")

    # Show sample soldiers
    print("\nSample Soldiers:")
    print(soldiers_df[["soldier_id", "uic", "duty_position", "paygrade", "mos"]].head(10))

    return generator, soldiers_df, soldiers_ext


def test_2_manning_document_creation():
    """Test 2: Create manning documents from templates."""
    print("\n" + "="*80)
    print("TEST 2: Manning Document Creation")
    print("="*80)

    # Use pre-built template
    manning_doc = ManningDocumentTemplates.infantry_task_force(location="Guam")

    print(f"\n✓ Created manning document: {manning_doc.exercise_name}")
    print(f"✓ Total capabilities: {manning_doc.total_capabilities()}")
    print(f"✓ Total billets (individuals): {manning_doc.total_billets()}")

    # Show requirements
    print("\nCapability Requirements:")
    for req in manning_doc.requirements:
        print(f"  {req.quantity}x {req.capability_name:30s} | "
              f"MOS:{req.mos_required} | Rank:{req.min_rank} | "
              f"Team:{req.team_size} | Priority:{req.priority}")

    # Convert to billets
    billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
    print(f"\n✓ Generated {len(billets_df)} billets from manning document")

    # Show sample billets
    print("\nSample Billets:")
    print(billets_df[["billet_id", "capability_name", "team_position", "mos_required", "min_rank"]].head(10))

    return manning_doc, billets_df


def test_3_readiness_validation():
    """Test 3: Apply readiness filters."""
    print("\n" + "="*80)
    print("TEST 3: Readiness Validation")
    print("="*80)

    # Generate test force
    generator, soldiers_df, soldiers_ext = quick_generate_force(
        n_battalions=1,
        companies_per_bn=2,
        seed=42,
        fill_rate=0.95
    )

    # Use Pacific exercise profile
    profile = StandardProfiles.pacific_exercise()

    print(f"\n✓ Readiness Profile: {profile.profile_name}")
    print(f"  Required training: {profile.required_training}")
    print(f"  Min dwell: {profile.min_dwell_months} months")
    print(f"  Max medical category: C{profile.max_med_cat}")

    # Analyze readiness
    print("\nUnit Readiness Summary:")
    readiness_df = ReadinessAnalyzer.force_readiness_rollup(
        generator.units,
        soldiers_df,
        soldiers_ext,
        profile
    )
    print(readiness_df[["unit_name", "total_soldiers", "ready_count", "ready_pct"]])

    # Filter to ready soldiers
    ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)
    print(f"\n✓ Ready soldiers: {len(ready_soldiers)}/{len(soldiers_df)} ({len(ready_soldiers)/len(soldiers_df):.1%})")

    return generator, ready_soldiers, soldiers_ext, profile


def test_4_unit_cohesion_identification():
    """Test 4: Identify organic teams."""
    print("\n" + "="*80)
    print("TEST 4: Unit Cohesion - Team Identification")
    print("="*80)

    generator, soldiers_df, soldiers_ext = quick_generate_force(
        n_battalions=1,
        companies_per_bn=2,
        seed=42
    )

    # Create task organizer
    task_organizer = TaskOrganizer(
        generator.units,
        soldiers_df,
        soldiers_ext
    )

    print(f"\n✓ Identified {len(task_organizer.all_teams)} organic teams")

    # Show teams
    print("\nOrganic Teams:")
    for team in task_organizer.all_teams[:10]:  # First 10
        print(f"  {team.team_id:25s} | Type:{team.team_type:6s} | "
              f"Size:{team.size():2d} | MOS:{team.mos}")

    return task_organizer, generator, soldiers_df, soldiers_ext


def test_5_end_to_end_optimization():
    """Test 5: Full end-to-end optimization with all enhancements."""
    print("\n" + "="*80)
    print("TEST 5: End-to-End Optimization")
    print("="*80)

    # 1. Generate force
    print("\n[1/6] Generating force structure...")
    generator, soldiers_df, soldiers_ext = quick_generate_force(
        n_battalions=3,
        companies_per_bn=4,
        seed=42,
        fill_rate=0.93
    )
    print(f"  ✓ Generated {len(generator.units)} units, {len(soldiers_df):,} soldiers")

    # 2. Create manning document
    print("\n[2/6] Creating manning document...")
    manning_doc = ManningDocumentTemplates.infantry_task_force(location="Guam")
    billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
    print(f"  ✓ Manning document created: {len(billets_df)} billets")

    # 3. Apply readiness filters
    print("\n[3/6] Applying readiness filters...")
    profile = StandardProfiles.pacific_exercise()
    ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)
    print(f"  ✓ Ready soldiers: {len(ready_soldiers)}/{len(soldiers_df)} ({len(ready_soldiers)/len(soldiers_df):.1%})")

    # 4. Create task organizer
    print("\n[4/6] Identifying organic teams...")
    task_organizer = TaskOrganizer(
        generator.units,
        ready_soldiers,  # Use filtered soldiers
        soldiers_ext
    )
    print(f"  ✓ Identified {len(task_organizer.all_teams)} organic teams")

    # 5. Initialize EMD with enhancements
    print("\n[5/6] Initializing EMD optimizer...")
    emd = EMD(
        soldiers_df=ready_soldiers,
        billets_df=billets_df,
        seed=42
    )

    # Attach extended components
    emd.soldiers_ext = soldiers_ext
    emd.task_organizer = task_organizer
    emd.readiness_profile = profile

    print(f"  ✓ EMD initialized with {len(emd.soldiers):,} soldiers, {len(emd.billets)} billets")

    # 6. Run optimization
    print("\n[6/6] Running optimization...")
    assignments, summary = emd.assign(mission_name="default")

    print(f"\n{'='*80}")
    print("RESULTS")
    print('='*80)
    print(f"Fill Rate:     {summary['fill_rate']:.1%}")
    print(f"Total Cost:    ${summary['total_cost']:,.0f}")
    print(f"Filled:        {summary['filled_billets']}/{summary['total_billets']}")

    # Analyze sourcing
    print("\nSourcing Analysis:")
    sourcing = task_organizer.generate_sourcing_report(assignments)
    print(sourcing.to_string(index=False))

    # Show sample assignments
    print("\nSample Assignments (top 10 by cost):")
    top_assignments = assignments.nsmallest(10, "pair_cost")
    print(top_assignments[[
        "soldier_id", "soldier_mos", "soldier_rank",
        "billet_id", "billet_mos_req", "billet_priority",
        "pair_cost"
    ]].to_string(index=False))

    return emd, assignments, summary


def test_6_comparison_with_without_cohesion():
    """Test 6: Compare results with and without cohesion preferences."""
    print("\n" + "="*80)
    print("TEST 6: Cohesion Impact Analysis")
    print("="*80)

    # Setup
    generator, soldiers_df, soldiers_ext = quick_generate_force(
        n_battalions=2, companies_per_bn=3, seed=42
    )
    manning_doc = ManningDocumentTemplates.infantry_task_force(location="Guam")
    billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
    profile = StandardProfiles.pacific_exercise()
    ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)

    # Scenario 1: WITHOUT cohesion
    print("\n[Scenario 1: WITHOUT cohesion preferences]")
    emd_no_cohesion = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
    emd_no_cohesion.soldiers_ext = soldiers_ext
    emd_no_cohesion.readiness_profile = profile
    # Note: NOT setting task_organizer

    assignments_1, summary_1 = emd_no_cohesion.assign()
    print(f"  Fill: {summary_1['fill_rate']:.1%} | Cost: ${summary_1['total_cost']:,.0f}")

    # Scenario 2: WITH cohesion
    print("\n[Scenario 2: WITH cohesion preferences]")
    task_organizer = TaskOrganizer(generator.units, ready_soldiers, soldiers_ext)
    emd_with_cohesion = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
    emd_with_cohesion.soldiers_ext = soldiers_ext
    emd_with_cohesion.readiness_profile = profile
    emd_with_cohesion.task_organizer = task_organizer

    assignments_2, summary_2 = emd_with_cohesion.assign()
    print(f"  Fill: {summary_2['fill_rate']:.1%} | Cost: ${summary_2['total_cost']:,.0f}")

    # Compare
    print("\nComparison:")
    print(f"  Cost difference: ${summary_2['total_cost'] - summary_1['total_cost']:+,.0f}")
    print(f"  Units sourced (w/o cohesion): {assignments_1['uic'].nunique() if 'uic' in assignments_1.columns else 'N/A'}")
    print(f"  Units sourced (w/ cohesion):  {assignments_2['uic'].nunique() if 'uic' in assignments_2.columns else 'N/A'}")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("MTOE-BASED MANNING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*80)

    try:
        # Run individual tests
        test_1_basic_mtoe_generation()
        test_2_manning_document_creation()
        test_3_readiness_validation()
        test_4_unit_cohesion_identification()
        test_5_end_to_end_optimization()
        test_6_comparison_with_without_cohesion()

        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
