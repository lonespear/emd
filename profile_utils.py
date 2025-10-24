"""
profile_utils.py
----------------

Utility functions for working with extended soldier profiles in DataFrames.

Provides helper functions for:
- Parsing JSON profile data from DataFrame columns
- Searching and filtering by qualifications
- Generating human-readable summaries
- Validating profile data integrity
- Analyzing qualification distributions

Used by dashboard, EMD agent, and other modules to work with extended profiles.
"""

import json
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import date, datetime

# Import profile data structures
try:
    from soldier_profile_extended import (
        SoldierProfileExtended, EducationLevel, DLPTLevel,
        COMMON_ASI_CODES, COMMON_SQI_CODES, COMMON_LANGUAGES,
        COMMON_BADGES, COMMON_AWARDS
    )
    EXTENDED_PROFILES_AVAILABLE = True
except ImportError:
    EXTENDED_PROFILES_AVAILABLE = False


# ============================================================================
# JSON Parsing Helpers
# ============================================================================

def parse_json_field(value: Any, default: Any = None) -> Any:
    """
    Safely parse a JSON field from a DataFrame.

    Handles:
    - None/NaN values -> returns default
    - Already parsed objects -> returns as-is
    - JSON strings -> parses and returns
    - Invalid JSON -> returns default

    Args:
        value: Value from DataFrame column
        default: Default value if parsing fails

    Returns:
        Parsed object or default
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default if default is not None else []

    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default if default is not None else []

    return default if default is not None else []


def get_languages(soldier_row: pd.Series) -> List[Dict]:
    """Extract language proficiencies from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('languages_json'), [])


def get_asi_codes(soldier_row: pd.Series) -> List[Dict]:
    """Extract ASI codes from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('asi_codes_json'), [])


def get_sqi_codes(soldier_row: pd.Series) -> List[Dict]:
    """Extract SQI codes from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('sqi_codes_json'), [])


def get_badges(soldier_row: pd.Series) -> List[Dict]:
    """Extract badges from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('badges_json'), [])


def get_awards(soldier_row: pd.Series) -> List[Dict]:
    """Extract awards from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('awards_json'), [])


def get_licenses(soldier_row: pd.Series) -> List[Dict]:
    """Extract civilian licenses from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('licenses_json'), [])


def get_deployments(soldier_row: pd.Series) -> List[Dict]:
    """Extract deployment history from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('deployments_json'), [])


