"""
qualifications.py - Consolidated Qualification System

Combines: soldier_profile_extended.py, profile_generator.py, profile_utils.py,
          billet_requirements.py, qualification_filter.py
"""

from __future__ import annotations

# ===== SECTION 1: Data Models (soldier_profile_extended.py) =====

"""
soldier_profile_extended.py
----------------------------

Extended soldier profile system mirroring Army IPPS-A/DTMS data structures.

Tracks comprehensive soldier qualifications including:
- Education (degrees, certifications, education level)
- Languages (DLPT scores, proficiency)
- Additional Skill Identifiers (ASI codes)
- Special Qualification Identifiers (SQI codes)
- Military badges and tabs
- Awards and decorations
- Civilian licenses
- Deployment history
- Duty station history
- Time in Service/Grade

Fully integrated with EMD optimization, filtering, and reporting.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from datetime import date, datetime
from enum import Enum
import json


# ==============================
# ENUMERATIONS (Army Standards)
# ==============================

class EducationLevel(Enum):
    """Standard Army education level codes."""
    HS = "High School Diploma"
    GED = "GED"
    SOME_COLLEGE = "Some College"
    AA = "Associate's Degree"
    BA = "Bachelor's Degree"
    MA = "Master's Degree"
    PHD = "Doctoral Degree"
    PROFESSIONAL = "Professional Degree (MD, JD, etc.)"


class DLPTLevel(Enum):
    """Defense Language Proficiency Test levels (0-5)."""
    LEVEL_0 = 0  # No proficiency
    LEVEL_1 = 1  # Elementary proficiency
    LEVEL_2 = 2  # Limited working proficiency
    LEVEL_3 = 3  # Professional working proficiency (ILR Level 3)
    LEVEL_4 = 4  # Full professional proficiency
    LEVEL_5 = 5  # Native or bilingual proficiency


class BadgeType(Enum):
    """Categories of military badges."""
    COMBAT = "Combat Badge"
    MARKSMANSHIP = "Marksmanship Badge"
    SKILL = "Skill Badge"
    IDENTIFICATION = "Identification Badge"
    FOREIGN = "Foreign Badge"


class AwardType(Enum):
    """Categories of military awards."""
    VALOR = "Valor Award"
    ACHIEVEMENT = "Achievement Medal"
    SERVICE = "Service Medal"
    CAMPAIGN = "Campaign Medal"
    FOREIGN = "Foreign Award"


# ==============================
# DATA CLASSES
# ==============================

@dataclass
class EducationRecord:
    """
    Record of formal education.

    Mirrors Army IPPS-A education tracking.
    """
    level: EducationLevel
    institution: str
    degree_name: Optional[str] = None
    major: Optional[str] = None
    graduation_date: Optional[date] = None
    gpa: Optional[float] = None
    verified: bool = False

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "level": self.level.name,
            "institution": self.institution,
            "degree_name": self.degree_name,
            "major": self.major,
            "graduation_date": self.graduation_date.isoformat() if self.graduation_date else None,
            "gpa": self.gpa,
            "verified": self.verified
        }

    @staticmethod
    def from_dict(data: Dict) -> 'EducationRecord':
        """Create from dictionary."""
        return EducationRecord(
            level=EducationLevel[data["level"]],
            institution=data["institution"],
            degree_name=data.get("degree_name"),
            major=data.get("major"),
            graduation_date=datetime.fromisoformat(data["graduation_date"]).date() if data.get("graduation_date") else None,
            gpa=data.get("gpa"),
            verified=data.get("verified", False)
        )


@dataclass
class LanguageProficiency:
    """
    Language proficiency with DLPT scores.

    Tracks Defense Language Proficiency Test scores (0-5 scale)
    for listening and reading in specific languages.
    """
    language_code: str  # ISO 639-1 code (ES, KO, AR, etc.)
    language_name: str  # Full name (Spanish, Korean, Arabic)
    listening_level: DLPTLevel
    reading_level: DLPTLevel
    test_date: Optional[date] = None
    expiration_date: Optional[date] = None
    native_speaker: bool = False

    def overall_level(self) -> int:
        """Get overall proficiency (average of listening/reading)."""
        return (self.listening_level.value + self.reading_level.value) // 2

    def is_proficient(self, min_level: int = 2) -> bool:
        """Check if meets minimum proficiency (default: 2/2)."""
        return (self.listening_level.value >= min_level and
                self.reading_level.value >= min_level)

    def is_current(self, as_of_date: Optional[date] = None) -> bool:
        """Check if DLPT is current (not expired)."""
        if not self.expiration_date:
            return True
        check_date = as_of_date or date.today()
        return check_date <= self.expiration_date

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "language_code": self.language_code,
            "language_name": self.language_name,
            "listening_level": self.listening_level.value,
            "reading_level": self.reading_level.value,
            "test_date": self.test_date.isoformat() if self.test_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "native_speaker": self.native_speaker
        }

    @staticmethod
    def from_dict(data: Dict) -> 'LanguageProficiency':
        """Create from dictionary."""
        return LanguageProficiency(
            language_code=data["language_code"],
            language_name=data["language_name"],
            listening_level=DLPTLevel(data["listening_level"]),
            reading_level=DLPTLevel(data["reading_level"]),
            test_date=datetime.fromisoformat(data["test_date"]).date() if data.get("test_date") else None,
            expiration_date=datetime.fromisoformat(data["expiration_date"]).date() if data.get("expiration_date") else None,
            native_speaker=data.get("native_speaker", False)
        )


@dataclass
class AdditionalSkillIdentifier:
    """
    Additional Skill Identifier (ASI).

    ASIs identify additional skills, special qualifications, or
    special assignment requirements (e.g., B4 Master Fitness Trainer,
    K3 Recruiter, L9 Equal Opportunity Advisor).
    """
    code: str  # 2-character code (B4, K3, L9, etc.)
    name: str  # Full name
    award_date: Optional[date] = None
    expiration_date: Optional[date] = None

    def is_current(self, as_of_date: Optional[date] = None) -> bool:
        """Check if ASI is current (not expired)."""
        if not self.expiration_date:
            return True
        check_date = as_of_date or date.today()
        return check_date <= self.expiration_date

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "code": self.code,
            "name": self.name,
            "award_date": self.award_date.isoformat() if self.award_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None
        }

    @staticmethod
    def from_dict(data: Dict) -> 'AdditionalSkillIdentifier':
        """Create from dictionary."""
        return AdditionalSkillIdentifier(
            code=data["code"],
            name=data["name"],
            award_date=datetime.fromisoformat(data["award_date"]).date() if data.get("award_date") else None,
            expiration_date=datetime.fromisoformat(data["expiration_date"]).date() if data.get("expiration_date") else None
        )


@dataclass
class SpecialQualificationIdentifier:
    """
    Special Qualification Identifier (SQI).

    SQIs identify special qualifications related to career management
    fields (e.g., V Ranger, W Drill Sergeant, X Recruiter, Y Senior Instructor).
    """
    code: str  # 1-character code (V, W, X, Y, etc.)
    name: str  # Full name
    award_date: Optional[date] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "code": self.code,
            "name": self.name,
            "award_date": self.award_date.isoformat() if self.award_date else None
        }

    @staticmethod
    def from_dict(data: Dict) -> 'SpecialQualificationIdentifier':
        """Create from dictionary."""
        return SpecialQualificationIdentifier(
            code=data["code"],
            name=data["name"],
            award_date=datetime.fromisoformat(data["award_date"]).date() if data.get("award_date") else None
        )


@dataclass
class MilitaryBadge:
    """
    Military badge or tab.

    Includes skill badges (Airborne, Air Assault), combat badges (CIB, CAB),
    marksmanship badges, and identification badges.
    """
    code: str  # Standardized code (AIRBORNE, RANGER, CIB, etc.)
    name: str  # Full name
    badge_type: BadgeType
    award_date: Optional[date] = None
    device: Optional[str] = None  # Star, Oak Leaf Cluster, etc.

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "code": self.code,
            "name": self.name,
            "badge_type": self.badge_type.name,
            "award_date": self.award_date.isoformat() if self.award_date else None,
            "device": self.device
        }

    @staticmethod
    def from_dict(data: Dict) -> 'MilitaryBadge':
        """Create from dictionary."""
        return MilitaryBadge(
            code=data["code"],
            name=data["name"],
            badge_type=BadgeType[data["badge_type"]],
            award_date=datetime.fromisoformat(data["award_date"]).date() if data.get("award_date") else None,
            device=data.get("device")
        )


@dataclass
class Award:
    """
    Military award or decoration.

    Includes valor awards, achievement medals, service medals,
    campaign medals, and foreign awards.
    """
    code: str  # Standardized abbreviation (ARCOM, AAM, BSM, etc.)
    name: str  # Full name
    award_type: AwardType
    award_date: Optional[date] = None
    device: Optional[str] = None  # "V" device, Oak Leaf Cluster, etc.
    award_number: int = 1  # 1st, 2nd, 3rd award

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "code": self.code,
            "name": self.name,
            "award_type": self.award_type.name,
            "award_date": self.award_date.isoformat() if self.award_date else None,
            "device": self.device,
            "award_number": self.award_number
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Award':
        """Create from dictionary."""
        return Award(
            code=data["code"],
            name=data["name"],
            award_type=AwardType[data["award_type"]],
            award_date=datetime.fromisoformat(data["award_date"]).date() if data.get("award_date") else None,
            device=data.get("device"),
            award_number=data.get("award_number", 1)
        )


@dataclass
class CivilianLicense:
    """
    Civilian license or certification.

    Includes CDL, medical licenses, IT certifications, trade licenses, etc.
    """
    license_type: str  # CDL, Medical, IT, Trade, etc.
    license_name: str  # Full name
    license_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None
    endorsements: List[str] = field(default_factory=list)

    def is_current(self, as_of_date: Optional[date] = None) -> bool:
        """Check if license is current (not expired)."""
        if not self.expiration_date:
            return True
        check_date = as_of_date or date.today()
        return check_date <= self.expiration_date

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "license_type": self.license_type,
            "license_name": self.license_name,
            "license_number": self.license_number,
            "issuing_authority": self.issuing_authority,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "endorsements": self.endorsements
        }

    @staticmethod
    def from_dict(data: Dict) -> 'CivilianLicense':
        """Create from dictionary."""
        return CivilianLicense(
            license_type=data["license_type"],
            license_name=data["license_name"],
            license_number=data.get("license_number"),
            issuing_authority=data.get("issuing_authority"),
            issue_date=datetime.fromisoformat(data["issue_date"]).date() if data.get("issue_date") else None,
            expiration_date=datetime.fromisoformat(data["expiration_date"]).date() if data.get("expiration_date") else None,
            endorsements=data.get("endorsements", [])
        )


@dataclass
class DeploymentRecord:
    """
    Combat deployment or contingency operation.

    Tracks deployment location, duration, and operation name.
    """
    operation_name: str  # OIF, OEF, OIR, etc.
    theater: str  # CENTCOM, INDOPACOM, etc.
    location: str  # Iraq, Afghanistan, Korea, etc.
    start_date: date
    end_date: Optional[date] = None
    duration_months: int = 0
    combat_deployment: bool = True

    def calculate_duration(self) -> int:
        """Calculate deployment duration in months."""
        if not self.end_date:
            return 0
        delta = (self.end_date.year - self.start_date.year) * 12 + (self.end_date.month - self.start_date.month)
        return max(0, delta)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "operation_name": self.operation_name,
            "theater": self.theater,
            "location": self.location,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_months": self.duration_months,
            "combat_deployment": self.combat_deployment
        }

    @staticmethod
    def from_dict(data: Dict) -> 'DeploymentRecord':
        """Create from dictionary."""
        return DeploymentRecord(
            operation_name=data["operation_name"],
            theater=data["theater"],
            location=data["location"],
            start_date=datetime.fromisoformat(data["start_date"]).date(),
            end_date=datetime.fromisoformat(data["end_date"]).date() if data.get("end_date") else None,
            duration_months=data.get("duration_months", 0),
            combat_deployment=data.get("combat_deployment", True)
        )


@dataclass
class DutyAssignment:
    """
    Previous duty assignment history.

    Tracks duty station, unit, position, and duration.
    """
    duty_station: str  # Fort Bragg, JBLM, etc.
    unit: str  # Unit designation
    position: str  # Position title
    start_date: date
    end_date: Optional[date] = None
    duration_months: int = 0

    def calculate_duration(self) -> int:
        """Calculate assignment duration in months."""
        end = self.end_date or date.today()
        delta = (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)
        return max(0, delta)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "duty_station": self.duty_station,
            "unit": self.unit,
            "position": self.position,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_months": self.duration_months
        }

    @staticmethod
    def from_dict(data: Dict) -> 'DutyAssignment':
        """Create from dictionary."""
        return DutyAssignment(
            duty_station=data["duty_station"],
            unit=data["unit"],
            position=data["position"],
            start_date=datetime.fromisoformat(data["start_date"]).date(),
            end_date=datetime.fromisoformat(data["end_date"]).date() if data.get("end_date") else None,
            duration_months=data.get("duration_months", 0)
        )


# ==============================
# MAIN CONTAINER CLASS
# ==============================

@dataclass
class SoldierProfileExtended:
    """
    Extended soldier profile with comprehensive qualification data.

    Mirrors Army IPPS-A/DTMS structure with full qualification tracking.
    Designed for integration with EMD optimization, filtering, and reporting.
    """
    # Basic identifiers
    soldier_id: str

    # Education
    highest_education: EducationLevel = EducationLevel.HS
    education_records: List[EducationRecord] = field(default_factory=list)

    # Languages
    languages: List[LanguageProficiency] = field(default_factory=list)

    # Skills & Qualifications
    asi_codes: List[AdditionalSkillIdentifier] = field(default_factory=list)
    sqi_codes: List[SpecialQualificationIdentifier] = field(default_factory=list)

    # Badges & Awards
    badges: List[MilitaryBadge] = field(default_factory=list)
    awards: List[Award] = field(default_factory=list)

    # Licenses
    licenses: List[CivilianLicense] = field(default_factory=list)

    # Experience
    time_in_service_months: int = 0
    time_in_grade_months: int = 0
    deployments: List[DeploymentRecord] = field(default_factory=list)
    duty_history: List[DutyAssignment] = field(default_factory=list)

    # Helper Methods

    def has_language(self, language_code: str, min_level: int = 2) -> bool:
        """Check if soldier has language at minimum proficiency."""
        for lang in self.languages:
            if lang.language_code == language_code and lang.is_proficient(min_level):
                return True
        return False

    def has_asi(self, asi_code: str) -> bool:
        """Check if soldier has specific ASI."""
        return any(asi.code == asi_code and asi.is_current() for asi in self.asi_codes)

    def has_sqi(self, sqi_code: str) -> bool:
        """Check if soldier has specific SQI."""
        return any(sqi.code == sqi_code for sqi in self.sqi_codes)

    def has_badge(self, badge_code: str) -> bool:
        """Check if soldier has specific badge."""
        return any(badge.code == badge_code for badge in self.badges)

    def has_license(self, license_type: str) -> bool:
        """Check if soldier has current license of specific type."""
        return any(lic.license_type == license_type and lic.is_current() for lic in self.licenses)

    def deployment_count(self, combat_only: bool = False) -> int:
        """Count total deployments."""
        if combat_only:
            return sum(1 for dep in self.deployments if dep.combat_deployment)
        return len(self.deployments)

    def total_deployment_months(self) -> int:
        """Calculate total months deployed."""
        return sum(dep.duration_months for dep in self.deployments)

    def has_theater_experience(self, theater: str) -> bool:
        """Check if soldier has deployed to specific theater."""
        return any(dep.theater == theater for dep in self.deployments)

    def get_education_level_value(self) -> int:
        """Get numeric education level (for comparisons)."""
        levels = {
            EducationLevel.HS: 1,
            EducationLevel.GED: 1,
            EducationLevel.SOME_COLLEGE: 2,
            EducationLevel.AA: 3,
            EducationLevel.BA: 4,
            EducationLevel.MA: 5,
            EducationLevel.PHD: 6,
            EducationLevel.PROFESSIONAL: 6
        }
        return levels.get(self.highest_education, 1)

    def to_dict(self) -> Dict:
        """Convert entire profile to dictionary for JSON storage."""
        return {
            "soldier_id": self.soldier_id,
            "highest_education": self.highest_education.name,
            "education_records": [rec.to_dict() for rec in self.education_records],
            "languages": [lang.to_dict() for lang in self.languages],
            "asi_codes": [asi.to_dict() for asi in self.asi_codes],
            "sqi_codes": [sqi.to_dict() for sqi in self.sqi_codes],
            "badges": [badge.to_dict() for badge in self.badges],
            "awards": [award.to_dict() for award in self.awards],
            "licenses": [lic.to_dict() for lic in self.licenses],
            "time_in_service_months": self.time_in_service_months,
            "time_in_grade_months": self.time_in_grade_months,
            "deployments": [dep.to_dict() for dep in self.deployments],
            "duty_history": [duty.to_dict() for duty in self.duty_history]
        }

    @staticmethod
    def from_dict(data: Dict) -> 'SoldierProfileExtended':
        """Create profile from dictionary."""
        return SoldierProfileExtended(
            soldier_id=data["soldier_id"],
            highest_education=EducationLevel[data.get("highest_education", "HS")],
            education_records=[EducationRecord.from_dict(r) for r in data.get("education_records", [])],
            languages=[LanguageProficiency.from_dict(l) for l in data.get("languages", [])],
            asi_codes=[AdditionalSkillIdentifier.from_dict(a) for a in data.get("asi_codes", [])],
            sqi_codes=[SpecialQualificationIdentifier.from_dict(s) for s in data.get("sqi_codes", [])],
            badges=[MilitaryBadge.from_dict(b) for b in data.get("badges", [])],
            awards=[Award.from_dict(a) for a in data.get("awards", [])],
            licenses=[CivilianLicense.from_dict(l) for l in data.get("licenses", [])],
            time_in_service_months=data.get("time_in_service_months", 0),
            time_in_grade_months=data.get("time_in_grade_months", 0),
            deployments=[DeploymentRecord.from_dict(d) for d in data.get("deployments", [])],
            duty_history=[DutyAssignment.from_dict(d) for d in data.get("duty_history", [])]
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_json(json_str: str) -> 'SoldierProfileExtended':
        """Create profile from JSON string."""
        return SoldierProfileExtended.from_dict(json.loads(json_str))


# ==============================
# REFERENCE DATA
# ==============================

# Common ASI Codes (subset - full list in CODE_REFERENCES.md)
COMMON_ASI_CODES = {
    "B4": "Master Fitness Trainer",
    "C8": "Composite Risk Management",
    "F3": "Air Traffic Control",
    "K3": "Recruiter",
    "L9": "Equal Opportunity Advisor",
    "M2": "Parachute Rigger",
    "P5": "Master Instructor",
    "S7": "Telecommunications Systems",
    "V5": "Armor Master Gunner",
    "2S": "Space Operations",
    "3Y": "Explosive Ordnance Disposal (EOD)",
    "5K": "Sniper",
    "8P": "Special Forces Communications",
}

# Common SQI Codes
COMMON_SQI_CODES = {
    "V": "Ranger Qualified",
    "W": "Drill Sergeant",
    "X": "Recruiter (Senior)",
    "Y": "Senior Instructor",
    "Z": "Master Instructor",
    "8": "Special Forces Qualified",
    "B": "Career Counselor",
    "P": "Pathfinder",
    "S": "SERE (Survival, Evasion, Resistance, Escape)",
}

# Common Languages (ISO 639-1 codes)
COMMON_LANGUAGES = {
    "AR": "Arabic",
    "ZH": "Chinese (Mandarin)",
    "FA": "Farsi (Persian)",
    "FR": "French",
    "DE": "German",
    "HE": "Hebrew",
    "HI": "Hindi",
    "IT": "Italian",
    "JA": "Japanese",
    "KO": "Korean",
    "PS": "Pashto",
    "PT": "Portuguese",
    "RU": "Russian",
    "ES": "Spanish",
    "UR": "Urdu",
}

# Common Badges
COMMON_BADGES = {
    "AIRBORNE": ("Airborne Badge", BadgeType.SKILL),
    "AIR_ASSAULT": ("Air Assault Badge", BadgeType.SKILL),
    "RANGER": ("Ranger Tab", BadgeType.SKILL),
    "SAPPER": ("Sapper Tab", BadgeType.SKILL),
    "CIB": ("Combat Infantryman Badge", BadgeType.COMBAT),
    "CAB": ("Combat Action Badge", BadgeType.COMBAT),
    "CMB": ("Combat Medical Badge", BadgeType.COMBAT),
    "EIB": ("Expert Infantryman Badge", BadgeType.SKILL),
    "ESB": ("Expert Soldier Badge", BadgeType.SKILL),
    "EFMB": ("Expert Field Medical Badge", BadgeType.SKILL),
    "PATHFINDER": ("Pathfinder Badge", BadgeType.SKILL),
    "JUMPMASTER": ("Jumpmaster Badge", BadgeType.SKILL),
    "SF": ("Special Forces Tab", BadgeType.SKILL),
    "DRIVER_WHEEL": ("Driver and Mechanic Badge", BadgeType.SKILL),
}

# Common Awards
COMMON_AWARDS = {
    # Valor
    "MOH": ("Medal of Honor", AwardType.VALOR),
    "DSC": ("Distinguished Service Cross", AwardType.VALOR),
    "SS": ("Silver Star", AwardType.VALOR),
    "BSM_V": ("Bronze Star with Valor", AwardType.VALOR),

    # Achievement
    "ARCOM": ("Army Commendation Medal", AwardType.ACHIEVEMENT),
    "AAM": ("Army Achievement Medal", AwardType.ACHIEVEMENT),
    "BSM": ("Bronze Star", AwardType.ACHIEVEMENT),
    "MSM": ("Meritorious Service Medal", AwardType.ACHIEVEMENT),

    # Service
    "GWOT_S": ("Global War on Terrorism Service Medal", AwardType.SERVICE),
    "GWOT_E": ("Global War on Terrorism Expeditionary Medal", AwardType.SERVICE),
    "ASR": ("Army Service Ribbon", AwardType.SERVICE),
    "NDSM": ("National Defense Service Medal", AwardType.SERVICE),
    "GWOTSM": ("Global War on Terrorism Service Medal", AwardType.SERVICE),
}

# Common License Types
COMMON_LICENSE_TYPES = {
    "CDL_A": "Commercial Driver's License Class A",
    "CDL_B": "Commercial Driver's License Class B",
    "CDL_C": "Commercial Driver's License Class C",
    "MEDICAL_EMT": "Emergency Medical Technician",
    "MEDICAL_PARAMEDIC": "Paramedic",
    "MEDICAL_RN": "Registered Nurse",
    "IT_CISSP": "Certified Information Systems Security Professional",
    "IT_COMPTIA": "CompTIA A+/Network+/Security+",
    "TRADE_ELECTRICIAN": "Licensed Electrician",
    "TRADE_PLUMBER": "Licensed Plumber",
    "FORKLIFT": "Forklift Operator",
    "CRANE": "Crane Operator",
}

# ===== SECTION 2: Profile Generator (profile_generator.py) =====

"""
profile_generator.py
--------------------

