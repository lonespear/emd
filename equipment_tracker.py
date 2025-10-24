"""
equipment_tracker.py
--------------------

Equipment and vehicle tracking for realistic mission planning.

Tracks:
- Serialized equipment (vehicles, weapons, radios)
- Equipment status (operational, maintenance, deadlined)
- Equipment assignments to units/soldiers
- Equipment requirements for missions

Classes:
- EquipmentItem: Represents a physical equipment item
- EquipmentInventory: Tracks unit equipment holdings
- EquipmentValidator: Validates mission equipment requirements
"""

from __future__ import annotations
import pandas as pd
from datetime import date
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class EquipmentStatus(Enum):
    """Equipment operational status."""
    OPERATIONAL = "Operational"
    MAINTENANCE = "Maintenance"
    DEADLINED = "Deadlined"  # Non-mission capable
    TRANSFERRED = "Transferred"
    LOST = "Lost"


class EquipmentCategory(Enum):
    """Equipment categories."""
    VEHICLE = "Vehicle"
    WEAPON = "Weapon"
    RADIO = "Radio"
    OPTICS = "Optics"
    PROTECTIVE = "Protective"
    MEDICAL = "Medical"
    TOOL = "Tool"


@dataclass
class EquipmentItem:
    """
    Represents a physical equipment item with serial number.

    Examples:
    - HMMWV (serial W123456)
    - M4 Carbine (serial 789012)
    - SINCGARS radio (serial R456789)
    """
    serial_number: str
    nomenclature: str  # Official name (e.g., "M1151 HMMWV")
    category: EquipmentCategory
    nsn: Optional[str] = None  # National Stock Number

    # Status
    status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    assigned_to_unit: Optional[str] = None  # UIC
    assigned_to_soldier: Optional[int] = None  # soldier_id
    location: str = "Home Station"

    # Maintenance
    last_service_date: Optional[date] = None
    next_service_due: Optional[date] = None
    hours_operated: int = 0
    miles_driven: int = 0  # For vehicles

    # Mission-specific
    required_license: Optional[str] = None  # For vehicles
    operator_mos: Optional[List[str]] = None  # MOSs that can operate

    notes: str = ""

    def is_mission_capable(self) -> bool:
        """Check if equipment is mission capable."""
        return self.status == EquipmentStatus.OPERATIONAL

    def is_assigned(self) -> bool:
        """Check if equipment is assigned to unit/soldier."""
        return self.assigned_to_unit is not None or self.assigned_to_soldier is not None


@dataclass
class EquipmentRequirement:
    """
    Defines equipment required for a capability or mission.

    Example: Infantry Squad needs 9x M4, 2x M249, 3x SINCGARS, 1x HMMWV
    """
    nomenclature: str
    category: EquipmentCategory
    quantity: int
    critical: bool = True  # Mission fails without this?
    substitutes: List[str] = field(default_factory=list)  # Acceptable substitutes


