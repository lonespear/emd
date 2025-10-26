"""
scenarios.py
------------

Pre-built scenario vignettes demonstrating EMD Dashboard utility.
Each scenario includes CONOP, requirements, and optimization parameters.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from datetime import date, timedelta


@dataclass
class ScenarioVignette:
    """A complete scenario vignette with CONOP and requirements."""
    id: str
    name: str
    category: str  # CTC, Deployment, Force Gen, Joint, Specialized
    duration_days: int
    location: str

    # CONOP elements
    situation: str
    mission: str
    execution: str
    required_capabilities_summary: str

    # Force requirements
    force_size: int
    capabilities: List[Dict]

    # Optimization parameters
    optimization_weights: Dict[str, float]

    # Success criteria
    target_fill_rate: float
    max_cost: int
    priority_focus: str


# ============================================================================
# COMBAT TRAINING CENTER SCENARIOS
# ============================================================================

NTC_BRIGADE_ROTATION = ScenarioVignette(
    id="ntc_brigade",
    name="NTC Brigade Rotation",
    category="Combat Training Center",
    duration_days=30,
    location="Fort Irwin",

    situation="""2-7 Infantry Brigade Combat Team is scheduled for NTC Rotation 25-06
    in 45 days. Current brigade strength is 82% following 12-month CENTCOM deployment.
    Need to field a task force of 3,500 soldiers for force-on-force operations against
    the OPFOR. Priority: maximize training value with intact squads/platoons.""",

    mission="""Build 3,500-soldier task force from available 2-7 IBCT and augment
    from sister brigades to conduct 30-day NTC rotation focused on combined arms
    maneuver, sustainment operations, and decisive action training.""",

    execution="""Main Effort: 3x Infantry Battalions (maneuver elements). Supporting
    Effort: 1x Field Artillery Battalion (indirect fire), 1x Engineer Company (mobility/
    counter-mobility). Sustainment: Brigade Support Battalion provides medical, supply,
    maintenance support throughout rotation.""",

    required_capabilities_summary="""Infantry squads (E-6 leaders + E-4/E-3), armor
    crews (19K), medics (68W), artillery crews (13B), engineers (12B), signal support
    (25U), logistics specialists (92Y, 92F).""",

    force_size=3500,
    capabilities=[
        {"name": "Infantry Squad Leader", "mos": "11B", "rank": "E-6", "quantity": 45, "team_size": 1, "priority": 1},
        {"name": "Rifleman", "mos": "11B", "rank": "E-4", "quantity": 200, "team_size": 2, "priority": 1},
        {"name": "Tank Commander", "mos": "19K", "rank": "E-7", "quantity": 12, "team_size": 1, "priority": 1},
        {"name": "Tank Crew", "mos": "19K", "rank": "E-4", "quantity": 36, "team_size": 1, "priority": 1},
        {"name": "Combat Medic", "mos": "68W", "rank": "E-5", "quantity": 40, "team_size": 1, "priority": 1},
        {"name": "Artillery Section Chief", "mos": "13B", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 2},
        {"name": "Cannon Crewmember", "mos": "13B", "rank": "E-4", "quantity": 40, "team_size": 1, "priority": 2},
        {"name": "Combat Engineer", "mos": "12B", "rank": "E-5", "quantity": 30, "team_size": 2, "priority": 2},
        {"name": "Signal Support", "mos": "25U", "rank": "E-5", "quantity": 25, "team_size": 2, "priority": 2},
        {"name": "Supply Specialist", "mos": "92Y", "rank": "E-5", "quantity": 20, "team_size": 2, "priority": 3},
    ],

    optimization_weights={
        "fill": 8.0,  # High - need all positions for realistic training
        "cost": 3.0,  # Lower - training value more important than travel costs
        "cohesion": 9.0,  # Critical - intact teams essential for collective training
        "cross_lev": 4.0  # Moderate concern about unit disruption
    },

    target_fill_rate=0.95,
    max_cost=250000,
    priority_focus="Unit cohesion - keep squads/platoons intact"
)


JRTC_SHORT_NOTICE = ScenarioVignette(
    id="jrtc_short_notice",
    name="Short-Notice JRTC Fill",
    category="Combat Training Center",
    duration_days=21,
    location="Fort Polk",

    situation="""4-25 IBCT canceled their JRTC rotation due to emergency CENTCOM tasking.
    Division has 45 days to field a battalion-sized element (800 soldiers) to fill the
    training slot. Must source from non-deploying units across division. Time-critical.""",

    mission="""Build composite battalion task force of 800 soldiers in 45 days to execute
    21-day JRTC rotation, focusing on light infantry operations in complex terrain and
    urban environments.""",

    execution="""Task organize 3 light infantry companies (C 1-501, B 2-501, A 3-501),
    augment with field artillery battery, engineer platoon, and forward support company.
    Conduct 10-day train-up prior to JRTC deployment.""",

    required_capabilities_summary="""Light infantry (11B), mortarmen (11C), scouts (19D),
    medics (68W), field artillery (13F), engineers (12B), signal (25U), logistics (92Y).""",

    force_size=800,
    capabilities=[
        {"name": "Infantry Squad Leader", "mos": "11B", "rank": "E-6", "quantity": 18, "team_size": 1, "priority": 1},
        {"name": "Rifleman", "mos": "11B", "rank": "E-3", "quantity": 90, "team_size": 2, "priority": 1},
        {"name": "Mortar Section Leader", "mos": "11C", "rank": "E-6", "quantity": 4, "team_size": 1, "priority": 1},
        {"name": "Mortarman", "mos": "11C", "rank": "E-4", "quantity": 20, "team_size": 1, "priority": 1},
        {"name": "Scout Team Leader", "mos": "19D", "rank": "E-6", "quantity": 6, "team_size": 1, "priority": 2},
        {"name": "Cavalry Scout", "mos": "19D", "rank": "E-4", "quantity": 18, "team_size": 1, "priority": 2},
        {"name": "Combat Medic", "mos": "68W", "rank": "E-5", "quantity": 16, "team_size": 1, "priority": 1},
        {"name": "Fire Support Specialist", "mos": "13F", "rank": "E-5", "quantity": 8, "team_size": 1, "priority": 2},
        {"name": "Combat Engineer", "mos": "12B", "rank": "E-5", "quantity": 12, "team_size": 2, "priority": 2},
        {"name": "Signal Support", "mos": "25U", "rank": "E-5", "quantity": 10, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 9.0,  # Critical - slot must be filled
        "cost": 5.0,  # Moderate - short notice means higher costs acceptable
        "cohesion": 7.0,  # Important but time-constrained
        "cross_lev": 2.0  # Low priority given time constraint
    },

    target_fill_rate=0.98,
    max_cost=180000,
    priority_focus="Speed - fill positions rapidly with qualified personnel"
)


# ============================================================================
# OPERATIONAL DEPLOYMENT SCENARIOS
# ============================================================================

EUCOM_POLAND = ScenarioVignette(
    id="eucom_poland",
    name="EUCOM Poland Rotation",
    category="Operational Deployment",
    duration_days=270,
    location="Poland",

    situation="""EUCOM requests armored company team for 9-month Enhanced Forward Presence
    rotation in Poland. Mission supports NATO deterrence operations. Must source from
    CONUS ABCTs with certified tank crews and support elements. High-visibility mission.""",

    mission="""Deploy company team of 180 soldiers to Poznan, Poland for 9-month EFP
    rotation conducting combined training with Polish Land Forces and maintaining
    credible combat power as part of NATO's eastern flank deterrence.""",

    execution="""Main Effort: Armored company (14x M1A2 Abrams tanks). Supporting Effort:
    Mechanized infantry platoon (4x Bradley), engineer squad, forward support team. Coordinate
    with 173rd Airborne as higher HQ. Emphasis on interoperability and readiness.""",

    required_capabilities_summary="""Tank commanders/crew (19K), Bradley crew (11B/19K),
    mechanics (91A, 91M), supply (92Y), medics (68W). All must meet OCONUS deployment criteria.""",

    force_size=180,
    capabilities=[
        {"name": "Tank Commander", "mos": "19K", "rank": "E-7", "quantity": 14, "team_size": 1, "priority": 1},
        {"name": "Tank Gunner", "mos": "19K", "rank": "E-5", "quantity": 14, "team_size": 1, "priority": 1},
        {"name": "Tank Driver/Loader", "mos": "19K", "rank": "E-4", "quantity": 28, "team_size": 1, "priority": 1},
        {"name": "Bradley Commander", "mos": "11B", "rank": "E-6", "quantity": 4, "team_size": 1, "priority": 1},
        {"name": "Bradley Gunner", "mos": "19K", "rank": "E-5", "quantity": 4, "team_size": 1, "priority": 1},
        {"name": "Bradley Infantry", "mos": "11B", "rank": "E-4", "quantity": 24, "team_size": 1, "priority": 1},
        {"name": "Tank Mechanic", "mos": "91A", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 1},
        {"name": "Combat Medic", "mos": "68W", "rank": "E-5", "quantity": 6, "team_size": 1, "priority": 1},
        {"name": "Supply Specialist", "mos": "92Y", "rank": "E-5", "quantity": 4, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 10.0,  # Maximum - cannot deploy with gaps
        "cost": 7.0,  # High - OCONUS travel expensive
        "cohesion": 10.0,  # Maximum - tank crews must train together
        "cross_lev": 6.0  # Significant concern for unit readiness back home
    },

    target_fill_rate=1.0,
    max_cost=400000,
    priority_focus="Crew integrity - tank/Bradley crews must be certified together"
)