Generates realistic extended soldier profiles with Army-standard qualifications.

Integrates with mtoe_generator.py to add comprehensive qualification data:
- Education (correlates with rank/experience)
- Languages (varies by MOS and geography)
- ASIs/SQIs (based on position and experience)
- Badges (realistic distribution by MOS/unit)
- Awards (based on TIS/deployments)
- Licenses (based on MOS requirements)
- Deployment history (realistic theaters and durations)
- Duty station history (tracks career progression)

Uses realistic distributions and correlations to mirror actual Army demographics.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from qualifications import (
    SoldierProfileExtended, EducationLevel, EducationRecord,
    LanguageProficiency, DLPTLevel, AdditionalSkillIdentifier,
    SpecialQualificationIdentifier, MilitaryBadge, BadgeType,
    Award, AwardType, CivilianLicense, DeploymentRecord,
    DutyAssignment,
    COMMON_ASI_CODES, COMMON_SQI_CODES, COMMON_LANGUAGES,
    COMMON_BADGES, COMMON_AWARDS, COMMON_LICENSE_TYPES
)


class ProfileGenerator:
    """
    Generates realistic extended soldier profiles.

    Uses rank, MOS, TIS/TIG, and deployment history to generate
    correlated qualification data matching Army demographics.
    """

    # Realistic distribution probabilities
    EDUCATION_BY_RANK = {
        "PVT": {"HS": 0.85, "SOME_COLLEGE": 0.10, "AA": 0.03, "BA": 0.02},
        "PV2": {"HS": 0.80, "SOME_COLLEGE": 0.15, "AA": 0.03, "BA": 0.02},
        "PFC": {"HS": 0.75, "SOME_COLLEGE": 0.18, "AA": 0.05, "BA": 0.02},
        "SPC": {"HS": 0.65, "SOME_COLLEGE": 0.20, "AA": 0.10, "BA": 0.05},
        "CPL": {"HS": 0.60, "SOME_COLLEGE": 0.22, "AA": 0.12, "BA": 0.06},
        "SGT": {"HS": 0.50, "SOME_COLLEGE": 0.25, "AA": 0.15, "BA": 0.08, "MA": 0.02},
        "SSG": {"HS": 0.40, "SOME_COLLEGE": 0.25, "AA": 0.20, "BA": 0.12, "MA": 0.03},
        "SFC": {"HS": 0.30, "SOME_COLLEGE": 0.20, "AA": 0.22, "BA": 0.20, "MA": 0.08},
        "MSG": {"HS": 0.20, "SOME_COLLEGE": 0.15, "AA": 0.20, "BA": 0.30, "MA": 0.15},
        "SGM": {"HS": 0.15, "SOME_COLLEGE": 0.10, "AA": 0.15, "BA": 0.35, "MA": 0.25},
        "CSM": {"HS": 0.10, "SOME_COLLEGE": 0.08, "AA": 0.12, "BA": 0.40, "MA": 0.30},
    }

    # Language probabilities by MOS category
    LANGUAGE_BY_MOS_CATEGORY = {
        "INTELLIGENCE": 0.40,  # 35 series - high language requirement
        "SPECIAL_FORCES": 0.80,  # 18 series - very high
        "CIVIL_AFFAIRS": 0.50,  # 38 series - high
        "INFANTRY": 0.10,  # 11 series - low
        "LOGISTICS": 0.05,  # 88/92 series - very low
        "DEFAULT": 0.08  # Other MOSs
    }

    # Common languages by region of interest
    STRATEGIC_LANGUAGES = ["AR", "ZH", "KO", "RU", "FA", "PS", "UR"]  # High-priority
    COMMON_LANGUAGES_LIST = ["ES", "FR", "DE", "JA", "PT"]  # Medium-priority

    # Badge probabilities by unit type
    BADGE_PROBABILITY = {
        "AIRBORNE": {"82ND": 0.95, "173RD": 0.90, "DEFAULT": 0.15},
        "AIR_ASSAULT": {"101ST": 0.85, "DEFAULT": 0.20},
        "RANGER": {"75TH": 0.90, "DEFAULT": 0.03},
        "SAPPER": {"ENGINEER": 0.15, "DEFAULT": 0.02},
        "PATHFINDER": {"AIRBORNE": 0.10, "DEFAULT": 0.01},
    }

    # ASI probabilities by MOS/role
    ASI_BY_ROLE = {
        "RECRUITER": ["K3"],
        "MASTER_FITNESS": ["B4"],
        "EO_ADVISOR": ["L9"],
        "INSTRUCTOR": ["P5"],
        "RIGGER": ["M2"],
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducibility."""
        if seed is not None:
            np.random.seed(seed)
            self.rng = np.random.default_rng(seed)
        else:
            self.rng = np.random.default_rng()

    def generate_profile(self,
                        soldier_id: str,
                        rank: str,
                        mos: str,
                        base: str,
                        tis_months: int,
                        tig_months: int,
                        unit_type: Optional[str] = None) -> SoldierProfileExtended:
        """
        Generate complete extended profile for a soldier.

        Args:
            soldier_id: Soldier identifier
            rank: Current rank (PVT, PFC, SGT, etc.)
            mos: Military Occupational Specialty
            base: Current duty station
            tis_months: Time in service (months)
            tig_months: Time in grade (months)
            unit_type: Type of unit (for badge correlations)

        Returns:
            Complete SoldierProfileExtended object
        """
        profile = SoldierProfileExtended(
            soldier_id=soldier_id,
            time_in_service_months=tis_months,
            time_in_grade_months=tig_months
        )

        # Generate each component
        profile.highest_education = self._generate_education_level(rank)
        profile.education_records = self._generate_education_records(profile.highest_education, rank)
        profile.languages = self._generate_languages(mos, base)
        profile.asi_codes = self._generate_asis(mos, rank, tis_months)
        profile.sqi_codes = self._generate_sqis(mos, rank, tis_months, unit_type)
        profile.badges = self._generate_badges(mos, unit_type, tis_months)
        profile.awards = self._generate_awards(rank, tis_months)
        profile.licenses = self._generate_licenses(mos)
        profile.deployments = self._generate_deployments(tis_months)
        profile.duty_history = self._generate_duty_history(tis_months, base)

        return profile

    def _generate_education_level(self, rank: str) -> EducationLevel:
        """Generate education level correlated with rank."""
        distribution = self.EDUCATION_BY_RANK.get(rank, self.EDUCATION_BY_RANK["SPC"])

        # Sample from distribution
        levels = list(distribution.keys())
        probabilities = list(distribution.values())

        chosen_level_str = self.rng.choice(levels, p=probabilities)
        return EducationLevel[chosen_level_str]

    def _generate_education_records(self,
                                   highest_level: EducationLevel,
                                   rank: str) -> List[EducationRecord]:
        """Generate detailed education records."""
        records = []

        if highest_level == EducationLevel.HS:
            # High school diploma
            records.append(EducationRecord(
                level=EducationLevel.HS,
                institution=self._random_high_school(),
                graduation_date=self._random_date_years_ago(10, 25),
                verified=True
            ))

        elif highest_level in [EducationLevel.SOME_COLLEGE, EducationLevel.AA]:
            # High school + some college
            records.append(EducationRecord(
                level=EducationLevel.HS,
                institution=self._random_high_school(),
                graduation_date=self._random_date_years_ago(10, 20),
                verified=True
            ))

            if highest_level == EducationLevel.AA:
                records.append(EducationRecord(
                    level=EducationLevel.AA,
                    institution=self._random_community_college(),
                    degree_name="Associate of Arts" if self.rng.random() > 0.5 else "Associate of Science",
                    major=self._random_major("AA"),
                    graduation_date=self._random_date_years_ago(5, 15),
                    gpa=self.rng.uniform(2.5, 4.0),
                    verified=True
                ))

        elif highest_level == EducationLevel.BA:
            # High school + bachelor's
            records.append(EducationRecord(
                level=EducationLevel.HS,
                institution=self._random_high_school(),
                graduation_date=self._random_date_years_ago(10, 20),
                verified=True
            ))
            records.append(EducationRecord(
                level=EducationLevel.BA,
                institution=self._random_university(),
                degree_name="Bachelor of Arts" if self.rng.random() > 0.5 else "Bachelor of Science",
                major=self._random_major("BA"),
                graduation_date=self._random_date_years_ago(3, 12),
                gpa=self.rng.uniform(2.5, 4.0),
                verified=True
            ))

        elif highest_level in [EducationLevel.MA, EducationLevel.PHD]:
            # High school + bachelor's + graduate
            records.append(EducationRecord(
                level=EducationLevel.HS,
                institution=self._random_high_school(),
                graduation_date=self._random_date_years_ago(15, 25),
                verified=True
            ))
            records.append(EducationRecord(
                level=EducationLevel.BA,
                institution=self._random_university(),
                degree_name="Bachelor of Science",
                major=self._random_major("BA"),
                graduation_date=self._random_date_years_ago(8, 18),
                gpa=self.rng.uniform(2.8, 4.0),
                verified=True
            ))
            records.append(EducationRecord(
                level=highest_level,
                institution=self._random_university(),
                degree_name="Master of Arts" if highest_level == EducationLevel.MA else "Doctor of Philosophy",
                major=self._random_major("MA"),
                graduation_date=self._random_date_years_ago(2, 10),
                gpa=self.rng.uniform(3.0, 4.0),
                verified=True
            ))

        return records

    def _generate_languages(self, mos: str, base: str) -> List[LanguageProficiency]:
        """Generate language proficiencies based on MOS and location."""
        languages = []

        # Determine probability based on MOS
        mos_prefix = mos[:2] if len(mos) >= 2 else "00"
        if mos_prefix == "35":
            language_prob = self.LANGUAGE_BY_MOS_CATEGORY["INTELLIGENCE"]
        elif mos_prefix == "18":
            language_prob = self.LANGUAGE_BY_MOS_CATEGORY["SPECIAL_FORCES"]
        elif mos_prefix == "38":
            language_prob = self.LANGUAGE_BY_MOS_CATEGORY["CIVIL_AFFAIRS"]
        elif mos_prefix == "11":
            language_prob = self.LANGUAGE_BY_MOS_CATEGORY["INFANTRY"]
        elif mos_prefix in ["88", "92"]:
            language_prob = self.LANGUAGE_BY_MOS_CATEGORY["LOGISTICS"]
        else:
            language_prob = self.LANGUAGE_BY_MOS_CATEGORY["DEFAULT"]

        # Roll for language proficiency
        if self.rng.random() < language_prob:
            # Choose language (strategic languages more likely for intel/SF)
            if mos_prefix in ["35", "18", "38"]:
                language_pool = self.STRATEGIC_LANGUAGES + self.COMMON_LANGUAGES_LIST
                weights = [2.0] * len(self.STRATEGIC_LANGUAGES) + [1.0] * len(self.COMMON_LANGUAGES_LIST)
            else:
                language_pool = self.COMMON_LANGUAGES_LIST
                weights = [1.0] * len(language_pool)

            lang_code = self.rng.choice(language_pool, p=np.array(weights) / sum(weights))
            lang_name = COMMON_LANGUAGES.get(lang_code, "Unknown")

            # Generate DLPT scores (intel/SF tend to be more proficient)
            if mos_prefix in ["35", "18"]:
                listening_level = DLPTLevel(self.rng.choice([2, 3, 3, 4], p=[0.3, 0.4, 0.2, 0.1]))
                reading_level = DLPTLevel(self.rng.choice([2, 3, 3, 4], p=[0.3, 0.4, 0.2, 0.1]))
            else:
                listening_level = DLPTLevel(self.rng.choice([1, 2, 2, 3], p=[0.2, 0.5, 0.2, 0.1]))
                reading_level = DLPTLevel(self.rng.choice([1, 2, 2, 3], p=[0.2, 0.5, 0.2, 0.1]))

            languages.append(LanguageProficiency(
                language_code=lang_code,
                language_name=lang_name,
                listening_level=listening_level,
                reading_level=reading_level,
                test_date=self._random_date_years_ago(0, 3),
                expiration_date=self._random_date_years_future(1, 3),
                native_speaker=False
            ))

        return languages

    def _generate_asis(self, mos: str, rank: str, tis_months: int) -> List[AdditionalSkillIdentifier]:
        """Generate ASIs based on MOS, rank, and experience."""
        asis = []

        # More experienced soldiers more likely to have ASIs
        asi_probability = min(0.05 + (tis_months / 2400), 0.40)  # 5% to 40% over 20 years

        if self.rng.random() < asi_probability:
            # Choose random ASI from common codes
            asi_code = self.rng.choice(list(COMMON_ASI_CODES.keys()))
            asi_name = COMMON_ASI_CODES[asi_code]

            asis.append(AdditionalSkillIdentifier(
                code=asi_code,
                name=asi_name,
                award_date=self._random_date_years_ago(1, int(tis_months / 12)),
                expiration_date=None  # Most ASIs don't expire
            ))

        return asis

    def _generate_sqis(self, mos: str, rank: str, tis_months: int, unit_type: Optional[str]) -> List[SpecialQualificationIdentifier]:
        """Generate SQIs based on MOS, rank, unit, and experience."""
        sqis = []

        # NCOs more likely to have SQIs
        if rank in ["SSG", "SFC", "MSG", "SGM", "CSM"]:
            sqi_probability = 0.25
        elif rank in ["SGT"]:
            sqi_probability = 0.10
        else:
            sqi_probability = 0.02

        if self.rng.random() < sqi_probability:
            # Choose based on context
            if unit_type and "RANGER" in unit_type.upper():
                sqi_code = "V"
                sqi_name = "Ranger Qualified"
            elif rank in ["SSG", "SFC"] and self.rng.random() < 0.3:
                sqi_code = "W"
                sqi_name = "Drill Sergeant"
            elif rank in ["MSG", "SGM"] and self.rng.random() < 0.2:
                sqi_code = "Y"
                sqi_name = "Senior Instructor"
            else:
                sqi_code = self.rng.choice(list(COMMON_SQI_CODES.keys()))
                sqi_name = COMMON_SQI_CODES[sqi_code]

            sqis.append(SpecialQualificationIdentifier(
                code=sqi_code,
                name=sqi_name,
                award_date=self._random_date_years_ago(1, int(tis_months / 12))
            ))

        return sqis

    def _generate_badges(self, mos: str, unit_type: Optional[str], tis_months: int) -> List[MilitaryBadge]:
        """Generate badges based on MOS, unit type, and experience."""
        badges = []

        # Airborne
        airborne_prob = 0.15
        if unit_type and any(x in unit_type.upper() for x in ["82ND", "173RD", "AIRBORNE"]):
            airborne_prob = 0.90
        if self.rng.random() < airborne_prob:
            badges.append(MilitaryBadge(
                code="AIRBORNE",
                name="Airborne Badge",
                badge_type=BadgeType.SKILL,
                award_date=self._random_date_years_ago(1, int(tis_months / 12))
            ))

        # Air Assault
        air_assault_prob = 0.20
        if unit_type and "101ST" in unit_type.upper():
            air_assault_prob = 0.85
        if self.rng.random() < air_assault_prob:
            badges.append(MilitaryBadge(
                code="AIR_ASSAULT",
                name="Air Assault Badge",
                badge_type=BadgeType.SKILL,
                award_date=self._random_date_years_ago(1, int(tis_months / 12))
            ))

        # Combat badges (based on deployments - will correlate later)
        if tis_months > 36:  # At least 3 years TIS
            if mos.startswith("11"):  # Infantry
                cib_prob = 0.40
                if self.rng.random() < cib_prob:
                    badges.append(MilitaryBadge(
                        code="CIB",
                        name="Combat Infantryman Badge",
                        badge_type=BadgeType.COMBAT,
                        award_date=self._random_date_years_ago(1, 10)
                    ))
            elif mos.startswith("68"):  # Medical
                cmb_prob = 0.20
                if self.rng.random() < cmb_prob:
                    badges.append(MilitaryBadge(
                        code="CMB",
                        name="Combat Medical Badge",
                        badge_type=BadgeType.COMBAT,
                        award_date=self._random_date_years_ago(1, 10)
                    ))
            else:  # Other MOSs
                cab_prob = 0.15
                if self.rng.random() < cab_prob:
                    badges.append(MilitaryBadge(
                        code="CAB",
                        name="Combat Action Badge",
                        badge_type=BadgeType.COMBAT,
                        award_date=self._random_date_years_ago(1, 10)
                    ))

        # Ranger tab (rare)
        if self.rng.random() < 0.03:
            badges.append(MilitaryBadge(
                code="RANGER",
                name="Ranger Tab",
                badge_type=BadgeType.SKILL,
                award_date=self._random_date_years_ago(1, int(tis_months / 12))
            ))

        return badges

    def _generate_awards(self, rank: str, tis_months: int) -> List[Award]:
        """Generate awards based on rank and TIS."""
        awards = []

        # Army Service Ribbon (everyone gets this)
        awards.append(Award(
            code="ASR",
            name="Army Service Ribbon",
            award_type=AwardType.SERVICE,
            award_date=self._random_date_years_ago(int(tis_months / 12), int(tis_months / 12) + 1)
        ))

        # AAM (common for junior enlisted/NCOs)
        if tis_months > 24:
            num_aams = int(self.rng.poisson(lam=max(1, tis_months / 36)))  # Roughly 1 per 3 years
            for i in range(min(num_aams, 5)):  # Cap at 5
                awards.append(Award(
                    code="AAM",
                    name="Army Achievement Medal",
                    award_type=AwardType.ACHIEVEMENT,
                    award_date=self._random_date_years_ago(1, int(tis_months / 12)),
                    award_number=i + 1
                ))

        # ARCOM (for senior NCOs/mid-career)
        if tis_months > 60 and rank in ["SSG", "SFC", "MSG", "SGM", "CSM"]:
            num_arcoms = int(self.rng.poisson(lam=max(1, tis_months / 72)))  # Roughly 1 per 6 years
            for i in range(min(num_arcoms, 3)):
                awards.append(Award(
                    code="ARCOM",
                    name="Army Commendation Medal",
                    award_type=AwardType.ACHIEVEMENT,
                    award_date=self._random_date_years_ago(1, int(tis_months / 12)),
                    award_number=i + 1
                ))

        # Service medals (GWOT common)
        if tis_months > 12:
            awards.append(Award(
                code="GWOT_S",
                name="Global War on Terrorism Service Medal",
                award_type=AwardType.SERVICE,
                award_date=self._random_date_years_ago(1, int(tis_months / 12))
            ))

        return awards

    def _generate_licenses(self, mos: str) -> List[CivilianLicense]:
        """Generate civilian licenses based on MOS."""
        licenses = []

        # CDL for 88M (Motor Transport)
        if mos.startswith("88M"):
            cdl_type = self.rng.choice(["CDL_A", "CDL_B"], p=[0.7, 0.3])
            licenses.append(CivilianLicense(
                license_type="CDL",
                license_name=COMMON_LICENSE_TYPES[cdl_type],
                license_number=f"CDL{self.rng.integers(100000, 999999)}",
                issuing_authority="State DMV",
                issue_date=self._random_date_years_ago(1, 5),
                expiration_date=self._random_date_years_future(1, 3)
            ))

        # Medical licenses for 68 series
        if mos.startswith("68W"):  # Combat medic
            if self.rng.random() < 0.40:  # 40% have EMT
                licenses.append(CivilianLicense(
                    license_type="MEDICAL",
                    license_name="Emergency Medical Technician",
                    license_number=f"EMT{self.rng.integers(10000, 99999)}",
                    issuing_authority="NREMT",
                    issue_date=self._random_date_years_ago(1, 3),
                    expiration_date=self._random_date_years_future(1, 2)
                ))

        # IT certifications for 25 series
        if mos.startswith("25"):  # Signal
            if self.rng.random() < 0.25:  # 25% have IT certs
                cert_type = self.rng.choice(["IT_COMPTIA", "IT_CISSP"], p=[0.8, 0.2])
                licenses.append(CivilianLicense(
                    license_type="IT",
                    license_name=COMMON_LICENSE_TYPES.get(cert_type, "IT Certification"),
                    license_number=f"CERT{self.rng.integers(100000, 999999)}",
                    issuing_authority="CompTIA" if "COMPTIA" in cert_type else "ISC2",
                    issue_date=self._random_date_years_ago(0, 3),
                    expiration_date=self._random_date_years_future(1, 3)
                ))

        return licenses

    def _generate_deployments(self, tis_months: int) -> List[DeploymentRecord]:
        """Generate deployment history based on TIS."""
        deployments = []

        # Deployment probability increases with TIS
        if tis_months < 24:
            num_deployments = 0
        elif tis_months < 60:
            num_deployments = int(self.rng.poisson(lam=0.5))
        elif tis_months < 120:
            num_deployments = int(self.rng.poisson(lam=1.5))
        else:
            num_deployments = int(self.rng.poisson(lam=2.5))

        num_deployments = min(num_deployments, 5)  # Cap at 5

        # Generate deployments
        operations = ["OIF", "OEF", "OIR", "OFS", "Atlantic Resolve"]
        theaters = ["CENTCOM", "CENTCOM", "CENTCOM", "CENTCOM", "EUCOM"]
        locations = ["Iraq", "Afghanistan", "Iraq", "Afghanistan", "Poland"]

        for i in range(num_deployments):
            op_idx = self.rng.integers(0, len(operations))

            # Calculate max years ago (at least 1 year more than min to avoid low >= high)
            max_years_ago = max(2, int(tis_months / 12) - 1)
            start_date = self._random_date_years_ago(1, max_years_ago)
            duration = int(self.rng.integers(9, 13))  # 9-12 months typical
            end_date = start_date + timedelta(days=duration * 30)

            deployments.append(DeploymentRecord(
                operation_name=operations[op_idx],
                theater=theaters[op_idx],
                location=locations[op_idx],
                start_date=start_date,
                end_date=end_date,
                duration_months=duration,
                combat_deployment=True
            ))

        return deployments

    def _generate_duty_history(self, tis_months: int, current_base: str) -> List[DutyAssignment]:
        """Generate duty station history."""
        history = []

        # Typical assignment is 2-3 years
        num_assignments = max(1, int(tis_months / 36))  # Roughly 1 per 3 years

        bases = ["JBLM", "Fort Bragg", "Fort Campbell", "Fort Hood", "Fort Carson",
                "Schofield Barracks", "Fort Riley", "Fort Stewart", "Fort Drum"]

        for i in range(num_assignments):
            if i == num_assignments - 1:
                # Current assignment
                base = current_base
                start_date = self._random_date_years_ago(0, 3)
                end_date = None
                duration = 0
            else:
                # Previous assignment
                base = self.rng.choice([b for b in bases if b != current_base])
                years_ago_end = int((num_assignments - i - 1) * 3)
                years_ago_start = years_ago_end + 3
                start_date = self._random_date_years_ago(years_ago_start, years_ago_start + 1)
                end_date = self._random_date_years_ago(years_ago_end, years_ago_end + 1)
                duration = 36

            history.append(DutyAssignment(
                duty_station=base,
                unit="Unit TBD",  # Would need unit context
                position="Position TBD",
                start_date=start_date,
                end_date=end_date,
                duration_months=duration
            ))

        return history

    # Helper methods for realistic data generation

    def _random_high_school(self) -> str:
        """Generate random high school name."""
        cities = ["Springfield", "Lincoln", "Washington", "Jefferson", "Madison", "Central", "East", "West"]
        return f"{self.rng.choice(cities)} High School"

    def _random_community_college(self) -> str:
        """Generate random community college name."""
        locations = ["Metro", "Central", "City", "County", "Regional", "State"]
        return f"{self.rng.choice(locations)} Community College"

    def _random_university(self) -> str:
        """Generate random university name."""
        states = ["State", "Tech", "A&M", "University of"]
        names = ["Western", "Eastern", "Northern", "Southern", "Central"]
        return f"{self.rng.choice(names)} {self.rng.choice(states)} University"

    def _random_major(self, degree_level: str) -> str:
        """Generate random academic major."""
        if degree_level == "AA":
            majors = ["General Studies", "Business", "Liberal Arts", "Criminal Justice"]
        elif degree_level == "BA":
            majors = ["Business Administration", "Psychology", "Criminal Justice",
                     "Computer Science", "History", "Political Science", "Communications"]
        else:  # MA/PhD
            majors = ["Management", "Leadership", "Public Administration",
                     "Education", "Information Systems"]
        return self.rng.choice(majors)

    def _random_date_years_ago(self, min_years: int, max_years: int) -> date:
        """Generate random date X years in the past."""
        days_ago = int(self.rng.integers(min_years * 365, max_years * 365))
        return date.today() - timedelta(days=days_ago)

    def _random_date_years_future(self, min_years: int, max_years: int) -> date:
        """Generate random date X years in the future."""
        days_future = int(self.rng.integers(min_years * 365, max_years * 365))
        return date.today() + timedelta(days=days_future)


# Convenience function for integration with existing code
def generate_extended_profile(soldier_id: str,
                              rank: str,
                              mos: str,
                              base: str,
                              tis_months: int,
                              tig_months: int,
                              unit_type: Optional[str] = None,
                              seed: Optional[int] = None) -> SoldierProfileExtended:
    """
    Convenience function to generate a single extended profile.

    Args:
        soldier_id: Soldier identifier
        rank: Current rank
        mos: MOS code
        base: Current duty station
        tis_months: Time in service (months)
        tig_months: Time in grade (months)
        unit_type: Unit type (optional, for badge correlations)
        seed: Random seed (optional)

    Returns:
        SoldierProfileExtended object
    """
    generator = ProfileGenerator(seed=seed)
    return generator.generate_profile(
        soldier_id=soldier_id,
        rank=rank,
        mos=mos,
        base=base,
        tis_months=tis_months,
        tig_months=tig_months,
        unit_type=unit_type
    )

# ===== SECTION 3: Profile Utils (profile_utils.py) =====

"""
profile_utils.py
----------------

Utility functions for working with extended soldier profiles in DataFrames.

Provides helper functions for:
- Parsing JSON profile data from DataFrame columns
- Searching and filtering by qualifications
- Generating human-readable summaries
- Validating profile data integrity
- Analyzing qualification distributions

Used by dashboard, EMD agent, and other modules to work with extended profiles.
"""

import json
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import date, datetime

# Import profile data structures
try:
    from qualifications import (
        SoldierProfileExtended, EducationLevel, DLPTLevel,
        COMMON_ASI_CODES, COMMON_SQI_CODES, COMMON_LANGUAGES,
        COMMON_BADGES, COMMON_AWARDS
    )
    EXTENDED_PROFILES_AVAILABLE = True
except ImportError:
    EXTENDED_PROFILES_AVAILABLE = False


# ============================================================================
# JSON Parsing Helpers
# ============================================================================

def parse_json_field(value: Any, default: Any = None) -> Any:
    """
    Safely parse a JSON field from a DataFrame.

    Handles:
    - None/NaN values -> returns default
    - Already parsed objects -> returns as-is
    - JSON strings -> parses and returns
    - Invalid JSON -> returns default

    Args:
        value: Value from DataFrame column
        default: Default value if parsing fails

    Returns:
        Parsed object or default
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default if default is not None else []

    if isinstance(value, (list, dict)):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return default if default is not None else []

    return default if default is not None else []


def get_languages(soldier_row: pd.Series) -> List[Dict]:
    """Extract language proficiencies from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('languages_json'), [])


def get_asi_codes(soldier_row: pd.Series) -> List[Dict]:
    """Extract ASI codes from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('asi_codes_json'), [])


