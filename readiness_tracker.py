"""
readiness_tracker.py
--------------------

Training status and readiness validation system.

Tracks training currency, equipment qualifications, deployment history, and
validates soldier readiness for assignment based on exercise requirements.

Classes:
- ReadinessProfile: Defines training requirements for a mission/exercise
- ReadinessValidator: Validates soldier readiness against requirements
- ReadinessAnalyzer: Provides aggregate readiness reporting for units
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

from unit_types import SoldierExtended, TrainingGate, Equipment, DeploymentRecord, Unit


@dataclass
class ReadinessProfile:
    """
    Defines training and qualification requirements for a mission or exercise.

    Example: A Pacific deployment might require SERE, passport, and specific clearances.
    """
    profile_name: str

    # Required training gates (must be current)
    required_training: List[str] = field(default_factory=list)

    # Required equipment qualifications
    required_equipment: List[str] = field(default_factory=list)

    # Minimum dwell time (months since last deployment)
    min_dwell_months: int = 0

    # Maximum deployment count (career limit check)
    max_deployment_count: Optional[int] = None

    # Medical/dental category requirements
    max_med_cat: int = 2  # Must be C1 or C2
    max_dental_cat: int = 2

    # Additional flags
    require_passport: bool = False
    require_covid_vaccination: bool = False

    # Scoring preferences (not hard requirements, but weighted in optimization)
    prefer_deployment_experience: bool = False
    prefer_high_acft: bool = False
    prefer_marksmanship: bool = False


class ReadinessValidator:
    """
    Validates soldier readiness against a ReadinessProfile.

    Provides detailed pass/fail analysis with reasons.
    """

    @staticmethod
    def validate_soldier(
        soldier_row: pd.Series,
        soldier_ext: Optional[SoldierExtended],
        profile: ReadinessProfile,
        as_of_date: Optional[date] = None
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a soldier against a readiness profile.

        Args:
            soldier_row: DataFrame row from EMD.soldiers
            soldier_ext: Extended soldier data (if available)
            profile: ReadinessProfile to validate against
            as_of_date: Date to validate against (default: today)

        Returns:
            (is_ready, passes, failures)
            - is_ready: True if all requirements met
            - passes: List of requirements passed
            - failures: List of requirements failed with reasons
        """
        check_date = as_of_date or date.today()
        passes = []
        failures = []

        # Medical/dental category
        if soldier_row["med_cat"] <= profile.max_med_cat:
            passes.append(f"Medical: C{soldier_row['med_cat']}")
        else:
            failures.append(f"Medical: C{soldier_row['med_cat']} exceeds max C{profile.max_med_cat}")

        if soldier_row["dental_cat"] <= profile.max_dental_cat:
            passes.append(f"Dental: C{soldier_row['dental_cat']}")
        else:
            failures.append(f"Dental: C{soldier_row['dental_cat']} exceeds max C{profile.max_dental_cat}")

        # Deployability
        if soldier_row["deployable"] == 1:
            passes.append("Deployable")
        else:
            failures.append("Non-deployable status")

        # Dwell time
        if soldier_row["dwell_months"] >= profile.min_dwell_months:
            passes.append(f"Dwell: {soldier_row['dwell_months']} months")
        else:
            failures.append(f"Dwell: {soldier_row['dwell_months']} months < {profile.min_dwell_months} required")

        # Extended validation (if available)
        if soldier_ext:
            # Training gates
            for gate_name in profile.required_training:
                if gate_name in soldier_ext.training_gates:
                    gate = soldier_ext.training_gates[gate_name]
                    if gate.is_current(check_date):
                        passes.append(f"Training: {gate_name} current")
                    else:
                        days_expired = -gate.days_until_expiry(check_date)
                        failures.append(f"Training: {gate_name} expired {days_expired} days ago")
                else:
                    failures.append(f"Training: {gate_name} not completed")

            # Equipment qualifications
            required_equipment = getattr(profile, 'required_equipment', [])
            for eq_type in required_equipment:
                qualified = any(
                    eq.equipment_type == eq_type and eq.is_valid(check_date)
                    for eq in soldier_ext.equipment_quals
                )
                if qualified:
                    passes.append(f"Equipment: {eq_type} qualified")
                else:
                    failures.append(f"Equipment: {eq_type} not qualified or expired")

            # Deployment history
            max_deployment_count = getattr(profile, 'max_deployment_count', None)
            if max_deployment_count is not None:
                dep_count = len(soldier_ext.deployment_history)
                if dep_count <= max_deployment_count:
                    passes.append(f"Deployments: {dep_count}/{max_deployment_count}")
                else:
                    failures.append(f"Deployments: {dep_count} exceeds max {max_deployment_count}")

        is_ready = len(failures) == 0
        return is_ready, passes, failures

    @staticmethod
    def calculate_readiness_score(
        soldier_row: pd.Series,
        soldier_ext: Optional[SoldierExtended],
        profile: ReadinessProfile
    ) -> float:
        """
        Calculate a readiness score (0.0-1.0) based on profile preferences.

        This is separate from hard validation - it's for optimization weighting.
        """
        score = 0.5  # Base score

        # Deployment experience
        if profile.prefer_deployment_experience and soldier_ext:
            if len(soldier_ext.deployment_history) > 0:
                score += 0.15

        # ACFT score
        if profile.prefer_high_acft:
            acft = soldier_row.get("acft_score", 0)
            if acft >= 500:
                score += 0.15
            elif acft >= 450:
                score += 0.10

        # Marksmanship
        if profile.prefer_marksmanship:
            m4_score = soldier_row.get("m4_score", 0)
            if m4_score >= 38:  # Expert
                score += 0.15
            elif m4_score >= 36:  # Sharpshooter
                score += 0.10

        # Training currency (all gates current)
        if soldier_ext:
            all_current = all(
                gate.is_current() for gate in soldier_ext.training_gates.values()
            )
            if all_current:
                score += 0.05

        return min(score, 1.0)


