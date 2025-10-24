"""
manning_document.py
-------------------

Manning document system for exercise tasking.

Creates capability-based requirements (not individual positions) and converts
them to billets for EMD optimization. Mirrors real-world tasking process.

Classes:
- CapabilityRequirement: Defines a capability need (e.g., "Infantry Squad")
- ManningDocument: Collection of requirements for an exercise
- ManningDocumentBuilder: Converts requirements to EMD billets
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import json

from unit_types import Unit, LeadershipLevel
from readiness_tracker import ReadinessProfile

# Import extended requirements
try:
    from billet_requirements import BilletRequirements, create_basic_requirements
    EXTENDED_REQUIREMENTS_AVAILABLE = True
except ImportError:
    EXTENDED_REQUIREMENTS_AVAILABLE = False
    BilletRequirements = None


@dataclass
class CapabilityRequirement:
    """
    Defines a capability requirement (not a specific position).

    Example: "Need 3x Infantry Squads" or "Need 1x MI Analysis Team"

    This is how real tasking works - you ask for capabilities, not individuals.
    """
    capability_name: str
    quantity: int  # How many of this capability

    # Core requirements
    mos_required: str
    min_rank: str
    max_rank: Optional[str] = None
    skill_level_req: int = 1
    clearance_req: str = "Secret"

    # Team composition (for multi-person capabilities)
    team_size: int = 1  # If >1, represents a team/squad
    leader_required: bool = False  # Does this need a leader?
    subordinate_ranks: Optional[List[str]] = None  # Ranks for subordinates

    # Special requirements
    airborne_required: bool = False
    language_required: Optional[str] = None
    equipment_required: List[str] = field(default_factory=list)
    training_gates_required: List[str] = field(default_factory=list)

    # Priority
    priority: int = 2  # 1=low, 2=med, 3=high

    # Location
    location: str = "JBLM"
    start_date: Optional[date] = None
    duration_days: int = 90

    # Sourcing preferences
    prefer_from_uic: Optional[str] = None  # Prefer sourcing from specific unit
    keep_team_together: bool = True  # Prefer pulling intact teams vs individuals

    # Extended qualifications (optional, for detailed matching)
    extended_requirements: Optional[BilletRequirements] = None


@dataclass
class ManningDocument:
    """
    A manning document defining all requirements for an exercise.

    This is analogous to a WARNO/FRAGO tasking with manning requirements.
    """
    document_id: str
    exercise_name: str
    mission_description: str
    requesting_unit: str  # Who requested this manning

    # Requirements
    requirements: List[CapabilityRequirement] = field(default_factory=list)

    # Constraints
    max_units_sourced: Optional[int] = None  # Limit cross-leveling complexity
    readiness_profile: Optional[str] = None  # Reference to ReadinessProfile

    # Timeline
    publication_date: date = field(default_factory=date.today)
    execution_start: date = field(default_factory=lambda: date.today() + timedelta(days=30))
    execution_end: Optional[date] = None

    # Metadata
    author: str = "G-3"
    classification: str = "UNCLASS"

    def total_billets(self) -> int:
        """Calculate total number of billets (individuals) needed."""
        return sum(req.quantity * req.team_size for req in self.requirements)

    def total_capabilities(self) -> int:
        """Calculate total number of capabilities (teams/units) needed."""
        return sum(req.quantity for req in self.requirements)

    def requirements_by_priority(self) -> Dict[int, List[CapabilityRequirement]]:
        """Group requirements by priority."""
        by_priority = {1: [], 2: [], 3: []}
        for req in self.requirements:
            by_priority[req.priority].append(req)
        return by_priority

    def add_requirement(self, requirement: CapabilityRequirement):
        """Add a requirement to the document."""
        self.requirements.append(requirement)

    def export_json(self, filepath: str):
        """Export manning document to JSON."""
        data = {
            "document_id": self.document_id,
            "exercise_name": self.exercise_name,
            "mission_description": self.mission_description,
            "requesting_unit": self.requesting_unit,
            "publication_date": str(self.publication_date),
            "execution_start": str(self.execution_start),
            "total_billets": self.total_billets(),
            "requirements": [
                {
                    "capability": req.capability_name,
                    "quantity": req.quantity,
                    "team_size": req.team_size,
                    "mos": req.mos_required,
                    "rank": f"{req.min_rank}-{req.max_rank or req.min_rank}",
                    "priority": req.priority,
                    "location": req.location,
                }
                for req in self.requirements
            ]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


class ManningDocumentBuilder:
    """
    Converts ManningDocument requirements to EMD billets.

    This is the bridge between capability-based tasking and position-based optimization.
    """

    @staticmethod
    def generate_billets_from_document(
        manning_doc: ManningDocument,
        base_billet_id: int = 101
    ) -> pd.DataFrame:
        """
        Convert a ManningDocument to EMD-compatible billets DataFrame.

        Each CapabilityRequirement may generate multiple billets if team_size > 1.

        Returns:
            DataFrame with columns matching EMD.billets structure
        """
        billets = []
        billet_id = base_billet_id

        rank_num_map = {"E-1":1, "E-2":2, "E-3":3, "E-4":4, "E-5":5, "E-6":6, "E-7":7, "E-8":8, "O-1":1, "O-2":2, "O-3":3}
        clear_num_map = {"None":0, "Secret":1, "TS":2}

        # Helper function to add extended requirements to billet dict
        def add_extended_requirements(billet_dict: Dict, req: CapabilityRequirement, position_type: str = "individual"):
            """Add extended requirements to billet dictionary if available."""
            if EXTENDED_REQUIREMENTS_AVAILABLE and req.extended_requirements:
                ext_req = req.extended_requirements
                ext_req.billet_id = billet_dict['billet_id']
                ext_req.capability_name = req.capability_name
                ext_req.position_title = f"{req.capability_name} - {position_type}"

                # Merge extended requirement fields
                req_dict = ext_req.to_dict()
                billet_dict.update(req_dict)

            return billet_dict

        for req in manning_doc.requirements:
            # Generate billets for each quantity requested
            for i in range(req.quantity):
                # If team, generate leader + subordinates
                if req.team_size > 1 and req.leader_required:
                    # Leader billet
                    leader_billet = {
                        "billet_id": billet_id,
                        "base": req.location,
                        "priority": req.priority,
                        "mos_required": req.mos_required,
                        "min_rank": req.min_rank,
                        "max_rank": req.max_rank or req.min_rank,
                        "skill_level_req": req.skill_level_req,
                        "clearance_req": req.clearance_req,
                        "airborne_required": 1 if req.airborne_required else 0,
                        "language_required": req.language_required or "None",
                        "start_date": req.start_date or manning_doc.execution_start,
                        "min_rank_num": rank_num_map.get(req.min_rank, 3),
                        "max_rank_num": rank_num_map.get(req.max_rank or req.min_rank, 6),
                        "clear_req_num": clear_num_map.get(req.clearance_req, 1),
                        "capability_name": req.capability_name,
                        "capability_instance": i + 1,
                        "team_position": "leader",
                        "keep_together": req.keep_team_together,
                    }
                    leader_billet = add_extended_requirements(leader_billet, req, "leader")
                    billets.append(leader_billet)
                    billet_id += 1

                    # Subordinate billets
                    subordinate_count = req.team_size - 1
                    for j in range(subordinate_count):
                        # Subordinates typically one rank lower
                        sub_rank = req.subordinate_ranks[j] if req.subordinate_ranks and j < len(req.subordinate_ranks) else ManningDocumentBuilder._decrement_rank(req.min_rank)

                        sub_billet = {
                            "billet_id": billet_id,
                            "base": req.location,
                            "priority": req.priority,
                            "mos_required": req.mos_required,
                            "min_rank": sub_rank,
                            "max_rank": sub_rank,
                            "skill_level_req": max(1, req.skill_level_req - 1),
                            "clearance_req": req.clearance_req,
                            "airborne_required": 1 if req.airborne_required else 0,
                            "language_required": req.language_required or "None",
                            "start_date": req.start_date or manning_doc.execution_start,
                            "min_rank_num": rank_num_map.get(sub_rank, 3),
                            "max_rank_num": rank_num_map.get(sub_rank, 4),
                            "clear_req_num": clear_num_map.get(req.clearance_req, 1),
                            "capability_name": req.capability_name,
                            "capability_instance": i + 1,
                            "team_position": f"member_{j+1}",
                            "keep_together": req.keep_team_together,
                        }
                        sub_billet = add_extended_requirements(sub_billet, req, f"member_{j+1}")
                        billets.append(sub_billet)
                        billet_id += 1

                else:
                    # Single-person capability
                    single_billet = {
                        "billet_id": billet_id,
                        "base": req.location,
                        "priority": req.priority,
                        "mos_required": req.mos_required,
                        "min_rank": req.min_rank,
                        "max_rank": req.max_rank or req.min_rank,
                        "skill_level_req": req.skill_level_req,
                        "clearance_req": req.clearance_req,
                        "airborne_required": 1 if req.airborne_required else 0,
                        "language_required": req.language_required or "None",
                        "start_date": req.start_date or manning_doc.execution_start,
                        "min_rank_num": rank_num_map.get(req.min_rank, 3),
                        "max_rank_num": rank_num_map.get(req.max_rank or req.min_rank, 6),
                        "clear_req_num": clear_num_map.get(req.clearance_req, 1),
                        "capability_name": req.capability_name,
                        "capability_instance": i + 1,
                        "team_position": "individual",
                        "keep_together": False,
                    }
                    single_billet = add_extended_requirements(single_billet, req, "individual")
                    billets.append(single_billet)
                    billet_id += 1

        return pd.DataFrame(billets)

    @staticmethod
    def _decrement_rank(rank: str) -> str:
        """Helper to get one rank lower."""
        rank_sequence = ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9"]
        try:
            idx = rank_sequence.index(rank)
            return rank_sequence[max(0, idx - 1)]
        except ValueError:
            return "E-4"  # Default


# -------------------------
# Pre-built manning document templates
# -------------------------

class ManningDocumentTemplates:
    """Common manning document templates for exercises."""

    @staticmethod
    def infantry_task_force(location: str = "Guam") -> ManningDocument:
        """
        Infantry task force for joint exercise.

        3x Infantry Squads + Fire Support Team + HQ element
        """
        doc = ManningDocument(
            document_id="MDTF-2025-001",
            exercise_name="Valiant Shield 2025",
            mission_description="Infantry task force for joint forcible entry exercise",
            requesting_unit="1st MDTF"
        )

        # Infantry squads
        doc.add_requirement(CapabilityRequirement(
            capability_name="Infantry Squad",
            quantity=3,
            mos_required="11B",
            min_rank="E-6",  # Squad leader
            team_size=9,
            leader_required=True,
            subordinate_ranks=["E-5", "E-4", "E-4", "E-5", "E-4", "E-3", "E-3", "E-3"],
            priority=3,
            location=location,
            keep_team_together=True
        ))

        # Fire Support Team
        doc.add_requirement(CapabilityRequirement(
            capability_name="Fire Support Team",
            quantity=1,
            mos_required="13F",
            min_rank="E-6",
            team_size=4,
            leader_required=True,
            subordinate_ranks=["E-5", "E-4", "E-4"],
            priority=3,
            location=location,
            keep_team_together=True
        ))

        # Headquarters element
        doc.add_requirement(CapabilityRequirement(
            capability_name="Task Force Commander",
            quantity=1,
            mos_required="11A",
            min_rank="O-3",
            max_rank="O-4",
            priority=3,
            location=location
        ))

        doc.add_requirement(CapabilityRequirement(
            capability_name="Task Force Senior NCO",
            quantity=1,
            mos_required="11B",
            min_rank="E-8",
            priority=3,
            location=location
        ))

        return doc

    @staticmethod
    def intelligence_support_package(location: str = "Japan") -> ManningDocument:
        """
        Intelligence support for theater operations.
        """
        doc = ManningDocument(
            document_id="MDTF-2025-002",
            exercise_name="Orient Shield 2025",
            mission_description="Intelligence support package for theater security cooperation",
            requesting_unit="I Corps G-2"
        )

        # All-source analysis team
        doc.add_requirement(CapabilityRequirement(
            capability_name="All-Source Analysis Team",
            quantity=2,
            mos_required="35F",
            min_rank="E-5",
            team_size=4,
            leader_required=True,
            clearance_req="TS",
            priority=3,
            location=location,
            keep_team_together=True
        ))

        # HUMINT collection team
        doc.add_requirement(CapabilityRequirement(
            capability_name="HUMINT Collection Team",
            quantity=1,
            mos_required="35M",
            min_rank="E-6",
            team_size=3,
            leader_required=True,
            clearance_req="TS",
            language_required="Arabic",
            priority=2,
            location=location,
            keep_team_together=True
        ))

        # Signals intelligence
        doc.add_requirement(CapabilityRequirement(
            capability_name="SIGINT Analyst",
            quantity=4,
            mos_required="35N",
            min_rank="E-4",
            clearance_req="TS",
            priority=2,
            location=location
        ))

        return doc

    @staticmethod
    def logistics_support_element(location: str = "Hawaii") -> ManningDocument:
        """
        Logistics support for extended operations.
        """
        doc = ManningDocument(
            document_id="MDTF-2025-003",
            exercise_name="Pacific Pathways 2025",
            mission_description="Logistics support element for multi-nation training",
            requesting_unit="1st MDTF S-4"
        )

        # Supply specialists
        doc.add_requirement(CapabilityRequirement(
            capability_name="Supply Team",
            quantity=2,
            mos_required="92Y",
            min_rank="E-5",
            team_size=3,
            leader_required=True,
            priority=2,
            location=location
        ))

        # Motor transport
        doc.add_requirement(CapabilityRequirement(
            capability_name="Motor Transport Operator",
            quantity=6,
            mos_required="88M",
            min_rank="E-4",
            equipment_required=["LMTV_license"],
            priority=2,
            location=location
        ))

        # Medical support
        doc.add_requirement(CapabilityRequirement(
            capability_name="Combat Medic",
            quantity=4,
            mos_required="68W",
            min_rank="E-4",
            skill_level_req=2,
            priority=3,
            location=location
        ))

        return doc


def create_custom_manning_document(
    exercise_name: str,
    capabilities: List[Dict],
    location: str = "JBLM"
) -> ManningDocument:
    """
    Create a custom manning document from a simple capability list.

    Args:
        exercise_name: Name of the exercise
        capabilities: List of dicts with keys: name, mos, rank, quantity, priority, team_size
        location: Base location

    Returns:
        ManningDocument

    Example:
        capabilities = [
            {"name": "Rifle Squad", "mos": "11B", "rank": "E-6", "quantity": 2, "priority": 3, "team_size": 9},
            {"name": "Medic", "mos": "68W", "rank": "E-5", "quantity": 3, "priority": 3, "team_size": 1}
        ]
    """
    doc = ManningDocument(
        document_id=f"CUSTOM-{datetime.now().strftime('%Y%m%d-%H%M')}",
        exercise_name=exercise_name,
        mission_description=f"Custom manning for {exercise_name}",
        requesting_unit="User"
    )

    for cap in capabilities:
        req = CapabilityRequirement(
            capability_name=cap["name"],
            quantity=cap.get("quantity", 1),
            mos_required=cap["mos"],
            min_rank=cap["rank"],
            team_size=cap.get("team_size", 1),
            leader_required=cap.get("team_size", 1) > 1,
            priority=cap.get("priority", 2),
            location=location
        )
        doc.add_requirement(req)

    return doc
