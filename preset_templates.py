"""
preset_templates.py
-------------------

Preset scenario templates for quick-start and common use cases.
Each template defines a complete manning scenario with force composition,
requirements, and optimization parameters.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from datetime import date, timedelta


@dataclass
class ScenarioTemplate:
    """A complete scenario template."""
    name: str
    description: str
    location: str
    duration_days: int
    force_size: int
    division_type: str
    capabilities: List[Dict]
    optimization_weights: Dict[str, float]
    readiness_profile_name: str


# ============================================================================
# TEMPLATE DEFINITIONS
# ============================================================================

NTC_ROTATION = ScenarioTemplate(
    name="NTC Rotation",
    description="Typical National Training Center rotation at Fort Irwin, CA. Infantry-focused brigade combat team for 30-day training rotation.",
    location="Fort Irwin",
    duration_days=30,
    force_size=1500,
    division_type="infantry",
    capabilities=[
        {
            "name": "Rifle Squad",
            "mos": "11B",
            "rank": "E-6",
            "quantity": 12,
            "team_size": 9,
            "priority": 1  # Critical
        },
        {
            "name": "Weapons Squad",
            "mos": "11B",
            "rank": "E-6",
            "quantity": 6,
            "team_size": 9,
            "priority": 1
        },
        {
            "name": "Combat Medic",
            "mos": "68W",
            "rank": "E-5",
            "quantity": 15,
            "team_size": 1,
            "priority": 1
        },
        {
            "name": "Mortar Section",
            "mos": "11C",
            "rank": "E-6",
            "quantity": 4,
            "team_size": 6,
            "priority": 2  # High
        },
        {
            "name": "Scout Team",
            "mos": "19D",
            "rank": "E-6",
            "quantity": 6,
            "team_size": 4,
            "priority": 2
        },
        {
            "name": "Fire Support Team",
            "mos": "13F",
            "rank": "E-5",
            "quantity": 8,
            "team_size": 3,
            "priority": 2
        },
        {
            "name": "Supply Specialist",
            "mos": "92Y",
            "rank": "E-5",
            "quantity": 10,
            "team_size": 2,
            "priority": 3  # Normal
        }
    ],
    optimization_weights={
        "fill": 7.0,  # High priority on filling all positions
        "cost": 4.0,  # Moderate cost concern
        "cohesion": 6.0,  # Important to keep teams together for training
        "cross_lev": 3.0  # Some concern about unit disruption
    },
    readiness_profile_name="ntc_rotation"
)


JRTC_EXERCISE = ScenarioTemplate(
    name="JRTC Exercise",
    description="Joint Readiness Training Center exercise at Fort Polk, LA. Combined arms training for 21 days.",
    location="Fort Polk",
    duration_days=21,
    force_size=1200,
    division_type="mixed",
    capabilities=[
        {
            "name": "Infantry Squad",
            "mos": "11B",
            "rank": "E-6",
            "quantity": 10,
            "team_size": 9,
            "priority": 1
        },
        {
            "name": "Tank Crew",
            "mos": "19K",
            "rank": "E-6",
            "quantity": 8,
            "team_size": 4,
            "priority": 1
        },
        {
            "name": "Bradley Crew",
            "mos": "19K",
            "rank": "E-6",
            "quantity": 10,
            "team_size": 3,
            "priority": 1
        },
        {
            "name": "Combat Engineer",
            "mos": "12B",
            "rank": "E-5",
            "quantity": 6,
            "team_size": 4,
            "priority": 2
        },
        {
            "name": "Medic Team",
            "mos": "68W",
            "rank": "E-5",
            "quantity": 12,
            "team_size": 2,
            "priority": 1
        },
        {
            "name": "Signal Support",
            "mos": "25U",
            "rank": "E-5",
            "quantity": 8,
            "team_size": 2,
            "priority": 2
        },
        {
            "name": "Logistics Coordination",
            "mos": "92Y",
            "rank": "E-5",
            "quantity": 5,
            "team_size": 3,
            "priority": 3
        }
    ],
    optimization_weights={
        "fill": 8.0,  # Very high - need all positions for joint training
        "cost": 3.0,  # Lower priority, training focus
        "cohesion": 7.0,  # Very important for combined arms coordination
        "cross_lev": 2.0  # Less concern, training environment
    },
    readiness_profile_name="jrtc_exercise"
)


EUCOM_DEPLOYMENT = ScenarioTemplate(
    name="EUCOM Deployment",
    description="European Command deployment to Germany. 180-day rotational force for deterrence operations.",
    location="Germany",
    duration_days=180,
    force_size=2000,
    division_type="armor",
    capabilities=[
        {
            "name": "Tank Platoon",
            "mos": "19K",
            "rank": "E-7",
            "quantity": 6,
            "team_size": 16,
            "priority": 1
        },
        {
            "name": "Mechanized Infantry Squad",
            "mos": "11B",
            "rank": "E-6",
            "quantity": 15,
            "team_size": 9,
            "priority": 1
        },
        {
            "name": "Air Defense Team",
            "mos": "14S",
            "rank": "E-6",
            "quantity": 8,
            "team_size": 4,
            "priority": 1
        },
        {
            "name": "Military Police",
            "mos": "31B",
            "rank": "E-5",
            "quantity": 10,
            "team_size": 2,
            "priority": 2
        },
        {
            "name": "Intelligence Analyst",
            "mos": "35F",
            "rank": "E-5",
            "quantity": 12,
            "team_size": 1,
            "priority": 1
        },
        {
            "name": "Maintenance Team",
            "mos": "91B",
            "rank": "E-6",
            "quantity": 15,
            "team_size": 4,
            "priority": 2
        },
        {
            "name": "Cyber Operations",
            "mos": "17C",
            "rank": "E-5",
            "quantity": 6,
            "team_size": 2,
            "priority": 2
        },
        {
            "name": "Medical Support",
            "mos": "68W",
            "rank": "E-5",
            "quantity": 20,
            "team_size": 2,
            "priority": 1
        }
    ],
    optimization_weights={
        "fill": 9.0,  # Critical - operational deployment
        "cost": 6.0,  # Significant travel costs to Europe
        "cohesion": 8.0,  # Very important for extended deployment
        "cross_lev": 5.0  # Moderate concern for unit readiness
    },
    readiness_profile_name="eucom_deployment"
)


INDOPACOM_DEPLOYMENT = ScenarioTemplate(
    name="INDOPACOM Deployment",
    description="Indo-Pacific Command deployment to Guam. Expeditionary force for 180-day Pacific deterrence mission.",
    location="Guam",
    duration_days=180,
    force_size=1800,
    division_type="airborne",
    capabilities=[
        {
            "name": "Airborne Infantry Squad",
            "mos": "11B",
            "rank": "E-6",
            "quantity": 18,
            "team_size": 9,
            "priority": 1
        },
        {
            "name": "Pathfinder Team",
            "mos": "11B",
            "rank": "E-7",
            "quantity": 4,
            "team_size": 6,
            "priority": 1
        },
        {
            "name": "Airborne Medic",
            "mos": "68W",
            "rank": "E-5",
            "quantity": 15,
            "team_size": 2,
            "priority": 1
        },
        {
            "name": "Air Traffic Control",
            "mos": "15Q",
            "rank": "E-6",
            "quantity": 5,
            "team_size": 3,
            "priority": 2
        },
        {
            "name": "Jumpmaster Team",
            "mos": "11B",
            "rank": "E-7",
            "quantity": 8,
            "team_size": 1,
            "priority": 1
        },
        {
            "name": "Signal Intelligence",
            "mos": "35N",
            "rank": "E-5",
            "quantity": 10,
            "team_size": 2,
            "priority": 2
        },
        {
            "name": "Quartermaster",
            "mos": "92Y",
            "rank": "E-5",
            "quantity": 12,
            "team_size": 2,
            "priority": 2
        },
        {
            "name": "Aviation Mechanic",
            "mos": "15T",
            "rank": "E-6",
            "quantity": 10,
            "team_size": 3,
            "priority": 2
        }
    ],
    optimization_weights={
        "fill": 9.0,  # Critical - expeditionary mission
        "cost": 8.0,  # Very high - Pacific travel costs
        "cohesion": 9.0,  # Critical for airborne operations
        "cross_lev": 6.0  # Higher concern for specialized units
    },
    readiness_profile_name="indopacom_deployment"
)


# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

TEMPLATES = {
    "ntc": NTC_ROTATION,
    "jrtc": JRTC_EXERCISE,
    "eucom": EUCOM_DEPLOYMENT,
    "indopacom": INDOPACOM_DEPLOYMENT
}


def get_template(template_key: str) -> ScenarioTemplate:
    """Get a template by key."""
    return TEMPLATES.get(template_key)


def get_all_templates() -> Dict[str, ScenarioTemplate]:
    """Get all available templates."""
    return TEMPLATES


def get_template_names() -> List[str]:
    """Get list of template display names."""
    return [t.name for t in TEMPLATES.values()]
