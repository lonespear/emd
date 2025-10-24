"""
example_mtoe_exercise.py
------------------------

Complete example showing how to use the MTOE system with exercise_builder.

This demonstrates a realistic workflow:
1. Generate a multi-battalion force
2. Create a manning document for a Pacific exercise
3. Apply readiness filters
4. Run optimization with cohesion preferences
5. Export results and analyze

Run this as a template for your own exercises.
"""

import pandas as pd
from datetime import date

# MTOE system imports
from mtoe_generator import quick_generate_force, UnitGenerator, MTOELibrary
from manning_document import ManningDocumentTemplates, ManningDocumentBuilder
from readiness_tracker import StandardProfiles, ReadinessAnalyzer, filter_ready_soldiers
from task_organizer import TaskOrganizer

# Original EMD imports
from emd_agent import EMD, ManningAgent
from exercise_builder import ExerciseBuilder, ExerciseBuilderConfig


def generate_1st_mdtf_force():
    """
    Generate a representative 1st MDTF force structure.

    1st MDTF is organized as a multi-domain task force with:
    - Infantry companies
    - Field artillery
    - Intelligence
    - Engineers
    """
    print("\n🏗️  Generating 1st MDTF Force Structure")
    print("="*80)

    generator = UnitGenerator(seed=42)

    # Battalion 1: 1-2 SBCT (Mixed Infantry/Artillery)
    print("\n[1/3] Creating 1-2 SBCT...")
    soldiers_1, ext_1 = generator.generate_battalion(
        battalion_uic="WFF01",
        battalion_name="1-2 SBCT",
        unit_types=["Infantry", "Infantry", "Infantry", "FieldArtillery"],
        home_station="JBLM",
        fill_rate=0.93
    )

    # Battalion 2: 1-3 SBCT (MI-heavy)
    print("[2/3] Creating 1-3 SBCT...")
    soldiers_2, ext_2 = generator.generate_battalion(
        battalion_uic="WFF02",
        battalion_name="1-3 SBCT",
        unit_types=["MilitaryIntelligence", "MilitaryIntelligence", "Infantry", "Engineer"],
        home_station="JBLM",
        fill_rate=0.91
    )

    # Battalion 3: Support Battalion
    print("[3/3] Creating Support Battalion...")
    soldiers_3, ext_3 = generator.generate_battalion(
        battalion_uic="WFF03",
        battalion_name="1-1 SPT",
        unit_types=["Engineer", "FieldArtillery", "Infantry", "Infantry"],
        home_station="Hawaii",
        fill_rate=0.89
    )

    # Combine all
    all_soldiers = pd.concat([soldiers_1, soldiers_2, soldiers_3], ignore_index=True)
    all_ext = {**ext_1, **ext_2, **ext_3}

    print(f"\n✅ Force Generation Complete")
    print(f"   Total Units: {len(generator.units)}")
    print(f"   Total Soldiers: {len(all_soldiers):,}")
    print(f"   Authorized Strength: {sum(u.authorized_strength for u in generator.units.values()):,}")
    print(f"   Assigned Strength: {sum(u.assigned_strength for u in generator.units.values()):,}")
    print(f"   Overall Fill: {sum(u.assigned_strength for u in generator.units.values()) / sum(u.authorized_strength for u in generator.units.values()):.1%}")

    # Show by location
    by_location = all_soldiers.groupby("base")["soldier_id"].count()
    print(f"\n   Distribution by Location:")
    for base, count in by_location.items():
        print(f"     {base:10s}: {count:4d} soldiers")

    return generator, all_soldiers, all_ext


