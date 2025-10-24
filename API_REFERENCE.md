# EMD Qualification System - API Quick Reference

## Quick Import Guide

```python
# Core system
from mtoe_generator import UnitGenerator, MTOELibrary
from manning_document import ManningDocument, CapabilityRequirement, ManningDocumentBuilder
from emd_agent import EMD

# Qualification system
from qualification_filter import QualificationFilter, FilterCriterion, FilterGroup
from billet_requirements import (
    BilletRequirements, BilletRequirementTemplates,
    LanguageRequirement, BadgeRequirement, ExperienceRequirement
)
from profile_utils import (
    get_languages, filter_by_education, has_combat_experience,
    generate_qualification_summary
)
```

---

## QualificationFilter

### Initialization
```python
qf = QualificationFilter(soldiers_df: pd.DataFrame)
```

### Preset Filters (Quick Access)
```python
# 9 preset filters available
presets = qf.list_available_presets()
# Returns: ['airborne_qualified', 'ranger_qualified', 'combat_veteran',
#           'high_fitness', 'nco_leadership', 'language_qualified',
#           'fully_deployable', 'senior_nco', 'special_operations']

# Apply preset
results = qf.apply_preset(preset_name: str) -> pd.DataFrame

# Get description
desc = qf.get_preset_description(preset_name: str) -> str
```

### Basic Filters
```python
# Rank & MOS
qf.filter_by_rank(ranks: List[str]) -> pd.DataFrame
qf.filter_by_mos(mos_codes: List[str]) -> pd.DataFrame

# Fitness
qf.filter_by_acft_score(min_score: int) -> pd.DataFrame
qf.filter_by_acft_range(min_score: int, max_score: int) -> pd.DataFrame

# Readiness
qf.filter_deployable() -> pd.DataFrame
qf.filter_by_dwell(min_months: int) -> pd.DataFrame
```

### Qualification Filters
```python
# Badges & Skills
qf.filter_by_badge(badge_name: str) -> pd.DataFrame  # "AIRBORNE", "RANGER", etc.
qf.filter_combat_badge_holders() -> pd.DataFrame

# Languages
qf.filter_by_language(language_code: str, min_level: int = 2) -> pd.DataFrame
qf.filter_has_any_language(min_level: int = 2) -> pd.DataFrame

# Experience
qf.filter_combat_veterans() -> pd.DataFrame
qf.filter_by_deployment_count(min_count: int, combat_only: bool = False) -> pd.DataFrame

# Education
qf.filter_by_education(min_level: str) -> pd.DataFrame  # "HS", "Some College", "Bachelor", etc.

# Time-based
qf.filter_by_tis_range(min_months: int, max_months: int) -> pd.DataFrame
qf.filter_by_tig_range(min_months: int, max_months: int) -> pd.DataFrame
```

### Advanced Filtering
```python
# Single criterion
criterion = FilterCriterion(
    field: str,         # "acft_score", "ranger", "paygrade", etc.
    operator: str,      # "eq", "ne", "gt", "gte", "lt", "lte", "in"
    value: Any,         # Value to compare
    description: str = ""  # Optional description
)
results = qf.apply_criterion(criterion) -> pd.DataFrame

# Filter group (AND/OR logic)
group = FilterGroup(
    criteria: List[FilterCriterion],
    logic: str = "AND",  # "AND" or "OR"
    name: str = "",
    description: str = ""
)
results = qf.apply_filter_group(group) -> pd.DataFrame

# Multiple groups
results = qf.filter_with_multiple_groups(
    groups: List[FilterGroup],
    group_logic: str = "OR"  # How to combine groups
) -> pd.DataFrame
```

### Search Functions
```python
# By soldier ID
qf.search_by_soldier_id(soldier_id: int) -> pd.DataFrame

# Text search in qualification fields
qf.search_qualification_text(search_text: str) -> pd.DataFrame
```

### Statistics
```python
stats = qf.get_filter_statistics(filtered_df: pd.DataFrame) -> Dict

# Returns:
# {
#     'total_soldiers': int,
#     'filtered_count': int,
#     'filter_rate': float,
#     'avg_acft': float,
#     'avg_dwell': float,
#     'avg_tis': float,
#     'deployable_pct': float,
#     'ranks': Dict[str, int],
#     'mos_codes': Dict[str, int]
# }
```

