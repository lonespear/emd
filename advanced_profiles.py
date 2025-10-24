"""
advanced_profiles.py
--------------------

Advanced readiness profiles for CONUS training rotations and AOR-specific
deployments/exercises.

Features:
- CONUS training profiles (NTC, JRTC, TDY exercises, home station)
- AOR-specific profiles (INDOPACOM, EUCOM, SOUTHCOM, AFRICOM)
- Location-aware training requirements
- Exercise cycles and typical durations
- Theater-specific constraints

Classes:
- AdvancedReadinessProfile: Extended readiness profile with location info
- StandardCONUSProfiles: CONUS training rotation profiles
- AORProfiles: Area of Responsibility specific profiles
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import date

from readiness_tracker import ReadinessProfile


@dataclass
class AdvancedReadinessProfile:
    """
    Extended readiness profile with geographic and AOR context.

    Wraps a base ReadinessProfile and adds:
    - Primary location (exercise/deployment location)
    - AOR (Area of Responsibility)
    - Typical duration
    - Exercise cycle (if recurring)
    - Theater-specific requirements
    """
    # Core readiness profile
    profile_name: str
    required_training: List[str] = field(default_factory=list)
    min_dwell_months: int = 0
    max_med_cat: int = 2
    max_dental_cat: int = 2

    # Geographic/AOR extensions
    primary_location: str = "CONUS"
    aor: str = "NORTHCOM"
    typical_duration_days: int = 14
    exercise_cycle: Optional[str] = None  # Name of recurring exercise cycle
    theater_constraints: List[str] = field(default_factory=list)  # Theater-specific notes

    def to_readiness_profile(self) -> ReadinessProfile:
        """Convert to base ReadinessProfile for compatibility."""
        return ReadinessProfile(
            profile_name=self.profile_name,
            required_training=self.required_training,
            min_dwell_months=self.min_dwell_months,
            max_med_cat=self.max_med_cat,
            max_dental_cat=self.max_dental_cat
        )

    def is_oconus(self) -> bool:
        """Check if profile is for OCONUS location."""
        return self.aor not in ["NORTHCOM"]

    def get_location_type(self) -> str:
        """Get location type (CONUS, Near OCONUS, Far OCONUS)."""
        if self.aor == "NORTHCOM":
            return "CONUS"
        elif self.aor in ["EUCOM", "SOUTHCOM"]:
            return "OCONUS - Near"
        else:
            return "OCONUS - Far"


class StandardCONUSProfiles:
    """
    Standard CONUS training profiles.

    Profiles:
    1. NTC Rotation - Fort Irwin, CA
    2. JRTC Rotation - Fort Polk, LA
    3. TDY Exercise - Various CONUS locations
    4. Home Station Exercise - Unit's home station
    """

    @staticmethod
    def ntc_rotation() -> AdvancedReadinessProfile:
        """
        National Training Center Rotation (Fort Irwin, CA).

        Duration: 30 days (typical brigade rotation)
        Focus: High-intensity combined arms training in desert environment
        """
        return AdvancedReadinessProfile(
            profile_name="NTC_Rotation",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "crew_qualification",  # For vehicle crews
                "driver_license",  # HMMWV/LMTV at minimum
                "heat_injury_prevention",  # Desert environment
                "laser_safety",  # MILES gear
                "land_navigation",
                "combatives_level1"
            ],
            min_dwell_months=3,
            max_med_cat=2,
            max_dental_cat=2,
            primary_location="NTC",
            aor="NORTHCOM",
            typical_duration_days=30,
            exercise_cycle="Quarterly Brigade Rotations",
            theater_constraints=[
                "Desert environment (110°F+ in summer)",
                "High operational tempo (72hr missions)",
                "Vehicle-intensive operations"
            ]
        )

    @staticmethod
    def jrtc_rotation() -> AdvancedReadinessProfile:
        """
        Joint Readiness Training Center Rotation (Fort Polk, LA).

        Duration: 21 days (typical battalion rotation)
        Focus: Light infantry and unconventional warfare in forested/swamp terrain
        """
        return AdvancedReadinessProfile(
            profile_name="JRTC_Rotation",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "jungle_operations",  # Swamp/forest environment
                "heat_injury_prevention",  # Humid environment
                "insect_borne_disease",  # Mosquitoes, ticks
                "land_navigation"
            ],
            min_dwell_months=3,
            max_med_cat=2,
            max_dental_cat=2,
            primary_location="JRTC",
            aor="NORTHCOM",
            typical_duration_days=21,
            exercise_cycle="Quarterly Battalion Rotations",
            theater_constraints=[
                "Forested/swamp terrain",
                "High humidity (90%+)",
                "Dismounted infantry focus",
                "Limited vehicle operations"
            ]
        )

    @staticmethod
    def tdy_exercise() -> AdvancedReadinessProfile:
        """
        Temporary Duty (TDY) Exercise - Various CONUS locations.

        Duration: 7-14 days
        Focus: Shorter training events, often multi-unit exercises
        """
        return AdvancedReadinessProfile(
            profile_name="TDY_Exercise",
            required_training=[
                "weapons_qual",
                "pha",
                "acft"
            ],
            min_dwell_months=1,
            max_med_cat=3,
            max_dental_cat=3,
            primary_location="Various CONUS",
            aor="NORTHCOM",
            typical_duration_days=10,
            exercise_cycle=None,
            theater_constraints=[
                "Short duration (minimize TDY costs)",
                "Lower training intensity than NTC/JRTC"
            ]
        )

    @staticmethod
    def home_station_exercise() -> AdvancedReadinessProfile:
        """
        Home Station Exercise - Unit's local training area.

        Duration: 3-7 days
        Focus: Unit-level training at home installation
        """
        return AdvancedReadinessProfile(
            profile_name="Home_Station_Exercise",
            required_training=[
                "weapons_qual",
                "pha"
            ],
            min_dwell_months=0,
            max_med_cat=3,
            max_dental_cat=4,
            primary_location="Home Station",
            aor="NORTHCOM",
            typical_duration_days=5,
            exercise_cycle=None,
            theater_constraints=[
                "No TDY costs",
                "Flexible participation (non-deployable can participate)"
            ]
        )


class AORProfiles:
    """
    Area of Responsibility (AOR) specific profiles.

    Each AOR has unique:
    - Locations
    - Training requirements
    - Exercise cycles
    - Deployment durations
    - Theater constraints
    """

    @staticmethod
    def indopacom_exercise() -> AdvancedReadinessProfile:
        """
        INDOPACOM Exercise (Korea, Japan, Guam, Australia, Philippines).

        Typical exercises: Valiant Shield, Orient Shield, Pacific Pathways,
                          Talisman Sabre, Balikatan
        Duration: 14-21 days (exercises) or 9-12 months (rotations)
        """
        return AdvancedReadinessProfile(
            profile_name="INDOPACOM_Exercise",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "sere",  # SERE-C for Pacific theater
                "passport_current",
                "typhoon_prep",  # Typhoon season awareness
                "cultural_awareness_asia",
                "heat_acclimation"
            ],
            min_dwell_months=6,
            max_med_cat=2,
            max_dental_cat=2,
            primary_location="Camp Humphreys",  # Default to Korea
            aor="INDOPACOM",
            typical_duration_days=14,
            exercise_cycle="Valiant Shield, Orient Shield, Pacific Pathways",
            theater_constraints=[
                "Long-distance travel (7000+ miles from CONUS)",
                "Typhoon season (Jun-Nov)",
                "Host nation coordination required",
                "Time zone differences (12-17 hours from CONUS)"
            ]
        )

    @staticmethod
    def indopacom_rotation() -> AdvancedReadinessProfile:
        """
        INDOPACOM Rotation (9-12 month deployment to Korea).

        Differs from exercise: longer duration, more stringent requirements
        """
        profile = AORProfiles.indopacom_exercise()
        profile.profile_name = "INDOPACOM_Rotation"
        profile.typical_duration_days = 270  # 9 months
        profile.min_dwell_months = 12  # Require 1:1 dwell ratio
        profile.required_training.extend([
            "anthrax_vaccine",
            "korean_driving_license"
        ])
        profile.exercise_cycle = "9-12 month rotations"
        return profile

    @staticmethod
    def eucom_exercise() -> AdvancedReadinessProfile:
        """
        EUCOM Exercise (Germany, Poland, Romania, Baltic States).

        Typical exercises: Defender Europe, Saber Strike, Swift Response,
                          Combined Resolve
        Duration: 14-30 days
        """
        return AdvancedReadinessProfile(
            profile_name="EUCOM_Exercise",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "sere",  # SERE-C for Europe
                "passport_current",
                "cold_weather",  # Northern/Eastern Europe can be cold
                "european_driving",  # Different road rules
                "cultural_awareness_europe"
            ],
            min_dwell_months=6,
            max_med_cat=2,
            max_dental_cat=2,
            primary_location="Grafenwoehr",
            aor="EUCOM",
            typical_duration_days=21,
            exercise_cycle="Defender Europe, Saber Strike, Swift Response",
            theater_constraints=[
                "NATO interoperability requirements",
                "Host nation coordination (multiple countries)",
                "Winter operations possible (Nov-Mar)",
                "Rail/road movement across borders"
            ]
        )

    @staticmethod
    def southcom_exercise() -> AdvancedReadinessProfile:
        """
        SOUTHCOM Exercise (Honduras, Colombia, Peru, Panama).

        Typical exercises: Fuerzas Aliadas, Tradewinds, Beyond the Horizon
        Duration: 14-21 days
        """
        return AdvancedReadinessProfile(
            profile_name="SOUTHCOM_Exercise",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "sere",
                "passport_current",
                "jungle_operations",
                "tropical_disease",  # Malaria, dengue, yellow fever
                "altitude_training",  # Andes mountains
                "cultural_awareness_latin_america"
            ],
            min_dwell_months=3,
            max_med_cat=2,
            max_dental_cat=2,
            primary_location="Soto Cano",
            aor="SOUTHCOM",
            typical_duration_days=14,
            exercise_cycle="Fuerzas Aliadas, Tradewinds",
            theater_constraints=[
                "Spanish language highly beneficial",
                "Jungle/mountain environment",
                "Limited medical facilities",
                "Altitude (up to 12,000ft in Andes)"
            ]
        )

    @staticmethod
    def africom_exercise() -> AdvancedReadinessProfile:
        """
        AFRICOM Exercise (Djibouti, Niger, Kenya, Ghana).

        Typical exercises: African Lion, Flintlock, Justified Accord
        Duration: 14-21 days
        """
        return AdvancedReadinessProfile(
            profile_name="AFRICOM_Exercise",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "sere",
                "passport_current",
                "desert_operations",
                "tropical_disease",  # Malaria prevalent
                "water_purification",
                "cultural_awareness_africa"
            ],
            min_dwell_months=3,
            max_med_cat=2,
            max_dental_cat=2,
            primary_location="Djibouti",
            aor="AFRICOM",
            typical_duration_days=14,
            exercise_cycle="African Lion, Flintlock",
            theater_constraints=[
                "Austere environment (limited infrastructure)",
                "Extreme heat (120°F+ in summer)",
                "Limited medical facilities",
                "Multiple host nations (coordination complex)",
                "French or Arabic language helpful"
            ]
        )

    @staticmethod
    def centcom_deployment() -> AdvancedReadinessProfile:
        """
        CENTCOM Deployment (Kuwait, Qatar, Jordan, Iraq remnants).

        Note: Most CENTCOM operations are deployments, not exercises.
        Duration: 9-12 months
        """
        return AdvancedReadinessProfile(
            profile_name="CENTCOM_Deployment",
            required_training=[
                "weapons_qual",
                "pha",
                "acft",
                "sere",
                "passport_current",
                "desert_operations",
                "heat_injury_prevention",
                "combatives_level1",
                "combat_lifesaver",
                "anthrax_vaccine",
                "cultural_awareness_middle_east"
            ],
            min_dwell_months=12,
            max_med_cat=1,
            max_dental_cat=1,
            primary_location="Kuwait",
            aor="CENTCOM",
            typical_duration_days=270,  # 9 months
            exercise_cycle=None,  # Deployments, not exercises
            theater_constraints=[
                "Combat zone (higher risk)",
                "Extreme heat (130°F+ in summer)",
                "Austere conditions",
                "12 month dwell requirement post-deployment",
                "Strict medical/dental standards"
            ]
        )


# ===========================
# Profile Registry
# ===========================

class ProfileRegistry:
    """
    Central registry of all available profiles.

    Organizes profiles by category for easy access.
    """

    @staticmethod
    def get_all_profiles() -> Dict[str, AdvancedReadinessProfile]:
        """Get all available profiles as a dictionary."""
        profiles = {}

        # CONUS profiles
        profiles["NTC Rotation"] = StandardCONUSProfiles.ntc_rotation()
        profiles["JRTC Rotation"] = StandardCONUSProfiles.jrtc_rotation()
        profiles["TDY Exercise"] = StandardCONUSProfiles.tdy_exercise()
        profiles["Home Station Exercise"] = StandardCONUSProfiles.home_station_exercise()

        # AOR profiles
        profiles["INDOPACOM Exercise"] = AORProfiles.indopacom_exercise()
        profiles["INDOPACOM Rotation"] = AORProfiles.indopacom_rotation()
        profiles["EUCOM Exercise"] = AORProfiles.eucom_exercise()
        profiles["SOUTHCOM Exercise"] = AORProfiles.southcom_exercise()
        profiles["AFRICOM Exercise"] = AORProfiles.africom_exercise()
        profiles["CENTCOM Deployment"] = AORProfiles.centcom_deployment()

        return profiles

    @staticmethod
    def get_by_name(name: str) -> Optional[AdvancedReadinessProfile]:
        """Get profile by name."""
        profiles = ProfileRegistry.get_all_profiles()
        return profiles.get(name)

    @staticmethod
    def get_conus_profiles() -> List[AdvancedReadinessProfile]:
        """Get all CONUS profiles."""
        return [
            StandardCONUSProfiles.ntc_rotation(),
            StandardCONUSProfiles.jrtc_rotation(),
            StandardCONUSProfiles.tdy_exercise(),
            StandardCONUSProfiles.home_station_exercise()
        ]

    @staticmethod
    def get_aor_profiles() -> List[AdvancedReadinessProfile]:
        """Get all AOR profiles."""
        return [
            AORProfiles.indopacom_exercise(),
            AORProfiles.indopacom_rotation(),
            AORProfiles.eucom_exercise(),
            AORProfiles.southcom_exercise(),
            AORProfiles.africom_exercise(),
            AORProfiles.centcom_deployment()
        ]

    @staticmethod
    def get_by_aor(aor: str) -> List[AdvancedReadinessProfile]:
        """Get all profiles for a specific AOR."""
        all_profiles = ProfileRegistry.get_all_profiles()
        return [p for p in all_profiles.values() if p.aor == aor]


# ===========================
# Helper Functions
# ===========================

def get_recommended_profile(location: str, duration_days: int = 14) -> AdvancedReadinessProfile:
    """
    Get recommended profile based on location and duration.

    Args:
        location: Exercise/deployment location
        duration_days: Expected duration

    Returns:
        Recommended AdvancedReadinessProfile
    """
    location_lower = location.lower()

    # CONUS training centers
    if "ntc" in location_lower or "irwin" in location_lower:
        return StandardCONUSProfiles.ntc_rotation()
    elif "jrtc" in location_lower or "polk" in location_lower:
        return StandardCONUSProfiles.jrtc_rotation()

    # AOR-based recommendations
    elif any(x in location_lower for x in ["korea", "japan", "guam", "humphreys", "kadena", "darwin", "philippines"]):
        if duration_days > 60:
            return AORProfiles.indopacom_rotation()
        else:
            return AORProfiles.indopacom_exercise()

    elif any(x in location_lower for x in ["germany", "poland", "romania", "grafenwoehr", "estonia", "latvia", "lithuania"]):
        return AORProfiles.eucom_exercise()

    elif any(x in location_lower for x in ["honduras", "colombia", "peru", "panama", "soto cano"]):
        return AORProfiles.southcom_exercise()

    elif any(x in location_lower for x in ["djibouti", "niger", "kenya", "ghana", "africa"]):
        return AORProfiles.africom_exercise()

    elif any(x in location_lower for x in ["kuwait", "qatar", "bahrain", "iraq"]):
        return AORProfiles.centcom_deployment()

    # Default to TDY exercise for CONUS
    else:
        return StandardCONUSProfiles.tdy_exercise()