def create_valiant_shield_tasking():
    """
    Create a manning document for Valiant Shield 2025.

    Exercise scenario:
    - Joint forcible entry exercise in Guam
    - Multi-domain operations
    - High intelligence requirement
    - Airborne/rapid deployment focus
    """
    print("\n📋 Creating Valiant Shield 2025 Manning Document")
    print("="*80)

    from manning_document import ManningDocument, CapabilityRequirement

    doc = ManningDocument(
        document_id="1MDTF-VS2025-001",
        exercise_name="Valiant Shield 2025",
        mission_description="Multi-domain forcible entry exercise with joint/combined force integration",
        requesting_unit="1st MDTF",
        execution_start=date(2025, 6, 1)
    )

    # Infantry task force (main effort)
    print("\n[1/4] Infantry Task Force...")
    doc.add_requirement(CapabilityRequirement(
        capability_name="Infantry Rifle Squad",
        quantity=5,
        mos_required="11B",
        min_rank="E-6",
        team_size=9,
        leader_required=True,
        airborne_required=True,  # Jump-capable for forcible entry
        priority=3,
        location="Guam",
        keep_team_together=True
    ))

    doc.add_requirement(CapabilityRequirement(
        capability_name="Fire Support Team",
        quantity=2,
        mos_required="13F",
        min_rank="E-6",
        team_size=4,
        leader_required=True,
        priority=3,
        location="Guam",
        keep_team_together=True
    ))

    # Intelligence package (supporting effort)
    print("[2/4] Intelligence Support Package...")
    doc.add_requirement(CapabilityRequirement(
        capability_name="All-Source Analysis Team",
        quantity=3,
        mos_required="35F",
        min_rank="E-5",
        team_size=4,
        leader_required=True,
        clearance_req="TS",
        priority=3,
        location="Guam",
        keep_team_together=True
    ))

    doc.add_requirement(CapabilityRequirement(
        capability_name="HUMINT Collection Team",
        quantity=2,
        mos_required="35M",
        min_rank="E-6",
        team_size=3,
        leader_required=True,
        clearance_req="TS",
        priority=2,
        location="Guam",
        keep_team_together=True
    ))

    # Engineer support
    print("[3/4] Engineer Support...")
    doc.add_requirement(CapabilityRequirement(
        capability_name="Combat Engineer Squad",
        quantity=2,
        mos_required="12B",
        min_rank="E-6",
        team_size=8,
        leader_required=True,
        priority=2,
        location="Guam",
        keep_team_together=True
    ))

    # Logistics/medical
    print("[4/4] Combat Service Support...")
    doc.add_requirement(CapabilityRequirement(
        capability_name="Combat Medic",
        quantity=8,
        mos_required="68W",
        min_rank="E-4",
        skill_level_req=2,
        priority=3,
        location="Guam"
    ))

    doc.add_requirement(CapabilityRequirement(
        capability_name="Motor Transport Operator",
        quantity=6,
        mos_required="88M",
        min_rank="E-4",
        equipment_required=["LMTV_license"],
        priority=2,
        location="Guam"
    ))

    print(f"\n✅ Manning Document Created")
    print(f"   Total Capabilities: {doc.total_capabilities()}")
    print(f"   Total Billets: {doc.total_billets()}")

    # Export
    doc.export_json("ValiantShield2025_manning_doc.json")
    print(f"   Exported: ValiantShield2025_manning_doc.json")

    return doc


def run_valiant_shield_exercise():
    """
    Complete Valiant Shield 2025 exercise execution.
    """
    print("\n" + "="*80)
    print("VALIANT SHIELD 2025 - MANNING OPTIMIZATION")
    print("="*80)

    # Step 1: Generate force
    generator, soldiers_df, soldiers_ext = generate_1st_mdtf_force()

    # Step 2: Create tasking
    manning_doc = create_valiant_shield_tasking()

    # Step 3: Convert to billets
    print("\n🔄 Converting Manning Document to Billets")
    print("="*80)
    billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
    print(f"✅ Generated {len(billets_df)} billets")

    # Step 4: Apply readiness filters
    print("\n🏥 Applying Readiness Validation")
    print("="*80)
    profile = StandardProfiles.pacific_exercise()
    print(f"Profile: {profile.profile_name}")
    print(f"Required training: {', '.join(profile.required_training)}")
    print(f"Min dwell: {profile.min_dwell_months} months")

    # Analyze before filtering
    readiness_summary = ReadinessAnalyzer.force_readiness_rollup(
        generator.units, soldiers_df, soldiers_ext, profile
    )
    print("\nUnit Readiness:")
    print(readiness_summary[["unit_name", "total_soldiers", "ready_count", "ready_pct"]].to_string(index=False))

    ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)
    print(f"\n✅ Ready Soldiers: {len(ready_soldiers)}/{len(soldiers_df)} ({len(ready_soldiers)/len(soldiers_df):.1%})")

    # Step 5: Create task organizer
    print("\n🤝 Identifying Organic Teams")
    print("="*80)
    task_organizer = TaskOrganizer(generator.units, ready_soldiers, soldiers_ext)
    print(f"✅ Identified {len(task_organizer.all_teams)} organic teams")

    # Show team breakdown by type
    team_types = {}
    for team in task_organizer.all_teams:
        team_types[team.team_type] = team_types.get(team.team_type, 0) + 1
    print("\nTeam Breakdown:")
    for ttype, count in team_types.items():
        print(f"  {ttype:10s}: {count:3d} teams")

    # Step 6: Run optimization
    print("\n⚙️  Running Optimization")
    print("="*80)

    emd = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
    emd.soldiers_ext = soldiers_ext
    emd.task_organizer = task_organizer
    emd.readiness_profile = profile

    # Tune policies for this exercise
    emd.tune_policy(
        unit_cohesion_bonus=-700,  # Strong preference for intact teams
        airborne_required_penalty=2000,  # Airborne is critical
        clearance_mismatch_penalty=3000,  # TS clearance is critical for MI
        TDY_cost_weight=1.2  # Pacific TDY is expensive
    )

    assignments, summary = emd.assign(mission_name="ValiantShield")

    # Step 7: Results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\n✅ Optimization Complete")
    print(f"   Fill Rate:     {summary['fill_rate']:.1%}")
    print(f"   Total Cost:    ${summary['total_cost']:,.0f}")
    print(f"   Filled:        {summary['filled_billets']}/{summary['total_billets']} billets")

    # Sourcing analysis
    if 'uic' in assignments.columns:
        print("\n📊 Sourcing Analysis:")
        sourcing = task_organizer.generate_sourcing_report(assignments)
        print(sourcing.to_string(index=False))

    # By capability
    if 'capability_name' in assignments.columns:
        print("\n📦 Fill by Capability:")
        by_cap = assignments.groupby("capability_name").agg({
            "billet_id": "count",
            "pair_cost": ["mean", "sum"]
        }).round(0)
        by_cap.columns = ["filled", "avg_cost", "total_cost"]
        print(by_cap.to_string())

    # Export results
    print("\n💾 Exporting Results...")
    assignments.to_csv("ValiantShield2025_assignments.csv", index=False)
    pd.DataFrame([summary]).to_json("ValiantShield2025_summary.json", orient="records", indent=2)
    print("   ✅ ValiantShield2025_assignments.csv")
    print("   ✅ ValiantShield2025_summary.json")

    # Top quality assignments
    print("\n⭐ Top Quality Assignments (lowest cost):")
    top = assignments.nsmallest(10, "pair_cost")
    display_cols = ["soldier_id", "soldier_mos", "soldier_rank", "billet_id",
                    "capability_name", "team_position", "pair_cost"]
    available_cols = [c for c in display_cols if c in top.columns]
    print(top[available_cols].to_string(index=False))

    return emd, assignments, summary