---

## BilletRequirements

### Initialization
```python
req = BilletRequirements(
    # Basic info
    position_title: str,
    billet_id: Optional[str] = None,

    # Education
    min_education_level: Optional[str] = None,  # "HS", "Some College", "Bachelor", etc.
    preferred_education_level: Optional[str] = None,

    # Languages
    languages_required: List[LanguageRequirement] = [],

    # ASI/SQI
    asi_codes_required: List[str] = [],
    asi_codes_preferred: List[str] = [],
    sqi_codes_required: List[str] = [],
    sqi_codes_preferred: List[str] = [],

    # Badges
    badges_required: List[BadgeRequirement] = [],
    badges_preferred: List[BadgeRequirement] = [],

    # Licenses
    licenses_required: List[LicenseRequirement] = [],

    # Experience
    experience_required: List[ExperienceRequirement] = [],

    # Awards
    awards_required: List[str] = [],

    # Fitness & Medical
    min_acft_score: Optional[int] = None,
    max_body_fat_pct: Optional[float] = None,
    max_medical_category: Optional[int] = None,

    # Security
    security_clearance: Optional[str] = None,  # "SECRET", "TS", "TS/SCI"

    # Age & Time
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_tis_months: Optional[int] = None,
    min_tig_months: Optional[int] = None,

    # Other
    combat_experience_required: bool = False,
    deployment_count_required: Optional[int] = None,
    criticality: int = 1  # 1-4 (4 = most critical)
)
```

### Sub-requirements

**LanguageRequirement**
```python
LanguageRequirement(
    language_code: str,      # ISO 639-1 code ("ar", "fa", "zh", etc.)
    language_name: str,      # "Arabic", "Farsi", "Chinese"
    min_listening_level: int = 2,  # DLPT 0-5
    min_reading_level: int = 2,
    required: bool = True,   # False = preferred
    native_acceptable: bool = True
)
```

**BadgeRequirement**
```python
BadgeRequirement(
    badge_name: str,         # "AIRBORNE", "RANGER", "AIR_ASSAULT", etc.
    required: bool = True,   # False = preferred
    alternative_badges: List[str] = []  # Acceptable alternatives
)
```

**ExperienceRequirement**
```python
ExperienceRequirement(
    description: str,        # Freeform description
    min_months: Optional[int] = None,
    position_type: Optional[str] = None,
    theater: Optional[str] = None,  # "CENTCOM", "INDOPACOM", etc.
    combat: bool = False
)
```

### Methods
```python
# Serialize
req_dict = req.to_dict() -> Dict

# Deserialize
req = BilletRequirements.from_dict(data: Dict)

# Human-readable summary
summary = req.get_summary() -> str
```

### Pre-built Templates
```python
# 7 templates available
BilletRequirementTemplates.ranger_qualified_infantry_leader() -> BilletRequirements
BilletRequirementTemplates.intelligence_analyst_strategic_language() -> BilletRequirements
BilletRequirementTemplates.special_forces_comms_sergeant() -> BilletRequirements
BilletRequirementTemplates.combat_medic_instructor() -> BilletRequirements
BilletRequirementTemplates.logistics_operations_chief() -> BilletRequirements
BilletRequirementTemplates.airborne_infantry_rifleman() -> BilletRequirements
BilletRequirementTemplates.signal_support_specialist() -> BilletRequirements

# Helper function
create_basic_requirements(
    position_title: str,
    min_education: str = "HS",
    badges: List[str] = [],
    combat_required: bool = False,
    min_deployments: int = 0
) -> BilletRequirements
```

---

## EMD (Enhanced)

### Qualification Policy Parameters