def get_sqi_codes(soldier_row: pd.Series) -> List[Dict]:
    """Extract SQI codes from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('sqi_codes_json'), [])


def get_badges(soldier_row: pd.Series) -> List[Dict]:
    """Extract badges from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('badges_json'), [])


def get_awards(soldier_row: pd.Series) -> List[Dict]:
    """Extract awards from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('awards_json'), [])


def get_licenses(soldier_row: pd.Series) -> List[Dict]:
    """Extract civilian licenses from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('licenses_json'), [])


def get_deployments(soldier_row: pd.Series) -> List[Dict]:
    """Extract deployment history from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('deployments_json'), [])


def get_duty_history(soldier_row: pd.Series) -> List[Dict]:
    """Extract duty station history from soldier DataFrame row."""
    return parse_json_field(soldier_row.get('duty_history_json'), [])


# ============================================================================
# Qualification Checking Helpers
# ============================================================================

def has_language(soldier_row: pd.Series,
                 language_code: str,
                 min_level: int = 2) -> bool:
    """
    Check if soldier has a specific language at minimum proficiency.

    Args:
        soldier_row: Soldier DataFrame row
        language_code: ISO 639-1 language code (e.g., 'AR', 'ES', 'KO')
        min_level: Minimum DLPT level (0-5, default 2 for "Limited Working")

    Returns:
        True if soldier has language at required level
    """
    languages = get_languages(soldier_row)
    for lang in languages:
        if lang.get('language_code') == language_code:
            listening = lang.get('listening_level', 0)
            reading = lang.get('reading_level', 0)
            return listening >= min_level and reading >= min_level
    return False


def has_any_language(soldier_row: pd.Series, min_level: int = 2) -> bool:
    """Check if soldier has any foreign language at minimum proficiency."""
    languages = get_languages(soldier_row)
    for lang in languages:
        listening = lang.get('listening_level', 0)
        reading = lang.get('reading_level', 0)
        if listening >= min_level and reading >= min_level:
            return True
    return False


def has_asi(soldier_row: pd.Series, asi_code: str) -> bool:
    """
    Check if soldier has a specific ASI.

    Args:
        soldier_row: Soldier DataFrame row
        asi_code: 2-character ASI code (e.g., 'B4', 'K3', 'L9')

    Returns:
        True if soldier has the ASI
    """
    asis = get_asi_codes(soldier_row)
    for asi in asis:
        if asi.get('code') == asi_code:
            # Check if not expired
            exp_date = asi.get('expiration_date')
            if exp_date is None:
                return True
            # Parse date if string
            if isinstance(exp_date, str):
                exp_date = datetime.fromisoformat(exp_date).date()
            return exp_date >= date.today()
    return False


def has_sqi(soldier_row: pd.Series, sqi_code: str) -> bool:
    """
    Check if soldier has a specific SQI.

    Args:
        soldier_row: Soldier DataFrame row
        sqi_code: 1-character SQI code (e.g., 'V', 'W', 'X', 'Y')

    Returns:
        True if soldier has the SQI
    """
    sqis = get_sqi_codes(soldier_row)
    return any(sqi.get('code') == sqi_code for sqi in sqis)


def has_badge(soldier_row: pd.Series, badge_code: str) -> bool:
    """
    Check if soldier has a specific badge.

    Args:
        soldier_row: Soldier DataFrame row
        badge_code: Badge code (e.g., 'AIRBORNE', 'RANGER', 'CIB', 'EFMB')

    Returns:
        True if soldier has the badge
    """
    badges = get_badges(soldier_row)
    return any(badge.get('code') == badge_code for badge in badges)


def has_award(soldier_row: pd.Series, award_type: str) -> bool:
    """
    Check if soldier has a specific award type.

    Args:
        soldier_row: Soldier DataFrame row
        award_type: Award type (e.g., 'BSM', 'ARCOM', 'AAM', 'MSM')

    Returns:
        True if soldier has the award
    """
    awards = get_awards(soldier_row)
    return any(award.get('award_type') == award_type for award in awards)


def has_combat_badge(soldier_row: pd.Series) -> bool:
    """Check if soldier has any combat badge (CIB, CAB, CMB, etc.)."""
    badges = get_badges(soldier_row)
    combat_badges = {'CIB', 'CAB', 'CMB', 'CIB_2', 'CIB_3'}
    return any(badge.get('code') in combat_badges for badge in badges)


def has_combat_experience(soldier_row: pd.Series) -> bool:
    """Check if soldier has combat deployment experience."""
    deployments = get_deployments(soldier_row)
    return any(deploy.get('combat_deployment', False) for deploy in deployments)


def get_deployment_count(soldier_row: pd.Series,
                        combat_only: bool = False) -> int:
    """
    Count soldier's deployments.

    Args:
        soldier_row: Soldier DataFrame row
        combat_only: If True, only count combat deployments

    Returns:
        Number of deployments
    """
    deployments = get_deployments(soldier_row)
    if combat_only:
        return sum(1 for d in deployments if d.get('combat_deployment', False))
    return len(deployments)


def has_theater_experience(soldier_row: pd.Series, theater: str) -> bool:
    """
    Check if soldier has deployment experience in a specific theater.

    Args:
        soldier_row: Soldier DataFrame row
        theater: Theater name (e.g., 'CENTCOM', 'EUCOM', 'INDOPACOM')

    Returns:
        True if soldier deployed to theater
    """
    deployments = get_deployments(soldier_row)
    return any(deploy.get('theater') == theater for deploy in deployments)


def get_education_level_value(soldier_row: pd.Series) -> int:
    """
    Get numeric value of education level for comparisons.

    Returns:
        0=None, 1=GED, 2=HS, 3=SOME_COLLEGE, 4=AA, 5=BA, 6=MA, 7=PHD
    """
    edu = soldier_row.get('education_level', 'HS')
    if isinstance(edu, str):
        edu_map = {
            'NONE': 0, 'GED': 1, 'HS': 2, 'SOME_COLLEGE': 3,
            'AA': 4, 'BA': 5, 'MA': 6, 'PHD': 7, 'PROFESSIONAL': 7
        }
        return edu_map.get(edu, 2)
    return 2  # Default to HS


def has_minimum_education(soldier_row: pd.Series,
                         min_level: str = 'HS') -> bool:
    """
    Check if soldier meets minimum education requirement.

    Args:
        soldier_row: Soldier DataFrame row
        min_level: Minimum education level (e.g., 'HS', 'BA', 'MA')

    Returns:
        True if soldier meets or exceeds requirement
    """
    edu_map = {
        'NONE': 0, 'GED': 1, 'HS': 2, 'SOME_COLLEGE': 3,
        'AA': 4, 'BA': 5, 'MA': 6, 'PHD': 7, 'PROFESSIONAL': 7
    }
    soldier_level = get_education_level_value(soldier_row)
    required_level = edu_map.get(min_level, 2)
    return soldier_level >= required_level


# ============================================================================
# Profile Summary Generators
# ============================================================================

def generate_qualification_summary(soldier_row: pd.Series) -> str:
    """
    Generate human-readable qualification summary for a soldier.

    Returns:
        Multi-line string with soldier qualifications
    """
    lines = []

    # Basic info
    soldier_id = soldier_row.get('soldier_id', 'Unknown')
    rank = soldier_row.get('paygrade', 'Unknown')
    mos = soldier_row.get('mos', 'Unknown')
    lines.append(f"Soldier {soldier_id}: {rank} {mos}")

    # Education
    edu = soldier_row.get('education_level', 'HS')
    lines.append(f"  Education: {edu}")

    # Languages
    languages = get_languages(soldier_row)
    if languages:
        lang_str = ", ".join([
            f"{lang.get('language_name', 'Unknown')} "
            f"(L{lang.get('listening_level', 0)}/R{lang.get('reading_level', 0)})"
            for lang in languages
        ])
        lines.append(f"  Languages: {lang_str}")

    # ASIs
    asis = get_asi_codes(soldier_row)
    if asis:
        asi_str = ", ".join([asi.get('code', '??') for asi in asis])
        lines.append(f"  ASIs: {asi_str}")

    # SQIs
    sqis = get_sqi_codes(soldier_row)
    if sqis:
        sqi_str = ", ".join([sqi.get('code', '?') for sqi in sqis])
        lines.append(f"  SQIs: {sqi_str}")

    # Badges
    badges = get_badges(soldier_row)
    if badges:
        badge_str = ", ".join([badge.get('code', 'Unknown') for badge in badges])
        lines.append(f"  Badges: {badge_str}")

    # Awards
    awards = get_awards(soldier_row)
    if awards:
        lines.append(f"  Awards: {len(awards)} total")

    # Deployments
    deployments = get_deployments(soldier_row)
    if deployments:
        combat_count = sum(1 for d in deployments if d.get('combat_deployment', False))
        lines.append(f"  Deployments: {len(deployments)} total ({combat_count} combat)")

    # TIS/TIG
    tis = soldier_row.get('time_in_service_months', 0)
    tig = soldier_row.get('time_in_grade_months', 0)
    if tis > 0:
        lines.append(f"  TIS: {tis} months, TIG: {tig} months")

    return "\n".join(lines)


def generate_short_summary(soldier_row: pd.Series) -> str:
    """
    Generate brief one-line qualification summary.

    Returns:
        Single-line summary string
    """
    parts = []

    # Languages
    languages = get_languages(soldier_row)
    if languages:
        parts.append(f"{len(languages)} lang")

    # Badges
    badges = get_badges(soldier_row)
    if badges:
        parts.append(f"{len(badges)} badge")

    # Deployments
    deploy_count = get_deployment_count(soldier_row, combat_only=True)
    if deploy_count > 0:
        parts.append(f"{deploy_count} deploy")

    # Education
    edu = soldier_row.get('education_level', 'HS')
    if edu not in ['HS', 'GED', 'NONE']:
        parts.append(edu)

    return ", ".join(parts) if parts else "Standard qualifications"


# ============================================================================
# DataFrame Filtering Functions
# ============================================================================

def filter_by_language(df: pd.DataFrame,
                      language_code: str,
                      min_level: int = 2) -> pd.DataFrame:
    """
    Filter DataFrame to soldiers with specific language proficiency.

    Args:
        df: Soldiers DataFrame
        language_code: ISO 639-1 language code
        min_level: Minimum DLPT level

    Returns:
        Filtered DataFrame
    """
    mask = df.apply(lambda row: has_language(row, language_code, min_level), axis=1)
    return df[mask]


def filter_by_asi(df: pd.DataFrame, asi_code: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with specific ASI."""
    mask = df.apply(lambda row: has_asi(row, asi_code), axis=1)
    return df[mask]


