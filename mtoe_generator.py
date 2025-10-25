"""
mtoe_generator.py
-----------------

MTOE template library and unit instantiation system.

Generates realistic military units based on doctrinal MTOEs with organic soldiers.
Supports company-level organizations across multiple unit types.

Classes:
- MTOETemplate: Defines the structure of a unit type
- MTOELibrary: Catalog of standard unit templates
- UnitGenerator: Creates units and populates them with soldiers
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from unit_types import (
    Unit, Position, SoldierExtended, TrainingGate, Equipment,
    DeploymentRecord, LeadershipLevel
)

# Import extended profile generation
try:
    from qualifications import ProfileGenerator
    EXTENDED_PROFILES_AVAILABLE = True
except ImportError:
    EXTENDED_PROFILES_AVAILABLE = False
    ProfileGenerator = None


@dataclass
class MTOETemplate:
    """
    Defines the structure of a unit type (e.g., Infantry Company, FA Battery).

    A template is a blueprint for creating actual units.
    """
    unit_type: str
    echelon: str
    authorized_strength: int
    positions: List[Position] = field(default_factory=list)

    # Default distribution of attributes
    mos_distribution: Dict[str, float] = field(default_factory=dict)
    rank_distribution: Dict[str, float] = field(default_factory=dict)


class MTOELibrary:
    """
    Catalog of doctrinal MTOE templates.

    Includes simplified versions of common Army unit types.
    """

    @staticmethod
    def infantry_rifle_company() -> MTOETemplate:
        """
        Standard Infantry Rifle Company (per FM 3-21.10).

        Structure:
        - Company HQ (CDR, XO, 1SG, RTO, Armorer, Supply, etc.)
        - 3x Rifle Platoons (PL, PSG, RTO, 3x Squads)
        - Weapons Squad (optional, simplified here)

        ~130 soldiers
        """
        positions = []

        # Company HQ
        positions.extend([
            Position("00AA", "Company Commander", "11A", "O-3", leadership_level=LeadershipLevel.FIRST_SGT),
            Position("00AB", "Executive Officer", "11A", "O-2", leadership_level=LeadershipLevel.PLATOON_SGT),
            Position("00AC", "First Sergeant", "11B", "E-8", leadership_level=LeadershipLevel.FIRST_SGT),
            Position("00AD", "Company RTO", "11B", "E-4", training_gates_required=["radio_operator"]),
            Position("00AE", "Armorer", "11B", "E-4", equipment_required=["armory_certified"]),
            Position("00AF", "Supply Sergeant", "92Y", "E-6", leadership_level=LeadershipLevel.TEAM_LEADER),
            Position("00AG", "Supply Specialist", "92Y", "E-4"),
        ])

        # 3x Rifle Platoons
        for plt in range(1, 4):
            prefix = f"{plt:02d}"
            positions.extend([
                Position(f"{prefix}AA", f"Platoon Leader (PLT {plt})", "11A", "O-1",
                         leadership_level=LeadershipLevel.PLATOON_SGT),
                Position(f"{prefix}AB", f"Platoon Sergeant (PLT {plt})", "11B", "E-7",
                         leadership_level=LeadershipLevel.PLATOON_SGT,
                         supervisor_paraline=f"{prefix}AA"),
                Position(f"{prefix}AC", f"Platoon RTO (PLT {plt})", "11B", "E-4",
                         training_gates_required=["radio_operator"]),
            ])

            # 3x Squads per platoon
            for sqd in range(1, 4):
                sq_code = chr(ord('A') + sqd + 2)  # D, E, F for squads 1,2,3
                positions.extend([
                    Position(f"{prefix}{sq_code}A", f"Squad Leader (PLT{plt}/SQD{sqd})", "11B", "E-6",
                             leadership_level=LeadershipLevel.SQUAD_LEADER,
                             supervisor_paraline=f"{prefix}AB"),
                    Position(f"{prefix}{sq_code}B", f"Team Leader 1 (PLT{plt}/SQD{sqd})", "11B", "E-5",
                             leadership_level=LeadershipLevel.TEAM_LEADER,
                             supervisor_paraline=f"{prefix}{sq_code}A"),
                    Position(f"{prefix}{sq_code}C", f"Rifleman (PLT{plt}/SQD{sqd})", "11B", "E-3"),
                    Position(f"{prefix}{sq_code}D", f"Grenadier (PLT{plt}/SQD{sqd})", "11B", "E-3"),
                    Position(f"{prefix}{sq_code}E", f"Team Leader 2 (PLT{plt}/SQD{sqd})", "11B", "E-5",
                             leadership_level=LeadershipLevel.TEAM_LEADER,
                             supervisor_paraline=f"{prefix}{sq_code}A"),
                    Position(f"{prefix}{sq_code}F", f"Automatic Rifleman (PLT{plt}/SQD{sqd})", "11B", "E-4",
                             equipment_required=["M249_qualified"]),
                    Position(f"{prefix}{sq_code}G", f"Rifleman (PLT{plt}/SQD{sqd})", "11B", "E-3"),
                ])

        return MTOETemplate(
            unit_type="Infantry",
            echelon="Company",
            authorized_strength=len(positions),
            positions=positions,
            mos_distribution={"11B": 0.85, "11A": 0.05, "92Y": 0.05, "68W": 0.05},
            rank_distribution={"E-3": 0.35, "E-4": 0.25, "E-5": 0.15, "E-6": 0.10, "E-7": 0.05,
                               "E-8": 0.02, "O-1": 0.03, "O-2": 0.02, "O-3": 0.03}
        )

    @staticmethod
    def field_artillery_battery() -> MTOETemplate:
        """
        Field Artillery Battery (simplified, ~90 soldiers).

        Structure:
        - Battery HQ
        - Fire Direction Center (FDC)
        - 6x Gun sections (Howitzer crews)
        """
        positions = []

        # Battery HQ
        positions.extend([
            Position("00AA", "Battery Commander", "13A", "O-3", leadership_level=LeadershipLevel.FIRST_SGT),
            Position("00AB", "Executive Officer", "13A", "O-2", leadership_level=LeadershipLevel.PLATOON_SGT),
            Position("00AC", "First Sergeant", "13B", "E-8", leadership_level=LeadershipLevel.FIRST_SGT),
            Position("00AD", "Battery RTO", "13B", "E-4", training_gates_required=["radio_operator"]),
        ])

        # FDC
        positions.extend([
            Position("01AA", "FDC Chief", "13D", "E-7", leadership_level=LeadershipLevel.PLATOON_SGT),
            Position("01AB", "Computer Operator", "13D", "E-5"),
            Position("01AC", "Computer Operator", "13D", "E-4"),
            Position("01AD", "Recorder", "13B", "E-4"),
        ])

        # Gun sections (6 guns, ~10 per crew)
        for gun in range(1, 7):
            prefix = f"{gun+1:02d}"
            positions.extend([
                Position(f"{prefix}AA", f"Section Chief (Gun {gun})", "13B", "E-6",
                         leadership_level=LeadershipLevel.SQUAD_LEADER),
                Position(f"{prefix}AB", f"Gunner (Gun {gun})", "13B", "E-5",
                         leadership_level=LeadershipLevel.TEAM_LEADER),
                Position(f"{prefix}AC", f"Assistant Gunner (Gun {gun})", "13B", "E-4"),
                Position(f"{prefix}AD", f"Ammo Bearer (Gun {gun})", "13B", "E-3"),
                Position(f"{prefix}AE", f"Ammo Bearer (Gun {gun})", "13B", "E-3"),
                Position(f"{prefix}AF", f"Driver (Gun {gun})", "13B", "E-4",
                         equipment_required=["LMTV_license"]),
            ])

        return MTOETemplate(
            unit_type="FieldArtillery",
            echelon="Battery",
            authorized_strength=len(positions),
            positions=positions,
            mos_distribution={"13B": 0.70, "13D": 0.10, "13A": 0.05, "92Y": 0.05, "68W": 0.05, "88M": 0.05},
            rank_distribution={"E-3": 0.30, "E-4": 0.30, "E-5": 0.15, "E-6": 0.10, "E-7": 0.05,
                               "E-8": 0.02, "O-1": 0.03, "O-2": 0.02, "O-3": 0.03}
        )

    @staticmethod
    def military_intelligence_company() -> MTOETemplate:
        """
        Military Intelligence Company (simplified, ~80 soldiers).

        Heavy on analysts, linguists, and signals intelligence.
        """
        positions = []

        # Company HQ
        positions.extend([
            Position("00AA", "Company Commander", "35A", "O-3", leadership_level=LeadershipLevel.FIRST_SGT,
                     clearance="TS"),
            Position("00AB", "Executive Officer", "35A", "O-2", leadership_level=LeadershipLevel.PLATOON_SGT,
                     clearance="TS"),
            Position("00AC", "First Sergeant", "35F", "E-8", leadership_level=LeadershipLevel.FIRST_SGT,
                     clearance="TS"),
            Position("00AD", "Company RTO", "25U", "E-4", training_gates_required=["radio_operator"],
                     clearance="Secret"),
        ])

        # Analysis & Control Element
        positions.extend([
            Position("01AA", "ACE Chief", "35F", "E-7", leadership_level=LeadershipLevel.PLATOON_SGT,
                     clearance="TS"),
            Position("01AB", "Senior Analyst", "35F", "E-6", clearance="TS"),
            Position("01AC", "All-Source Analyst", "35F", "E-5", clearance="TS"),
            Position("01AD", "All-Source Analyst", "35F", "E-4", clearance="TS"),
        ])

        # HUMINT Section
        positions.extend([
            Position("02AA", "HUMINT Section Lead", "35M", "E-7", leadership_level=LeadershipLevel.PLATOON_SGT,
                     clearance="TS"),
            Position("02AB", "HUMINT Collector", "35M", "E-6", clearance="TS", language_required="Arabic"),
            Position("02AC", "HUMINT Collector", "35M", "E-5", clearance="TS"),
            Position("02AD", "HUMINT Collector", "35M", "E-4", clearance="TS"),
        ])

        # SIGINT Section
        positions.extend([
            Position("03AA", "SIGINT Section Lead", "35N", "E-7", leadership_level=LeadershipLevel.PLATOON_SGT,
                     clearance="TS"),
            Position("03AB", "SIGINT Analyst", "35N", "E-5", clearance="TS"),
            Position("03AC", "SIGINT Analyst", "35N", "E-5", clearance="TS"),
            Position("03AD", "Signals Collector", "35P", "E-4", clearance="TS", language_required="Spanish"),
        ])

        # Fill in remaining positions (simplified)
        for i in range(len(positions), 80):
            mos = np.random.choice(["35F", "35M", "35N", "25U"], p=[0.4, 0.3, 0.2, 0.1])
            rank = np.random.choice(["E-3", "E-4", "E-5"], p=[0.4, 0.4, 0.2])
            positions.append(
                Position(f"99{chr(65+i%26)}{chr(65+(i//26)%26)}", f"Analyst/Collector {i}", mos, rank,
                         clearance="TS" if mos.startswith("35") else "Secret")
            )

        return MTOETemplate(
            unit_type="MilitaryIntelligence",
            echelon="Company",
            authorized_strength=len(positions),
            positions=positions,
            mos_distribution={"35F": 0.30, "35M": 0.25, "35N": 0.15, "35P": 0.10, "25U": 0.10, "35A": 0.05, "92Y": 0.05},
            rank_distribution={"E-3": 0.25, "E-4": 0.30, "E-5": 0.20, "E-6": 0.10, "E-7": 0.05,
                               "E-8": 0.02, "O-1": 0.03, "O-2": 0.02, "O-3": 0.03}
        )

    @staticmethod
    def engineer_company() -> MTOETemplate:
        """Engineer Company (simplified, ~100 soldiers)."""
        positions = []

        positions.extend([
            Position("00AA", "Company Commander", "12A", "O-3", leadership_level=LeadershipLevel.FIRST_SGT),
            Position("00AB", "Executive Officer", "12A", "O-2", leadership_level=LeadershipLevel.PLATOON_SGT),
            Position("00AC", "First Sergeant", "12B", "E-8", leadership_level=LeadershipLevel.FIRST_SGT),
        ])

        # 3x Engineer Platoons
        for plt in range(1, 4):
            prefix = f"{plt:02d}"
            positions.extend([
                Position(f"{prefix}AA", f"Platoon Leader (PLT {plt})", "12A", "O-1",
                         leadership_level=LeadershipLevel.PLATOON_SGT),
                Position(f"{prefix}AB", f"Platoon Sergeant (PLT {plt})", "12B", "E-7",
                         leadership_level=LeadershipLevel.PLATOON_SGT),
            ])

            # 2x Squads
            for sqd in range(1, 3):
                sq_code = chr(ord('A') + sqd + 1)
                positions.extend([
                    Position(f"{prefix}{sq_code}A", f"Squad Leader (PLT{plt}/SQD{sqd})", "12B", "E-6",
                             leadership_level=LeadershipLevel.SQUAD_LEADER),
                    Position(f"{prefix}{sq_code}B", f"Combat Engineer", "12B", "E-5",
                             leadership_level=LeadershipLevel.TEAM_LEADER),
                    Position(f"{prefix}{sq_code}C", f"Combat Engineer", "12B", "E-4"),
                    Position(f"{prefix}{sq_code}D", f"Combat Engineer", "12B", "E-3"),
                    Position(f"{prefix}{sq_code}E", f"Combat Engineer", "12B", "E-3"),
                ])

        # Fill to ~100
        for i in range(len(positions), 100):
            positions.append(
                Position(f"99{chr(65+i%26)}{chr(65+(i//26)%26)}", f"Engineer {i}", "12B",
                         np.random.choice(["E-3", "E-4", "E-5"], p=[0.5, 0.3, 0.2]))
            )

        return MTOETemplate(
            unit_type="Engineer",
            echelon="Company",
            authorized_strength=len(positions),
            positions=positions,
            mos_distribution={"12B": 0.75, "12A": 0.05, "12C": 0.05, "92Y": 0.05, "68W": 0.05, "88M": 0.05},
            rank_distribution={"E-3": 0.35, "E-4": 0.25, "E-5": 0.15, "E-6": 0.10, "E-7": 0.05,
                               "E-8": 0.02, "O-1": 0.03, "O-2": 0.02, "O-3": 0.03}
        )


class UnitGenerator:
    """
    Creates units and populates them with soldiers using MTOE templates.

    Integrates with EMD's soldier generation to add unit structure.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)
        self.units: Dict[str, Unit] = {}
        self.soldiers_extended: Dict[int, SoldierExtended] = {}
        self.soldier_counter = 0

        # Initialize extended profile generator
        if EXTENDED_PROFILES_AVAILABLE:
            self.profile_generator = ProfileGenerator(seed=seed)
        else:
            self.profile_generator = None

    def create_unit(
        self,
        template: MTOETemplate,
        uic: str,
        name: str,
        short_name: str,
        home_station: str = "JBLM",
        parent_uic: Optional[str] = None
    ) -> Unit:
        """
        Create a unit from an MTOE template.
        """
        unit = Unit(
            uic=uic,
            name=name,
            short_name=short_name,
            unit_type=template.unit_type,
            echelon=template.echelon,
            parent_uic=parent_uic,
            home_station=home_station,
            current_location=home_station,
            authorized_strength=template.authorized_strength,
            assigned_strength=0  # Will be filled when soldiers assigned
        )

        # Add positions from template
        for pos_template in template.positions:
            unit.add_position(pos_template)

        self.units[uic] = unit
        return unit

    def generate_soldiers_for_unit(
        self,
        unit: Unit,
        fill_rate: float = 0.95,
        base_soldier_id: int = 1
    ) -> Tuple[pd.DataFrame, Dict[int, SoldierExtended]]:
        """
        Generate soldiers for a specific unit based on its MTOE positions.

        Uses realistic fill priority: leaders first, then specialists, then soldiers.

        Returns:
            - soldiers_df: DataFrame compatible with EMD.soldiers
            - soldiers_extended: Dict of SoldierExtended with additional structure
        """
        self.soldier_counter = base_soldier_id
        soldiers_data = []
        soldiers_ext = {}

        # Prioritize positions: leaders > specialists > soldiers
        positions_prioritized = self._prioritize_positions(list(unit.positions.values()))
        n_to_fill = int(len(positions_prioritized) * fill_rate)
        positions_to_fill = positions_prioritized[:n_to_fill]

        for position in positions_to_fill:
            soldier_id = self.soldier_counter
            self.soldier_counter += 1

            # Generate soldier attributes based on position requirements
            soldier_row = self._generate_soldier_from_position(soldier_id, unit, position)
            soldiers_data.append(soldier_row)

            # Create extended soldier record
            soldier_ext = self._create_extended_soldier(soldier_id, unit, position)
            soldiers_ext[soldier_id] = soldier_ext

            # Mark position as filled
            position.is_filled = True
            position.assigned_soldier_id = soldier_id

        unit.assigned_strength = len(soldiers_data)

        # Second pass: Link supervisors now that all soldiers are created
        self._link_supervisors(unit, soldiers_ext)

        # Convert to DataFrame
        soldiers_df = pd.DataFrame(soldiers_data)
        return soldiers_df, soldiers_ext

    def _prioritize_positions(self, positions: List[Position]) -> List[Position]:
        """
        Prioritize positions for filling: leaders first, then specialists, then soldiers.

        Priority order:
        1. Command team (CSM/1SG level)
        2. Senior leaders (PSG level)
        3. Team/squad leaders (SL/TL level)
        4. Specialists (medics, RTOs, etc.)
        5. Regular soldiers

        Within each tier, randomize to simulate natural variation.
        """
        from unit_types import LeadershipLevel

        # Categorize positions
        tiers = {
            "command": [],      # E-8+, O-3+
            "senior_leaders": [],  # E-7, E-8 (PSG level)
            "leaders": [],      # E-5, E-6 (TL/SL level)
            "specialists": [],  # Special MOSs or requirements
            "soldiers": []      # Everyone else
        }

        for pos in positions:
            if pos.leadership_level >= LeadershipLevel.FIRST_SGT:
                tiers["command"].append(pos)
            elif pos.leadership_level == LeadershipLevel.PLATOON_SGT:
                tiers["senior_leaders"].append(pos)
            elif pos.leadership_level in [LeadershipLevel.SQUAD_LEADER, LeadershipLevel.TEAM_LEADER]:
                tiers["leaders"].append(pos)
            elif len(pos.equipment_required) > 0 or len(pos.training_gates_required) > 0:
                tiers["specialists"].append(pos)
            else:
                tiers["soldiers"].append(pos)

        # Shuffle within each tier for natural variation
        for tier_list in tiers.values():
            np.random.shuffle(tier_list)

        # Concatenate in priority order
        prioritized = (
            tiers["command"] +
            tiers["senior_leaders"] +
            tiers["leaders"] +
            tiers["specialists"] +
            tiers["soldiers"]
        )

        return prioritized

    def _link_supervisors(self, unit: Unit, soldiers_ext: Dict[int, SoldierExtended]):
        """
        Link soldiers to their supervisors based on position hierarchy.

        This is done in a second pass after all soldiers are created.
        """
        # Build para_line -> soldier_id mapping
        paraline_to_soldier = {}
        for soldier_id, soldier_ext in soldiers_ext.items():
            if soldier_ext.uic == unit.uic:
                paraline_to_soldier[soldier_ext.para_line] = soldier_id

        # Link subordinates to supervisors
        for position in unit.positions.values():
            if not position.is_filled:
                continue

            soldier_id = position.assigned_soldier_id
            if soldier_id not in soldiers_ext:
                continue

            # Find supervisor position
            if position.supervisor_paraline:
                supervisor_id = paraline_to_soldier.get(position.supervisor_paraline)
                if supervisor_id:
                    soldiers_ext[soldier_id].supervisor_id = supervisor_id

    def _generate_soldier_from_position(
        self,
        soldier_id: int,
        unit: Unit,
        position: Position
    ) -> Dict:
        """Generate a soldier matching position requirements (EMD-compatible format)."""

        # Parse rank
        rank = position.rank_required
        if position.min_rank:
            rank = np.random.choice([position.min_rank, position.max_rank or position.min_rank])

        # Determine skill level from rank
        rank_skill_map = {"E-1":[1], "E-2":[1], "E-3":[1], "E-4":[1,2], "E-5":[2,3], "E-6":[3,4], "E-7":[4,5], "E-8":[4,5]}
        skill_level = np.random.choice(rank_skill_map.get(rank, [position.skill_level]))

        # PME based on rank
        pme_map = {"E-3":"None", "E-4":"BLC", "E-5":"ALC", "E-6":"ALC", "E-7":"SLC", "E-8":"SLC"}
        pme = pme_map.get(rank, "None")

        # Calculate time in service and time in grade
        tig_months = self._realistic_tig_for_rank(rank)
        # TIS is TIG + additional time from previous ranks
        rank_progression_months = {"E-1":0, "E-2":6, "E-3":18, "E-4":30, "E-5":48, "E-6":78, "E-7":126, "E-8":174, "O-1":0, "O-2":24, "O-3":48}
        base_tis = rank_progression_months.get(rank, 24)
        tis_months = base_tis + tig_months

        # Determine unit type for badge correlation
        unit_type = unit.short_name if hasattr(unit, 'short_name') else None

        # Generate extended profile if available
        extended_profile_data = {}
        if self.profile_generator is not None:
            try:
                extended_profile = self.profile_generator.generate_profile(
                    soldier_id=str(soldier_id),
                    rank=rank,
                    mos=position.mos_required,
                    base=unit.home_station,
                    tis_months=tis_months,
                    tig_months=tig_months,
                    unit_type=unit_type
                )
                # Convert to dictionary for DataFrame storage
                profile_dict = extended_profile.to_dict()

                # Add extended profile columns
                extended_profile_data = {
                    "education_level": profile_dict["highest_education"],
                    "education_records_json": json.dumps(profile_dict.get("education_records", [])),
                    "languages_json": json.dumps(profile_dict.get("languages", [])),
                    "asi_codes_json": json.dumps(profile_dict.get("asi_codes", [])),
                    "sqi_codes_json": json.dumps(profile_dict.get("sqi_codes", [])),
                    "badges_json": json.dumps(profile_dict.get("badges", [])),
                    "awards_json": json.dumps(profile_dict.get("awards", [])),
                    "licenses_json": json.dumps(profile_dict.get("licenses", [])),
                    "time_in_service_months": tis_months,
                    "time_in_grade_months": tig_months,
                    "deployments_json": json.dumps(profile_dict.get("deployments", [])),
                    "duty_history_json": json.dumps(profile_dict.get("duty_history", []))
                }
            except Exception as e:
                # If profile generation fails, continue without extended data
                print(f"Warning: Failed to generate extended profile for soldier {soldier_id}: {e}")

        # Generate base attributes
        base_data = {
            "soldier_id": soldier_id,
            "base": unit.home_station,
            "paygrade": rank,
            "mos": position.mos_required,
            "skill_level": skill_level,
            "clearance": position.clearance,
            "pme": pme,
            "airborne": 1 if position.airborne_required else np.random.choice([0,1], p=[0.7, 0.3]),
            "pathfinder": np.random.choice([0,1], p=[0.95, 0.05]),
            "ranger": np.random.choice([0,1], p=[0.95, 0.05]),
            "umo": np.random.choice([0,1], p=[0.95, 0.05]),
            "m4_score": np.clip(int(np.random.normal(35, 3)), 23, 40),
            "acft_score": np.clip(np.random.normal(450, 60), 360, 600),
            "body_composition_pass": np.random.choice([0,1], p=[0.10, 0.90]),
            "asi_air_assault": np.random.choice([0,1], p=[0.85, 0.15]),
            "asi_sniper": np.random.choice([0,1], p=[0.97, 0.03]),
            "asi_jumpmaster": np.random.choice([0,1], p=[0.95, 0.05]),
            "driver_license": np.random.choice(["None","HMMWV","LMTV","JLTV"], p=[0.20, 0.40, 0.30, 0.10]),
            "med_cat": np.random.choice([1,2,3,4], p=[0.70, 0.20, 0.08, 0.02]),
            "dental_cat": np.random.choice([1,2,3,4], p=[0.80, 0.15, 0.04, 0.01]),
            "language": position.language_required if position.language_required else np.random.choice(
                ["None","Spanish","Arabic","French"], p=[0.70, 0.15, 0.10, 0.05]
            ),
            "dwell_months": np.random.randint(6, 36),  # Realistic dwell (6-36 months)
            "available_from": (datetime.today() + timedelta(days=int(np.random.randint(0, 90)))).date(),
            "rank_num": {"E-1":1, "E-2":2, "E-3":3, "E-4":4, "E-5":5, "E-6":6, "E-7":7, "E-8":8, "O-1":1, "O-2":2, "O-3":3}.get(rank, 3),
            "clear_num": {"None":0, "Secret":1, "TS":2}.get(position.clearance, 1),
            "deployable": 1 if np.random.rand() > 0.1 else 0,
            # Unit-specific fields
            "uic": unit.uic,
            "para_line": position.para_line,
            "duty_position": position.title,
            "leadership_level": int(position.leadership_level),
        }

        # Merge extended profile data if available
        base_data.update(extended_profile_data)

        return base_data

    def _create_extended_soldier(
        self,
        soldier_id: int,
        unit: Unit,
        position: Position
    ) -> SoldierExtended:
        """Create extended soldier record with training, equipment, history."""

        # Parse rank from position
        rank = position.rank_required
        if position.min_rank:
            rank = np.random.choice([position.min_rank, position.max_rank or position.min_rank])

        # Generate training gates
        training_gates = {}

        # Standard gates for all soldiers
        training_gates["weapons_qual"] = TrainingGate(
            name="M4_Qualification",
            completion_date=date.today() - timedelta(days=np.random.randint(0, 180)),
            currency_days=365,
            category="weapon"
        )
        training_gates["pha"] = TrainingGate(
            name="Periodic_Health_Assessment",
            completion_date=date.today() - timedelta(days=np.random.randint(0, 365)),
            currency_days=365,
            category="medical"
        )
        training_gates["sere"] = TrainingGate(
            name="SERE_Training",
            completion_date=date.today() - timedelta(days=np.random.randint(0, 1095)),
            currency_days=1825,  # 5 years
            category="deployment"
        )

        # Position-specific training
        if "radio_operator" in position.training_gates_required:
            training_gates["radio_operator"] = TrainingGate(
                name="Radio_Operator_Course",
                completion_date=date.today() - timedelta(days=np.random.randint(0, 730)),
                currency_days=1825,
                category="general"
            )

        # Equipment qualifications
        equipment_quals = []
        if "LMTV_license" in position.equipment_required:
            equipment_quals.append(Equipment(
                equipment_type="LMTV",
                qualification_level="operator",
                certified_date=date.today() - timedelta(days=np.random.randint(180, 730)),
                expiry_date=date.today() + timedelta(days=365)
            ))

        # Deployment history (20% have deployed)
        deployment_history = []
        if np.random.rand() < 0.20:
            deployment_history.append(DeploymentRecord(
                deployment_name="Operation Inherent Resolve",
                location="Iraq",
                start_date=date.today() - timedelta(days=np.random.randint(540, 1095)),
                end_date=date.today() - timedelta(days=np.random.randint(180, 540)),
                deployment_type="combat",
                positions_held=[position.title]
            ))

        return SoldierExtended(
            soldier_id=soldier_id,
            uic=unit.uic,
            para_line=position.para_line,
            duty_position=position.title,
            leadership_level=position.leadership_level,
            supervisor_id=None,  # Will be linked later if needed
            training_gates=training_gates,
            equipment_quals=equipment_quals,
            deployment_history=deployment_history,
            time_in_position_months=np.random.randint(3, 24),
            time_in_grade_months=self._realistic_tig_for_rank(rank),
            previous_positions=[],
            career_progression_on_track=True
        )

    def _realistic_tig_for_rank(self, rank: str) -> int:
        """Generate realistic time-in-grade based on rank."""
        # Minimum TIG + random additional time
        tig_ranges = {
            "E-1": (1, 6),
            "E-2": (4, 12),
            "E-3": (6, 18),
            "E-4": (12, 36),
            "E-5": (18, 48),
            "E-6": (30, 72),
            "E-7": (48, 96),
            "E-8": (60, 120),
            "O-1": (12, 24),
            "O-2": (24, 36),
            "O-3": (36, 72),
        }

        min_tig, max_tig = tig_ranges.get(rank, (12, 36))
        return np.random.randint(min_tig, max_tig + 1)

    def generate_battalion(
        self,
        battalion_uic: str,
        battalion_name: str,
        unit_types: List[str],
        home_station: str = "JBLM",
        fill_rate: float = 0.95
    ) -> Tuple[pd.DataFrame, Dict[int, SoldierExtended]]:
        """
        Generate an entire battalion with multiple companies.

        Args:
            battalion_uic: Parent battalion UIC
            battalion_name: Battalion name (e.g., "1st Battalion, 2nd Infantry")
            unit_types: List of company types (e.g., ["Infantry", "Infantry", "Infantry", "FieldArtillery"])
            home_station: Base location
            fill_rate: Manning level (0.0-1.0)

        Returns:
            Combined DataFrame of all soldiers and extended records
        """
        all_soldiers_df = []
        all_soldiers_ext = {}

        template_map = {
            "Infantry": MTOELibrary.infantry_rifle_company,
            "FieldArtillery": MTOELibrary.field_artillery_battery,
            "MilitaryIntelligence": MTOELibrary.military_intelligence_company,
            "Engineer": MTOELibrary.engineer_company,
        }

        for idx, unit_type in enumerate(unit_types):
            company_letter = chr(65 + idx)  # A, B, C, D, ...
            company_uic = f"{battalion_uic}{company_letter}"
            company_short_name = f"{company_letter}/{battalion_name.split(',')[0]}"
            company_name = f"{company_letter} Company, {battalion_name}"

            template_func = template_map.get(unit_type)
            if not template_func:
                raise ValueError(f"Unknown unit type: {unit_type}")

            template = template_func()
            unit = self.create_unit(
                template=template,
                uic=company_uic,
                name=company_name,
                short_name=company_short_name,
                home_station=home_station,
                parent_uic=battalion_uic
            )

            soldiers_df, soldiers_ext = self.generate_soldiers_for_unit(
                unit, fill_rate=fill_rate, base_soldier_id=self.soldier_counter
            )

            all_soldiers_df.append(soldiers_df)
            all_soldiers_ext.update(soldiers_ext)

        combined_df = pd.concat(all_soldiers_df, ignore_index=True)
        return combined_df, all_soldiers_ext