def get_duty_history(soldier_row: pd.Series) -> List[Dict]:
    """Extract duty station history from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('duty_history_json'), [])


# ============================================================================
# Qualification Checking Helpers
# ============================================================================

def has_language(soldier_row: pd.Series,
                 language_code: str,
                 min_level: int = 2) -> bool:
    """
    Check if soldier has a specific language at minimum proficiency.

    Args:
        soldier_row: Soldier DataFrame row
        language_code: ISO 639-1 language code (e.g., 'AR', 'ES', 'KO')
        min_level: Minimum DLPT level (0-5, default 2 for "Limited Working")

    Returns:
        True if soldier has language at required level
    """
    languages = get_languages(soldier_row)
    for lang in languages:
        if lang.get('language_code') == language_code:
            listening = lang.get('listening_level', 0)
            reading = lang.get('reading_level', 0)
            return listening >= min_level and reading >= min_level
    return False


def has_any_language(soldier_row: pd.Series, min_level: int = 2) -> bool:
    """Check if soldier has any foreign language at minimum proficiency."""
    languages = get_languages(soldier_row)
    for lang in languages:
        listening = lang.get('listening_level', 0)
        reading = lang.get('reading_level', 0)
        if listening >= min_level and reading >= min_level:
            return True
    return False


def has_asi(soldier_row: pd.Series, asi_code: str) -> bool:
    """
    Check if soldier has a specific ASI.

    Args:
        soldier_row: Soldier DataFrame row
        asi_code: 2-character ASI code (e.g., 'B4', 'K3', 'L9')

    Returns:
        True if soldier has the ASI
    """
    asis = get_asi_codes(soldier_row)
    for asi in asis:
        if asi.get('code') == asi_code:
            # Check if not expired
            exp_date = asi.get('expiration_date')
            if exp_date is None:
                return True
            # Parse date if string
            if isinstance(exp_date, str):
                exp_date = datetime.fromisoformat(exp_date).date()
            return exp_date >= date.today()
    return False


def has_sqi(soldier_row: pd.Series, sqi_code: str) -> bool:
    """
    Check if soldier has a specific SQI.

    Args:
        soldier_row: Soldier DataFrame row
        sqi_code: 1-character SQI code (e.g., 'V', 'W', 'X', 'Y')

    Returns:
        True if soldier has the SQI
    """
    sqis = get_sqi_codes(soldier_row)
    return any(sqi.get('code') == sqi_code for sqi in sqis)


def has_badge(soldier_row: pd.Series, badge_code: str) -> bool:
    """
    Check if soldier has a specific badge.

    Args:
        soldier_row: Soldier DataFrame row
        badge_code: Badge code (e.g., 'AIRBORNE', 'RANGER', 'CIB', 'EFMB')

    Returns:
        True if soldier has the badge
    """
    badges = get_badges(soldier_row)
    return any(badge.get('code') == badge_code for badge in badges)


def has_award(soldier_row: pd.Series, award_type: str) -> bool:
    """
    Check if soldier has a specific award type.

    Args:
        soldier_row: Soldier DataFrame row
        award_type: Award type (e.g., 'BSM', 'ARCOM', 'AAM', 'MSM')

    Returns:
        True if soldier has the award
    """
    awards = get_awards(soldier_row)
    return any(award.get('award_type') == award_type for award in awards)


def has_combat_badge(soldier_row: pd.Series) -> bool:
    """Check if soldier has any combat badge (CIB, CAB, CMB, etc.)."""
    badges = get_badges(soldier_row)
    combat_badges = {'CIB', 'CAB', 'CMB', 'CIB_2', 'CIB_3'}
    return any(badge.get('code') in combat_badges for badge in badges)


def has_combat_experience(soldier_row: pd.Series) -> bool:
    """Check if soldier has combat deployment experience."""
    deployments = get_deployments(soldier_row)
    return any(deploy.get('combat_deployment', False) for deploy in deployments)


def get_deployment_count(soldier_row: pd.Series,
                        combat_only: bool = False) -> int:
    """
    Count soldier's deployments.

    Args:
        soldier_row: Soldier DataFrame row
        combat_only: If True, only count combat deployments

    Returns:
        Number of deployments
    """
    deployments = get_deployments(soldier_row)
    if combat_only:
        return sum(1 for d in deployments if d.get('combat_deployment', False))
    return len(deployments)


def has_theater_experience(soldier_row: pd.Series, theater: str) -> bool:
    """
    Check if soldier has deployment experience in a specific theater.

    Args:
        soldier_row: Soldier DataFrame row
        theater: Theater name (e.g., 'CENTCOM', 'EUCOM', 'INDOPACOM')

    Returns:
        True if soldier deployed to theater
    """
    deployments = get_deployments(soldier_row)
    return any(deploy.get('theater') == theater for deploy in deployments)


def get_education_level_value(soldier_row: pd.Series) -> int:
    """
    Get numeric value of education level for comparisons.

    Returns:
        0=None, 1=GED, 2=HS, 3=SOME_COLLEGE, 4=AA, 5=BA, 6=MA, 7=PHD
    """
    edu = soldier_row.get('education_level', 'HS')
    if isinstance(edu, str):
        edu_map = {
            'NONE': 0, 'GED': 1, 'HS': 2, 'SOME_COLLEGE': 3,
            'AA': 4, 'BA': 5, 'MA': 6, 'PHD': 7, 'PROFESSIONAL': 7
        }
        return edu_map.get(edu, 2)
    return 2  # Default to HS


def has_minimum_education(soldier_row: pd.Series,
                         min_level: str = 'HS') -> bool:
    """
    Check if soldier meets minimum education requirement.

    Args:
        soldier_row: Soldier DataFrame row
        min_level: Minimum education level (e.g., 'HS', 'BA', 'MA')

    Returns:
        True if soldier meets or exceeds requirement
    """
    edu_map = {
        'NONE': 0, 'GED': 1, 'HS': 2, 'SOME_COLLEGE': 3,
        'AA': 4, 'BA': 5, 'MA': 6, 'PHD': 7, 'PROFESSIONAL': 7
    }
    soldier_level = get_education_level_value(soldier_row)
    required_level = edu_map.get(min_level, 2)
    return soldier_level >= required_level


# ============================================================================
# Profile Summary Generators
# ============================================================================

def generate_qualification_summary(soldier_row: pd.Series) -> str:
    """
    Generate human-readable qualification summary for a soldier.

    Returns:
        Multi-line string with soldier qualifications
    """
    lines = []

    # Basic info
    soldier_id = soldier_row.get('soldier_id', 'Unknown')
    rank = soldier_row.get('paygrade', 'Unknown')
    mos = soldier_row.get('mos', 'Unknown')
    lines.append(f"Soldier {soldier_id}: {rank} {mos}")

    # Education
    edu = soldier_row.get('education_level', 'HS')
    lines.append(f"  Education: {edu}")

    # Languages
    languages = get_languages(soldier_row)
    if languages:
        lang_str = ", ".join([
            f"{lang.get('language_name', 'Unknown')} "
            f"(L{lang.get('listening_level', 0)}/R{lang.get('reading_level', 0)})"
            for lang in languages
        ])
        lines.append(f"  Languages: {lang_str}")

    # ASIs
    asis = get_asi_codes(soldier_row)
    if asis:
        asi_str = ", ".join([asi.get('code', '??') for asi in asis])
        lines.append(f"  ASIs: {asi_str}")

    # SQIs
    sqis = get_sqi_codes(soldier_row)
    if sqis:
        sqi_str = ", ".join([sqi.get('code', '?') for sqi in sqis])
        lines.append(f"  SQIs: {sqi_str}")

    # Badges
    badges = get_badges(soldier_row)
    if badges:
        badge_str = ", ".join([badge.get('code', 'Unknown') for badge in badges])
        lines.append(f"  Badges: {badge_str}")

    # Awards
    awards = get_awards(soldier_row)
    if awards:
        lines.append(f"  Awards: {len(awards)} total")

    # Deployments
    deployments = get_deployments(soldier_row)
    if deployments:
        combat_count = sum(1 for d in deployments if d.get('combat_deployment', False))
        lines.append(f"  Deployments: {len(deployments)} total ({combat_count} combat)")

    # TIS/TIG
    tis = soldier_row.get('time_in_service_months', 0)
    tig = soldier_row.get('time_in_grade_months', 0)
    if tis > 0:
        lines.append(f"  TIS: {tis} months, TIG: {tig} months")

    return "\n".join(lines)


def generate_short_summary(soldier_row: pd.Series) -> str:
    """
    Generate brief one-line qualification summary.

    Returns:
        Single-line summary string
    """
    parts = []

    # Languages
    languages = get_languages(soldier_row)
    if languages:
        parts.append(f"{len(languages)} lang")

    # Badges
    badges = get_badges(soldier_row)
    if badges:
        parts.append(f"{len(badges)} badge")

    # Deployments
    deploy_count = get_deployment_count(soldier_row, combat_only=True)
    if deploy_count > 0:
        parts.append(f"{deploy_count} deploy")

    # Education
    edu = soldier_row.get('education_level', 'HS')
    if edu not in ['HS', 'GED', 'NONE']:
        parts.append(edu)

    return ", ".join(parts) if parts else "Standard qualifications"


# ============================================================================
# DataFrame Filtering Functions
# ============================================================================

def filter_by_language(df: pd.DataFrame,
                      language_code: str,
                      min_level: int = 2) -> pd.DataFrame:
    """
    Filter DataFrame to soldiers with specific language proficiency.

    Args:
        df: Soldiers DataFrame
        language_code: ISO 639-1 language code
        min_level: Minimum DLPT level

    Returns:
        Filtered DataFrame
    """
    mask = df.apply(lambda row: has_language(row, language_code, min_level), axis=1)
    return df[mask]


def filter_by_asi(df: pd.DataFrame, asi_code: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with specific ASI."""
    mask = df.apply(lambda row: has_asi(row, asi_code), axis=1)
    return df[mask]