```python
# Access policies
emd = EMD(soldiers_df, billets_df)
emd.policies  # Dict of all parameters

# Education (2 params)
"education_mismatch_penalty": 1000
"education_exceed_bonus": -100

# Languages (4 params)
"language_proficiency_penalty": 2000
"language_native_bonus": -200
"any_language_bonus": -150
"language_preferred_bonus": -100

# ASI/SQI (4 params)
"asi_missing_penalty": 1500
"asi_preferred_bonus": -200
"sqi_missing_penalty": 2500
"sqi_preferred_bonus": -300

# Badges (5 params)
"badge_missing_penalty": 1200
"badge_alternative_penalty": 400
"badge_preferred_bonus": -150
"ranger_bonus": -300
"airborne_bonus": -200
"combat_badge_bonus": -250

# Licenses (2 params)
"license_missing_penalty": 800
"license_preferred_bonus": -100

# Experience (5 params)
"combat_experience_bonus": -400
"deployment_count_bonus": -100
"theater_experience_bonus": -200
"leadership_experience_bonus": -200
"experience_mismatch_penalty": 600

# Awards (2 params)
"award_missing_penalty": 500
"high_award_bonus": -300

# Medical/Fitness (2 params)
"medical_category_penalty": 1000
"acft_below_requirement_penalty": 800

# Availability (2 params)
"tis_below_requirement_penalty": 1000
"tig_below_requirement_penalty": 800

# Special (2 params)
"perfect_match_bonus": -1000
"critical_qual_missing_penalty": 5000
```

### Tune Policies
```python
emd.tune_policy(
    education_mismatch_penalty=1500,
    language_proficiency_penalty=3000,
    badge_missing_penalty=1200,
    # ... any policy parameter
)
```

### New Method
```python
# Apply qualification penalties to cost matrix
enhanced_matrix = emd.apply_qualification_penalties(
    cost_matrix: np.ndarray
) -> np.ndarray
```

### Enhanced assign()
```python
# Automatically applies qualification penalties
assignments, summary = emd.assign(mission_name: str = "default")

# Summary may include:
# - 'qual_penalty_avg': float
# - 'match_quality': Dict[str, int]
# - 'top_requirements': List[str]
```

---

## Profile Utilities

### Language Functions
```python
from profile_utils import *

# Get languages for a soldier
langs = get_languages(profile: SoldierProfileExtended) -> List[LanguageProficiency]

# Language distribution
lang_dist = get_language_distribution(
    soldiers_df: pd.DataFrame
) -> Dict[str, int]

# Check if has language
has_lang = has_language(
    soldier_row: pd.Series,
    language_code: str,
    min_level: int = 2
) -> bool

# Check any language
has_any = has_any_language(
    soldier_row: pd.Series,
    min_level: int = 2
) -> bool
```

### Badge Functions
```python
# Get badges
badges = get_badges(profile: SoldierProfileExtended) -> List[MilitaryBadge]

# Badge distribution
badge_dist = get_badge_distribution(
    profiles: List[SoldierProfileExtended]
) -> Dict[str, int]

# Check badge
has_it = has_badge(soldier_row: pd.Series, badge_name: str) -> bool

# Combat badges
has_combat = has_combat_badge(soldier_row: pd.Series) -> bool
```

### Experience Functions
```python
# Deployments
deployments = get_deployments(profile: SoldierProfileExtended) -> List[DeploymentRecord]

# Deployment count
count = get_deployment_count(
    profile: SoldierProfileExtended,
    combat_only: bool = False
) -> int

# Combat experience
has_combat = has_combat_experience(profile: SoldierProfileExtended) -> bool

# Theater experience
has_theater = has_theater_experience(
    profile: SoldierProfileExtended,
    theater: str  # "CENTCOM", "INDOPACOM", etc.
) -> bool

# Deployment statistics
stats = get_deployment_statistics(
    profiles: List[SoldierProfileExtended]
) -> Dict
```

### Education Functions
```python
# Education level value (for comparison)
level_val = get_education_level_value(soldier_row: pd.Series) -> int

# Check minimum education
meets_req = has_minimum_education(
    soldier_row: pd.Series,
    min_level: str  # "HS", "Bachelor", etc.
) -> bool

# Education distribution
edu_dist = get_education_distribution(
    soldiers_df: pd.DataFrame
) -> Dict[str, int]

# Filter by education
filtered = filter_by_education(
    soldiers_df: pd.DataFrame,
    soldiers_ext: Dict[int, SoldierProfileExtended],
    min_level: str
) -> pd.DataFrame
```

