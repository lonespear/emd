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

from __future__ import annotations
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