def filter_by_sqi(df: pd.DataFrame, sqi_code: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with specific SQI."""
    mask = df.apply(lambda row: has_sqi(row, sqi_code), axis=1)
    return df[mask]


def filter_by_badge(df: pd.DataFrame, badge_code: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with specific badge."""
    mask = df.apply(lambda row: has_badge(row, badge_code), axis=1)
    return df[mask]


def filter_by_combat_experience(df: pd.DataFrame) -> pd.DataFrame:
    """Filter DataFrame to soldiers with combat deployment experience."""
    mask = df.apply(has_combat_experience, axis=1)
    return df[mask]


def filter_by_education(df: pd.DataFrame, min_level: str = 'BA') -> pd.DataFrame:
    """Filter DataFrame to soldiers meeting minimum education."""
    mask = df.apply(lambda row: has_minimum_education(row, min_level), axis=1)
    return df[mask]


def filter_by_theater(df: pd.DataFrame, theater: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with experience in specific theater."""
    mask = df.apply(lambda row: has_theater_experience(row, theater), axis=1)
    return df[mask]


# ============================================================================
# Statistical Analysis Functions
# ============================================================================

def get_language_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get distribution of language proficiencies across DataFrame.

    Returns:
        Dictionary mapping language codes to soldier counts
    """
    lang_counts = {}

    for idx, row in df.iterrows():
        languages = get_languages(row)
        for lang in languages:
            code = lang.get('language_code', 'Unknown')
            lang_counts[code] = lang_counts.get(code, 0) + 1

    return dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True))


