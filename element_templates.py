"""
Element Templates - Pre-defined military unit element structures

Provides standard organizational templates for common military elements
from squad to company level, including specialized teams.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Position:
    """Individual position within an element."""
    position_name: str
    rank: str
    mos: str
    count: int
    is_leader: bool = False


@dataclass
class ElementTemplate:
    """Template defining structure of a military element."""
    name: str
    description: str
    total_size: int
    primary_mos: str  # Primary MOS for the element
    positions: List[Position]
    element_type: str  # "Infantry", "Support", "Medical", "Maintenance", "Aviation"


# ============================================================================
# Infantry Elements
# ============================================================================

INFANTRY_PLATOON = ElementTemplate(
    name="Infantry Platoon",
    description="Standard infantry platoon with 3 squads",
    total_size=40,
    primary_mos="11B",
    element_type="Infantry",
    positions=[
        Position("Platoon Leader", "O-1", "11A", 1, is_leader=True),
        Position("Platoon Sergeant", "E-7", "11B", 1, is_leader=True),
        Position("Radio Operator", "E-4", "11B", 1),
        Position("Platoon Medic", "E-5", "68W", 1),
        # 3 Squads (12 each = 36 total)
        Position("Squad Leader", "E-6", "11B", 3, is_leader=True),
        Position("Team Leader", "E-5", "11B", 6),
        Position("Grenadier", "E-4", "11B", 6),
        Position("Automatic Rifleman", "E-4", "11B", 6),
        Position("Rifleman", "E-3", "11B", 15),
    ]
)

INFANTRY_COMPANY = ElementTemplate(
    name="Infantry Company",
    description="Standard infantry rifle company with 3 platoons",
    total_size=180,
    primary_mos="11B",
    element_type="Infantry",
    positions=[
        # Company HQ
        Position("Company Commander", "O-3", "11A", 1, is_leader=True),
        Position("Executive Officer", "O-2", "11A", 1, is_leader=True),
        Position("First Sergeant", "E-8", "11B", 1, is_leader=True),
        Position("Company Medic", "E-6", "68W", 2),
        Position("Radio Operator", "E-4", "25U", 2),
        Position("Supply Sergeant", "E-6", "92Y", 1),
        Position("Armorer", "E-5", "11B", 1),
        # 3 Platoons (40 each = 120 total)
        Position("Platoon Leader", "O-1", "11A", 3, is_leader=True),
        Position("Platoon Sergeant", "E-7", "11B", 3, is_leader=True),
        Position("Squad Leader", "E-6", "11B", 9),
        Position("Team Leader", "E-5", "11B", 18),
        Position("Grenadier", "E-4", "11B", 18),
        Position("Automatic Rifleman", "E-4", "11B", 18),
        Position("Rifleman", "E-3", "11B", 45),
        Position("Platoon Medic", "E-5", "68W", 3),
        Position("Platoon RTO", "E-4", "11B", 3),
        # Weapons Platoon (51 total)
        Position("Weapons Platoon Leader", "O-1", "11A", 1, is_leader=True),
        Position("Weapons Platoon Sergeant", "E-7", "11B", 1, is_leader=True),
        Position("Mortar Section Leader", "E-6", "11C", 1),
        Position("Mortar Squad Leader", "E-5", "11C", 2),
        Position("Mortar Gunner", "E-4", "11C", 6),
        Position("Mortar Ammo Bearer", "E-3", "11C", 6),
        Position("MG Section Leader", "E-6", "11B", 1),
        Position("MG Squad Leader", "E-5", "11B", 2),
        Position("Machine Gunner", "E-4", "11B", 6),
        Position("Asst Gunner", "E-3", "11B", 6),
        Position("Javelin Gunner", "E-4", "11B", 4),
        Position("Weapons Squad Member", "E-3", "11B", 10),
    ]
)


# ============================================================================
# Support Elements
# ============================================================================

MAINTENANCE_SECTION = ElementTemplate(
    name="Maintenance Section",
    description="Field maintenance section for equipment repair",
    total_size=12,
    primary_mos="91B",
    element_type="Maintenance",
    positions=[
        Position("Section Chief", "E-6", "91B", 1, is_leader=True),
        Position("Assistant Section Chief", "E-5", "91B", 1),
        Position("Wheel Mechanic", "E-4", "91B", 3),
        Position("Track Mechanic", "E-4", "91M", 2),
        Position("Recovery Specialist", "E-4", "91R", 1),
        Position("Apprentice Mechanic", "E-3", "91B", 3),
        Position("Parts Clerk", "E-4", "92A", 1),
    ]
)

FIELD_FEEDING_TEAM = ElementTemplate(
    name="Field Feeding Team",
    description="Mobile field kitchen team",
    total_size=8,
    primary_mos="92G",
    element_type="Support",
    positions=[
        Position("Team Leader", "E-6", "92G", 1, is_leader=True),
        Position("Assistant Team Leader", "E-5", "92G", 1),
        Position("Cook", "E-4", "92G", 3),
        Position("Food Service Specialist", "E-3", "92G", 2),
        Position("Driver", "E-4", "88M", 1),
    ]
)


# ============================================================================
# Medical Elements
# ============================================================================

FORWARD_SURGICAL_TEAM = ElementTemplate(
    name="Forward Surgical Team (FST)",
    description="Mobile surgical team for forward trauma care",
    total_size=20,
    primary_mos="Multiple",
    element_type="Medical",
    positions=[
        Position("Team Chief (Surgeon)", "O-4", "6 1H", 1, is_leader=True),
        Position("General Surgeon", "O-4", "61H", 1, is_leader=True),
        Position("Orthopedic Surgeon", "O-3", "61H", 1),
        Position("Anesthesiologist", "O-3", "60N", 1),
        Position("Certified Nurse Anesthetist", "O-2", "66F", 1),
        Position("OR Nurse", "O-2", "66H", 2),
        Position("OR Specialist", "E-6", "68D", 2),
        Position("Licensed Practical Nurse", "E-5", "68C", 2),
        Position("Combat Medic (Surgical)", "E-5", "68W", 4),
        Position("Combat Medic", "E-4", "68W", 3),
        Position("Medical Supply Specialist", "E-5", "68J", 1),
        Position("Biomedical Equipment Specialist", "E-5", "68A", 1),
    ]
)


# ============================================================================
# Element Template Registry
# ============================================================================

ALL_ELEMENT_TEMPLATES: Dict[str, ElementTemplate] = {
    "Infantry Platoon": INFANTRY_PLATOON,
    "Infantry Company": INFANTRY_COMPANY,
    "Maintenance Section": MAINTENANCE_SECTION,
    "Field Feeding Team": FIELD_FEEDING_TEAM,
    "Forward Surgical Team (FST)": FORWARD_SURGICAL_TEAM,
}


def get_element_template(name: str) -> ElementTemplate:
    """Get element template by name."""
    if name not in ALL_ELEMENT_TEMPLATES:
        raise ValueError(f"Unknown element template: {name}")
    return ALL_ELEMENT_TEMPLATES[name]


def get_all_element_names() -> List[str]:
    """Get list of all available element template names."""
    return list(ALL_ELEMENT_TEMPLATES.keys())


def get_element_summary(name: str) -> str:
    """Get formatted summary string for dropdown display."""
    template = get_element_template(name)
    return f"{template.name} (~{template.total_size} soldiers)"