class ReadinessAnalyzer:
    """
    Provides aggregate readiness reporting for units and soldier pools.
    """

    @staticmethod
    def unit_readiness_summary(
        unit: Unit,
        soldiers_df: pd.DataFrame,
        soldiers_ext: Dict[int, SoldierExtended],
        profile: ReadinessProfile
    ) -> Dict:
        """
        Generate a readiness summary for a unit against a profile.

        Returns:
            Dict with readiness metrics (ready_count, ready_pct, failures_by_type, etc.)
        """
        # Filter soldiers in this unit
        unit_soldiers = soldiers_df[soldiers_df["uic"] == unit.uic]

        ready_count = 0
        failure_counts = {}

        for idx, soldier_row in unit_soldiers.iterrows():
            soldier_id = soldier_row["soldier_id"]
            soldier_ext = soldiers_ext.get(soldier_id)

            is_ready, passes, failures = ReadinessValidator.validate_soldier(
                soldier_row, soldier_ext, profile
            )

            if is_ready:
                ready_count += 1
            else:
                # Aggregate failure reasons
                for failure in failures:
                    category = failure.split(":")[0]  # e.g., "Medical", "Training"
                    failure_counts[category] = failure_counts.get(category, 0) + 1

        total = len(unit_soldiers)
        ready_pct = ready_count / total if total > 0 else 0.0

        return {
            "uic": unit.uic,
            "unit_name": unit.short_name,
            "total_soldiers": total,
            "ready_count": ready_count,
            "ready_pct": ready_pct,
            "not_ready_count": total - ready_count,
            "failure_counts": failure_counts,
            "c_rating": unit.c_rating,
        }

    @staticmethod
    def force_readiness_rollup(
        units: Dict[str, Unit],
        soldiers_df: pd.DataFrame,
        soldiers_ext: Dict[int, SoldierExtended],
        profile: ReadinessProfile
    ) -> pd.DataFrame:
        """
        Generate readiness summary for all units.

        Returns:
            DataFrame with columns: uic, unit_name, total, ready_count, ready_pct, etc.
        """
        summaries = []
        for uic, unit in units.items():
            summary = ReadinessAnalyzer.unit_readiness_summary(
                unit, soldiers_df, soldiers_ext, profile
            )
            summaries.append(summary)

        df = pd.DataFrame(summaries)
        return df.sort_values("ready_pct", ascending=False)

    @staticmethod
    def identify_training_gaps(
        soldiers_df: pd.DataFrame,
        soldiers_ext: Dict[int, SoldierExtended],
        profile: ReadinessProfile
    ) -> pd.DataFrame:
        """
        Identify specific training gaps across the force.

        Returns:
            DataFrame with columns: training_gate, expired_count, not_completed_count
        """
        gap_data = {gate: {"expired": 0, "not_completed": 0} for gate in profile.required_training}

        for soldier_id, soldier_ext in soldiers_ext.items():
            for gate_name in profile.required_training:
                if gate_name not in soldier_ext.training_gates:
                    gap_data[gate_name]["not_completed"] += 1
                elif not soldier_ext.training_gates[gate_name].is_current():
                    gap_data[gate_name]["expired"] += 1

        rows = []
        for gate, counts in gap_data.items():
            rows.append({
                "training_gate": gate,
                "expired_count": counts["expired"],
                "not_completed_count": counts["not_completed"],
                "total_gaps": counts["expired"] + counts["not_completed"]
            })

        df = pd.DataFrame(rows)
        return df.sort_values("total_gaps", ascending=False)


