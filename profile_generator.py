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

from soldier_profile_extended import (
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
