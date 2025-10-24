"""
unit_types.py
-------------

Core data classes for military unit structure, positions, and training requirements.

Classes:
- TrainingGate: Represents a training requirement with currency tracking
- Equipment: Represents equipment qualifications and operator certifications
- Position: Represents a duty position within a unit's MTOE
- Unit: Represents a military unit with organizational hierarchy
- DeploymentRecord: Tracks historical deployment information
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Set
from enum import IntEnum


class LeadershipLevel(IntEnum):
    """Hierarchical leadership levels for span-of-control calculations."""
    SOLDIER = 0      # E-1 to E-4 (no supervisory)
    TEAM_LEADER = 1  # E-5, E-6 (2-4 subordinates)
    SQUAD_LEADER = 2 # E-6, E-7 (2-3 teams, 6-12 soldiers)
    PLATOON_SGT = 3  # E-7, E-8 (3-4 squads, 20-40 soldiers)
    FIRST_SGT = 4    # E-8 (company-level, 60-200 soldiers)
    SGM_CSM = 5      # E-9 (battalion+)


@dataclass
class TrainingGate:
    """
    Represents a training requirement that expires after a certain period.

    Examples: weapons qualification, CBRN, driver's license, medical readiness
    """
    name: str
    completion_date: date
    currency_days: int  # How many days until it expires
    category: str = "general"  # "weapon", "medical", "license", "deployment", "general"
    score: Optional[float] = None  # For scored events (e.g., ACFT, M4 qual)

    def is_current(self, as_of_date: Optional[date] = None) -> bool:
        """Check if the training is still current."""
        check_date = as_of_date or date.today()
        expiry = self.completion_date + timedelta(days=self.currency_days)
        return check_date <= expiry

    def days_until_expiry(self, as_of_date: Optional[date] = None) -> int:
        """Returns days until expiry (negative if already expired)."""
        check_date = as_of_date or date.today()
        expiry = self.completion_date + timedelta(days=self.currency_days)
        return (expiry - check_date).days


@dataclass
class Equipment:
    """
    Represents equipment qualifications and operator certifications.

    Examples: HMMWV license, LMTV license, UAS operator, radio operator
    """
    equipment_type: str  # "HMMWV", "LMTV", "JLTV", "Gray Eagle", "SINCGARS"
    qualification_level: str  # "operator", "maintainer", "instructor"
    certified_date: date
    expiry_date: Optional[date] = None
    license_number: Optional[str] = None

    def is_valid(self, as_of_date: Optional[date] = None) -> bool:
        """Check if qualification is still valid."""
        if self.expiry_date is None:
            return True  # No expiry
        check_date = as_of_date or date.today()
        return check_date <= self.expiry_date


@dataclass
class DeploymentRecord:
    """Tracks historical deployment information for dwell time and experience."""
    deployment_name: str
    location: str  # Theater (e.g., "Afghanistan", "Iraq", "Poland")
    start_date: date
    end_date: date
    deployment_type: str = "combat"  # "combat", "training", "humanitarian"
    positions_held: List[str] = field(default_factory=list)

    def duration_months(self) -> int:
        """Calculate deployment duration in months."""
        return int((self.end_date - self.start_date).days / 30)

    def dwell_months(self, as_of_date: Optional[date] = None) -> int:
        """Calculate months since returning (dwell time)."""
        check_date = as_of_date or date.today()
        return int((check_date - self.end_date).days / 30)


@dataclass
class Position:
    """
    Represents a duty position within a unit's MTOE (para/line).

    A Position is a slot in the MTOE, not a specific person.
    """
    para_line: str  # MTOE para/line identifier (e.g., "01AA", "02BB")
    title: str      # Duty title (e.g., "Company Commander", "Team Leader")
    mos_required: str
    rank_required: str  # Can be a range like "E-5" or single
    min_rank: Optional[str] = None  # For rank ranges
    max_rank: Optional[str] = None
    skill_level: int = 1
    clearance: str = "Secret"
    leadership_level: LeadershipLevel = LeadershipLevel.SOLDIER

    # Organizational hierarchy
    supervisor_paraline: Optional[str] = None  # Links to supervisor position
    subordinate_paralines: List[str] = field(default_factory=list)

    # Special requirements
    airborne_required: bool = False
    language_required: Optional[str] = None
    equipment_required: List[str] = field(default_factory=list)  # Equipment types needed
    training_gates_required: List[str] = field(default_factory=list)  # Training gate names

    # Manning
    is_filled: bool = False
    assigned_soldier_id: Optional[int] = None

    def get_leadership_span(self) -> int:
        """Expected number of subordinates for this leadership position."""
        span_map = {
            LeadershipLevel.SOLDIER: 0,
            LeadershipLevel.TEAM_LEADER: 3,      # 3-4 soldiers
            LeadershipLevel.SQUAD_LEADER: 8,     # 2-3 teams
            LeadershipLevel.PLATOON_SGT: 30,     # 3-4 squads
            LeadershipLevel.FIRST_SGT: 100,      # company-level
            LeadershipLevel.SGM_CSM: 400,        # battalion+
        }
        return span_map.get(self.leadership_level, 0)


@dataclass
class Unit:
    """
    Represents a military unit with organizational hierarchy.

    For company-level tracking, this would be a company (e.g., "A/1-2 IN").
    """
    uic: str                    # Unit Identification Code (e.g., "WFF1AA")
    name: str                   # Human-readable (e.g., "Alpha Company, 1st Battalion, 2nd Infantry")
    short_name: str             # (e.g., "A/1-2 IN")
    unit_type: str              # "Infantry", "Artillery", "Engineer", "MI", "CA", etc.
    echelon: str                # "Company", "Battery", "Troop", "Detachment"

    # Organizational hierarchy
    parent_uic: Optional[str] = None       # Parent unit (e.g., battalion)
    subordinate_uics: List[str] = field(default_factory=list)

    # Location
    home_station: str = "JBLM"
    current_location: str = "JBLM"  # May differ if deployed

    # MTOE structure
    positions: Dict[str, Position] = field(default_factory=dict)  # para_line -> Position
    authorized_strength: int = 0
    assigned_strength: int = 0

    # Readiness
    c_rating: str = "C-1"  # C-1 to C-4

    def get_fill_rate(self) -> float:
        """Calculate current manning percentage."""
        if self.authorized_strength == 0:
            return 0.0
        return self.assigned_strength / self.authorized_strength

    def get_leadership_positions(self) -> List[Position]:
        """Return all leadership positions (TL and above)."""
        return [
            pos for pos in self.positions.values()
            if pos.leadership_level >= LeadershipLevel.TEAM_LEADER
        ]

    def get_unfilled_positions(self) -> List[Position]:
        """Return positions without assigned soldiers."""
        return [pos for pos in self.positions.values() if not pos.is_filled]

    def add_position(self, position: Position):
        """Add a position to the unit's MTOE."""
        self.positions[position.para_line] = position
        self.authorized_strength += 1


