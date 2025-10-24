# MTOE-Based Manning System

## Overview

This enhanced EMD system introduces **realistic military unit structure** and **capability-based tasking** to make the optimization framework align with how the Army actually conducts manning operations.

## Key Enhancements

### 1. **Unit Structure (MTOE-based)**
- Generate soldiers from doctrinal MTOE templates
- Company-level organization with organic positions
- Leadership hierarchy (CDR → 1SG → PSG → SL → TL)
- Track para/line assignments and duty positions

### 2. **Manning Documents**
- Capability-based requirements (not individual positions)
- Team-based tasking (e.g., "3x Infantry Squads")
- Mirrors real WARNO/FRAGO tasking process
- Converts capabilities to optimization billets

### 3. **Readiness Validation**
- Training gate tracking (weapons qual, SERE, PHA, etc.)
- Equipment qualifications with expiry dates
- Deployment history and dwell time
- Medical/dental category validation
- Configurable readiness profiles per mission

### 4. **Unit Cohesion**
- Identify organic teams from unit structure
- Prefer keeping teams intact when sourcing
- Apply penalties for breaking up established units
- Balance between unit cohesion and optimal fill

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Manning Workflow                         │
└─────────────────────────────────────────────────────────────┘

    1. MTOE Templates → Unit Generator
              ↓
    2. Organic Soldiers (with unit assignments, positions)
              ↓
    3. Manning Document (capability requirements)
              ↓
    4. Readiness Filter (apply training/medical gates)
              ↓
    5. Task Organizer (identify teams, cohesion logic)
              ↓
    6. EMD Optimizer (enhanced cost function)
              ↓
    7. Assignments + Validation + Orders
```

## Core Components

### `unit_types.py`
Data classes for military structure:
- `Unit`: Company-level organization
- `Position`: MTOE para/line positions
- `SoldierExtended`: Enhanced soldier with training/history
- `TrainingGate`: Training requirements with currency
- `Equipment`: Qualifications and certifications
- `DeploymentRecord`: Historical deployment data
- `LeadershipLevel`: Hierarchical leadership enum

### `mtoe_generator.py`
MTOE template library and unit instantiation:
- `MTOETemplate`: Blueprint for unit types
- `MTOELibrary`: Pre-defined templates (Infantry, FA, MI, Engineer)
- `UnitGenerator`: Creates units and populates with soldiers
- `quick_generate_force()`: Generate multi-battalion forces

**Available Templates:**
- Infantry Rifle Company (~130 soldiers)
- Field Artillery Battery (~90 soldiers)
- Military Intelligence Company (~80 soldiers)
- Engineer Company (~100 soldiers)

### `manning_document.py`
Capability-based tasking system:
- `CapabilityRequirement`: Defines a capability need
- `ManningDocument`: Collection of requirements
- `ManningDocumentBuilder`: Converts to EMD billets
- `ManningDocumentTemplates`: Pre-built scenarios

**Example Manning Documents:**
- Infantry Task Force (3x squads + FST + HQ)
- Intelligence Support Package (Analysis + HUMINT + SIGINT)
- Logistics Support Element (Supply + Transport + Medical)

### `readiness_tracker.py`
Training status and readiness validation:
- `ReadinessProfile`: Defines requirements for a mission
- `ReadinessValidator`: Validates soldier readiness
- `ReadinessAnalyzer`: Aggregate readiness reporting
- `StandardProfiles`: Pre-defined mission profiles

**Standard Profiles:**
- CONUS Training (basic requirements)
- OCONUS Training (passport, SERE)
- Combat Deployment (full deployment readiness)
- Pacific Exercise (theater-specific)

### `task_organizer.py`
Unit cohesion management:
- `OrganicTeam`: Represents intact team from a unit
- `TeamIdentifier`: Identifies teams from structure
- `CohesionCalculator`: Calculates cohesion bonuses/penalties
- `TaskOrganizer`: Manages hybrid sourcing strategy

**Sourcing Strategy:**
1. Try to source intact teams first (best cohesion)
2. Accept partial teams if available (moderate)
3. Individual backfill as last resort (least cohesion)

### `emd_agent.py` (Enhanced)
New integration points:
- Accept pre-generated soldiers/billets DataFrames
- Optional `soldiers_ext`, `task_organizer`, `readiness_profile`
- `apply_cohesion_adjustments()`: Modify cost matrix for cohesion
- `apply_readiness_penalties()`: Add readiness gate penalties
- New policies: `unit_cohesion_bonus`, `readiness_failure_penalty`, etc.

## Usage Examples

### Example 1: Basic MTOE Force Generation

```python
from mtoe_generator import quick_generate_force

# Generate a 2-battalion force
generator, soldiers_df, soldiers_ext = quick_generate_force(
    n_battalions=2,
    companies_per_bn=4,
    seed=42,
    fill_rate=0.92
)

print(f"Generated {len(generator.units)} companies")
print(f"Total soldiers: {len(soldiers_df):,}")

# Access units
for uic, unit in generator.units.items():
    print(f"{unit.short_name}: {unit.assigned_strength}/{unit.authorized_strength}")
```

### Example 2: Create Manning Document

```python
from manning_document import ManningDocumentTemplates, ManningDocumentBuilder

# Use pre-built template
manning_doc = ManningDocumentTemplates.infantry_task_force(location="Guam")

# Or create custom
from manning_document import create_custom_manning_document

capabilities = [
    {"name": "Rifle Squad", "mos": "11B", "rank": "E-6", "quantity": 2,
     "priority": 3, "team_size": 9},
    {"name": "Combat Medic", "mos": "68W", "rank": "E-5", "quantity": 3,
     "priority": 3, "team_size": 1}
]
manning_doc = create_custom_manning_document("My Exercise", capabilities, "Hawaii")