def get_badge_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of badges across DataFrame."""
    badge_counts = {}

    for idx, row in df.iterrows():
        badges = get_badges(row)
        for badge in badges:
            code = badge.get('code', 'Unknown')
            badge_counts[code] = badge_counts.get(code, 0) + 1

    return dict(sorted(badge_counts.items(), key=lambda x: x[1], reverse=True))


def get_asi_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of ASIs across DataFrame."""
    asi_counts = {}

    for idx, row in df.iterrows():
        asis = get_asi_codes(row)
        for asi in asis:
            code = asi.get('code', 'Unknown')
            asi_counts[code] = asi_counts.get(code, 0) + 1

    return dict(sorted(asi_counts.items(), key=lambda x: x[1], reverse=True))


def get_education_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of education levels across DataFrame."""
    if 'education_level' not in df.columns:
        return {}

    return df['education_level'].value_counts().to_dict()


def get_deployment_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get deployment statistics for DataFrame.

    Returns:
        Dictionary with deployment metrics
    """
    stats = {
        'total_soldiers': len(df),
        'soldiers_with_deployments': 0,
        'soldiers_with_combat': 0,
        'total_deployments': 0,
        'total_combat_deployments': 0,
        'avg_deployments_per_soldier': 0.0,
        'theaters': {}
    }

    for idx, row in df.iterrows():
        deployments = get_deployments(row)
        if deployments:
            stats['soldiers_with_deployments'] += 1
            stats['total_deployments'] += len(deployments)

            for deploy in deployments:
                if deploy.get('combat_deployment', False):
                    stats['total_combat_deployments'] += 1

                theater = deploy.get('theater', 'Unknown')
                stats['theaters'][theater] = stats['theaters'].get(theater, 0) + 1

        if has_combat_experience(row):
            stats['soldiers_with_combat'] += 1

    if stats['total_soldiers'] > 0:
        stats['avg_deployments_per_soldier'] = stats['total_deployments'] / stats['total_soldiers']

    return stats


