# EMD Qualification System - Tutorial

## 5-Minute Walkthrough

This tutorial walks you through the complete workflow of the EMD qualification system.

---

## Step 1: Generate Soldiers with Extended Profiles (1 min)

```python
from mtoe_generator import UnitGenerator, MTOELibrary

# Create generator with seed for reproducibility
generator = UnitGenerator(seed=42)

# Load MTOE template
template = MTOELibrary.infantry_rifle_company()

# Create unit
unit = generator.create_unit(
    template=template,
    uic="A1234",
    name="Alpha Company, 1st Battalion, 2nd Infantry",
    short_name="A/1-2 IN",
    home_station="JBLM"
)

# Generate soldiers WITH extended profiles
soldiers_df, soldiers_ext = generator.generate_soldiers_for_unit(
    unit,
    fill_rate=0.85  # 85% manning
)

print(f"Generated {len(soldiers_df)} soldiers")
print(f"Extended profiles: {len(soldiers_ext)}")
print(f"Columns: {soldiers_df.columns.tolist()}")
```

**What you get**:
- `soldiers_df`: DataFrame with base + extended columns
- `soldiers_ext`: Dict of detailed profile objects (key: soldier_id)

**Extended columns include**:
- `education_level`, `dlpt_scores_json`
- `badges_json`, `awards_json`
- `deployments_json`, `licenses_json`
- And more!

---

## Step 2: Filter Qualified Soldiers (1 min)

```python
from qualification_filter import QualificationFilter

# Initialize filter
qf = QualificationFilter(soldiers_df)

# Use preset filters
print("\nPreset Filter Results:")
print(f"  Airborne qualified: {len(qf.apply_preset('airborne_qualified'))}")
print(f"  Ranger qualified: {len(qf.apply_preset('ranger_qualified'))}")
print(f"  Combat veterans: {len(qf.apply_preset('combat_veteran'))}")
print(f"  High fitness: {len(qf.apply_preset('high_fitness'))}")
print(f"  NCO leadership: {len(qf.apply_preset('nco_leadership'))}")

# Custom filtering
rangers = qf.filter_by_badge("RANGER")
combat_fit = qf.filter_combat_veterans()
high_acft = qf.filter_by_acft_score(540)

print(f"\nCustom Filters:")
print(f"  Rangers: {len(rangers)}")
print(f"  Combat veterans: {len(combat_fit)}")
print(f"  ACFT 540+: {len(high_acft)}")

# Combine filters with AND logic
from qualification_filter import FilterGroup, FilterCriterion

elite_filter = FilterGroup(
    criteria=[
        FilterCriterion("acft_score", "gte", 540),
        FilterCriterion("ranger", "eq", 1),
        FilterCriterion("_has_combat_experience", "eq", True)
    ],
    logic="AND",
    name="Elite Soldiers"
)

elite = qf.apply_filter_group(elite_filter)
print(f"\nElite soldiers (Ranger + Combat + ACFT 540+): {len(elite)}")

# Get statistics
stats = qf.get_filter_statistics(elite)
print(f"\nElite soldier stats:")
print(f"  Avg ACFT: {stats.get('avg_acft', 0):.0f}")
print(f"  Avg dwell: {stats.get('avg_dwell', 0):.1f} months")
print(f"  Deployable: {stats.get('deployable_pct', 0)*100:.1f}%")
```

---

## Step 3: Create Billets with Requirements (1 min)