# Convert to billets
billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
```

### Example 3: Apply Readiness Filters

```python
from readiness_tracker import StandardProfiles, filter_ready_soldiers

# Select readiness profile
profile = StandardProfiles.pacific_exercise()

# Filter soldiers
ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)

print(f"Ready: {len(ready_soldiers)}/{len(soldiers_df)} soldiers")
```

### Example 4: Full Optimization with Cohesion

```python
from emd_agent import EMD
from task_organizer import TaskOrganizer

# Setup
generator, soldiers_df, soldiers_ext = quick_generate_force(...)
manning_doc = ManningDocumentTemplates.infantry_task_force(...)
billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
profile = StandardProfiles.pacific_exercise()
ready_soldiers = filter_ready_soldiers(soldiers_df, soldiers_ext, profile)

# Create task organizer
task_organizer = TaskOrganizer(generator.units, ready_soldiers, soldiers_ext)

# Initialize EMD with enhancements
emd = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
emd.soldiers_ext = soldiers_ext
emd.task_organizer = task_organizer
emd.readiness_profile = profile

# Run optimization
assignments, summary = emd.assign()

print(f"Fill: {summary['fill_rate']:.1%}, Cost: ${summary['total_cost']:,.0f}")

# Analyze sourcing
sourcing_report = task_organizer.generate_sourcing_report(assignments)
print(sourcing_report)
```

## Testing

Run the comprehensive test suite:

```bash
cd C:\Users\jonathan.day\Documents\emd
python test_mtoe_system.py
```

**Test Coverage:**
1. MTOE unit generation
2. Manning document creation
3. Readiness validation
4. Team identification
5. End-to-end optimization
6. Cohesion impact analysis

## Integration with Existing Code

The new system is **backward compatible** with existing EMD code:

```python
# Old way (still works)
emd = EMD(n_soldiers=800, n_billets=75, seed=42)
assignments, summary = emd.assign()

# New way (with MTOE enhancements)
generator, soldiers_df, soldiers_ext = quick_generate_force(...)
manning_doc = ManningDocumentTemplates.infantry_task_force(...)
billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)

emd = EMD(soldiers_df=soldiers_df, billets_df=billets_df, seed=42)
# Optionally attach enhancements
emd.soldiers_ext = soldiers_ext
emd.task_organizer = TaskOrganizer(...)
emd.readiness_profile = StandardProfiles.pacific_exercise()

assignments, summary = emd.assign()
```

## Policy Knobs

### New Policies (added to `emd_agent.py`)

| Policy | Default | Description |
|--------|---------|-------------|
| `dwell_short_penalty` | 1500 | Penalty for moving soldier with insufficient dwell time |
| `unit_cohesion_bonus` | -500 | Bonus for keeping organic teams together |
| `unit_split_penalty` | 300 | Penalty for breaking up teams |
| `cross_unit_penalty` | 200 | Penalty per additional unit sourced from |
| `readiness_failure_penalty` | 2000 | Penalty per readiness gate failed |
| `training_currency_bonus` | -100 | Bonus for all training current |

Tune policies as needed:

```python
emd.tune_policy(
    unit_cohesion_bonus=-800,  # Increase cohesion preference
    readiness_failure_penalty=3000  # Stricter readiness enforcement
)
```

## Data Model

### Soldiers DataFrame (Extended)

Original columns plus:
- `uic`: Unit Identification Code
- `para_line`: MTOE para/line position
- `duty_position`: Duty title (e.g., "Squad Leader")
- `leadership_level`: 0=soldier, 1=TL, 2=SL, 3=PSG, 4=1SG

### Billets DataFrame (Extended)

Original columns plus:
- `capability_name`: Capability this billet belongs to
- `capability_instance`: Which instance (e.g., Squad 1, Squad 2)
- `team_position`: Role within team (leader, member_1, etc.)
- `keep_together`: Flag to prefer intact team sourcing

### SoldierExtended (new)

Complex data not in DataFrame:
- `training_gates`: Dict[str, TrainingGate]
- `equipment_quals`: List[Equipment]
- `deployment_history`: List[DeploymentRecord]
- `time_in_position_months`: int
- `previous_positions`: List[str]

## Future Enhancements

### Potential Additions:
1. **Platoon/Squad-level fidelity** - Currently company-level
2. **Equipment tracking** - Track serialized equipment assignments
3. **Replacement flow** - Model turnover and replacement timelines
4. **DTMS integration** - Pull real training status from DTMS exports
5. **FMSWeb import** - Load actual MTOEs from FMSWeb
6. **Career progression** - Validate assignments against career maps
7. **Cost estimation** - Real TDY/PCS cost estimation from DTS data
8. **Multi-objective** - Pareto frontier for fill vs. cost vs. cohesion

## Files Created

### Core System (5 files, ~2500 LOC)
- `unit_types.py` - Data classes (350 LOC)
- `mtoe_generator.py` - MTOE templates and generation (650 LOC)
- `readiness_tracker.py` - Training validation (450 LOC)
- `manning_document.py` - Capability-based tasking (500 LOC)
- `task_organizer.py` - Cohesion logic (400 LOC)

### Integration
- `emd_agent.py` - Enhanced (added ~150 LOC)

### Testing & Documentation
- `test_mtoe_system.py` - Comprehensive test suite (450 LOC)
- `README_MTOE_SYSTEM.md` - This file

## Questions?

For questions or issues with the MTOE system:
1. Check `test_mtoe_system.py` for usage examples
2. Review individual module docstrings
3. Examine `quick_generate_force()` for realistic defaults

---

**Version:** 1.0
**Last Updated:** 2025-01-23
**Compatibility:** Python 3.8+, Requires: numpy, pandas, scipy (optional)