def comparison_study():
    """
    Compare optimization with and without MTOE enhancements.
    """
    print("\n" + "="*80)
    print("COMPARISON STUDY: Traditional vs. MTOE-Enhanced")
    print("="*80)

    # Generate force
    generator, soldiers_df, soldiers_ext = generate_1st_mdtf_force()
    manning_doc = create_valiant_shield_tasking()
    billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
    profile = StandardProfiles.pacific_exercise()
    ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)

    # Scenario 1: Traditional (no enhancements)
    print("\n[Scenario 1: Traditional EMD]")
    print("-" * 80)
    emd_trad = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
    assign_trad, summary_trad = emd_trad.assign()
    print(f"Fill: {summary_trad['fill_rate']:.1%} | Cost: ${summary_trad['total_cost']:,.0f}")

    # Scenario 2: With readiness only
    print("\n[Scenario 2: With Readiness Validation]")
    print("-" * 80)
    emd_readiness = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
    emd_readiness.soldiers_ext = soldiers_ext
    emd_readiness.readiness_profile = profile
    assign_readiness, summary_readiness = emd_readiness.assign()
    print(f"Fill: {summary_readiness['fill_rate']:.1%} | Cost: ${summary_readiness['total_cost']:,.0f}")

    # Scenario 3: Full MTOE (readiness + cohesion)
    print("\n[Scenario 3: Full MTOE Enhancement]")
    print("-" * 80)
    task_organizer = TaskOrganizer(generator.units, ready_soldiers, soldiers_ext)
    emd_full = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
    emd_full.soldiers_ext = soldiers_ext
    emd_full.readiness_profile = profile
    emd_full.task_organizer = task_organizer
    assign_full, summary_full = emd_full.assign()
    print(f"Fill: {summary_full['fill_rate']:.1%} | Cost: ${summary_full['total_cost']:,.0f}")

    # Summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"\n{'Scenario':<30s} | {'Fill Rate':>10s} | {'Total Cost':>15s} | {'Δ Cost':>15s}")
    print("-" * 75)
    print(f"{'Traditional':<30s} | {summary_trad['fill_rate']:>9.1%} | ${summary_trad['total_cost']:>13,.0f} | {'baseline':>15s}")
    print(f"{'+ Readiness':<30s} | {summary_readiness['fill_rate']:>9.1%} | ${summary_readiness['total_cost']:>13,.0f} | ${summary_readiness['total_cost'] - summary_trad['total_cost']:>+14,.0f}")
    print(f"{'+ Readiness + Cohesion':<30s} | {summary_full['fill_rate']:>9.1%} | ${summary_full['total_cost']:>13,.0f} | ${summary_full['total_cost'] - summary_trad['total_cost']:>+14,.0f}")

    print("\n💡 Insights:")
    print(f"   - Readiness validation adds quality control")
    print(f"   - Cohesion preference may increase cost but preserves unit effectiveness")
    print(f"   - Final cost reflects realistic constraints vs. pure optimization")


if __name__ == "__main__":
    # Run the full exercise
    emd, assignments, summary = run_valiant_shield_exercise()

    # Optional: Run comparison study
    print("\n\n")
    response = input("Run comparison study? (y/n): ")
    if response.lower() == 'y':
        comparison_study()

    print("\n✅ Example complete!")