### Summary Functions
```python
# Generate qualification summary
summary = generate_qualification_summary(
    profile: SoldierProfileExtended
) -> str

# Short summary
short = generate_short_summary(profile: SoldierProfileExtended) -> str

# Print to console
print_profile_summary(profile: SoldierProfileExtended)
```

### Validation Functions
```python
# Validate DataFrame schema
is_valid = validate_dataframe_schema(
    df: pd.DataFrame,
    required_columns: List[str]
) -> bool

# Validate profile data
is_valid = validate_profile_data(profile: SoldierProfileExtended) -> bool

# Print DataFrame statistics
print_dataframe_statistics(df: pd.DataFrame, name: str = "DataFrame")
```

---

## Common Patterns

### Pattern 1: Filter → Assign
```python
# Filter qualified soldiers
qf = QualificationFilter(all_soldiers_df)
qualified = qf.apply_preset("fully_deployable")

# Use only qualified soldiers
emd = EMD(soldiers_df=qualified, billets_df=billets_df)
assignments, summary = emd.assign()
```

### Pattern 2: Progressive Requirements
```python
# Try strict requirements first
strict_req = BilletRequirements(
    min_education_level="Bachelor",
    min_acft_score=540,
    combat_experience_required=True
)

# If not enough, relax to preferred
relaxed_req = BilletRequirements(
    preferred_education_level="Bachelor",  # Not required
    min_acft_score=500,  # Lower threshold
    combat_experience_required=False
)
```

### Pattern 3: Multi-Group Filtering
```python
# Find soldiers matching ANY of these profiles
profiles = [
    build_ranger_filter(),
    build_high_performer_filter(),
    FilterGroup(criteria=[...], logic="AND", name="Custom")
]

results = qf.filter_with_multiple_groups(profiles, group_logic="OR")
```

---

## Enumerations

### Education Levels
```python
from soldier_profile_extended import EducationLevel

EducationLevel.LESS_THAN_HS      # 0
EducationLevel.HIGH_SCHOOL       # 1
EducationLevel.SOME_COLLEGE      # 2
EducationLevel.ASSOCIATE         # 3
EducationLevel.BACHELOR          # 4
EducationLevel.MASTER            # 5
EducationLevel.PROFESSIONAL      # 6
EducationLevel.DOCTORATE         # 7
```

### DLPT Levels
```python
from soldier_profile_extended import DLPTLevel

DLPTLevel.LEVEL_0  # No proficiency
DLPTLevel.LEVEL_1  # Elementary
DLPTLevel.LEVEL_2  # Limited working
DLPTLevel.LEVEL_3  # Professional working
DLPTLevel.LEVEL_4  # Full professional
DLPTLevel.LEVEL_5  # Native or bilingual
```

### Badge Types
```python
from soldier_profile_extended import BadgeType

BadgeType.AIRBORNE
BadgeType.RANGER
BadgeType.AIR_ASSAULT
BadgeType.PATHFINDER
BadgeType.SAPPER
# ... more available
```

---

## Error Handling

All functions handle missing data gracefully:

```python
# Safe to call even if extended profiles don't exist
qf = QualificationFilter(soldiers_df)  # Works with basic or extended
results = qf.filter_by_badge("RANGER")  # Returns empty if no badge column

# Safe to use with None values
has_badge(soldier_row, "RANGER")  # Returns False if badge column missing
```

---

## Performance Tips

1. **Filter before creating QualificationFilter** if dataset is large
2. **Use preset filters** - they're optimized
3. **Chain filters progressively** rather than one complex group
4. **Tune policy parameters** to avoid excessive penalties

---

**For complete examples, see:**
- `TUTORIAL.md` - Step-by-step walkthrough
- `README_QUALIFICATION_SYSTEM.md` - Full documentation
- `test_*.py` - Working code examples

**Quick Help:**
```bash
python validate_system.py      # System health check
python run_all_tests.py --quick  # Run tests
streamlit run dashboard.py     # Launch UI
```
