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

from __future__ import annotations
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
