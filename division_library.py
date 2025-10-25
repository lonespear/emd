"""
Division Library - Real U.S. Army Active Division Structures

Contains the actual brigade composition for all active U.S. Army divisions.
Data sourced from official Army organization as of 2024-2025.
"""

from typing import Dict, List, TypedDict


class BrigadeConfig(TypedDict):
    """Brigade configuration within a division."""
    name: str  # e.g., "1st BCT", "2nd ABCT"
    type: str  # "IBCT", "SBCT", "ABCT"
    specialty: str  # "airborne", "air_assault", "stryker", "armor", "standard"
    soldiers: int  # Approximate authorized strength


class DivisionConfig(TypedDict):
    """Complete division configuration."""
    name: str
    nickname: str
    home_station: str
    theater: str  # "FORSCOM", "USAREUR", "INDOPACOM", "USARAK"
    brigades: List[BrigadeConfig]
    div_artillery: bool  # Has division artillery brigade
    div_support: bool  # Has division support/sustainment brigade
    total_soldiers: int


# ============================================================================
# Active U.S. Army Divisions
# ============================================================================

ACTIVE_DIVISIONS: Dict[str, DivisionConfig] = {

    # ------------------------------------------------------------------------
    # XVIII Airborne Corps
    # ------------------------------------------------------------------------

    "82nd_airborne": {
        "name": "82nd Airborne Division",
        "nickname": "All American",
        "home_station": "Fort Liberty",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st BCT", "type": "IBCT", "specialty": "airborne", "soldiers": 3200},
            {"name": "2nd BCT", "type": "IBCT", "specialty": "airborne", "soldiers": 3200},
            {"name": "3rd BCT", "type": "IBCT", "specialty": "airborne", "soldiers": 3200},
        ],
        "div_artillery": True,  # 82nd DIVARTY
        "div_support": True,  # 82nd Sustainment Brigade
        "total_soldiers": 11500,
    },

    "101st_airborne": {
        "name": "101st Airborne Division (Air Assault)",
        "nickname": "Screaming Eagles",
        "home_station": "Fort Campbell",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st BCT", "type": "IBCT", "specialty": "air_assault", "soldiers": 4100},
            {"name": "2nd BCT", "type": "IBCT", "specialty": "air_assault", "soldiers": 4100},
            {"name": "3rd BCT", "type": "IBCT", "specialty": "air_assault", "soldiers": 4100},
            {"name": "4th BCT (RAKKASANS)", "type": "IBCT", "specialty": "air_assault", "soldiers": 4100},
        ],
        "div_artillery": True,  # 101st DIVARTY
        "div_support": True,  # 101st Sustainment Brigade
        "total_soldiers": 19000,
    },

    "10th_mountain": {
        "name": "10th Mountain Division (Light Infantry)",
        "nickname": "Climb to Glory",
        "home_station": "Fort Drum",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st BCT", "type": "IBCT", "specialty": "light_infantry", "soldiers": 4300},
            {"name": "2nd BCT", "type": "IBCT", "specialty": "light_infantry", "soldiers": 4300},
            {"name": "3rd BCT", "type": "IBCT", "specialty": "light_infantry", "soldiers": 4300},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 15000,
    },

    "3rd_infantry": {
        "name": "3rd Infantry Division (Mechanized)",
        "nickname": "Rock of the Marne",
        "home_station": "Fort Stewart",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4700},
            {"name": "2nd ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4700},
            {"name": "1st SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4500},
            {"name": "2nd IBCT", "type": "IBCT", "specialty": "standard", "soldiers": 4200},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 20500,
    },

    # ------------------------------------------------------------------------
    # III Corps
    # ------------------------------------------------------------------------

    "1st_cavalry": {
        "name": "1st Cavalry Division",
        "nickname": "First Team",
        "home_station": "Fort Cavazos",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st ABCT (Ironhorse)", "type": "ABCT", "specialty": "armor", "soldiers": 4800},
            {"name": "2nd ABCT (Blackjack)", "type": "ABCT", "specialty": "armor", "soldiers": 4800},
            {"name": "3rd ABCT (Greywolf)", "type": "ABCT", "specialty": "armor", "soldiers": 4800},
            {"name": "1st SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4600},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 21000,
    },

    "1st_armored": {
        "name": "1st Armored Division",
        "nickname": "Old Ironsides",
        "home_station": "Fort Bliss",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4750},
            {"name": "2nd ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4750},
            {"name": "3rd ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4750},
            {"name": "1st SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4550},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 20800,
    },

    "1st_infantry": {
        "name": "1st Infantry Division",
        "nickname": "Big Red One",
        "home_station": "Fort Riley",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4700},
            {"name": "2nd ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4700},
            {"name": "1st IBCT", "type": "IBCT", "specialty": "standard", "soldiers": 4100},
            {"name": "2nd IBCT (Dagger)", "type": "IBCT", "specialty": "standard", "soldiers": 4100},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 19500,
    },

    "4th_infantry": {
        "name": "4th Infantry Division (Mechanized)",
        "nickname": "Ivy Division",
        "home_station": "Fort Carson",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4500},
            {"name": "2nd SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4500},
            {"name": "1st IBCT", "type": "IBCT", "specialty": "standard", "soldiers": 4200},
            {"name": "3rd ABCT", "type": "ABCT", "specialty": "armor", "soldiers": 4700},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 19800,
    },

    # ------------------------------------------------------------------------
    # I Corps
    # ------------------------------------------------------------------------

    "7th_infantry": {
        "name": "7th Infantry Division",
        "nickname": "Bayonet",
        "home_station": "JBLM",
        "theater": "FORSCOM",
        "brigades": [
            {"name": "1st SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4600},
            {"name": "2nd SBCT (Arrowhead)", "type": "SBCT", "specialty": "stryker", "soldiers": 4600},
            {"name": "2nd IBCT (Commando)", "type": "IBCT", "specialty": "standard", "soldiers": 4200},
            {"name": "3rd IBCT", "type": "IBCT", "specialty": "standard", "soldiers": 4200},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 19500,
    },

    "25th_infantry": {
        "name": "25th Infantry Division (Light)",
        "nickname": "Tropic Lightning",
        "home_station": "Hawaii",
        "theater": "INDOPACOM",
        "brigades": [
            {"name": "1st SBCT (Arctic Wolves)", "type": "SBCT", "specialty": "stryker", "soldiers": 4400},
            {"name": "2nd IBCT (Lightning)", "type": "IBCT", "specialty": "standard", "soldiers": 4100},
            {"name": "3rd IBCT (Bronco)", "type": "IBCT", "specialty": "standard", "soldiers": 4100},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 14500,
    },

    # ------------------------------------------------------------------------
    # USARAK (Alaska)
    # ------------------------------------------------------------------------

    "11th_airborne": {
        "name": "11th Airborne Division",
        "nickname": "Arctic Angels",
        "home_station": "JBER",
        "theater": "USARAK",
        "brigades": [
            {"name": "1st BCT (Spartan)", "type": "IBCT", "specialty": "airborne", "soldiers": 3800},
            {"name": "2nd BCT (Arctic Wolves)", "type": "IBCT", "specialty": "airborne", "soldiers": 3800},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 9000,
    },

    # ------------------------------------------------------------------------
    # INDOPACOM (Korea)
    # ------------------------------------------------------------------------

    "2nd_infantry": {
        "name": "2nd Infantry Division",
        "nickname": "Indianhead / Warriors",
        "home_station": "Camp Humphreys",
        "theater": "INDOPACOM",
        "brigades": [
            {"name": "1st SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4400},
            {"name": "2nd SBCT", "type": "SBCT", "specialty": "stryker", "soldiers": 4400},
        ],
        "div_artillery": True,
        "div_support": True,
        "total_soldiers": 10500,
    },

    # ------------------------------------------------------------------------
    # USAREUR (Europe)
    # ------------------------------------------------------------------------

    "173rd_airborne": {
        "name": "173rd Airborne Brigade",
        "nickname": "Sky Soldiers",
        "home_station": "Vicenza",
        "theater": "USAREUR",
        "brigades": [
            {"name": "173rd IBCT", "type": "IBCT", "specialty": "airborne", "soldiers": 3800},
        ],
        "div_artillery": False,  # Standalone brigade
        "div_support": True,
        "total_soldiers": 4500,
    },
}


# ============================================================================
# Utility Functions
# ============================================================================

def get_division_by_key(key: str) -> DivisionConfig:
    """Get division configuration by key."""
    if key not in ACTIVE_DIVISIONS:
        raise ValueError(f"Unknown division: {key}. Available: {list(ACTIVE_DIVISIONS.keys())}")
    return ACTIVE_DIVISIONS[key]


def get_divisions_by_theater(theater: str) -> Dict[str, DivisionConfig]:
    """Get all divisions in a specific theater."""
    return {k: v for k, v in ACTIVE_DIVISIONS.items() if v["theater"] == theater}


def get_divisions_by_type(brigade_type: str) -> Dict[str, DivisionConfig]:
    """Get divisions that have specific brigade types."""
    return {
        k: v for k, v in ACTIVE_DIVISIONS.items()
        if any(b["type"] == brigade_type for b in v["brigades"])
    }


def list_all_divisions() -> List[tuple]:
    """Return list of (key, name, soldiers, location) for all divisions."""
    return [
        (key, config["name"], config["total_soldiers"], config["home_station"])
        for key, config in ACTIVE_DIVISIONS.items()
    ]


# ============================================================================
# Display Helpers for Dashboard
# ============================================================================

def get_divisions_grouped_by_theater() -> Dict[str, List[tuple]]:
    """Group divisions by theater for dropdown display."""
    grouped = {}
    for key, config in ACTIVE_DIVISIONS.items():
        theater = config["theater"]
        if theater not in grouped:
            grouped[theater] = []

        # Format: (key, display_name)
        display = f"{config['name']} ({config['home_station']}) - {config['total_soldiers']:,} soldiers"
        grouped[theater].append((key, display))

    return grouped