# -------------------------
# Standard readiness profiles
# -------------------------

class StandardProfiles:
    """Pre-defined readiness profiles for common mission types."""

    @staticmethod
    def conus_training() -> ReadinessProfile:
        """Basic CONUS training exercise."""
        return ReadinessProfile(
            profile_name="CONUS_Training",
            required_training=["weapons_qual", "pha"],
            required_equipment=[],
            min_dwell_months=0,
            max_med_cat=3,  # More permissive
            max_dental_cat=3,
            require_passport=False
        )

    @staticmethod
    def oconus_training() -> ReadinessProfile:
        """OCONUS training exercise (e.g., Pacific Pathways)."""
        return ReadinessProfile(
            profile_name="OCONUS_Training",
            required_training=["weapons_qual", "pha", "sere"],
            required_equipment=[],
            min_dwell_months=6,
            max_med_cat=2,
            max_dental_cat=2,
            require_passport=True,
            prefer_deployment_experience=True
        )

    @staticmethod
    def combat_deployment() -> ReadinessProfile:
        """Full deployment readiness."""
        return ReadinessProfile(
            profile_name="Combat_Deployment",
            required_training=["weapons_qual", "pha", "sere"],
            required_equipment=[],
            min_dwell_months=12,
            max_deployment_count=4,  # Career limit
            max_med_cat=2,
            max_dental_cat=2,
            require_passport=True,
            require_covid_vaccination=True,
            prefer_deployment_experience=True,
            prefer_high_acft=True,
            prefer_marksmanship=True
        )

    @staticmethod
    def pacific_exercise() -> ReadinessProfile:
        """USINDOPACOM exercise (Valiant Shield, Orient Shield, etc.)."""
        return ReadinessProfile(
            profile_name="Pacific_Exercise",
            required_training=["weapons_qual", "pha", "sere"],
            required_equipment=[],
            min_dwell_months=6,
            max_med_cat=2,
            max_dental_cat=2,
            require_passport=True,
            prefer_deployment_experience=False,
            prefer_high_acft=True
        )


def filter_ready_soldiers(
    soldiers_df: pd.DataFrame,
    soldiers_ext: Dict[int, SoldierExtended],
    profile: ReadinessProfile
) -> pd.DataFrame:
    """
    Filter soldiers DataFrame to only include those meeting readiness requirements.

    Returns:
        Filtered DataFrame with only ready soldiers
    """
    ready_ids = []

    for idx, soldier_row in soldiers_df.iterrows():
        soldier_id = soldier_row["soldier_id"]
        soldier_ext_rec = soldiers_ext.get(soldier_id)

        is_ready, _, _ = ReadinessValidator.validate_soldier(
            soldier_row, soldier_ext_rec, profile
        )

        if is_ready:
            ready_ids.append(soldier_id)

    return soldiers_df[soldiers_df["soldier_id"].isin(ready_ids)].copy()


def add_readiness_penalty(
    cost: float,
    soldier_row: pd.Series,
    soldier_ext: Optional[SoldierExtended],
    profile: ReadinessProfile,
    penalty_per_failure: float = 2000.0
) -> float:
    """
    Add cost penalty for readiness failures.

    Use this to integrate readiness validation into EMD cost function.
    """
    is_ready, _, failures = ReadinessValidator.validate_soldier(
        soldier_row, soldier_ext, profile
    )

    if not is_ready:
        cost += penalty_per_failure * len(failures)

    return cost