@dataclass
class SoldierExtended:
    """
    Extended soldier attributes beyond the base EMD soldier generation.

    This augments the DataFrame-based soldier data with additional structure.
    Used to store complex data that doesn't fit cleanly in a DataFrame.
    """
    soldier_id: int

    # Unit assignment
    uic: str
    para_line: str
    duty_position: str
    leadership_level: LeadershipLevel
    supervisor_id: Optional[int] = None

    # Training & readiness
    training_gates: Dict[str, TrainingGate] = field(default_factory=dict)
    equipment_quals: List[Equipment] = field(default_factory=list)

    # History
    deployment_history: List[DeploymentRecord] = field(default_factory=list)
    time_in_position_months: int = 0
    time_in_grade_months: int = 0

    # Career tracking
    previous_positions: List[str] = field(default_factory=list)
    career_progression_on_track: bool = True

    def is_training_current(self, gate_names: List[str]) -> bool:
        """Check if all specified training gates are current."""
        return all(
            gate_name in self.training_gates and
            self.training_gates[gate_name].is_current()
            for gate_name in gate_names
        )

    def has_equipment_quals(self, equipment_types: List[str]) -> bool:
        """Check if soldier has all required equipment qualifications."""
        qualified = {eq.equipment_type for eq in self.equipment_quals if eq.is_valid()}
        return all(eq_type in qualified for eq_type in equipment_types)

    def last_deployment(self) -> Optional[DeploymentRecord]:
        """Get most recent deployment record."""
        if not self.deployment_history:
            return None
        return max(self.deployment_history, key=lambda d: d.end_date)

    def total_deployment_months(self) -> int:
        """Sum of all deployment durations."""
        return sum(d.duration_months() for d in self.deployment_history)

    def time_in_service_months(self) -> int:
        """Calculate total time in service (TIS)."""
        # Simple approximation: time_in_grade + time in previous grades
        # For more accuracy, would need enlistment date
        return self.time_in_grade_months + (self.time_in_position_months * 2)

    def meets_rank_requirements(self, rank: str) -> bool:
        """Check if soldier meets minimum TIS/TIG for rank."""
        rank_requirements = {
            "E-1": {"tis_months": 0, "tig_months": 0},
            "E-2": {"tis_months": 6, "tig_months": 6},
            "E-3": {"tis_months": 12, "tig_months": 4},
            "E-4": {"tis_months": 24, "tig_months": 6},
            "E-5": {"tis_months": 48, "tig_months": 12},
            "E-6": {"tis_months": 72, "tig_months": 24},
            "E-7": {"tis_months": 96, "tig_months": 36},
            "E-8": {"tis_months": 120, "tig_months": 48},
        }

        req = rank_requirements.get(rank)
        if not req:
            return True  # Officer ranks or unknown

        return (self.time_in_service_months() >= req["tis_months"] and
                self.time_in_grade_months >= req["tig_months"])