def filter_by_sqi(df: pd.DataFrame, sqi_code: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with specific SQI."""
    mask = df.apply(lambda row: has_sqi(row, sqi_code), axis=1)
    return df[mask]


def filter_by_badge(df: pd.DataFrame, badge_code: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with specific badge."""
    mask = df.apply(lambda row: has_badge(row, badge_code), axis=1)
    return df[mask]


def filter_by_combat_experience(df: pd.DataFrame) -> pd.DataFrame:
    """Filter DataFrame to soldiers with combat deployment experience."""
    mask = df.apply(has_combat_experience, axis=1)
    return df[mask]


def filter_by_education(df: pd.DataFrame, min_level: str = 'BA') -> pd.DataFrame:
    """Filter DataFrame to soldiers meeting minimum education."""
    mask = df.apply(lambda row: has_minimum_education(row, min_level), axis=1)
    return df[mask]


def filter_by_theater(df: pd.DataFrame, theater: str) -> pd.DataFrame:
    """Filter DataFrame to soldiers with experience in specific theater."""
    mask = df.apply(lambda row: has_theater_experience(row, theater), axis=1)
    return df[mask]


# ============================================================================
# Statistical Analysis Functions
# ============================================================================

def get_language_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get distribution of language proficiencies across DataFrame.

    Returns:
        Dictionary mapping language codes to soldier counts
    """
    lang_counts = {}

    for idx, row in df.iterrows():
        languages = get_languages(row)
        for lang in languages:
            code = lang.get('language_code', 'Unknown')
            lang_counts[code] = lang_counts.get(code, 0) + 1

    return dict(sorted(lang_counts.items(), key=lambda x: x[1], reverse=True))


def get_badge_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of badges across DataFrame."""
    badge_counts = {}

    for idx, row in df.iterrows():
        badges = get_badges(row)
        for badge in badges:
            code = badge.get('code', 'Unknown')
            badge_counts[code] = badge_counts.get(code, 0) + 1

    return dict(sorted(badge_counts.items(), key=lambda x: x[1], reverse=True))


def get_asi_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of ASIs across DataFrame."""
    asi_counts = {}

    for idx, row in df.iterrows():
        asis = get_asi_codes(row)
        for asi in asis:
            code = asi.get('code', 'Unknown')
            asi_counts[code] = asi_counts.get(code, 0) + 1

    return dict(sorted(asi_counts.items(), key=lambda x: x[1], reverse=True))


def get_education_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Get distribution of education levels across DataFrame."""
    if 'education_level' not in df.columns:
        return {}

    return df['education_level'].value_counts().to_dict()


def get_deployment_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get deployment statistics for DataFrame.

    Returns:
        Dictionary with deployment metrics
    """
    stats = {
        'total_soldiers': len(df),
        'soldiers_with_deployments': 0,
        'soldiers_with_combat': 0,
        'total_deployments': 0,
        'total_combat_deployments': 0,
        'avg_deployments_per_soldier': 0.0,
        'theaters': {}
    }

    for idx, row in df.iterrows():
        deployments = get_deployments(row)
        if deployments:
            stats['soldiers_with_deployments'] += 1
            stats['total_deployments'] += len(deployments)

            for deploy in deployments:
                if deploy.get('combat_deployment', False):
                    stats['total_combat_deployments'] += 1

                theater = deploy.get('theater', 'Unknown')
                stats['theaters'][theater] = stats['theaters'].get(theater, 0) + 1

        if has_combat_experience(row):
            stats['soldiers_with_combat'] += 1

    if stats['total_soldiers'] > 0:
        stats['avg_deployments_per_soldier'] = stats['total_deployments'] / stats['total_soldiers']

    return stats


def get_qualification_coverage(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate what percentage of soldiers have various qualifications.

    Returns:
        Dictionary mapping qualification types to percentages (0.0-1.0)
    """
    total = len(df)
    if total == 0:
        return {}

    coverage = {}

    # Language proficiency
    lang_count = sum(1 for _, row in df.iterrows() if has_any_language(row))
    coverage['any_language'] = lang_count / total

    # Combat experience
    combat_count = sum(1 for _, row in df.iterrows() if has_combat_experience(row))
    coverage['combat_experience'] = combat_count / total

    # Combat badges
    badge_count = sum(1 for _, row in df.iterrows() if has_combat_badge(row))
    coverage['combat_badge'] = badge_count / total

    # College education
    college_count = sum(1 for _, row in df.iterrows()
                       if has_minimum_education(row, 'SOME_COLLEGE'))
    coverage['some_college'] = college_count / total

    # Bachelor's degree
    ba_count = sum(1 for _, row in df.iterrows()
                  if has_minimum_education(row, 'BA'))
    coverage['bachelors'] = ba_count / total

    return coverage


# ============================================================================
# Validation Functions
# ============================================================================

def validate_profile_data(soldier_row: pd.Series) -> Tuple[bool, List[str]]:
    """
    Validate extended profile data for a soldier.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Check required fields exist
    required_fields = ['soldier_id', 'paygrade', 'mos', 'base']
    for field in required_fields:
        if field not in soldier_row or pd.isna(soldier_row.get(field)):
            errors.append(f"Missing required field: {field}")

    # Validate TIS/TIG if present
    tis = soldier_row.get('time_in_service_months', 0)
    tig = soldier_row.get('time_in_grade_months', 0)

    if tis < 0:
        errors.append(f"Invalid TIS: {tis} (must be >= 0)")
    if tig < 0:
        errors.append(f"Invalid TIG: {tig} (must be >= 0)")
    if tig > tis:
        errors.append(f"TIG ({tig}) cannot exceed TIS ({tis})")

    # Validate JSON fields can be parsed
    json_fields = ['languages_json', 'asi_codes_json', 'badges_json',
                  'awards_json', 'deployments_json']
    for field in json_fields:
        if field in soldier_row:
            try:
                parse_json_field(soldier_row[field], [])
            except Exception as e:
                errors.append(f"Invalid JSON in {field}: {e}")

    return (len(errors) == 0, errors)


def validate_dataframe_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame has expected extended profile schema.

    Returns:
        (is_valid, list_of_warnings)
    """
    warnings = []

    # Check for extended profile columns
    expected_columns = [
        'education_level', 'languages_json', 'asi_codes_json',
        'sqi_codes_json', 'badges_json', 'awards_json',
        'licenses_json', 'deployments_json', 'time_in_service_months'
    ]

    missing = []
    for col in expected_columns:
        if col not in df.columns:
            missing.append(col)

    if missing:
        warnings.append(f"Missing extended profile columns: {missing}")
        warnings.append("Extended profile features may not be available")

    return (len(warnings) == 0, warnings)


# ============================================================================
# Export/Import Helpers
# ============================================================================

def export_profile_to_dict(soldier_row: pd.Series) -> Dict[str, Any]:
    """
    Export soldier profile to a complete dictionary.

    Returns:
        Dictionary with all profile data (parsed JSON fields)
    """
    profile = {}

    # Basic fields
    for field in ['soldier_id', 'paygrade', 'mos', 'base', 'education_level',
                 'time_in_service_months', 'time_in_grade_months']:
        profile[field] = soldier_row.get(field)

    # Parse JSON fields
    profile['languages'] = get_languages(soldier_row)
    profile['asi_codes'] = get_asi_codes(soldier_row)
    profile['sqi_codes'] = get_sqi_codes(soldier_row)
    profile['badges'] = get_badges(soldier_row)
    profile['awards'] = get_awards(soldier_row)
    profile['licenses'] = get_licenses(soldier_row)
    profile['deployments'] = get_deployments(soldier_row)
    profile['duty_history'] = get_duty_history(soldier_row)

    return profile


# ============================================================================
# Convenience Functions
# ============================================================================

def print_profile_summary(soldier_row: pd.Series) -> None:
    """Print formatted profile summary to console."""
    print(generate_qualification_summary(soldier_row))


def print_dataframe_statistics(df: pd.DataFrame) -> None:
    """Print statistical summary of DataFrame qualifications."""
    print("="*80)
    print("EXTENDED PROFILE STATISTICS")
    print("="*80)
    print(f"\nTotal Soldiers: {len(df)}")

    # Education
    print("\nEducation Distribution:")
    edu_dist = get_education_distribution(df)
    for edu, count in sorted(edu_dist.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(df) * 100
        print(f"  {edu}: {count} ({pct:.1f}%)")

    # Languages
    print("\nTop Languages:")
    lang_dist = get_language_distribution(df)
    for lang, count in list(lang_dist.items())[:10]:
        pct = count / len(df) * 100
        print(f"  {lang}: {count} ({pct:.1f}%)")

    # Badges
    print("\nTop Badges:")
    badge_dist = get_badge_distribution(df)
    for badge, count in list(badge_dist.items())[:10]:
        pct = count / len(df) * 100
        print(f"  {badge}: {count} ({pct:.1f}%)")

    # Deployments
    print("\nDeployment Statistics:")
    deploy_stats = get_deployment_statistics(df)
    print(f"  Soldiers with deployments: {deploy_stats['soldiers_with_deployments']} "
          f"({deploy_stats['soldiers_with_deployments']/len(df)*100:.1f}%)")
    print(f"  Soldiers with combat: {deploy_stats['soldiers_with_combat']} "
          f"({deploy_stats['soldiers_with_combat']/len(df)*100:.1f}%)")
    print(f"  Avg deployments per soldier: {deploy_stats['avg_deployments_per_soldier']:.2f}")

    # Coverage
    print("\nQualification Coverage:")
    coverage = get_qualification_coverage(df)
    for qual, pct in coverage.items():
        print(f"  {qual}: {pct*100:.1f}%")

    print("="*80)

# ===== SECTION 4: Billet Requirements (billet_requirements.py) =====

"""
billet_requirements.py
----------------------

Extended qualification requirements for billets.

Adds comprehensive qualification matching to the manning document system:
- Education requirements (minimum degree level)
- Language requirements (specific languages with proficiency levels)
- ASI/SQI requirements (special qualifications)
- Badge requirements (Airborne, Ranger, CIB, etc.)
- License requirements (CDL, medical, IT certs)
- Experience requirements (deployments, theaters, TIS/TIG)
- Award requirements (valor, achievement, service)

Integrates with soldier_profile_extended.py and profile_utils.py for matching.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set
from datetime import date


@dataclass
class LanguageRequirement:
    """
    Language proficiency requirement.

    Specifies required language(s) and minimum DLPT levels.
    """
    language_code: str  # ISO 639-1 code (e.g., 'AR', 'KO', 'ES')
    language_name: str  # Full name (e.g., 'Arabic', 'Korean', 'Spanish')
    min_listening_level: int = 2  # DLPT 0-5 scale (2 = Limited Working)
    min_reading_level: int = 2
    required: bool = True  # If False, this is preferred but not required
    native_acceptable: bool = True  # Accept native speakers without DLPT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            'language_code': self.language_code,
            'language_name': self.language_name,
            'min_listening_level': self.min_listening_level,
            'min_reading_level': self.min_reading_level,
            'required': self.required,
            'native_acceptable': self.native_acceptable
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> LanguageRequirement:
        """Create from dictionary."""
        return LanguageRequirement(**data)


@dataclass
class BadgeRequirement:
    """
    Badge/tab requirement.

    Specifies required or preferred badges.
    """
    badge_code: str  # e.g., 'AIRBORNE', 'RANGER', 'CIB', 'EFMB'
    badge_name: str
    required: bool = True  # If False, this is preferred
    alternative_badges: List[str] = field(default_factory=list)  # Acceptable alternatives

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            'badge_code': self.badge_code,
            'badge_name': self.badge_name,
            'required': self.required,
            'alternative_badges': self.alternative_badges
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> BadgeRequirement:
        """Create from dictionary."""
        return BadgeRequirement(**data)


@dataclass
class ExperienceRequirement:
    """
    Experience requirement.

    Specifies deployment, combat, or theater-specific experience.
    """
    requirement_type: str  # 'combat', 'deployment', 'theater', 'leadership'
    description: str
    required: bool = True

    # Deployment/combat requirements
    min_deployments: int = 0
    combat_required: bool = False
    theater: Optional[str] = None  # Specific theater (e.g., 'CENTCOM', 'INDOPACOM')

    # Leadership requirements
    min_leadership_level: int = 0  # 0=none, 1=team, 2=squad, 3=platoon, 4=company

    # Time requirements
    min_time_in_service_months: int = 0
    min_time_in_grade_months: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            'requirement_type': self.requirement_type,
            'description': self.description,
            'required': self.required,
            'min_deployments': self.min_deployments,
            'combat_required': self.combat_required,
            'theater': self.theater,
            'min_leadership_level': self.min_leadership_level,
            'min_time_in_service_months': self.min_time_in_service_months,
            'min_time_in_grade_months': self.min_time_in_grade_months
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ExperienceRequirement:
        """Create from dictionary."""
        return ExperienceRequirement(**data)


@dataclass
class BilletRequirements:
    """
    Comprehensive qualification requirements for a billet.

    This extends the basic CapabilityRequirement with detailed qualifications
    that can be matched against SoldierProfileExtended.
    """
    # Basic identification
    billet_id: Optional[int] = None
    capability_name: str = ""
    position_title: str = ""

    # Education requirements
    min_education_level: Optional[str] = None  # 'HS', 'AA', 'BA', 'MA', 'PHD'
    preferred_education_level: Optional[str] = None
    education_major: Optional[str] = None  # Preferred major (e.g., 'Engineering')

    # Language requirements
    languages_required: List[LanguageRequirement] = field(default_factory=list)
    any_language_acceptable: bool = False  # Accept any foreign language

    # ASI/SQI requirements
    asi_codes_required: List[str] = field(default_factory=list)  # e.g., ['B4', 'K3']
    asi_codes_preferred: List[str] = field(default_factory=list)
    sqi_codes_required: List[str] = field(default_factory=list)  # e.g., ['V', 'W']
    sqi_codes_preferred: List[str] = field(default_factory=list)

    # Badge requirements
    badges_required: List[BadgeRequirement] = field(default_factory=list)
    badges_preferred: List[BadgeRequirement] = field(default_factory=list)

    # License requirements
    licenses_required: List[str] = field(default_factory=list)  # e.g., ['CDL_A', 'EMT']
    licenses_preferred: List[str] = field(default_factory=list)

    # Experience requirements
    experience_required: List[ExperienceRequirement] = field(default_factory=list)
    experience_preferred: List[ExperienceRequirement] = field(default_factory=list)

    # Award requirements (rare, but possible for high-visibility positions)
    awards_required: List[str] = field(default_factory=list)  # e.g., ['BSM', 'ARCOM']
    awards_preferred: List[str] = field(default_factory=list)

    # Medical/fitness requirements
    max_medical_category: int = 2  # 1-4 (1=fully fit, 4=non-deployable)
    max_dental_category: int = 2
    min_acft_score: Optional[int] = None
    min_weapons_qual: Optional[int] = None

    # Availability requirements
    available_start_date: Optional[date] = None
    min_dwell_months: int = 0  # Minimum time since last deployment

    # Priority/criticality
    criticality: int = 2  # 1=low, 2=medium, 3=high, 4=critical

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame storage."""
        return {
            'billet_id': self.billet_id,
            'capability_name': self.capability_name,
            'position_title': self.position_title,
            'min_education_level': self.min_education_level,
            'preferred_education_level': self.preferred_education_level,
            'education_major': self.education_major,
            'languages_required_json': json.dumps([lang.to_dict() for lang in self.languages_required]),
            'any_language_acceptable': self.any_language_acceptable,
            'asi_codes_required_json': json.dumps(self.asi_codes_required),
            'asi_codes_preferred_json': json.dumps(self.asi_codes_preferred),
            'sqi_codes_required_json': json.dumps(self.sqi_codes_required),
            'sqi_codes_preferred_json': json.dumps(self.sqi_codes_preferred),
            'badges_required_json': json.dumps([badge.to_dict() for badge in self.badges_required]),
            'badges_preferred_json': json.dumps([badge.to_dict() for badge in self.badges_preferred]),
            'licenses_required_json': json.dumps(self.licenses_required),
            'licenses_preferred_json': json.dumps(self.licenses_preferred),
            'experience_required_json': json.dumps([exp.to_dict() for exp in self.experience_required]),
            'experience_preferred_json': json.dumps([exp.to_dict() for exp in self.experience_preferred]),
            'awards_required_json': json.dumps(self.awards_required),
            'awards_preferred_json': json.dumps(self.awards_preferred),
            'max_medical_category': self.max_medical_category,
            'max_dental_category': self.max_dental_category,
            'min_acft_score': self.min_acft_score,
            'min_weapons_qual': self.min_weapons_qual,
            'available_start_date': str(self.available_start_date) if self.available_start_date else None,
            'min_dwell_months': self.min_dwell_months,
            'criticality': self.criticality
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> BilletRequirements:
        """Create from dictionary."""
        req = BilletRequirements(
            billet_id=data.get('billet_id'),
            capability_name=data.get('capability_name', ''),
            position_title=data.get('position_title', ''),
            min_education_level=data.get('min_education_level'),
            preferred_education_level=data.get('preferred_education_level'),
            education_major=data.get('education_major'),
            any_language_acceptable=data.get('any_language_acceptable', False),
            max_medical_category=data.get('max_medical_category', 2),
            max_dental_category=data.get('max_dental_category', 2),
            min_acft_score=data.get('min_acft_score'),
            min_weapons_qual=data.get('min_weapons_qual'),
            min_dwell_months=data.get('min_dwell_months', 0),
            criticality=data.get('criticality', 2)
        )

        # Parse JSON fields
        if 'languages_required_json' in data:
            langs_data = json.loads(data['languages_required_json'])
            req.languages_required = [LanguageRequirement.from_dict(lang) for lang in langs_data]

        if 'asi_codes_required_json' in data:
            req.asi_codes_required = json.loads(data['asi_codes_required_json'])

        if 'asi_codes_preferred_json' in data:
            req.asi_codes_preferred = json.loads(data['asi_codes_preferred_json'])

        if 'sqi_codes_required_json' in data:
            req.sqi_codes_required = json.loads(data['sqi_codes_required_json'])

        if 'sqi_codes_preferred_json' in data:
            req.sqi_codes_preferred = json.loads(data['sqi_codes_preferred_json'])

        if 'badges_required_json' in data:
            badges_data = json.loads(data['badges_required_json'])
            req.badges_required = [BadgeRequirement.from_dict(badge) for badge in badges_data]

        if 'badges_preferred_json' in data:
            badges_data = json.loads(data['badges_preferred_json'])
            req.badges_preferred = [BadgeRequirement.from_dict(badge) for badge in badges_data]

        if 'licenses_required_json' in data:
            req.licenses_required = json.loads(data['licenses_required_json'])

        if 'licenses_preferred_json' in data:
            req.licenses_preferred = json.loads(data['licenses_preferred_json'])

        if 'experience_required_json' in data:
            exp_data = json.loads(data['experience_required_json'])
            req.experience_required = [ExperienceRequirement.from_dict(exp) for exp in exp_data]

        if 'experience_preferred_json' in data:
            exp_data = json.loads(data['experience_preferred_json'])
            req.experience_preferred = [ExperienceRequirement.from_dict(exp) for exp in exp_data]

        if 'awards_required_json' in data:
            req.awards_required = json.loads(data['awards_required_json'])

        if 'awards_preferred_json' in data:
            req.awards_preferred = json.loads(data['awards_preferred_json'])

        if 'available_start_date' in data and data['available_start_date']:
            req.available_start_date = date.fromisoformat(data['available_start_date'])

        return req

    def get_summary(self) -> str:
        """Generate human-readable summary of requirements."""
        lines = [f"Requirements for: {self.position_title or self.capability_name}"]

        if self.min_education_level:
            lines.append(f"  Education: {self.min_education_level}+ required")

        if self.languages_required:
            lang_str = ", ".join([f"{lang.language_name} (L{lang.min_listening_level}+)"
                                 for lang in self.languages_required])
            lines.append(f"  Languages: {lang_str}")

        if self.asi_codes_required:
            lines.append(f"  ASIs: {', '.join(self.asi_codes_required)}")

        if self.sqi_codes_required:
            lines.append(f"  SQIs: {', '.join(self.sqi_codes_required)}")

        if self.badges_required:
            badge_str = ", ".join([badge.badge_code for badge in self.badges_required])
            lines.append(f"  Badges: {badge_str}")

        if self.experience_required:
            for exp in self.experience_required:
                lines.append(f"  Experience: {exp.description}")

        if self.min_acft_score:
            lines.append(f"  Min ACFT: {self.min_acft_score}")

        if self.min_dwell_months:
            lines.append(f"  Min dwell: {self.min_dwell_months} months")

        return "\n".join(lines)


# ============================================================================
# Common requirement templates
# ============================================================================

class BilletRequirementTemplates:
    """Pre-built requirement templates for common positions."""

    @staticmethod
    def ranger_qualified_infantry_leader() -> BilletRequirements:
        """Requirements for Ranger-qualified infantry leadership position."""
        return BilletRequirements(
            position_title="Ranger-Qualified Infantry Leader",
            min_education_level="HS",
            badges_required=[
                BadgeRequirement(badge_code="RANGER", badge_name="Ranger Tab", required=True),
                BadgeRequirement(badge_code="AIRBORNE", badge_name="Airborne Badge", required=True)
            ],
            experience_required=[
                ExperienceRequirement(
                    requirement_type="combat",
                    description="Combat deployment experience required",
                    combat_required=True,
                    min_deployments=1
                ),
                ExperienceRequirement(
                    requirement_type="leadership",
                    description="Squad leadership or higher",
                    min_leadership_level=2
                )
            ],
            max_medical_category=1,
            min_acft_score=500,
            criticality=3
        )

    @staticmethod
    def intelligence_analyst_strategic_language() -> BilletRequirements:
        """Requirements for strategic language intelligence analyst."""
        return BilletRequirements(
            position_title="Strategic Language Intelligence Analyst",
            min_education_level="AA",
            preferred_education_level="BA",
            languages_required=[
                LanguageRequirement(
                    language_code="AR",
                    language_name="Arabic",
                    min_listening_level=3,
                    min_reading_level=3,
                    required=True
                )
            ],
            asi_codes_preferred=["L9"],  # EO Advisor
            experience_required=[
                ExperienceRequirement(
                    requirement_type="theater",
                    description="CENTCOM theater experience preferred",
                    theater="CENTCOM",
                    required=False
                )
            ],
            max_medical_category=2,
            criticality=4
        )

    @staticmethod
    def special_forces_comms_sergeant() -> BilletRequirements:
        """Requirements for SF communications sergeant."""
        return BilletRequirements(
            position_title="Special Forces Communications Sergeant",
            min_education_level="HS",
            sqi_codes_required=["W"],  # SF qualified
            badges_required=[
                BadgeRequirement(badge_code="AIRBORNE", badge_name="Airborne Badge", required=True)
            ],
            licenses_required=["HAM_RADIO", "IT_CERT"],
            experience_required=[
                ExperienceRequirement(
                    requirement_type="combat",
                    description="Combat deployment with SF unit",
                    combat_required=True,
                    min_deployments=2
                ),
                ExperienceRequirement(
                    requirement_type="leadership",
                    description="Team leadership experience",
                    min_leadership_level=1
                )
            ],
            max_medical_category=1,
            min_acft_score=540,
            criticality=4
        )

    @staticmethod
    def combat_medic_instructor() -> BilletRequirements:
        """Requirements for combat medic instructor position."""
        return BilletRequirements(
            position_title="Combat Medic Instructor",
            min_education_level="AA",
            asi_codes_required=["P5"],  # Instructor
            badges_preferred=[
                BadgeRequirement(badge_code="EFMB", badge_name="Expert Field Medical Badge", required=False)
            ],
            licenses_required=["EMT", "NREMT"],
            experience_required=[
                ExperienceRequirement(
                    requirement_type="combat",
                    description="Combat medic experience",
                    combat_required=True,
                    min_deployments=1
                ),
                ExperienceRequirement(
                    requirement_type="leadership",
                    description="Minimum 5 years TIS",
                    min_time_in_service_months=60
                )
            ],
            max_medical_category=2,
            criticality=3
        )

    @staticmethod
    def logistics_operations_chief() -> BilletRequirements:
        """Requirements for logistics operations chief."""
        return BilletRequirements(
            position_title="Logistics Operations Chief",
            min_education_level="AA",
            preferred_education_level="BA",
            education_major="Supply Chain Management",
            asi_codes_preferred=["H8"],  # Material Management
            licenses_required=["CDL_A"],
            experience_required=[
                ExperienceRequirement(
                    requirement_type="leadership",
                    description="Platoon sergeant level leadership",
                    min_leadership_level=3
                ),
                ExperienceRequirement(
                    requirement_type="deployment",
                    description="Deployment logistics experience",
                    min_deployments=2
                )
            ],
            max_medical_category=2,
            criticality=3
        )

    @staticmethod
    def airborne_infantry_rifleman() -> BilletRequirements:
        """Requirements for standard airborne infantry rifleman."""
        return BilletRequirements(
            position_title="Airborne Infantry Rifleman",
            min_education_level="HS",
            badges_required=[
                BadgeRequirement(badge_code="AIRBORNE", badge_name="Airborne Badge", required=True)
            ],
            max_medical_category=1,
            min_acft_score=450,
            min_weapons_qual=30,
            criticality=2
        )

    @staticmethod
    def signal_support_specialist() -> BilletRequirements:
        """Requirements for signal support specialist."""
        return BilletRequirements(
            position_title="Signal Support Specialist",
            min_education_level="HS",
            licenses_preferred=["COMPTIA_SEC_PLUS", "COMPTIA_NET_PLUS"],
            experience_preferred=[
                ExperienceRequirement(
                    requirement_type="deployment",
                    description="Deployment signal support experience",
                    min_deployments=1,
                    required=False
                )
            ],
            max_medical_category=2,
            criticality=2
        )


# ============================================================================
# Helper functions for generating requirements
# ============================================================================

def create_basic_requirements(
    position_title: str,
    min_education: Optional[str] = None,
    badges: Optional[List[str]] = None,
    languages: Optional[List[Tuple[str, str, int]]] = None,
    combat_required: bool = False,
    min_deployments: int = 0
) -> BilletRequirements:
    """
    Create basic billet requirements from simple parameters.

    Args:
        position_title: Position title
        min_education: Minimum education level
        badges: List of required badge codes
        languages: List of (code, name, min_level) tuples
        combat_required: Require combat experience
        min_deployments: Minimum deployment count

    Returns:
        BilletRequirements object
    """
    req = BilletRequirements(
        position_title=position_title,
        min_education_level=min_education
    )

    # Add badge requirements
    if badges:
        for badge_code in badges:
            req.badges_required.append(
                BadgeRequirement(badge_code=badge_code, badge_name=badge_code, required=True)
            )

    # Add language requirements
    if languages:
        for lang_code, lang_name, min_level in languages:
            req.languages_required.append(
                LanguageRequirement(
                    language_code=lang_code,
                    language_name=lang_name,
                    min_listening_level=min_level,
                    min_reading_level=min_level
                )
            )

    # Add experience requirements
    if combat_required or min_deployments > 0:
        req.experience_required.append(
            ExperienceRequirement(
                requirement_type="combat" if combat_required else "deployment",
                description=f"{'Combat' if combat_required else 'Deployment'} experience required",
                combat_required=combat_required,
                min_deployments=min_deployments
            )
        )

    return req


def merge_requirements_with_billet_df(
    billets_df,
    requirements: Dict[int, BilletRequirements]
) -> None:
    """
    Merge BilletRequirements into billets DataFrame (in-place).

    Args:
        billets_df: DataFrame with billet data
        requirements: Dictionary mapping billet_id to BilletRequirements
    """
    # Add requirement columns if they don't exist
    req_columns = [
        'min_education_level', 'languages_required_json', 'asi_codes_required_json',
        'badges_required_json', 'experience_required_json', 'min_acft_score',
        'min_dwell_months', 'criticality'
    ]

    for col in req_columns:
        if col not in billets_df.columns:
            billets_df[col] = None

    # Merge requirements into DataFrame
    for billet_id, req in requirements.items():
        mask = billets_df['billet_id'] == billet_id
        if mask.any():
            req_dict = req.to_dict()
            for col in req_columns:
                if col in req_dict:
                    billets_df.loc[mask, col] = req_dict[col]

# ===== SECTION 5: Qualification Filter (qualification_filter.py) =====

"""
qualification_filter.py
-----------------------

Advanced filtering and search for soldiers based on qualifications.

Provides powerful filtering capabilities for the dashboard:
- Multi-criteria filtering (AND/OR logic)
- Range-based filtering (TIS, ACFT scores, etc.)
- Set-based filtering (badges, ASIs, languages)
- Text search across qualification data
- Saved filter presets
- Filter combination and composition

Used by dashboard for soldier selection and billet matching analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import date

from qualifications import (
    has_language, has_asi, has_sqi, has_badge, has_award,
    has_combat_experience, has_theater_experience,
    get_deployment_count, has_minimum_education,
    has_combat_badge, has_any_language,
    parse_json_field
)


@dataclass
class FilterCriterion:
    """
    A single filter criterion.

    Can be a simple comparison (e.g., ACFT >= 500) or a complex check
    (e.g., has language proficiency in Arabic at level 3).
    """
    field_name: str
    operator: str  # 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'in', 'contains', 'has', 'range'
    value: Any
    description: str = ""

    def __post_init__(self):
        if not self.description:
            self.description = f"{self.field_name} {self.operator} {self.value}"


@dataclass
class FilterGroup:
    """
    A group of filter criteria with AND/OR logic.

    Example:
        (ACFT >= 500 AND Airborne = True) OR (Ranger = True)
    """
    criteria: List[FilterCriterion] = field(default_factory=list)
    logic: str = "AND"  # 'AND' or 'OR'
    name: str = ""
    description: str = ""


class QualificationFilter:
    """
    Advanced filtering system for soldier qualifications.

    Provides flexible, composable filters for finding soldiers that meet
    specific qualification requirements.
    """

    def __init__(self, soldiers_df: pd.DataFrame):
        """
        Initialize filter with soldiers DataFrame.

        Args:
            soldiers_df: DataFrame with soldier data (including extended profiles)
        """
        self.soldiers = soldiers_df
        self.filter_groups: List[FilterGroup] = []
        self.preset_filters = self._initialize_presets()

    def _initialize_presets(self) -> Dict[str, FilterGroup]:
        """Initialize common preset filters."""
        presets = {}

        # Airborne qualified
        presets["airborne_qualified"] = FilterGroup(
            criteria=[FilterCriterion("airborne", "eq", 1)],
            name="Airborne Qualified",
            description="Soldiers with Airborne qualification"
        )

        # Ranger qualified
        presets["ranger_qualified"] = FilterGroup(
            criteria=[
                FilterCriterion("ranger", "eq", 1),
                FilterCriterion("airborne", "eq", 1)
            ],
            logic="AND",
            name="Ranger Qualified",
            description="Soldiers with Ranger Tab and Airborne"
        )

        # Combat veterans
        presets["combat_veteran"] = FilterGroup(
            criteria=[FilterCriterion("_has_combat_experience", "eq", True)],
            name="Combat Veteran",
            description="Soldiers with combat deployment experience"
        )

        # High fitness
        presets["high_fitness"] = FilterGroup(
            criteria=[
                FilterCriterion("acft_score", "gte", 500),
                FilterCriterion("body_composition_pass", "eq", 1)
            ],
            logic="AND",
            name="High Fitness",
            description="ACFT 500+ and passing body comp"
        )

        # NCO leadership
        presets["nco_leadership"] = FilterGroup(
            criteria=[
                FilterCriterion("paygrade", "in", ["E-5", "E-6", "E-7", "E-8"]),
                FilterCriterion("leadership_level", "gte", 2)
            ],
            logic="AND",
            name="NCO Leadership",
            description="NCOs with leadership experience"
        )

        # Language qualified
        presets["language_qualified"] = FilterGroup(
            criteria=[FilterCriterion("_has_any_language", "eq", True)],
            name="Language Qualified",
            description="Soldiers with foreign language proficiency"
        )

        # Fully deployable
        presets["fully_deployable"] = FilterGroup(
            criteria=[
                FilterCriterion("deployable", "eq", 1),
                FilterCriterion("med_cat", "lte", 2),
                FilterCriterion("dental_cat", "lte", 2),
                FilterCriterion("dwell_months", "gte", 12)
            ],
            logic="AND",
            name="Fully Deployable",
            description="Deployable with good medical/dental and sufficient dwell"
        )

        # Senior NCO
        presets["senior_nco"] = FilterGroup(
            criteria=[
                FilterCriterion("paygrade", "in", ["E-7", "E-8", "E-9"]),
                FilterCriterion("pme", "in", ["SLC", "USASMA"])
            ],
            logic="AND",
            name="Senior NCO",
            description="E-7 and above with PME"
        )

        # Special operations background
        presets["special_operations"] = FilterGroup(
            criteria=[
                FilterCriterion("ranger", "eq", 1),
            ],
            logic="OR",
            name="Special Operations Background",
            description="Ranger, SF, or high-speed qualified"
        )

        return presets

    # ========================================
    # Basic Filtering Methods
    # ========================================

    def filter_by_rank(self, ranks: List[str]) -> pd.DataFrame:
        """Filter soldiers by rank(s)."""
        return self.soldiers[self.soldiers['paygrade'].isin(ranks)]

    def filter_by_mos(self, mos_list: List[str]) -> pd.DataFrame:
        """Filter soldiers by MOS(s)."""
        return self.soldiers[self.soldiers['mos'].isin(mos_list)]

    def filter_by_base(self, bases: List[str]) -> pd.DataFrame:
        """Filter soldiers by home station(s)."""
        return self.soldiers[self.soldiers['base'].isin(bases)]

    def filter_by_clearance(self, min_clearance: str = "Secret") -> pd.DataFrame:
        """Filter soldiers by minimum clearance level."""
        clear_order = {"None": 0, "Secret": 1, "TS": 2}
        min_level = clear_order.get(min_clearance, 1)

        mask = self.soldiers['clearance'].apply(
            lambda x: clear_order.get(x, 0) >= min_level
        )
        return self.soldiers[mask]

    def filter_by_education(self, min_level: str = "HS") -> pd.DataFrame:
        """Filter soldiers by minimum education level."""
        if 'education_level' not in self.soldiers.columns:
            return self.soldiers

        mask = self.soldiers.apply(
            lambda row: has_minimum_education(row, min_level), axis=1
        )
        return self.soldiers[mask]

    def filter_by_acft_score(self, min_score: int = 450) -> pd.DataFrame:
        """Filter soldiers by minimum ACFT score."""
        return self.soldiers[self.soldiers['acft_score'] >= min_score]

    def filter_by_weapons_qual(self, min_score: int = 30) -> pd.DataFrame:
        """Filter soldiers by minimum weapons qualification."""
        return self.soldiers[self.soldiers['m4_score'] >= min_score]

    def filter_by_medical_category(self, max_category: int = 2) -> pd.DataFrame:
        """Filter soldiers by maximum medical category (1=best, 4=worst)."""
        return self.soldiers[self.soldiers['med_cat'] <= max_category]

    def filter_by_dwell(self, min_months: int = 12) -> pd.DataFrame:
        """Filter soldiers by minimum dwell time."""
        return self.soldiers[self.soldiers['dwell_months'] >= min_months]

    def filter_deployable(self) -> pd.DataFrame:
        """Filter to only deployable soldiers."""
        return self.soldiers[self.soldiers['deployable'] == 1]

    # ========================================
    # Qualification-based Filtering
    # ========================================

    def filter_by_language(self, language_code: str, min_level: int = 2) -> pd.DataFrame:
        """Filter soldiers with specific language proficiency."""
        mask = self.soldiers.apply(
            lambda row: has_language(row, language_code, min_level), axis=1
        )
        return self.soldiers[mask]

    def filter_has_any_language(self, min_level: int = 2) -> pd.DataFrame:
        """Filter soldiers with any foreign language proficiency."""
        mask = self.soldiers.apply(
            lambda row: has_any_language(row, min_level), axis=1
        )
        return self.soldiers[mask]

    def filter_by_asi(self, asi_code: str) -> pd.DataFrame:
        """Filter soldiers with specific ASI."""
        mask = self.soldiers.apply(lambda row: has_asi(row, asi_code), axis=1)
        return self.soldiers[mask]

    def filter_by_sqi(self, sqi_code: str) -> pd.DataFrame:
        """Filter soldiers with specific SQI."""
        mask = self.soldiers.apply(lambda row: has_sqi(row, sqi_code), axis=1)
        return self.soldiers[mask]

    def filter_by_badge(self, badge_code: str) -> pd.DataFrame:
        """Filter soldiers with specific badge."""
        mask = self.soldiers.apply(lambda row: has_badge(row, badge_code), axis=1)
        return self.soldiers[mask]

    def filter_combat_veterans(self) -> pd.DataFrame:
        """Filter soldiers with combat deployment experience."""
        mask = self.soldiers.apply(has_combat_experience, axis=1)
        return self.soldiers[mask]

    def filter_by_deployment_count(self, min_count: int = 1, combat_only: bool = False) -> pd.DataFrame:
        """Filter soldiers by minimum deployment count."""
        mask = self.soldiers.apply(
            lambda row: get_deployment_count(row, combat_only) >= min_count, axis=1
        )
        return self.soldiers[mask]

    def filter_by_theater_experience(self, theater: str) -> pd.DataFrame:
        """Filter soldiers with experience in specific theater."""
        mask = self.soldiers.apply(
            lambda row: has_theater_experience(row, theater), axis=1
        )
        return self.soldiers[mask]

    def filter_combat_badge_holders(self) -> pd.DataFrame:
        """Filter soldiers with combat badge (CIB, CAB, CMB)."""
        mask = self.soldiers.apply(has_combat_badge, axis=1)
        return self.soldiers[mask]

    # ========================================
    # Range-based Filtering
    # ========================================

    def filter_by_tis_range(self, min_months: int = 0, max_months: int = 999) -> pd.DataFrame:
        """Filter soldiers by time in service range."""
        if 'time_in_service_months' not in self.soldiers.columns:
            return self.soldiers

        return self.soldiers[
            (self.soldiers['time_in_service_months'] >= min_months) &
            (self.soldiers['time_in_service_months'] <= max_months)
        ]

    def filter_by_tig_range(self, min_months: int = 0, max_months: int = 999) -> pd.DataFrame:
        """Filter soldiers by time in grade range."""
        if 'time_in_grade_months' not in self.soldiers.columns:
            return self.soldiers

        return self.soldiers[
            (self.soldiers['time_in_grade_months'] >= min_months) &
            (self.soldiers['time_in_grade_months'] <= max_months)
        ]

    def filter_by_acft_range(self, min_score: int = 360, max_score: int = 600) -> pd.DataFrame:
        """Filter soldiers by ACFT score range."""
        return self.soldiers[
            (self.soldiers['acft_score'] >= min_score) &
            (self.soldiers['acft_score'] <= max_score)
        ]

    # ========================================
    # Advanced Filtering (Criterion-based)
    # ========================================

    def apply_criterion(self, criterion: FilterCriterion) -> pd.DataFrame:
        """Apply a single filter criterion."""
        field = criterion.field_name
        op = criterion.operator
        value = criterion.value

        # Handle special computed fields
        if field == "_has_combat_experience":
            mask = self.soldiers.apply(has_combat_experience, axis=1)
            return self.soldiers[mask] if value else self.soldiers[~mask]

        if field == "_has_any_language":
            mask = self.soldiers.apply(lambda row: has_any_language(row, 2), axis=1)
            return self.soldiers[mask] if value else self.soldiers[~mask]

        if field == "_has_combat_badge":
            mask = self.soldiers.apply(has_combat_badge, axis=1)
            return self.soldiers[mask] if value else self.soldiers[~mask]

        # Handle regular fields
        if field not in self.soldiers.columns:
            return self.soldiers  # Field doesn't exist, return all

        # Apply operator
        if op == "eq":
            return self.soldiers[self.soldiers[field] == value]
        elif op == "neq":
            return self.soldiers[self.soldiers[field] != value]
        elif op == "gt":
            return self.soldiers[self.soldiers[field] > value]
        elif op == "gte":
            return self.soldiers[self.soldiers[field] >= value]
        elif op == "lt":
            return self.soldiers[self.soldiers[field] < value]
        elif op == "lte":
            return self.soldiers[self.soldiers[field] <= value]
        elif op == "in":
            return self.soldiers[self.soldiers[field].isin(value)]
        elif op == "contains":
            mask = self.soldiers[field].astype(str).str.contains(str(value), case=False, na=False)
            return self.soldiers[mask]
        elif op == "range":
            min_val, max_val = value
            return self.soldiers[(self.soldiers[field] >= min_val) & (self.soldiers[field] <= max_val)]
        else:
            return self.soldiers

    def apply_filter_group(self, group: FilterGroup) -> pd.DataFrame:
        """Apply a filter group (multiple criteria with AND/OR logic)."""
        if not group.criteria:
            return self.soldiers

        if group.logic == "AND":
            # Start with all soldiers, then progressively filter
            result_indices = set(self.soldiers.index)

            for criterion in group.criteria:
                # Temporarily create a new filter with current result
                temp_filter = QualificationFilter(self.soldiers[self.soldiers.index.isin(result_indices)])
                filtered = temp_filter.apply_criterion(criterion)
                # Intersect with current results
                result_indices = result_indices.intersection(set(filtered.index))

            return self.soldiers[self.soldiers.index.isin(result_indices)]

        else:  # OR logic
            indices = set()
            for criterion in group.criteria:
                filtered = self.apply_criterion(criterion)
                indices.update(filtered.index)

            return self.soldiers[self.soldiers.index.isin(indices)]

    def apply_preset(self, preset_name: str) -> pd.DataFrame:
        """Apply a preset filter by name."""
        if preset_name not in self.preset_filters:
            return self.soldiers

        return self.apply_filter_group(self.preset_filters[preset_name])

    # ========================================
    # Complex Filtering (Multiple Groups)
    # ========================================

    def filter_with_multiple_groups(
        self,
        groups: List[FilterGroup],
        group_logic: str = "AND"
    ) -> pd.DataFrame:
        """
        Apply multiple filter groups with AND/OR logic between groups.

        Args:
            groups: List of FilterGroup objects
            group_logic: 'AND' or 'OR' - how to combine groups

        Returns:
            Filtered DataFrame
        """
        if not groups:
            return self.soldiers

        if group_logic == "AND":
            result = self.soldiers.copy()
            for group in groups:
                filtered = self.apply_filter_group(group)
                result = result[result.index.isin(filtered.index)]
            return result

        else:  # OR logic
            indices = set()
            for group in groups:
                filtered = self.apply_filter_group(group)
                indices.update(filtered.index)

            return self.soldiers[self.soldiers.index.isin(indices)]

    # ========================================
    # Search Functions
    # ========================================

    def search_by_soldier_id(self, soldier_id: int) -> pd.DataFrame:
        """Search for specific soldier by ID."""
        return self.soldiers[self.soldiers['soldier_id'] == soldier_id]

    def search_by_name_pattern(self, pattern: str) -> pd.DataFrame:
        """
        Search for soldiers by name pattern (if name field exists).

        Case-insensitive partial match.
        """
        if 'name' in self.soldiers.columns:
            mask = self.soldiers['name'].str.contains(pattern, case=False, na=False)
            return self.soldiers[mask]
        return pd.DataFrame()  # Empty if no name field

    def search_qualification_text(self, search_term: str) -> pd.DataFrame:
        """
        Search across all JSON qualification fields for text match.

        Searches in languages, ASIs, SQIs, badges, awards, licenses.
        """
        indices = set()

        json_fields = ['languages_json', 'asi_codes_json', 'sqi_codes_json',
                      'badges_json', 'awards_json', 'licenses_json']

        for field in json_fields:
            if field in self.soldiers.columns:
                for idx, value in self.soldiers[field].items():
                    if value and not pd.isna(value):
                        if search_term.lower() in str(value).lower():
                            indices.add(idx)

        return self.soldiers[self.soldiers.index.isin(indices)]

    # ========================================
    # Statistics and Analysis
    # ========================================

    def get_filter_statistics(self, filtered_df: pd.DataFrame) -> Dict[str, Any]:
        """Get statistics about filtered results."""
        total = len(self.soldiers)
        filtered = len(filtered_df)

        stats = {
            'total_soldiers': total,
            'filtered_count': filtered,
            'filter_rate': filtered / total if total > 0 else 0,
            'ranks': filtered_df['paygrade'].value_counts().to_dict() if filtered > 0 else {},
            'mos': filtered_df['mos'].value_counts().to_dict() if filtered > 0 else {},
            'bases': filtered_df['base'].value_counts().to_dict() if filtered > 0 else {},
        }

        if filtered > 0:
            stats['avg_acft'] = filtered_df['acft_score'].mean()
            stats['avg_dwell'] = filtered_df['dwell_months'].mean()
            stats['deployable_pct'] = (filtered_df['deployable'] == 1).sum() / filtered

        return stats

    def list_available_presets(self) -> List[str]:
        """List all available preset filter names."""
        return list(self.preset_filters.keys())

    def get_preset_description(self, preset_name: str) -> str:
        """Get description of a preset filter."""
        if preset_name in self.preset_filters:
            return self.preset_filters[preset_name].description
        return ""


# ============================================================================
# Helper Functions for Building Filters
# ============================================================================

def build_ranger_filter() -> FilterGroup:
    """Build filter for Ranger-qualified soldiers."""
    return FilterGroup(
        criteria=[
            FilterCriterion("ranger", "eq", 1),
            FilterCriterion("airborne", "eq", 1),
            FilterCriterion("_has_combat_experience", "eq", True)
        ],
        logic="AND",
        name="Ranger-Qualified Combat Veteran",
        description="Rangers with Airborne and combat experience"
    )


def build_language_filter(language_code: str, min_level: int = 2) -> FilterGroup:
    """Build filter for specific language proficiency."""
    return FilterGroup(
        criteria=[FilterCriterion(f"_has_language_{language_code}", "eq", True)],
        name=f"{language_code} Language Proficiency",
        description=f"Soldiers with {language_code} at level {min_level}+"
    )


def build_high_performer_filter() -> FilterGroup:
    """Build filter for high-performing soldiers."""
    return FilterGroup(
        criteria=[
            FilterCriterion("acft_score", "gte", 540),
            FilterCriterion("m4_score", "gte", 36),
            FilterCriterion("body_composition_pass", "eq", 1),
            FilterCriterion("med_cat", "eq", 1)
        ],
        logic="AND",
        name="High Performer",
        description="Top fitness and medical readiness"
    )


def build_ready_to_deploy_filter() -> FilterGroup:
    """Build filter for soldiers ready to deploy immediately."""
    return FilterGroup(
        criteria=[
            FilterCriterion("deployable", "eq", 1),
            FilterCriterion("med_cat", "lte", 2),
            FilterCriterion("dental_cat", "lte", 2),
            FilterCriterion("dwell_months", "gte", 12),
            FilterCriterion("available_from", "lte", date.today())
        ],
        logic="AND",
        name="Ready to Deploy",
        description="Deployable with good medical/dental, sufficient dwell, and available now"
    )