```python
from manning_document import ManningDocument, CapabilityRequirement
from manning_document import ManningDocumentBuilder
from billet_requirements import BilletRequirementTemplates, create_basic_requirements

# Create manning document
doc = ManningDocument(
    document_id="TUTORIAL-001",
    exercise_name="Pacific Shield 2025",
    mission_description="Joint exercise in INDOPACOM",
    requesting_unit="I Corps"
)

# Add Ranger-qualified team leaders
ranger_req = BilletRequirementTemplates.ranger_qualified_infantry_leader()
doc.add_requirement(CapabilityRequirement(
    capability_name="Ranger Team Leader",
    quantity=2,
    mos_required="11B",
    min_rank="E-6",
    priority=3,
    location="Guam",
    airborne_required=True,
    extended_requirements=ranger_req
))

# Add Intel analysts with language
intel_req = BilletRequirementTemplates.intelligence_analyst_strategic_language()
doc.add_requirement(CapabilityRequirement(
    capability_name="Intel Analyst",
    quantity=2,
    mos_required="35F",
    min_rank="E-5",
    clearance_req="TS",
    priority=3,
    location="Guam",
    extended_requirements=intel_req
))

# Add basic infantry riflemen
basic_req = create_basic_requirements(
    position_title="Infantry Rifleman",
    min_education="HS",
    combat_required=True,
    min_deployments=1
)
doc.add_requirement(CapabilityRequirement(
    capability_name="Infantry Rifleman",
    quantity=10,
    mos_required="11B",
    min_rank="E-3",
    max_rank="E-4",
    priority=2,
    location="Guam",
    extended_requirements=basic_req
))

# Generate billets DataFrame
billets_df = ManningDocumentBuilder.generate_billets_from_document(doc)

print(f"\nGenerated {len(billets_df)} billets")
print(f"Total capabilities: {doc.total_capabilities()}")
print(f"Total billets: {doc.total_billets()}")
print(f"\nBillet breakdown:")
for req in doc.requirements:
    print(f"  {req.capability_name}: {req.quantity}")
```

---

## Step 4: Run Assignment with Qualification Matching (1 min)

```python
from emd_agent import EMD

# Initialize EMD
emd = EMD(soldiers_df=soldiers_df, billets_df=billets_df, seed=42)

print(f"\nEMD initialized:")
print(f"  Soldiers: {len(emd.soldiers)}")
print(f"  Billets: {len(emd.billets)}")
print(f"  Policy parameters: {len(emd.policies)}")

# Check qualification policies
qual_policies = [k for k in emd.policies.keys() if any(x in k for x in
                 ['education', 'language', 'badge', 'asi_', 'sqi_'])]
print(f"  Qualification policies: {len(qual_policies)}")

# Optional: Tune policies for this mission
emd.tune_policy(
    language_proficiency_penalty=3000,  # Critical for INDOPACOM
    combat_experience_bonus=-500,       # Important for this exercise
    badge_missing_penalty=1500          # Ranger/Airborne important
)

# Run assignment
print("\nRunning assignment with qualification matching...")
assignments, summary = emd.assign("default")

print(f"\n✓ Assignment complete!")
print(f"  Fill rate: {summary.get('fill_rate', 0)*100:.1f}%")
print(f"  Total cost: ${summary.get('total_cost', 0):,.0f}")
print(f"  Filled billets: {summary.get('filled_billets', 0)}/{summary.get('total_billets', 0)}")

# Analyze assignment quality
if len(assignments) > 0:
    avg_cost = assignments['cost'].mean() if 'cost' in assignments.columns else 0
    print(f"  Avg cost/assignment: ${avg_cost:,.0f}")

# Show sample assignments
print(f"\nSample assignments:")
for idx, row in assignments.head(5).iterrows():
    soldier_id = row.get('soldier_id', '?')
    billet_id = row.get('billet_id', '?')
    cost = row.get('cost', 0)
    cap_name = row.get('capability_name', 'Unknown')
    print(f"  Soldier {soldier_id} → {cap_name} (Billet {billet_id}): ${cost:,.0f}")
```

---

## Step 5: Analyze Results (1 min)

