"""
deployment_tracker.py
---------------------

Deployment window and OPTEMPO tracking for realistic unit availability.

Tracks:
- Current deployments (units unavailable)
- Recent deployments (high OPTEMPO, reduced readiness)
- Projected deployments (planning constraints)

Classes:
- DeploymentWindow: Represents a deployment period
- OPTEMPOTracker: Tracks operational tempo and availability
- AvailabilityAnalyzer: Determines which units can be sourced
"""

from __future__ import annotations
import pandas as pd
from datetime import date, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from unit_types import Unit


@dataclass
class DeploymentWindow:
    """
    Represents a unit deployment or unavailability window.

    Types:
    - deployment: Actual combat deployment
    - exercise: Training exercise (shorter, less impact)
    - maintenance: Unit in reset/train-up cycle
    - alert: On-call status (partially available)
    """
    unit_uic: str
    deployment_type: str  # "deployment", "exercise", "maintenance", "alert"
    location: str
    start_date: date
    end_date: date
    pct_available: float = 0.0  # 0.0 = fully deployed, 0.5 = 50% available

    mission_name: Optional[str] = None
    notes: str = ""

    def is_active(self, check_date: date) -> bool:
        """Check if deployment is active on given date."""
        return self.start_date <= check_date <= self.end_date

    def overlaps(self, start: date, end: date) -> bool:
        """Check if deployment overlaps with given date range."""
        return not (self.end_date < start or self.start_date > end)

    def duration_months(self) -> int:
        """Deployment duration in months."""
        return int((self.end_date - self.start_date).days / 30)


@dataclass
class OPTEMPOMetrics:
    """
    Operational tempo metrics for a unit.

    Tracks deployment history to assess readiness and availability.
    """
    unit_uic: str
    unit_name: str

    # Recent history (last 36 months)
    deployments_last_12_months: int = 0
    deployments_last_36_months: int = 0
    months_deployed_last_12: int = 0
    months_deployed_last_36: int = 0

    # Current status
    currently_deployed: bool = False
    current_deployment_location: Optional[str] = None
    months_since_last_deployment: int = 0

    # Projections
    next_deployment_date: Optional[date] = None
    available_for_tasking: bool = True
    optempo_rating: str = "Normal"  # "Low", "Normal", "High", "Critical"

    def calculate_optempo_rating(self) -> str:
        """
        Calculate OPTEMPO rating based on deployment history.

        Ratings:
        - Low: < 3 months deployed in last 12
        - Normal: 3-6 months deployed in last 12
        - High: 6-9 months deployed in last 12
        - Critical: > 9 months deployed in last 12
        """
        if self.currently_deployed:
            return "Critical"
        elif self.months_deployed_last_12 > 9:
            return "Critical"
        elif self.months_deployed_last_12 > 6:
            return "High"
        elif self.months_deployed_last_12 > 3:
            return "Normal"
        else:
            return "Low"


