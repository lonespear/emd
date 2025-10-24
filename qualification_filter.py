"""
qualification_filter.py
-----------------------

Advanced filtering and search for soldiers based on qualifications.

Provides powerful filtering capabilities for the dashboard:
- Multi-criteria filtering (AND/OR logic)
- Range-based filtering (TIS, ACFT scores, etc.)
- Set-based filtering (badges, ASIs, languages)
- Text search across qualification data
- Saved filter presets
- Filter combination and composition

Used by dashboard for soldier selection and billet matching analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import date

from profile_utils import (
    has_language, has_asi, has_sqi, has_badge, has_award,
    has_combat_experience, has_theater_experience,
    get_deployment_count, has_minimum_education,
    has_combat_badge, has_any_language,
    parse_json_field
)


@dataclass
class FilterCriterion:
    """
    A single filter criterion.

    Can be a simple comparison (e.g., ACFT >= 500) or a complex check
    (e.g., has language proficiency in Arabic at level 3).
    """
    field_name: str
    operator: str  # 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'in', 'contains', 'has', 'range'
    value: Any
    description: str = ""

    def __post_init__(self):
        if not self.description:
            self.description = f"{self.field_name} {self.operator} {self.value}"


@dataclass
class FilterGroup:
    """
    A group of filter criteria with AND/OR logic.

    Example:
        (ACFT >= 500 AND Airborne = True) OR (Ranger = True)
    """
    criteria: List[FilterCriterion] = field(default_factory=list)
    logic: str = "AND"  # 'AND' or 'OR'
    name: str = ""
    description: str = ""


class QualificationFilter:
    """
    Advanced filtering system for soldier qualifications.

    Provides flexible, composable filters for finding soldiers that meet
    specific qualification requirements.
    """

    def __init__(self, soldiers_df: pd.DataFrame):
        """
        Initialize filter with soldiers DataFrame.

        Args:
            soldiers_df: DataFrame with soldier data (including extended profiles)
        """
        self.soldiers = soldiers_df
        self.filter_groups: List[FilterGroup] = []
        self.preset_filters = self._initialize_presets()

    def _initialize_presets(self) -> Dict[str, FilterGroup]:
        """Initialize common preset filters."""
        presets = {}

        # Airborne qualified
        presets["airborne_qualified"] = FilterGroup(
            criteria=[FilterCriterion("airborne", "eq", 1)],
            name="Airborne Qualified",
            description="Soldiers with Airborne qualification"
        )

        # Ranger qualified
        presets["ranger_qualified"] = FilterGroup(
            criteria=[
                FilterCriterion("ranger", "eq", 1),
                FilterCriterion("airborne", "eq", 1)
            ],
            logic="AND",
            name="Ranger Qualified",
            description="Soldiers with Ranger Tab and Airborne"
        )

        # Combat veterans
        presets["combat_veteran"] = FilterGroup(
            criteria=[FilterCriterion("_has_combat_experience", "eq", True)],
            name="Combat Veteran",
            description="Soldiers with combat deployment experience"
        )

        # High fitness
        presets["high_fitness"] = FilterGroup(
            criteria=[
                FilterCriterion("acft_score", "gte", 500),
                FilterCriterion("body_composition_pass", "eq", 1)
            ],
            logic="AND",
            name="High Fitness",
            description="ACFT 500+ and passing body comp"
        )

        # NCO leadership
        presets["nco_leadership"] = FilterGroup(
            criteria=[
                FilterCriterion("paygrade", "in", ["E-5", "E-6", "E-7", "E-8"]),
                FilterCriterion("leadership_level", "gte", 2)
            ],
            logic="AND",
            name="NCO Leadership",
            description="NCOs with leadership experience"
        )

        # Language qualified
        presets["language_qualified"] = FilterGroup(
            criteria=[FilterCriterion("_has_any_language", "eq", True)],
            name="Language Qualified",
            description="Soldiers with foreign language proficiency"
        )

        # Fully deployable
        presets["fully_deployable"] = FilterGroup(
            criteria=[
                FilterCriterion("deployable", "eq", 1),
                FilterCriterion("med_cat", "lte", 2),
                FilterCriterion("dental_cat", "lte", 2),
                FilterCriterion("dwell_months", "gte", 12)
            ],
            logic="AND",
            name="Fully Deployable",
            description="Deployable with good medical/dental and sufficient dwell"
        )

        # Senior NCO
        presets["senior_nco"] = FilterGroup(
            criteria=[
                FilterCriterion("paygrade", "in", ["E-7", "E-8", "E-9"]),
                FilterCriterion("pme", "in", ["SLC", "USASMA"])
            ],
            logic="AND",
            name="Senior NCO",
            description="E-7 and above with PME"
        )

        # Special operations background
        presets["special_operations"] = FilterGroup(
            criteria=[
                FilterCriterion("ranger", "eq", 1),
            ],
            logic="OR",
            name="Special Operations Background",
            description="Ranger, SF, or high-speed qualified"
        )

        return presets

    # ========================================
    # Basic Filtering Methods
    # ========================================

    def filter_by_rank(self, ranks: List[str]) -> pd.DataFrame:
        """Filter soldiers by rank(s)."""
        return self.soldiers[self.soldiers['paygrade'].isin(ranks)]

    def filter_by_mos(self, mos_list: List[str]) -> pd.DataFrame:
        """Filter soldiers by MOS(s)."""
        return self.soldiers[self.soldiers['mos'].isin(mos_list)]

    def filter_by_base(self, bases: List[str]) -> pd.DataFrame:
        """Filter soldiers by home station(s)."""
        return self.soldiers[self.soldiers['base'].isin(bases)]

    def filter_by_clearance(self, min_clearance: str = "Secret") -> pd.DataFrame:
        """Filter soldiers by minimum clearance level."""
        clear_order = {"None": 0, "Secret": 1, "TS": 2}
        min_level = clear_order.get(min_clearance, 1)

        mask = self.soldiers['clearance'].apply(
            lambda x: clear_order.get(x, 0) >= min_level
        )
        return self.soldiers[mask]

    def filter_by_education(self, min_level: str = "HS") -> pd.DataFrame:
        """Filter soldiers by minimum education level."""
        if 'education_level' not in self.soldiers.columns:
            return self.soldiers

        mask = self.soldiers.apply(
            lambda row: has_minimum_education(row, min_level), axis=1
        )
        return self.soldiers[mask]

    def filter_by_acft_score(self, min_score: int = 450) -> pd.DataFrame:
        """Filter soldiers by minimum ACFT score."""
        return self.soldiers[self.soldiers['acft_score'] >= min_score]

    def filter_by_weapons_qual(self, min_score: int = 30) -> pd.DataFrame:
        """Filter soldiers by minimum weapons qualification."""
        return self.soldiers[self.soldiers['m4_score'] >= min_score]

    def filter_by_medical_category(self, max_category: int = 2) -> pd.DataFrame:
        """Filter soldiers by maximum medical category (1=best, 4=worst)."""
        return self.soldiers[self.soldiers['med_cat'] <= max_category]

    def filter_by_dwell(self, min_months: int = 12) -> pd.DataFrame:
        """Filter soldiers by minimum dwell time."""
        return self.soldiers[self.soldiers['dwell_months'] >= min_months]

    def filter_deployable(self) -> pd.DataFrame:
        """Filter to only deployable soldiers."""
        return self.soldiers[self.soldiers['deployable'] == 1]

    # ========================================
    # Qualification-based Filtering
    # ========================================

    def filter_by_language(self, language_code: str, min_level: int = 2) -> pd.DataFrame:
        """Filter soldiers with specific language proficiency."""
        mask = self.soldiers.apply(
            lambda row: has_language(row, language_code, min_level), axis=1
        )
        return self.soldiers[mask]

    def filter_has_any_language(self, min_level: int = 2) -> pd.DataFrame:
        """Filter soldiers with any foreign language proficiency."""
        mask = self.soldiers.apply(
            lambda row: has_any_language(row, min_level), axis=1
        )
        return self.soldiers[mask]

    def filter_by_asi(self, asi_code: str) -> pd.DataFrame:
        """Filter soldiers with specific ASI."""
        mask = self.soldiers.apply(lambda row: has_asi(row, asi_code), axis=1)
        return self.soldiers[mask]

    def filter_by_sqi(self, sqi_code: str) -> pd.DataFrame:
        """Filter soldiers with specific SQI."""
        mask = self.soldiers.apply(lambda row: has_sqi(row, sqi_code), axis=1)
        return self.soldiers[mask]

    def filter_by_badge(self, badge_code: str) -> pd.DataFrame:
        """Filter soldiers with specific badge."""
        mask = self.soldiers.apply(lambda row: has_badge(row, badge_code), axis=1)
        return self.soldiers[mask]

    def filter_combat_veterans(self) -> pd.DataFrame:
        """Filter soldiers with combat deployment experience."""
        mask = self.soldiers.apply(has_combat_experience, axis=1)
        return self.soldiers[mask]

    def filter_by_deployment_count(self, min_count: int = 1, combat_only: bool = False) -> pd.DataFrame:
        """Filter soldiers by minimum deployment count."""
        mask = self.soldiers.apply(
            lambda row: get_deployment_count(row, combat_only) >= min_count, axis=1
        )
        return self.soldiers[mask]

    def filter_by_theater_experience(self, theater: str) -> pd.DataFrame:
        """Filter soldiers with experience in specific theater."""
        mask = self.soldiers.apply(
            lambda row: has_theater_experience(row, theater), axis=1
        )
        return self.soldiers[mask]

    def filter_combat_badge_holders(self) -> pd.DataFrame:
        """Filter soldiers with combat badge (CIB, CAB, CMB)."""
        mask = self.soldiers.apply(has_combat_badge, axis=1)
        return self.soldiers[mask]

    # ========================================
    # Range-based Filtering
    # ========================================

    def filter_by_tis_range(self, min_months: int = 0, max_months: int = 999) -> pd.DataFrame:
        """Filter soldiers by time in service range."""
        if 'time_in_service_months' not in self.soldiers.columns:
            return self.soldiers

        return self.soldiers[
            (self.soldiers['time_in_service_months'] >= min_months) &
            (self.soldiers['time_in_service_months'] <= max_months)
        ]

    def filter_by_tig_range(self, min_months: int = 0, max_months: int = 999) -> pd.DataFrame:
        """Filter soldiers by time in grade range."""
        if 'time_in_grade_months' not in self.soldiers.columns:
            return self.soldiers

        return self.soldiers[
            (self.soldiers['time_in_grade_months'] >= min_months) &
            (self.soldiers['time_in_grade_months'] <= max_months)
        ]

    def filter_by_acft_range(self, min_score: int = 360, max_score: int = 600) -> pd.DataFrame:
        """Filter soldiers by ACFT score range."""
        return self.soldiers[
            (self.soldiers['acft_score'] >= min_score) &
            (self.soldiers['acft_score'] <= max_score)
        ]

    # ========================================
    # Advanced Filtering (Criterion-based)
    # ========================================

    def apply_criterion(self, criterion: FilterCriterion) -> pd.DataFrame:
        """Apply a single filter criterion."""
        field = criterion.field_name
        op = criterion.operator
        value = criterion.value

        # Handle special computed fields
        if field == "_has_combat_experience":
            mask = self.soldiers.apply(has_combat_experience, axis=1)
            return self.soldiers[mask] if value else self.soldiers[~mask]

        if field == "_has_any_language":
            mask = self.soldiers.apply(lambda row: has_any_language(row, 2), axis=1)
            return self.soldiers[mask] if value else self.soldiers[~mask]

        if field == "_has_combat_badge":
            mask = self.soldiers.apply(has_combat_badge, axis=1)
            return self.soldiers[mask] if value else self.soldiers[~mask]

        # Handle regular fields
        if field not in self.soldiers.columns:
            return self.soldiers  # Field doesn't exist, return all

        # Apply operator
        if op == "eq":
            return self.soldiers[self.soldiers[field] == value]
        elif op == "neq":
            return self.soldiers[self.soldiers[field] != value]
        elif op == "gt":
            return self.soldiers[self.soldiers[field] > value]
        elif op == "gte":
            return self.soldiers[self.soldiers[field] >= value]
        elif op == "lt":
            return self.soldiers[self.soldiers[field] < value]
        elif op == "lte":
            return self.soldiers[self.soldiers[field] <= value]
        elif op == "in":
            return self.soldiers[self.soldiers[field].isin(value)]
        elif op == "contains":
            mask = self.soldiers[field].astype(str).str.contains(str(value), case=False, na=False)
            return self.soldiers[mask]
        elif op == "range":
            min_val, max_val = value
            return self.soldiers[(self.soldiers[field] >= min_val) & (self.soldiers[field] <= max_val)]
        else:
            return self.soldiers

    def apply_filter_group(self, group: FilterGroup) -> pd.DataFrame:
        """Apply a filter group (multiple criteria with AND/OR logic)."""
        if not group.criteria:
            return self.soldiers

        if group.logic == "AND":
            # Start with all soldiers, then progressively filter
            result_indices = set(self.soldiers.index)

            for criterion in group.criteria:
                # Temporarily create a new filter with current result
                temp_filter = QualificationFilter(self.soldiers[self.soldiers.index.isin(result_indices)])
                filtered = temp_filter.apply_criterion(criterion)
                # Intersect with current results
                result_indices = result_indices.intersection(set(filtered.index))

            return self.soldiers[self.soldiers.index.isin(result_indices)]

        else:  # OR logic
            indices = set()
            for criterion in group.criteria:
                filtered = self.apply_criterion(criterion)
                indices.update(filtered.index)

            return self.soldiers[self.soldiers.index.isin(indices)]

    def apply_preset(self, preset_name: str) -> pd.DataFrame:
        """Apply a preset filter by name."""
        if preset_name not in self.preset_filters:
            return self.soldiers

        return self.apply_filter_group(self.preset_filters[preset_name])

    # ========================================
    # Complex Filtering (Multiple Groups)
    # ========================================

    def filter_with_multiple_groups(
        self,
        groups: List[FilterGroup],
        group_logic: str = "AND"
    ) -> pd.DataFrame:
        """
        Apply multiple filter groups with AND/OR logic between groups.

        Args:
            groups: List of FilterGroup objects
            group_logic: 'AND' or 'OR' - how to combine groups

        Returns:
            Filtered DataFrame
        """
        if not groups:
            return self.soldiers

        if group_logic == "AND":
            result = self.soldiers.copy()
            for group in groups:
                filtered = self.apply_filter_group(group)
                result = result[result.index.isin(filtered.index)]
            return result

        else:  # OR logic
            indices = set()
            for group in groups:
                filtered = self.apply_filter_group(group)
                indices.update(filtered.index)

            return self.soldiers[self.soldiers.index.isin(indices)]

    # ========================================
    # Search Functions
    # ========================================

    def search_by_soldier_id(self, soldier_id: int) -> pd.DataFrame:
        """Search for specific soldier by ID."""
        return self.soldiers[self.soldiers['soldier_id'] == soldier_id]

    def search_by_name_pattern(self, pattern: str) -> pd.DataFrame:
        """
        Search for soldiers by name pattern (if name field exists).

        Case-insensitive partial match.
        """
        if 'name' in self.soldiers.columns:
            mask = self.soldiers['name'].str.contains(pattern, case=False, na=False)
            return self.soldiers[mask]
        return pd.DataFrame()  # Empty if no name field

    def search_qualification_text(self, search_term: str) -> pd.DataFrame:
        """
        Search across all JSON qualification fields for text match.

        Searches in languages, ASIs, SQIs, badges, awards, licenses.
        """
        indices = set()

        json_fields = ['languages_json', 'asi_codes_json', 'sqi_codes_json',
                      'badges_json', 'awards_json', 'licenses_json']

        for field in json_fields:
            if field in self.soldiers.columns:
                for idx, value in self.soldiers[field].items():
                    if value and not pd.isna(value):
                        if search_term.lower() in str(value).lower():
                            indices.add(idx)

        return self.soldiers[self.soldiers.index.isin(indices)]

    # ========================================
    # Statistics and Analysis
    # ========================================

    def get_filter_statistics(self, filtered_df: pd.DataFrame) -> Dict[str, Any]:
        """Get statistics about filtered results."""
        total = len(self.soldiers)
        filtered = len(filtered_df)

        stats = {
            'total_soldiers': total,
            'filtered_count': filtered,
            'filter_rate': filtered / total if total > 0 else 0,
            'ranks': filtered_df['paygrade'].value_counts().to_dict() if filtered > 0 else {},
            'mos': filtered_df['mos'].value_counts().to_dict() if filtered > 0 else {},
            'bases': filtered_df['base'].value_counts().to_dict() if filtered > 0 else {},
        }

        if filtered > 0:
            stats['avg_acft'] = filtered_df['acft_score'].mean()
            stats['avg_dwell'] = filtered_df['dwell_months'].mean()
            stats['deployable_pct'] = (filtered_df['deployable'] == 1).sum() / filtered

        return stats

    def list_available_presets(self) -> List[str]:
        """List all available preset filter names."""
        return list(self.preset_filters.keys())

    def get_preset_description(self, preset_name: str) -> str:
        """Get description of a preset filter."""
        if preset_name in self.preset_filters:
            return self.preset_filters[preset_name].description
        return ""


# ============================================================================
# Helper Functions for Building Filters
# ============================================================================

def build_ranger_filter() -> FilterGroup:
    """Build filter for Ranger-qualified soldiers."""
    return FilterGroup(
        criteria=[
            FilterCriterion("ranger", "eq", 1),
            FilterCriterion("airborne", "eq", 1),
            FilterCriterion("_has_combat_experience", "eq", True)
        ],
        logic="AND",
        name="Ranger-Qualified Combat Veteran",
        description="Rangers with Airborne and combat experience"
    )


def build_language_filter(language_code: str, min_level: int = 2) -> FilterGroup:
    """Build filter for specific language proficiency."""
    return FilterGroup(
        criteria=[FilterCriterion(f"_has_language_{language_code}", "eq", True)],
        name=f"{language_code} Language Proficiency",
        description=f"Soldiers with {language_code} at level {min_level}+"
    )


def build_high_performer_filter() -> FilterGroup:
    """Build filter for high-performing soldiers."""
    return FilterGroup(
        criteria=[
            FilterCriterion("acft_score", "gte", 540),
            FilterCriterion("m4_score", "gte", 36),
            FilterCriterion("body_composition_pass", "eq", 1),
            FilterCriterion("med_cat", "eq", 1)
        ],
        logic="AND",
        name="High Performer",
        description="Top fitness and medical readiness"
    )


def build_ready_to_deploy_filter() -> FilterGroup:
    """Build filter for soldiers ready to deploy immediately."""
    return FilterGroup(
        criteria=[
            FilterCriterion("deployable", "eq", 1),
            FilterCriterion("med_cat", "lte", 2),
            FilterCriterion("dental_cat", "lte", 2),
            FilterCriterion("dwell_months", "gte", 12),
            FilterCriterion("available_from", "lte", date.today())
        ],
        logic="AND",
        name="Ready to Deploy",
        description="Deployable with good medical/dental, sufficient dwell, and available now"
    )