# -------------------------
# Validation helpers
# -------------------------

def validate_leader_follower_ratio(
    leader: SoldierExtended,
    subordinates: List[SoldierExtended]
) -> tuple[bool, str]:
    """
    Validate that a leader has appropriate number of subordinates.

    Returns: (is_valid, message)
    """
    expected = leader.leadership_level
    actual_count = len(subordinates)

    if expected == LeadershipLevel.SOLDIER:
        if actual_count > 0:
            return False, f"Soldier (non-leader) should not have subordinates, has {actual_count}"
        return True, "OK"

    # Get expected range
    expected_span = Position(
        para_line="",
        title="",
        mos_required="",
        rank_required="",
        leadership_level=expected
    ).get_leadership_span()

    # Allow +/- 30% variance
    min_span = int(expected_span * 0.7)
    max_span = int(expected_span * 1.3)

    if actual_count < min_span:
        return False, f"Leader has too few subordinates: {actual_count} (expected ~{expected_span})"
    if actual_count > max_span:
        return False, f"Leader has too many subordinates: {actual_count} (expected ~{expected_span})"

    return True, "OK"


def calculate_unit_cohesion_penalty(
    source_unit: Unit,
    soldiers_taken: List[int],
    base_penalty: float = 500.0
) -> float:
    """
    Calculate penalty for breaking up a unit.

    Penalty scales with:
    - Percentage of unit taken
    - Leadership positions taken
    - Overall unit readiness impact
    """
    if not soldiers_taken:
        return 0.0

    # Base penalty per soldier
    penalty = base_penalty * len(soldiers_taken)

    # Scale by percentage taken (more = worse)
    pct_taken = len(soldiers_taken) / max(source_unit.assigned_strength, 1)
    penalty *= (1 + pct_taken)

    # TODO: Add leadership penalty when integrated with full soldier data
    # For now, assume proportional impact

    return penalty