class OPTEMPOTracker:
    """
    Tracks deployment windows and calculates OPTEMPO metrics.
    """

    def __init__(self):
        self.deployment_windows: List[DeploymentWindow] = []

    def add_deployment(self, deployment: DeploymentWindow):
        """Add a deployment window."""
        self.deployment_windows.append(deployment)

    def add_standard_rotation(
        self,
        unit_uic: str,
        rotation_name: str,
        start_date: date,
        duration_months: int = 9,
        deployment_type: str = "deployment"
    ):
        """Add a standard deployment rotation."""
        end_date = start_date + timedelta(days=duration_months * 30)
        self.add_deployment(DeploymentWindow(
            unit_uic=unit_uic,
            deployment_type=deployment_type,
            location="OCONUS",
            start_date=start_date,
            end_date=end_date,
            mission_name=rotation_name
        ))

    def get_active_deployments(self, check_date: date = None) -> List[DeploymentWindow]:
        """Get all deployments active on given date."""
        check_date = check_date or date.today()
        return [d for d in self.deployment_windows if d.is_active(check_date)]

    def get_unit_availability(
        self,
        unit_uic: str,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Calculate unit availability percentage during given period.

        Returns:
            0.0-1.0 representing percentage available
        """
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return 1.0

        # Find overlapping deployments
        unavailable_days = 0
        for deployment in self.deployment_windows:
            if deployment.unit_uic != unit_uic:
                continue

            if deployment.overlaps(start_date, end_date):
                # Calculate overlap days
                overlap_start = max(deployment.start_date, start_date)
                overlap_end = min(deployment.end_date, end_date)
                overlap_days = (overlap_end - overlap_start).days + 1

                # Reduce by pct_available (e.g., if alert status = 50% available)
                unavailable_days += overlap_days * (1.0 - deployment.pct_available)

        availability = max(0.0, 1.0 - (unavailable_days / total_days))
        return availability

    def calculate_optempo_metrics(
        self,
        unit_uic: str,
        unit_name: str,
        as_of_date: date = None
    ) -> OPTEMPOMetrics:
        """Calculate OPTEMPO metrics for a unit."""
        as_of_date = as_of_date or date.today()

        metrics = OPTEMPOMetrics(unit_uic=unit_uic, unit_name=unit_name)

        # Get deployments for this unit
        unit_deployments = [d for d in self.deployment_windows if d.unit_uic == unit_uic]

        # Check current status
        active_deployments = [d for d in unit_deployments if d.is_active(as_of_date)]
        if active_deployments:
            metrics.currently_deployed = True
            metrics.current_deployment_location = active_deployments[0].location
        else:
            # Find most recent deployment
            past_deployments = [d for d in unit_deployments if d.end_date < as_of_date]
            if past_deployments:
                last_deployment = max(past_deployments, key=lambda d: d.end_date)
                days_since = (as_of_date - last_deployment.end_date).days
                metrics.months_since_last_deployment = int(days_since / 30)

        # Count recent deployments
        twelve_months_ago = as_of_date - timedelta(days=365)
        thirtysix_months_ago = as_of_date - timedelta(days=365 * 3)

        for deployment in unit_deployments:
            # Count deployments in last 12 months
            if deployment.end_date >= twelve_months_ago:
                metrics.deployments_last_12_months += 1
                # Calculate months deployed
                overlap_start = max(deployment.start_date, twelve_months_ago)
                overlap_end = min(deployment.end_date, as_of_date)
                if overlap_end >= overlap_start:
                    days = (overlap_end - overlap_start).days
                    metrics.months_deployed_last_12 += int(days / 30)

            # Count deployments in last 36 months
            if deployment.end_date >= thirtysix_months_ago:
                metrics.deployments_last_36_months += 1
                overlap_start = max(deployment.start_date, thirtysix_months_ago)
                overlap_end = min(deployment.end_date, as_of_date)
                if overlap_end >= overlap_start:
                    days = (overlap_end - overlap_start).days
                    metrics.months_deployed_last_36 += int(days / 30)

        # Determine availability
        metrics.available_for_tasking = not metrics.currently_deployed
        metrics.optempo_rating = metrics.calculate_optempo_rating()

        return metrics


class AvailabilityAnalyzer:
    """
    Analyzes unit availability and determines sourcing feasibility.
    """

    @staticmethod
    def filter_available_units(
        units: Dict[str, Unit],
        exercise_start: date,
        exercise_end: date,
        tracker: OPTEMPOTracker,
        min_availability: float = 0.75
    ) -> Dict[str, Unit]:
        """
        Filter units to only those available for the exercise period.

        Args:
            units: All units
            exercise_start: Exercise start date
            exercise_end: Exercise end date
            tracker: OPTEMPOTracker with deployment windows
            min_availability: Minimum availability (0.0-1.0)

        Returns:
            Dict of available units
        """
        available = {}

        for uic, unit in units.items():
            availability = tracker.get_unit_availability(uic, exercise_start, exercise_end)

            if availability >= min_availability:
                available[uic] = unit

        return available

    @staticmethod
    def get_optempo_report(
        units: Dict[str, Unit],
        tracker: OPTEMPOTracker,
        as_of_date: date = None
    ) -> pd.DataFrame:
        """Generate OPTEMPO report for all units."""
        as_of_date = as_of_date or date.today()

        rows = []
        for uic, unit in units.items():
            metrics = tracker.calculate_optempo_metrics(uic, unit.short_name, as_of_date)

            rows.append({
                "uic": uic,
                "unit_name": unit.short_name,
                "currently_deployed": metrics.currently_deployed,
                "location": metrics.current_deployment_location or "Home Station",
                "months_since_last": metrics.months_since_last_deployment,
                "deployments_12mo": metrics.deployments_last_12_months,
                "months_deployed_12mo": metrics.months_deployed_last_12,
                "optempo_rating": metrics.optempo_rating,
                "available": metrics.available_for_tasking
            })

        df = pd.DataFrame(rows)
        return df.sort_values("optempo_rating", ascending=False)


# -------------------------
# Scenario builders
# -------------------------

def create_indopacom_deployment_cycle(tracker: OPTEMPOTracker, year: int = 2025):
    """
    Create typical USINDOPACOM deployment cycle.

    Rotations:
    - Korea rotations (9 months)
    - Pacific Pathways exercises (2-3 months)
    - Valiant Shield, Orient Shield, etc.
    """
    base_date = date(year, 1, 1)

    # Korea rotation cycle (9-month deployments)
    tracker.add_standard_rotation(
        "WFF01A",  # Example battalion
        "Korea Rotation",
        base_date + timedelta(days=90),
        duration_months=9
    )

    # Pacific Pathways (shorter, multiple units)
    tracker.add_deployment(DeploymentWindow(
        unit_uic="WFF02A",
        deployment_type="exercise",
        location="Australia",
        start_date=base_date + timedelta(days=180),
        end_date=base_date + timedelta(days=240),
        pct_available=0.2,  # 20% available for other taskings
        mission_name="Talisman Sabre"
    ))

    # Unit in reset (post-deployment)
    tracker.add_deployment(DeploymentWindow(
        unit_uic="WFF03A",
        deployment_type="maintenance",
        location="Home Station",
        start_date=base_date - timedelta(days=365),
        end_date=base_date - timedelta(days=275),
        pct_available=0.3,  # 30% available during reset
        mission_name="Post-Deployment Reset"
    ))


def apply_standard_dwell_requirements(
    tracker: OPTEMPOTracker,
    min_dwell_months: int = 12
) -> Set[str]:
    """
    Identify units that don't meet minimum dwell requirements.

    Returns:
        Set of UICs that should not be tasked
    """
    restricted_units = set()

    for deployment in tracker.deployment_windows:
        if deployment.deployment_type != "deployment":
            continue

        # Check if dwell time met
        months_since_return = (date.today() - deployment.end_date).days / 30

        if months_since_return < min_dwell_months:
            restricted_units.add(deployment.unit_uic)

    return restricted_units
