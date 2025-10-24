"""
task_organizer.py
-----------------

Task organization and unit cohesion management.

Implements hybrid optimization approach:
- Prefer keeping organic teams/squads together when possible
- Allow individual backfills when unit pulls are not feasible
- Apply cohesion penalties for breaking up established teams

Classes:
- TeamIdentifier: Identifies organic teams from unit structure
- CohesionCalculator: Calculates penalties for breaking up units
- TaskOrganizer: Manages sourcing strategy (unit vs individual)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

from unit_types import Unit, SoldierExtended, LeadershipLevel, calculate_unit_cohesion_penalty


@dataclass
class OrganicTeam:
    """
    Represents an organic team from a unit (squad, section, crew).

    Teams are identified by shared leadership chains.
    """
    team_id: str  # Unique identifier (e.g., "WFF01A_01DA" for PLT1/SQD1)
    unit_uic: str
    leader_id: int
    member_ids: List[int]
    team_type: str  # "squad", "team", "section", "crew"
    mos: str  # Primary MOS of the team

    def size(self) -> int:
        """Total team size including leader."""
        return 1 + len(self.member_ids)

    def all_members(self) -> List[int]:
        """Get all member IDs including leader."""
        return [self.leader_id] + self.member_ids


class TeamIdentifier:
    """
    Identifies organic teams from unit structure and soldier assignments.

    Uses leadership hierarchy to group soldiers into teams.
    """

    @staticmethod
    def identify_teams(
        unit: Unit,
        soldiers_df: pd.DataFrame,
        soldiers_ext: Dict[int, SoldierExtended]
    ) -> List[OrganicTeam]:
        """
        Identify all organic teams within a unit.

        Strategy:
        1. Find all team leaders (E-5, E-6 with leadership_level = TEAM_LEADER)
        2. Find all squad leaders (E-6, E-7 with leadership_level = SQUAD_LEADER)
        3. Group soldiers by their supervisor

        Returns:
            List of OrganicTeam objects
        """
        teams = []
        unit_soldiers = soldiers_df[soldiers_df["uic"] == unit.uic]

        # Build supervisor map
        supervisor_map = defaultdict(list)  # supervisor_id -> [subordinate_ids]
        for soldier_id, soldier_ext in soldiers_ext.items():
            if soldier_ext.uic == unit.uic and soldier_ext.supervisor_id:
                supervisor_map[soldier_ext.supervisor_id].append(soldier_id)

        # Find team-level leaders (TL, SL)
        for idx, soldier_row in unit_soldiers.iterrows():
            soldier_id = soldier_row["soldier_id"]
            soldier_ext = soldiers_ext.get(soldier_id)

            if not soldier_ext:
                continue

            # Team leaders and squad leaders
            if soldier_ext.leadership_level in [LeadershipLevel.TEAM_LEADER, LeadershipLevel.SQUAD_LEADER]:
                subordinates = supervisor_map.get(soldier_id, [])

                if len(subordinates) > 0:  # Only create team if has subordinates
                    team_type = "squad" if soldier_ext.leadership_level == LeadershipLevel.SQUAD_LEADER else "team"
                    team_id = f"{unit.uic}_{soldier_ext.para_line}"

                    teams.append(OrganicTeam(
                        team_id=team_id,
                        unit_uic=unit.uic,
                        leader_id=soldier_id,
                        member_ids=subordinates,
                        team_type=team_type,
                        mos=soldier_row["mos"]
                    ))

        return teams

    @staticmethod
    def find_intact_teams_for_requirement(
        requirement_mos: str,
        requirement_size: int,
        available_teams: List[OrganicTeam],
        used_team_ids: Set[str]
    ) -> Optional[OrganicTeam]:
        """
        Find an intact team matching the requirement.

        Args:
            requirement_mos: Required MOS
            requirement_size: Required team size
            available_teams: Pool of teams to search
            used_team_ids: Already-assigned team IDs

        Returns:
            OrganicTeam if found, None otherwise
        """
        for team in available_teams:
            if (team.team_id not in used_team_ids and
                team.mos == requirement_mos and
                team.size() >= requirement_size):
                return team

        return None


class CohesionCalculator:
    """
    Calculates cohesion penalties and bonuses for assignments.

    Cohesion is valuable - breaking up established teams has a cost.
    """

    @staticmethod
    def calculate_team_cohesion_bonus(
        soldiers_assigned: List[int],
        organic_team: OrganicTeam,
        base_bonus: float = -500.0  # Negative = good
    ) -> float:
        """
        Calculate bonus for keeping an organic team together.

        Bonus scales with:
        - Percentage of team kept together
        - Team size (larger teams = bigger bonus)
        """
        team_members = set(organic_team.all_members())
        assigned_set = set(soldiers_assigned)

        # How many team members are being kept together?
        kept_together = len(team_members.intersection(assigned_set))
        pct_together = kept_together / len(team_members)

        if pct_together >= 0.8:  # At least 80% together
            bonus = base_bonus * pct_together * (len(team_members) / 4.0)  # Scale by team size
            return bonus

        return 0.0  # No bonus if team is split

    @staticmethod
    def calculate_split_penalty(
        source_unit: Unit,
        soldiers_taken: List[int],
        all_teams: List[OrganicTeam],
        base_penalty: float = 300.0
    ) -> float:
        """
        Calculate penalty for partially breaking up teams.

        If you take some (but not all) members of a team, there's a penalty
        for leaving gaps in the source unit.
        """
        penalty = 0.0

        for team in all_teams:
            team_members = set(team.all_members())
            taken_set = set(soldiers_taken)
            taken_from_team = team_members.intersection(taken_set)

            # Partial team taken (not all, not none)
            if 0 < len(taken_from_team) < len(team_members):
                pct_taken = len(taken_from_team) / len(team_members)
                # Penalty is highest when ~50% taken (most disruptive)
                disruption_factor = 1.0 - abs(pct_taken - 0.5) * 2
                penalty += base_penalty * disruption_factor * len(team_members)

        return penalty

    @staticmethod
    def calculate_cross_unit_penalty(
        soldiers_assigned: pd.DataFrame,
        base_penalty: float = 200.0
    ) -> float:
        """
        Calculate penalty for pulling from multiple units.

        Complexity increases with number of source units (coordination overhead).
        """
        source_units = soldiers_assigned["uic"].nunique()

        if source_units <= 1:
            return 0.0

        # Penalty scales with number of units
        return base_penalty * (source_units - 1)


class TaskOrganizer:
    """
    Manages sourcing strategy for manning requirements.

    Implements hybrid approach: try to source intact teams first,
    backfill individuals as needed.
    """

    def __init__(
        self,
        units: Dict[str, Unit],
        soldiers_df: pd.DataFrame,
        soldiers_ext: Dict[int, SoldierExtended]
    ):
        self.units = units
        self.soldiers_df = soldiers_df
        self.soldiers_ext = soldiers_ext

        # Identify all teams
        self.all_teams: List[OrganicTeam] = []
        for unit in units.values():
            teams = TeamIdentifier.identify_teams(unit, soldiers_df, soldiers_ext)
            self.all_teams.extend(teams)

        self.used_team_ids: Set[str] = set()

    def source_capability(
        self,
        mos_required: str,
        team_size: int,
        prefer_intact: bool = True,
        prefer_from_uic: Optional[str] = None
    ) -> Tuple[List[int], str]:
        """
        Source soldiers for a capability requirement.

        Args:
            mos_required: Required MOS
            team_size: Number of soldiers needed
            prefer_intact: Try to source intact team first
            prefer_from_uic: Prefer specific unit

        Returns:
            (soldier_ids, sourcing_method)
            sourcing_method: "intact_team", "partial_team", or "individuals"
        """
        # Strategy 1: Intact team from preferred unit
        if prefer_intact and prefer_from_uic:
            unit_teams = [t for t in self.all_teams if t.unit_uic == prefer_from_uic]
            team = TeamIdentifier.find_intact_teams_for_requirement(
                mos_required, team_size, unit_teams, self.used_team_ids
            )
            if team:
                self.used_team_ids.add(team.team_id)
                return team.all_members()[:team_size], "intact_team"

        # Strategy 2: Intact team from any unit
        if prefer_intact:
            team = TeamIdentifier.find_intact_teams_for_requirement(
                mos_required, team_size, self.all_teams, self.used_team_ids
            )
            if team:
                self.used_team_ids.add(team.team_id)
                return team.all_members()[:team_size], "intact_team"

        # Strategy 3: Partial team (if available)
        # Find teams with some availability
        for team in self.all_teams:
            if team.team_id not in self.used_team_ids and team.mos == mos_required:
                available_count = min(team.size(), team_size)
                if available_count >= team_size * 0.5:  # At least 50% of need
                    self.used_team_ids.add(team.team_id)
                    return team.all_members()[:available_count], "partial_team"

        # Strategy 4: Individual backfill (last resort)
        # This would be handled by standard EMD optimization
        return [], "individuals"

    def get_cohesion_adjustment(
        self,
        soldier_id: int,
        billet_requirement: pd.Series,
        current_assignment: List[int]
    ) -> float:
        """
        Calculate cohesion adjustment for assigning a soldier to a billet.

        This integrates with EMD's cost function.

        Args:
            soldier_id: Soldier being considered
            billet_requirement: Billet (from manning document conversion)
            current_assignment: Other soldiers already assigned to this capability

        Returns:
            Cost adjustment (negative = bonus, positive = penalty)
        """
        adjustment = 0.0

        # Check if soldier is part of an organic team
        soldier_ext = self.soldiers_ext.get(soldier_id)
        if not soldier_ext:
            return 0.0

        # Find soldier's team
        soldier_team = None
        for team in self.all_teams:
            if soldier_id in team.all_members():
                soldier_team = team
                break

        if not soldier_team:
            return 0.0  # Not part of a team

        # Check if other team members are in current assignment
        team_members_assigned = [
            sid for sid in current_assignment
            if sid in soldier_team.all_members()
        ]

        # Bonus for keeping team together
        if len(team_members_assigned) > 0:
            # More team members together = bigger bonus
            pct_together = (len(team_members_assigned) + 1) / soldier_team.size()
            adjustment -= 300.0 * pct_together

        # Check if this would split the team in source unit
        if soldier_team.team_id not in self.used_team_ids:
            team_remaining = soldier_team.size() - len(team_members_assigned) - 1
            if 0 < team_remaining < soldier_team.size():
                # Penalty for leaving partial team
                adjustment += 200.0

        return adjustment

    def generate_sourcing_report(self, assignments: pd.DataFrame) -> pd.DataFrame:
        """
        Generate a report on how requirements were sourced.

        Shows:
        - Which units contributed soldiers
        - How many intact teams vs individuals
        - Cross-leveling complexity
        """
        # Check if UIC column exists
        if "uic" not in assignments.columns:
            return pd.DataFrame({
                "message": ["No UIC data available in assignments - using legacy soldier generation"]
            })

        sourcing_data = []

        by_unit = assignments.groupby("uic")["soldier_id"].count()

        for uic, count in by_unit.items():
            unit = self.units.get(uic)
            unit_name = unit.short_name if unit else uic

            # Count intact teams from this unit
            teams_from_unit = sum(
                1 for team in self.all_teams
                if team.team_id in self.used_team_ids and team.unit_uic == uic
            )

            sourcing_data.append({
                "uic": uic,
                "unit_name": unit_name,
                "soldiers_contributed": count,
                "intact_teams_sourced": teams_from_unit,
                "fill_impact_pct": count / unit.assigned_strength if unit else 0.0
            })

        if not sourcing_data:
            return pd.DataFrame({
                "message": ["No sourcing data available"]
            })

        df = pd.DataFrame(sourcing_data)
        return df.sort_values("soldiers_contributed", ascending=False)


def enhance_cost_matrix_with_cohesion(
    cost_matrix: np.ndarray,
    soldiers_df: pd.DataFrame,
    billets_df: pd.DataFrame,
    task_organizer: TaskOrganizer,
    cohesion_weight: float = 1.0
) -> np.ndarray:
    """
    Enhance existing cost matrix with cohesion adjustments.

    This modifies EMD's cost matrix to incorporate unit cohesion preferences.

    Args:
        cost_matrix: Original cost matrix from EMD.build_cost_matrix()
        soldiers_df: Soldiers DataFrame
        billets_df: Billets DataFrame (with capability metadata)
        task_organizer: TaskOrganizer instance
        cohesion_weight: How much to weight cohesion (1.0 = equal to other factors)

    Returns:
        Enhanced cost matrix
    """
    enhanced = cost_matrix.copy()

    # Reset indices to ensure they match matrix dimensions
    S = soldiers_df.reset_index(drop=True)
    B = billets_df.reset_index(drop=True)

    # Build soldier_id to matrix row index mapping
    soldier_id_to_row = {row["soldier_id"]: idx for idx, row in S.iterrows()}

    # Group billets by capability (if keep_together flag set)
    if "capability_name" in B.columns and "keep_together" in B.columns:
        for cap_name in B[B["keep_together"] == True]["capability_name"].unique():
            cap_billets = B[B["capability_name"] == cap_name]
            # Now indices are sequential 0, 1, 2, ... matching matrix columns
            billet_indices = cap_billets.index.tolist()

            # For each soldier, calculate cohesion adjustment for this capability
            for soldier_row_idx, soldier_row in S.iterrows():
                soldier_id = soldier_row["soldier_id"]

                # Find soldier's team
                soldier_team = None
                for team in task_organizer.all_teams:
                    if soldier_id in team.all_members():
                        soldier_team = team
                        break

                if soldier_team:
                    # Get matrix row indices for all team members
                    team_member_indices = [
                        soldier_id_to_row[sid]
                        for sid in soldier_team.all_members()
                        if sid in soldier_id_to_row
                    ]

                    # Reduce cost for all team members on this capability
                    for billet_idx in billet_indices:
                        for team_member_idx in team_member_indices:
                            enhanced[team_member_idx, billet_idx] -= 200.0 * cohesion_weight

    return enhanced