# -------------------------
# Convenience functions
# -------------------------

def quick_generate_force(
    n_battalions: int = 1,
    companies_per_bn: int = 4,
    seed: int = 42,
    fill_rate: float = 0.93  # More realistic 93% manning
) -> Tuple[UnitGenerator, pd.DataFrame, Dict[int, SoldierExtended]]:
    """
    Quick generation of a multi-battalion force.

    Returns:
        - generator: UnitGenerator instance with all units
        - soldiers_df: Combined DataFrame
        - soldiers_ext: Extended soldier records
    """
    generator = UnitGenerator(seed=seed)
    all_soldiers_df = []
    all_soldiers_ext = {}

    unit_type_pools = ["Infantry", "Infantry", "FieldArtillery", "Engineer", "MilitaryIntelligence"]

    for bn_idx in range(n_battalions):
        bn_uic = f"WFF{bn_idx+1:02d}"
        bn_name = f"{bn_idx+1}-2 SBCT"

        unit_types = np.random.choice(unit_type_pools, size=companies_per_bn, replace=True).tolist()

        soldiers_df, soldiers_ext = generator.generate_battalion(
            battalion_uic=bn_uic,
            battalion_name=bn_name,
            unit_types=unit_types,
            home_station=np.random.choice(["JBLM", "JBER", "Hawaii"]),
            fill_rate=fill_rate
        )

        all_soldiers_df.append(soldiers_df)
        all_soldiers_ext.update(soldiers_ext)

    combined_df = pd.concat(all_soldiers_df, ignore_index=True)
    return generator, combined_df, all_soldiers_ext