INDOPACOM_GUAM = ScenarioVignette(
    id="indopacom_guam",
    name="INDOPACOM Crisis Response",
    category="Operational Deployment",
    duration_days=180,
    location="Guam",

    situation="""INDOPACOM requires rapid deployment of airborne company to Guam within
    72 hours for exercise turned real-world contingency. 180 soldiers needed. All must be
    airborne-qualified with current jump status. Pacific theater experience preferred.""",

    mission="""Deploy airborne rifle company of 180 soldiers to Andersen AFB, Guam within
    72 hours to support Pacific Air Forces and conduct security operations in support of
    INDOPACOM OPLAN 5077.""",

    execution="""Rapid alert sequence: 6hr - personnel recall, 24hr - equipment prep,
    48hr - manifest/load, 72hr - wheels up. Main Effort: 3x rifle platoons. Supporting:
    weapons platoon, HQ element. Conduct in-flight rigging for potential JFEO.""",

    required_capabilities_summary="""Airborne infantry (11B), jumpmaster (additional skill),
    medics (68W), signal (25U), supply (92Y). All must have current jump status and be
    medically deployable.""",

    force_size=180,
    capabilities=[
        {"name": "Infantry Squad Leader", "mos": "11B", "rank": "E-6", "quantity": 9, "team_size": 1, "priority": 1},
        {"name": "Airborne Rifleman", "mos": "11B", "rank": "E-4", "quantity": 54, "team_size": 2, "priority": 1},
        {"name": "Jumpmaster", "mos": "11B", "rank": "E-7", "quantity": 6, "team_size": 1, "priority": 1},
        {"name": "Weapons Squad Leader", "mos": "11B", "rank": "E-6", "quantity": 4, "team_size": 1, "priority": 1},
        {"name": "Machine Gunner", "mos": "11B", "rank": "E-4", "quantity": 12, "team_size": 1, "priority": 1},
        {"name": "Airborne Medic", "mos": "68W", "rank": "E-5", "quantity": 8, "team_size": 1, "priority": 1},
        {"name": "Signal Support", "mos": "25U", "rank": "E-5", "quantity": 6, "team_size": 1, "priority": 2},
        {"name": "Supply Specialist", "mos": "92Y", "rank": "E-5", "quantity": 4, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 10.0,  # Maximum - rapid deployment critical
        "cost": 9.0,  # Very high - Pacific travel very expensive
        "cohesion": 10.0,  # Maximum - airborne operations demand team integrity
        "cross_lev": 7.0  # High concern - specialized airborne skillset
    },

    target_fill_rate=1.0,
    max_cost=500000,
    priority_focus="Readiness - all personnel must be deployment-ready now"
)


# ============================================================================
# FORCE GENERATION & READINESS SCENARIOS
# ============================================================================

DIVISION_READY_BRIGADE = ScenarioVignette(
    id="drb_rotation",
    name="Division Ready Brigade",
    category="Force Generation",
    duration_days=90,
    location="JBLM",

    situation="""Division maintains one brigade on 96-hour recall for contingency operations.
    Quarterly rotation cycle. Current ready brigade at end of cycle, next brigade at 73%
    strength. Need to build to 90% within 30 days for assumption of DRB mission.""",

    mission="""Build 1-2 SBCT to 90% strength (3,200 soldiers) within 30 days and maintain
    DRB readiness posture for 90-day cycle. All soldiers must meet deployment medical/
    training requirements.""",

    execution="""Cross-level from sister brigades (2-2, 3-2), receive inbound PCS soldiers,
    integrate new arrivals from OSUT/AIT. Priority: fill infantry, armor, medical, signal.
    Conduct validation exercise at 30-day mark.""",

    required_capabilities_summary="""Full brigade slice: infantry, armor, artillery,
    engineers, signal, intelligence, medical, logistics. Emphasis on combat arms fill.""",

    force_size=3200,
    capabilities=[
        {"name": "Infantry Squad Leader", "mos": "11B", "rank": "E-6", "quantity": 48, "team_size": 1, "priority": 1},
        {"name": "Rifleman", "mos": "11B", "rank": "E-4", "quantity": 240, "team_size": 2, "priority": 1},
        {"name": "Tank Commander", "mos": "19K", "rank": "E-7", "quantity": 18, "team_size": 1, "priority": 1},
        {"name": "Tank Crew", "mos": "19K", "rank": "E-4", "quantity": 54, "team_size": 1, "priority": 1},
        {"name": "Artillery Section Chief", "mos": "13B", "rank": "E-6", "quantity": 12, "team_size": 1, "priority": 1},
        {"name": "Cannon Crewmember", "mos": "13B", "rank": "E-4", "quantity": 60, "team_size": 1, "priority": 1},
        {"name": "Combat Medic", "mos": "68W", "rank": "E-5", "quantity": 48, "team_size": 1, "priority": 1},
        {"name": "Signal Support", "mos": "25U", "rank": "E-5", "quantity": 36, "team_size": 2, "priority": 2},
        {"name": "Intelligence Analyst", "mos": "35F", "rank": "E-5", "quantity": 24, "team_size": 1, "priority": 2},
        {"name": "Supply Specialist", "mos": "92Y", "rank": "E-5", "quantity": 30, "team_size": 2, "priority": 2},
    ],

    optimization_weights={
        "fill": 9.0,  # Very high - readiness requirement
        "cost": 2.0,  # Low - garrison cross-leveling minimal cost
        "cohesion": 6.0,  # Important but balanced with fill requirement
        "cross_lev": 5.0  # Moderate - must balance across division
    },

    target_fill_rate=0.90,
    max_cost=50000,
    priority_focus="Balanced readiness - spread load fairly across division"
)


POST_DEPLOYMENT_REFIT = ScenarioVignette(
    id="post_deployment",
    name="Post-Deployment Reconstitution",
    category="Force Generation",
    duration_days=180,
    location="Fort Hood",

    situation="""1-9 Cavalry returns from 12-month Iraq deployment at 73% strength due to
    combat losses, medical evacuations, and ETS. Must rebuild to 90% in 6 months to meet
    next deployment window. Balance cross-leveling vs. waiting for new accessions.""",

    mission="""Reconstitute 1-9 Cavalry to 90% authorized strength (1,800 soldiers) within
    180 days through combination of cross-leveling, PCS arrivals, and new accessions.
    Prioritize critical combat MOSs.""",

    execution="""Phase 1 (Days 1-60): Immediate cross-level for critical shortages (19K,
    68W, 91A). Phase 2 (Days 61-120): Integrate PCS arrivals, begin new soldier training.
    Phase 3 (Days 121-180): Final fills, validate training gates, certify ready.""",

    required_capabilities_summary="""Cavalry scouts (19D), tank crews (19K), mechanics
    (91A, 91M), medics (68W), signal (25U). Priority on experienced NCOs.""",

    force_size=1800,
    capabilities=[
        {"name": "Cavalry Scout Leader", "mos": "19D", "rank": "E-6", "quantity": 24, "team_size": 1, "priority": 1},
        {"name": "Cavalry Scout", "mos": "19D", "rank": "E-4", "quantity": 96, "team_size": 1, "priority": 1},
        {"name": "Tank Commander", "mos": "19K", "rank": "E-7", "quantity": 16, "team_size": 1, "priority": 1},
        {"name": "Tank Crew", "mos": "19K", "rank": "E-4", "quantity": 48, "team_size": 1, "priority": 1},
        {"name": "Tank Mechanic", "mos": "91A", "rank": "E-6", "quantity": 20, "team_size": 1, "priority": 1},
        {"name": "Bradley Mechanic", "mos": "91M", "rank": "E-5", "quantity": 16, "team_size": 1, "priority": 1},
        {"name": "Combat Medic", "mos": "68W", "rank": "E-5", "quantity": 28, "team_size": 1, "priority": 1},
        {"name": "Signal Support", "mos": "25U", "rank": "E-5", "quantity": 20, "team_size": 1, "priority": 2},
        {"name": "Supply Specialist", "mos": "92Y", "rank": "E-5", "quantity": 16, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 8.0,  # High but not maximum - have time
        "cost": 3.0,  # Low - mostly garrison sourcing
        "cohesion": 4.0,  # Lower - building new teams anyway
        "cross_lev": 6.0  # Higher - minimize impact on donor units
    },

    target_fill_rate=0.90,
    max_cost=80000,
    priority_focus="Phased approach - critical fills now, others over time"
)


# Continued in next part due to length...
# I'll create the remaining 6 scenarios next

RIMPAC_EXERCISE = ScenarioVignette(
    id="rimpac",
    name="RIMPAC Exercise Liaison",
    category="Joint Operations",
    duration_days=45,
    location="Hawaii",

    situation="""U.S. Army contributes 120-soldier liaison and training element to
    RIMPAC 2025 (Rim of the Pacific Exercise). Will work with 26 partner nations.
    Foreign language skills (Japanese, Korean, Tagalog) and prior multinational
    experience highly desired.""",

    mission="""Deploy 120-soldier liaison element to Joint Base Pearl Harbor-Hickam
    for 45-day RIMPAC exercise to facilitate multinational training, provide subject
    matter expertise, and strengthen Pacific partnerships.""",

    execution="""Organize into 6 multinational liaison teams (MLT) of 20 soldiers each.
    Teams embed with partner nation forces. Focus areas: combined arms, humanitarian
    assistance/disaster relief, amphibious operations. Coordinate through III MEF.""",

    required_capabilities_summary="""Infantry advisors (11B), intelligence (35F),
    logistics planners (92Y), medics (68W), signal (25U). Language and cultural
    awareness critical.""",

    force_size=120,
    capabilities=[
        {"name": "Senior Advisor", "mos": "11B", "rank": "E-7", "quantity": 6, "team_size": 1, "priority": 1},
        {"name": "Infantry Advisor", "mos": "11B", "rank": "E-6", "quantity": 24, "team_size": 1, "priority": 1},
        {"name": "Intelligence Advisor", "mos": "35F", "rank": "E-6", "quantity": 12, "team_size": 1, "priority": 2},
        {"name": "Logistics Planner", "mos": "92Y", "rank": "E-6", "quantity": 12, "team_size": 1, "priority": 2},
        {"name": "Medical Advisor", "mos": "68W", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 2},
        {"name": "Signal Advisor", "mos": "25U", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 2},
        {"name": "Interpreter/Liaison", "mos": "09L", "rank": "E-5", "quantity": 12, "team_size": 1, "priority": 1},
    ],

    optimization_weights={
        "fill": 7.0,  # Important but exercise can adjust
        "cost": 8.0,  # High - Pacific travel expensive
        "cohesion": 5.0,  # Moderate - teams forming for exercise
        "cross_lev": 4.0  # Moderate - distributed sourcing acceptable
    },

    target_fill_rate=0.95,
    max_cost=300000,
    priority_focus="Experience - select soldiers with deployment/multinational background"
)


SOF_SUPPORT = ScenarioVignette(
    id="sof_support",
    name="SOF Support Package",
    category="Specialized Mission",
    duration_days=120,
    location="OCONUS",

    situation="""JSOC requests 40 conventional enablers to support 4-month special
    operations. Need mature NCOs (E-6+) with specific ASIs/SQIs. All require TS/SCI
    clearances and must meet SOF medical standards. High-OPTEMPO environment.""",

    mission="""Provide 40-soldier enabler package to support JSOC task force conducting
    counter-terrorism operations. Focus areas: medical, signal, intelligence, explosive
    ordnance disposal.""",

    execution="""Package consists of: 12x Special Operations Medics (SOF-M qualified
    preferred), 10x Signal Intelligence, 8x All-Source Intelligence, 6x EOD, 4x Civil
    Affairs. Soldiers must pass SOF screening.""",

    required_capabilities_summary="""SOF medics (68W with W1/F1), SIGINT (35N/35S),
    intelligence (35F), EOD (89D), civil affairs (38B). TS/SCI required for all.""",

    force_size=40,
    capabilities=[
        {"name": "Special Operations Medic", "mos": "68W", "rank": "E-7", "quantity": 12, "team_size": 1, "priority": 1},
        {"name": "SIGINT Analyst", "mos": "35N", "rank": "E-6", "quantity": 10, "team_size": 1, "priority": 1},
        {"name": "All-Source Intelligence", "mos": "35F", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 1},
        {"name": "EOD Technician", "mos": "89D", "rank": "E-6", "quantity": 6, "team_size": 1, "priority": 1},
        {"name": "Civil Affairs Specialist", "mos": "38B", "rank": "E-6", "quantity": 4, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 10.0,  # Maximum - JSOC requirements inflexible
        "cost": 6.0,  # High but not primary concern
        "cohesion": 3.0,  # Low - individuals augmenting SOF teams
        "cross_lev": 8.0  # High - specialized skillsets scarce
    },

    target_fill_rate=1.0,
    max_cost=200000,
    priority_focus="Qualification match - clearances and ASIs non-negotiable"
)


OPFOR_AUGMENTATION = ScenarioVignette(
    id="opfor_aug",
    name="CTE OPFOR Augmentation",
    category="Installation Support",
    duration_days=180,
    location="Fort Irwin",

    situation="""Fort Irwin OPFOR requires 200 augmentees for 6-month peak rotation
    season (summer). Must source from non-rotating units. OPFOR training preferred but
    not required. Focus on infantry, scouts, and culturally aware soldiers.""",

    mission="""Augment 11th Armored Cavalry Regiment with 200 soldiers for 6 months
    to support NTC rotations. Soldiers will role-play near-peer adversary conducting
    combined arms operations against rotating BCTs.""",

    execution="""Integration training (2 weeks), OPFOR certification (2 weeks), then
    6x 30-day rotation cycles. Augmentees integrate into OPFOR companies. Preference
    for soldiers with armor/mechanized experience and those who speak Russian/Arabic.""",

    required_capabilities_summary="""Infantry (11B), scouts (19D), armor (19K),
    with preference for deployment experience and cultural awareness. OPFOR experience
    a plus.""",

    force_size=200,
    capabilities=[
        {"name": "OPFOR Infantry Leader", "mos": "11B", "rank": "E-6", "quantity": 16, "team_size": 1, "priority": 1},
        {"name": "OPFOR Infantryman", "mos": "11B", "rank": "E-4", "quantity": 80, "team_size": 2, "priority": 1},
        {"name": "OPFOR Scout Leader", "mos": "19D", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 2},
        {"name": "OPFOR Scout", "mos": "19D", "rank": "E-4", "quantity": 32, "team_size": 1, "priority": 2},
        {"name": "OPFOR Armor Crew", "mos": "19K", "rank": "E-5", "quantity": 24, "team_size": 1, "priority": 2},
        {"name": "OPFOR Support", "mos": "92Y", "rank": "E-5", "quantity": 8, "team_size": 1, "priority": 3},
    ],

    optimization_weights={
        "fill": 7.0,  # Important but can work with less
        "cost": 4.0,  # Moderate - TDY to Irwin manageable
        "cohesion": 2.0,  # Low - OPFOR builds new teams
        "cross_lev": 3.0  # Low - distributed sourcing preferred
    },

    target_fill_rate=0.90,
    max_cost=150000,
    priority_focus="Balance - spread OPFOR duty across division fairly"
)


EMERGENCY_EDRE = ScenarioVignette(
    id="edre",
    name="Emergency Deployment Exercise",
    category="Force Generation",
    duration_days=1,
    location="Corps-wide",

    situation="""XVIII Airborne Corps conducts no-notice EDRE. All units must account
    for deployable personnel within 12 hours. Corps G1 needs immediate readiness picture
    across 4 divisions (~65,000 soldiers). Manual reports take 48+ hours.""",

    mission="""Generate by-name deployment roster for entire XVIII Airborne Corps within
    12 hours of EDRE alert. Identify all non-deployable personnel with reasons. Provide
    commander accurate readiness assessment for COCOM reporting.""",

    execution="""Real-time query of HR systems, medical databases, training records.
    Filter soldiers by deployment criteria (medical, legal, training, family). Generate
    unit-by-unit manifests. Provide rollup to Corps CDR.""",

    required_capabilities_summary="""All MOSs across corps. Focus: identifying deployment-
    ready vs. non-deployable soldiers across entire force structure in hours, not days.""",

    force_size=65000,
    capabilities=[
        # This scenario is about rapid assessment, not specific capabilities
        # Would use entire force pool and filter by readiness
    ],

    optimization_weights={
        "fill": 10.0,  # N/A for this scenario - it's about speed/accuracy
        "cost": 0.0,   # N/A - no actual movement
        "cohesion": 0.0,  # N/A
        "cross_lev": 0.0  # N/A
    },

    target_fill_rate=1.0,  # 100% accountability
    max_cost=0,
    priority_focus="Speed and accuracy - instant readiness reporting"
)


HURRICANE_DSCA = ScenarioVignette(
    id="hurricane_dsca",
    name="Hurricane DSCA Response",
    category="Specialized Mission",
    duration_days=30,
    location="Puerto Rico",

    situation="""Category 5 hurricane devastates Puerto Rico. ARNORTH requires 500-soldier
    engineer-heavy task force within 96 hours for disaster response. Focus: infrastructure
    repair, route clearance, emergency medical. Spanish speakers highly desired.""",

    mission="""Deploy 500-soldier DSCA task force to San Juan within 96 hours to conduct
    humanitarian assistance/disaster relief operations. Priority: restore critical
    infrastructure, provide emergency medical care, distribute supplies.""",

    execution="""Task organize: 2x Engineer Companies (heavy equipment), 1x Medical Company,
    1x Logistics Company, HQ element. Coordinate through FEMA Region 2. 30-day initial
    commitment with possible extension.""",

    required_capabilities_summary="""Combat engineers (12B), heavy equipment operators
    (12N), combat medics (68W), logistics specialists (92Y), civil affairs (38B). Spanish
    language critical.""",

    force_size=500,
    capabilities=[
        {"name": "Engineer Squad Leader", "mos": "12B", "rank": "E-6", "quantity": 20, "team_size": 1, "priority": 1},
        {"name": "Combat Engineer", "mos": "12B", "rank": "E-4", "quantity": 120, "team_size": 2, "priority": 1},
        {"name": "Heavy Equipment Operator", "mos": "12N", "rank": "E-5", "quantity": 40, "team_size": 1, "priority": 1},
        {"name": "Medical Team Leader", "mos": "68W", "rank": "E-6", "quantity": 8, "team_size": 1, "priority": 1},
        {"name": "Combat Medic", "mos": "68W", "rank": "E-4", "quantity": 40, "team_size": 1, "priority": 1},
        {"name": "Civil Affairs", "mos": "38B", "rank": "E-6", "quantity": 12, "team_size": 1, "priority": 2},
        {"name": "Supply Specialist", "mos": "92Y", "rank": "E-5", "quantity": 30, "team_size": 2, "priority": 1},
        {"name": "Motor Transport Operator", "mos": "88M", "rank": "E-4", "quantity": 20, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 10.0,  # Maximum - lives at stake
        "cost": 5.0,   # Moderate - emergency justifies expense
        "cohesion": 6.0,  # Important for DSCA coordination
        "cross_lev": 4.0  # Moderate - spread burden fairly
    },

    target_fill_rate=1.0,
    max_cost=250000,
    priority_focus="Humanitarian - speed and capability over cost"
)


SFAB_ADVISORS = ScenarioVignette(
    id="sfab",
    name="SFAB Advisor Augmentation",
    category="Specialized Mission",
    duration_days=270,
    location="Afghanistan",

    situation="""1st Security Force Assistance Brigade requires 30 advisors for 9-month
    train/advise/assist mission in Afghanistan. Need E-7+ with multiple deployments,
    advisor training complete, cultural awareness. Will advise Afghan National Army.""",

    mission="""Augment 1st SFAB with 30 experienced NCO advisors for 9-month rotation
    conducting security force assistance operations. Advisors will embed with Afghan
    National Army units at kandak (battalion) level.""",

    execution="""Pre-deployment: 8-week advisor course, cultural training, language
    orientation. Deployment: Embed with ANA units, advise on operations, logistics,
    training. Coordinate through CJOA-A. High-risk environment.""",

    required_capabilities_summary="""Experienced NCOs (E-7+) from combat arms (11B, 19D,
    13F), logistics (92Y), medical (68W). Prior deployment and advisor experience essential.
    Dari/Pashto speakers preferred.""",

    force_size=30,
    capabilities=[
        {"name": "Senior Infantry Advisor", "mos": "11B", "rank": "E-8", "quantity": 8, "team_size": 1, "priority": 1},
        {"name": "Infantry Advisor", "mos": "11B", "rank": "E-7", "quantity": 12, "team_size": 1, "priority": 1},
        {"name": "Cavalry Advisor", "mos": "19D", "rank": "E-7", "quantity": 4, "team_size": 1, "priority": 1},
        {"name": "Fire Support Advisor", "mos": "13F", "rank": "E-7", "quantity": 2, "team_size": 1, "priority": 2},
        {"name": "Medical Advisor", "mos": "68W", "rank": "E-7", "quantity": 2, "team_size": 1, "priority": 1},
        {"name": "Logistics Advisor", "mos": "92Y", "rank": "E-7", "quantity": 2, "team_size": 1, "priority": 2},
    ],

    optimization_weights={
        "fill": 10.0,  # Maximum - high-visibility mission
        "cost": 7.0,   # High - OCONUS combat deployment
        "cohesion": 4.0,  # Lower - individual advisors
        "cross_lev": 9.0  # Very high - senior NCOs scarce resource
    },

    target_fill_rate=1.0,
    max_cost=350000,
    priority_focus="Quality over quantity - select absolute best advisors"
)


# ============================================================================
# SCENARIO REGISTRY
# ============================================================================

ALL_SCENARIOS = {
    "ntc_brigade": NTC_BRIGADE_ROTATION,
    "jrtc_short_notice": JRTC_SHORT_NOTICE,
    "eucom_poland": EUCOM_POLAND,
    "indopacom_guam": INDOPACOM_GUAM,
    "drb_rotation": DIVISION_READY_BRIGADE,
    "post_deployment": POST_DEPLOYMENT_REFIT,
    "rimpac": RIMPAC_EXERCISE,
    "sof_support": SOF_SUPPORT,
    "opfor_aug": OPFOR_AUGMENTATION,
    "edre": EMERGENCY_EDRE,
    "hurricane_dsca": HURRICANE_DSCA,
    "sfab": SFAB_ADVISORS,
}


SCENARIOS_BY_CATEGORY = {
    "Combat Training Center": [NTC_BRIGADE_ROTATION, JRTC_SHORT_NOTICE],
    "Operational Deployment": [EUCOM_POLAND, INDOPACOM_GUAM],
    "Force Generation": [DIVISION_READY_BRIGADE, POST_DEPLOYMENT_REFIT, EMERGENCY_EDRE],
    "Joint Operations": [RIMPAC_EXERCISE],
    "Specialized Mission": [SOF_SUPPORT, HURRICANE_DSCA, SFAB_ADVISORS],
    "Installation Support": [OPFOR_AUGMENTATION],
}


def get_scenario(scenario_id: str) -> ScenarioVignette:
    """Get a scenario by ID."""
    return ALL_SCENARIOS.get(scenario_id)


def get_scenarios_by_category(category: str) -> List[ScenarioVignette]:
    """Get all scenarios in a category."""
    return SCENARIOS_BY_CATEGORY.get(category, [])


def get_all_scenario_names() -> List[str]:
    """Get list of all scenario display names."""
    return [s.name for s in ALL_SCENARIOS.values()]


def load_scenario_to_session(scenario: ScenarioVignette, session_state):
    """
    Load a scenario into Streamlit session state.

    Args:
        scenario: ScenarioVignette to load
        session_state: Streamlit session_state object
    """
    session_state.capabilities = scenario.capabilities
    session_state.workflow_data['weights'] = scenario.optimization_weights
    session_state.workflow_data['location'] = scenario.location
    session_state.workflow_data['duration_days'] = scenario.duration_days
    session_state.workflow_data['template_used'] = scenario.name
    session_state.workflow_data['scenario_id'] = scenario.id
    session_state.exercise_location = scenario.location