class EquipmentInventory:
    """
    Tracks unit equipment holdings.

    Manages equipment assignment, status, and availability.
    """

    def __init__(self):
        self.equipment: Dict[str, EquipmentItem] = {}  # serial_number -> EquipmentItem

    def add_equipment(self, item: EquipmentItem):
        """Add equipment item to inventory."""
        self.equipment[item.serial_number] = item

    def get_unit_equipment(self, uic: str) -> List[EquipmentItem]:
        """Get all equipment assigned to a unit."""
        return [eq for eq in self.equipment.values() if eq.assigned_to_unit == uic]

    def get_available_equipment(
        self,
        category: Optional[EquipmentCategory] = None,
        nomenclature: Optional[str] = None
    ) -> List[EquipmentItem]:
        """
        Get available (unassigned, operational) equipment.

        Args:
            category: Filter by category
            nomenclature: Filter by nomenclature

        Returns:
            List of available equipment
        """
        available = []

        for eq in self.equipment.values():
            # Must be mission capable and unassigned
            if not eq.is_mission_capable() or eq.is_assigned():
                continue

            # Apply filters
            if category and eq.category != category:
                continue
            if nomenclature and eq.nomenclature != nomenclature:
                continue

            available.append(eq)

        return available

    def get_equipment_status_report(self, uic: Optional[str] = None) -> pd.DataFrame:
        """
        Generate equipment status report.

        Args:
            uic: If provided, filter to specific unit

        Returns:
            DataFrame with equipment status
        """
        equipment_list = self.get_unit_equipment(uic) if uic else list(self.equipment.values())

        rows = []
        for eq in equipment_list:
            rows.append({
                "serial_number": eq.serial_number,
                "nomenclature": eq.nomenclature,
                "category": eq.category.value,
                "status": eq.status.value,
                "assigned_unit": eq.assigned_to_unit or "Unassigned",
                "location": eq.location,
                "mission_capable": eq.is_mission_capable()
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            # Add summary statistics
            print("\nEquipment Status Summary:")
            print(f"  Total Items: {len(df)}")
            print(f"  Operational: {(df['status'] == 'Operational').sum()}")
            print(f"  Maintenance: {(df['status'] == 'Maintenance').sum()}")
            print(f"  Deadlined: {(df['status'] == 'Deadlined').sum()}")

        return df

    def calculate_readiness_rate(self, uic: Optional[str] = None) -> float:
        """
        Calculate equipment readiness rate (% mission capable).

        Args:
            uic: If provided, calculate for specific unit

        Returns:
            Readiness rate (0.0-1.0)
        """
        equipment_list = self.get_unit_equipment(uic) if uic else list(self.equipment.values())

        if not equipment_list:
            return 0.0

        operational_count = sum(1 for eq in equipment_list if eq.is_mission_capable())
        return operational_count / len(equipment_list)


class EquipmentValidator:
    """
    Validates that units/soldiers have required equipment for missions.
    """

    @staticmethod
    def validate_unit_equipment(
        uic: str,
        requirements: List[EquipmentRequirement],
        inventory: EquipmentInventory
    ) -> Tuple[bool, List[str]]:
        """
        Validate that a unit has required equipment.

        Args:
            uic: Unit to check
            requirements: List of equipment requirements
            inventory: Equipment inventory

        Returns:
            (has_all_equipment, list_of_shortfalls)
        """
        unit_equipment = inventory.get_unit_equipment(uic)
        shortfalls = []

        for req in requirements:
            # Count how many of this item the unit has (operational only)
            count = sum(
                1 for eq in unit_equipment
                if eq.nomenclature == req.nomenclature and eq.is_mission_capable()
            )

            # Check for substitutes if primary not available
            if count < req.quantity and req.substitutes:
                for substitute in req.substitutes:
                    substitute_count = sum(
                        1 for eq in unit_equipment
                        if eq.nomenclature == substitute and eq.is_mission_capable()
                    )
                    count += substitute_count

            # Record shortfall
            if count < req.quantity:
                shortfall_msg = f"{req.nomenclature}: need {req.quantity}, have {count}"
                if req.critical:
                    shortfall_msg += " (CRITICAL)"
                shortfalls.append(shortfall_msg)

        has_all = len(shortfalls) == 0
        return has_all, shortfalls

    @staticmethod
    def can_soldier_operate_equipment(
        soldier_row: pd.Series,
        equipment: EquipmentItem
    ) -> Tuple[bool, str]:
        """
        Check if a soldier can operate specific equipment.

        Args:
            soldier_row: Soldier DataFrame row
            equipment: Equipment item

        Returns:
            (can_operate, reason)
        """
        # Check MOS requirement
        if equipment.operator_mos:
            if soldier_row["mos"] not in equipment.operator_mos:
                return False, f"MOS {soldier_row['mos']} not qualified for {equipment.nomenclature}"

        # Check license requirement for vehicles
        if equipment.required_license:
            if "driver_license" in soldier_row:
                if equipment.required_license not in str(soldier_row["driver_license"]):
                    return False, f"Missing {equipment.required_license} license"

        return True, "Qualified"


# -------------------------
# Equipment generators
# -------------------------

def generate_infantry_company_equipment(uic: str, inventory: EquipmentInventory):
    """
    Generate typical Infantry Company equipment.

    - Weapons (M4s, M249s, M240s, etc.)
    - Vehicles (HMMWVs, JLTVs)
    - Radios (SINCGARS, ASIP)
    - Optics (ACOGs, PEQ-15s)
    """
    import random

    # Weapons
    for i in range(140):  # ~140 M4s for company
        inventory.add_equipment(EquipmentItem(
            serial_number=f"M4-{uic}-{i:04d}",
            nomenclature="M4 Carbine",
            category=EquipmentCategory.WEAPON,
            status=EquipmentStatus.OPERATIONAL if random.random() > 0.05 else EquipmentStatus.MAINTENANCE,
            assigned_to_unit=uic,
            operator_mos=["11B", "11A"]
        ))

    # SAWs (M249)
    for i in range(12):
        inventory.add_equipment(EquipmentItem(
            serial_number=f"M249-{uic}-{i:04d}",
            nomenclature="M249 SAW",
            category=EquipmentCategory.WEAPON,
            status=EquipmentStatus.OPERATIONAL if random.random() > 0.10 else EquipmentStatus.MAINTENANCE,
            assigned_to_unit=uic,
            operator_mos=["11B"]
        ))

    # Vehicles (HMMWVs)
    for i in range(15):
        inventory.add_equipment(EquipmentItem(
            serial_number=f"HMMWV-{uic}-{i:04d}",
            nomenclature="M1151 HMMWV",
            category=EquipmentCategory.VEHICLE,
            status=EquipmentStatus.OPERATIONAL if random.random() > 0.15 else EquipmentStatus.MAINTENANCE,
            assigned_to_unit=uic,
            required_license="HMMWV",
            miles_driven=random.randint(5000, 50000)
        ))

    # Radios
    for i in range(30):
        inventory.add_equipment(EquipmentItem(
            serial_number=f"SINCGARS-{uic}-{i:04d}",
            nomenclature="SINCGARS Radio",
            category=EquipmentCategory.RADIO,
            status=EquipmentStatus.OPERATIONAL if random.random() > 0.08 else EquipmentStatus.MAINTENANCE,
            assigned_to_unit=uic
        ))


def generate_field_artillery_battery_equipment(uic: str, inventory: EquipmentInventory):
    """Generate typical FA Battery equipment (Howitzers, FDC equipment, trucks)."""
    import random

    # M777 Howitzers
    for i in range(6):
        inventory.add_equipment(EquipmentItem(
            serial_number=f"M777-{uic}-{i:04d}",
            nomenclature="M777 Howitzer",
            category=EquipmentCategory.WEAPON,
            status=EquipmentStatus.OPERATIONAL if random.random() > 0.10 else EquipmentStatus.MAINTENANCE,
            assigned_to_unit=uic,
            operator_mos=["13B"]
        ))

    # LMTVs (for ammo/resupply)
    for i in range(10):
        inventory.add_equipment(EquipmentItem(
            serial_number=f"LMTV-{uic}-{i:04d}",
            nomenclature="LMTV 5-ton",
            category=EquipmentCategory.VEHICLE,
            status=EquipmentStatus.OPERATIONAL if random.random() > 0.15 else EquipmentStatus.MAINTENANCE,
            assigned_to_unit=uic,
            required_license="LMTV",
            miles_driven=random.randint(10000, 80000)
        ))