def get_qualification_coverage(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate what percentage of soldiers have various qualifications.

    Returns:
        Dictionary mapping qualification types to percentages (0.0-1.0)
    """
    total = len(df)
    if total == 0:
        return {}

    coverage = {}

    # Language proficiency
    lang_count = sum(1 for _, row in df.iterrows() if has_any_language(row))
    coverage['any_language'] = lang_count / total

    # Combat experience
    combat_count = sum(1 for _, row in df.iterrows() if has_combat_experience(row))
    coverage['combat_experience'] = combat_count / total

    # Combat badges
    badge_count = sum(1 for _, row in df.iterrows() if has_combat_badge(row))
    coverage['combat_badge'] = badge_count / total

    # College education
    college_count = sum(1 for _, row in df.iterrows()
                       if has_minimum_education(row, 'SOME_COLLEGE'))
    coverage['some_college'] = college_count / total

    # Bachelor's degree
    ba_count = sum(1 for _, row in df.iterrows()
                  if has_minimum_education(row, 'BA'))
    coverage['bachelors'] = ba_count / total

    return coverage


# ============================================================================
# Validation Functions
# ============================================================================

def validate_profile_data(soldier_row: pd.Series) -> Tuple[bool, List[str]]:
    """
    Validate extended profile data for a soldier.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Check required fields exist
    required_fields = ['soldier_id', 'paygrade', 'mos', 'base']
    for field in required_fields:
        if field not in soldier_row or pd.isna(soldier_row.get(field)):
            errors.append(f"Missing required field: {field}")

    # Validate TIS/TIG if present
    tis = soldier_row.get('time_in_service_months', 0)
    tig = soldier_row.get('time_in_grade_months', 0)

    if tis < 0:
        errors.append(f"Invalid TIS: {tis} (must be >= 0)")
    if tig < 0:
        errors.append(f"Invalid TIG: {tig} (must be >= 0)")
    if tig > tis:
        errors.append(f"TIG ({tig}) cannot exceed TIS ({tis})")

    # Validate JSON fields can be parsed
    json_fields = ['languages_json', 'asi_codes_json', 'badges_json',
                  'awards_json', 'deployments_json']
    for field in json_fields:
        if field in soldier_row:
            try:
                parse_json_field(soldier_row[field], [])
            except Exception as e:
                errors.append(f"Invalid JSON in {field}: {e}")

    return (len(errors) == 0, errors)


def validate_dataframe_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame has expected extended profile schema.

    Returns:
        (is_valid, list_of_warnings)
    """
    warnings = []

    # Check for extended profile columns
    expected_columns = [
        'education_level', 'languages_json', 'asi_codes_json',
        'sqi_codes_json', 'badges_json', 'awards_json',
        'licenses_json', 'deployments_json', 'time_in_service_months'
    ]

    missing = []
    for col in expected_columns:
        if col not in df.columns:
            missing.append(col)

    if missing:
        warnings.append(f"Missing extended profile columns: {missing}")
        warnings.append("Extended profile features may not be available")

    return (len(warnings) == 0, warnings)


# ============================================================================
# Export/Import Helpers
# ============================================================================

def export_profile_to_dict(soldier_row: pd.Series) -> Dict[str, Any]:
    """
    Export soldier profile to a complete dictionary.

    Returns:
        Dictionary with all profile data (parsed JSON fields)
    """
    profile = {}

    # Basic fields
    for field in ['soldier_id', 'paygrade', 'mos', 'base', 'education_level',
                 'time_in_service_months', 'time_in_grade_months']:
        profile[field] = soldier_row.get(field)

    # Parse JSON fields
    profile['languages'] = get_languages(soldier_row)
    profile['asi_codes'] = get_asi_codes(soldier_row)
    profile['sqi_codes'] = get_sqi_codes(soldier_row)
    profile['badges'] = get_badges(soldier_row)
    profile['awards'] = get_awards(soldier_row)
    profile['licenses'] = get_licenses(soldier_row)
    profile['deployments'] = get_deployments(soldier_row)
    profile['duty_history'] = get_duty_history(soldier_row)

    return profile


# ============================================================================
# Convenience Functions
# ============================================================================

def print_profile_summary(soldier_row: pd.Series) -> None:
    """Print formatted profile summary to console."""
    print(generate_qualification_summary(soldier_row))


def print_dataframe_statistics(df: pd.DataFrame) -> None:
    """Print statistical summary of DataFrame qualifications."""
    print("="*80)
    print("EXTENDED PROFILE STATISTICS")
    print("="*80)
    print(f"\nTotal Soldiers: {len(df)}")

    # Education
    print("\nEducation Distribution:")
    edu_dist = get_education_distribution(df)
    for edu, count in sorted(edu_dist.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(df) * 100
        print(f"  {edu}: {count} ({pct:.1f}%)")

    # Languages
    print("\nTop Languages:")
    lang_dist = get_language_distribution(df)
    for lang, count in list(lang_dist.items())[:10]:
        pct = count / len(df) * 100
        print(f"  {lang}: {count} ({pct:.1f}%)")

    # Badges
    print("\nTop Badges:")
    badge_dist = get_badge_distribution(df)
    for badge, count in list(badge_dist.items())[:10]:
        pct = count / len(df) * 100
        print(f"  {badge}: {count} ({pct:.1f}%)")

    # Deployments
    print("\nDeployment Statistics:")
    deploy_stats = get_deployment_statistics(df)
    print(f"  Soldiers with deployments: {deploy_stats['soldiers_with_deployments']} "
          f"({deploy_stats['soldiers_with_deployments']/len(df)*100:.1f}%)")
    print(f"  Soldiers with combat: {deploy_stats['soldiers_with_combat']} "
          f"({deploy_stats['soldiers_with_combat']/len(df)*100:.1f}%)")
    print(f"  Avg deployments per soldier: {deploy_stats['avg_deployments_per_soldier']:.2f}")

    # Coverage
    print("\nQualification Coverage:")
    coverage = get_qualification_coverage(df)
    for qual, pct in coverage.items():
        print(f"  {qual}: {pct*100:.1f}%")

    print("="*80)