```python
# Analyze by capability
print("\n" + "="*60)
print("ASSIGNMENT ANALYSIS BY CAPABILITY")
print("="*60)

if 'capability_name' in assignments.columns:
    by_cap = assignments.groupby('capability_name').agg({
        'billet_id': 'count',
        'cost': ['mean', 'sum']
    }).round(0)
    by_cap.columns = ['Filled', 'Avg Cost', 'Total Cost']

    # Add required count
    for req in doc.requirements:
        cap_name = req.capability_name
        if cap_name in by_cap.index:
            required = req.quantity
            filled = int(by_cap.loc[cap_name, 'Filled'])
            fill_pct = filled / required * 100

            print(f"\n{cap_name}:")
            print(f"  Required: {required}")
            print(f"  Filled: {filled} ({fill_pct:.0f}%)")
            print(f"  Avg cost: ${by_cap.loc[cap_name, 'Avg Cost']:,.0f}")
            print(f"  Total cost: ${by_cap.loc[cap_name, 'Total Cost']:,.0f}")

# Check who got assigned
print("\n" + "="*60)
print("SOLDIER ASSIGNMENT SUMMARY")
print("="*60)

if 'soldier_id' in assignments.columns:
    assigned_ids = set(assignments['soldier_id'].unique())

    # Check if any elite soldiers were assigned
    elite_assigned = assigned_ids.intersection(set(elite['soldier_id'].unique()))
    print(f"\nElite soldiers assigned: {len(elite_assigned)}/{len(elite)}")

    # Check Rangers
    if len(rangers) > 0:
        ranger_ids = set(rangers['soldier_id'].unique())
        rangers_assigned = assigned_ids.intersection(ranger_ids)
        print(f"Rangers assigned: {len(rangers_assigned)}/{len(rangers)}")

# Export results
assignments.to_csv("tutorial_assignments.csv", index=False)
print(f"\n✓ Results exported to tutorial_assignments.csv")
```

---

## Complete Working Example

Here's the complete code you can run:

```python
# Complete Tutorial Example - Run as a single script

from mtoe_generator import UnitGenerator, MTOELibrary
from qualification_filter import QualificationFilter, FilterGroup, FilterCriterion
from manning_document import ManningDocument, CapabilityRequirement, ManningDocumentBuilder
from billet_requirements import BilletRequirementTemplates, create_basic_requirements
from emd_agent import EMD

print("="*60)
print("EMD QUALIFICATION SYSTEM - COMPLETE TUTORIAL")
print("="*60)

# Step 1: Generate soldiers
print("\n[STEP 1] Generating soldiers...")
generator = UnitGenerator(seed=42)
template = MTOELibrary.infantry_rifle_company()
unit = generator.create_unit(template, uic="A1234", name="Alpha Co",
                             short_name="A/1-2", home_station="JBLM")
soldiers_df, soldiers_ext = generator.generate_soldiers_for_unit(unit, fill_rate=0.85)
print(f"✓ Generated {len(soldiers_df)} soldiers with extended profiles")

# Step 2: Filter qualified soldiers
print("\n[STEP 2] Filtering qualified soldiers...")
qf = QualificationFilter(soldiers_df)
rangers = qf.apply_preset("ranger_qualified")
elite = qf.apply_filter_group(FilterGroup(
    criteria=[
        FilterCriterion("acft_score", "gte", 540),
        FilterCriterion("ranger", "eq", 1),
        FilterCriterion("_has_combat_experience", "eq", True)
    ],
    logic="AND"
))
print(f"✓ Found {len(rangers)} Rangers, {len(elite)} elite soldiers")

# Step 3: Create billets
print("\n[STEP 3] Creating billets with requirements...")
doc = ManningDocument(document_id="TUT-001", exercise_name="Tutorial Exercise",
                     mission_description="Test", requesting_unit="Test Unit")

doc.add_requirement(CapabilityRequirement(
    capability_name="Ranger Team Leader", quantity=2, mos_required="11B",
    min_rank="E-6", priority=3, location="JBLM",
    extended_requirements=BilletRequirementTemplates.ranger_qualified_infantry_leader()
))

doc.add_requirement(CapabilityRequirement(
    capability_name="Infantry Rifleman", quantity=10, mos_required="11B",
    min_rank="E-3", max_rank="E-4", priority=2, location="JBLM",
    extended_requirements=create_basic_requirements("Rifleman", "HS", combat_required=True)
))

billets_df = ManningDocumentBuilder.generate_billets_from_document(doc)
print(f"✓ Generated {len(billets_df)} billets")

# Step 4: Run assignment
print("\n[STEP 4] Running assignment with qualification matching...")
emd = EMD(soldiers_df=soldiers_df, billets_df=billets_df, seed=42)
assignments, summary = emd.assign("default")
print(f"✓ Assignment complete: {summary['fill_rate']*100:.1f}% fill rate")

# Step 5: Analyze
print("\n[STEP 5] Analysis:")
print(f"  Filled: {summary['filled_billets']}/{summary['total_billets']}")
print(f"  Total cost: ${summary['total_cost']:,.0f}")
print(f"  Elite soldiers used: {len(set(assignments['soldier_id']).intersection(elite['soldier_id']))}")

print("\n" + "="*60)
print("TUTORIAL COMPLETE!")
print("="*60)
print("\nNext steps:")
print("  1. Try different filter presets")
print("  2. Create custom requirements")
print("  3. Tune policy parameters")
print("  4. Run the dashboard: streamlit run dashboard.py")
```

---

## Common Patterns

### Pattern 1: Mission-Specific Filtering

```python
# INDOPACOM mission - needs language qualified soldiers
def find_indopacom_qualified(soldiers_df):
    qf = QualificationFilter(soldiers_df)

    # Must have: deployable, good dwell, passport
    deployable = qf.filter_deployable()
    qf_temp = QualificationFilter(deployable)

    good_dwell = qf_temp.filter_by_dwell(12)
    qf_temp = QualificationFilter(good_dwell)

    # Prefer: language, INDOPACOM experience, high fitness
    lang_qualified = qf_temp.filter_has_any_language(2)

    return lang_qualified
```

### Pattern 2: Progressive Filtering

```python
# Start broad, narrow down
result = soldiers_df.copy()

# Must-haves
qf = QualificationFilter(result)
result = qf.filter_deployable()

qf = QualificationFilter(result)
result = qf.filter_by_acft_score(450)

# Nice-to-haves (if we have enough)
if len(result) > required_count * 1.5:
    qf = QualificationFilter(result)
    result = qf.filter_combat_veterans()
```

### Pattern 3: Quality Scoring

```python
def score_soldier_quality(soldier_row):
    """Assign quality score to a soldier."""
    score = 0

    # Fitness
    if soldier_row.get('acft_score', 0) >= 540:
        score += 10
    elif soldier_row.get('acft_score', 0) >= 500:
        score += 5

    # Qualifications
    if soldier_row.get('ranger', 0) == 1:
        score += 15
    if soldier_row.get('airborne', 0) == 1:
        score += 5

    # Experience
    if soldier_row.get('_has_combat_experience'):
        score += 10

    return score

# Add scores to soldiers
soldiers_df['quality_score'] = soldiers_df.apply(score_soldier_quality, axis=1)

# Get top soldiers
top_soldiers = soldiers_df.nlargest(20, 'quality_score')
```

---

## Next Steps

1. **Explore the Dashboard**
   ```bash
   streamlit run dashboard.py
   ```
   Navigate to "Qualification Filtering" page

2. **Run Tests**
   ```bash
   python run_all_tests.py --quick
   ```

3. **Read Full Documentation**
   See `README_QUALIFICATION_SYSTEM.md` for complete API reference

4. **Experiment with Policies**
   Try different penalty/bonus values to see how they affect assignments

5. **Create Custom Requirements**
   Build requirements tailored to your specific mission needs

---

## Troubleshooting Tutorial Issues

**No Rangers found?**
- Extended profile generation is random
- Try: Increase fill_rate to 0.95 or change seed

**Low fill rate?**
- Requirements may be too strict
- Try: Reduce penalty values or relax requirements

**All costs are $0?**
- Perfect matches found (good thing!)
- Try: Add stricter requirements to see penalties

**Import errors?**
- Run: `python validate_system.py`
- Ensure all modules are present

---

**Tutorial Complete!** You now know how to:
- ✅ Generate soldiers with extended profiles
- ✅ Filter soldiers by qualifications
- ✅ Create billets with requirements
- ✅ Run assignment with qualification matching
- ✅ Analyze results

Happy optimizing! 🎖️
