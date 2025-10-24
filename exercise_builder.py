"""
exercise_builder.py
--------------------

High-level scenario generator for 1st MDTF manpower allocation exercises
within the USINDOPACOM theater of operations.

Uses mission templates (Arctic Edge, Valiant Shield, Orient Shield, Talisman Sabre)
to configure bases, distances, policy biases, and tuning parameters, then runs
an EMD optimization or agentic loop (via ManningAgent) to generate assignments.

Classes:
- ExerciseBuilderConfig : dataclass holding configuration parameters
- ExerciseOutputs       : dataclass holding results and the configured EMD object
- ExerciseBuilder       : Orchestrator that builds, biases, and executes a mission

Example:
    >>> cfg = ExerciseBuilderConfig(mission_name="ValiantShield", n_soldiers=800)
    >>> builder = ExerciseBuilder(cfg)
    >>> out = builder.build()
    >>> print(out.summary)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from emd_agent import EMD, ManningAgent

# -----------------------------
# USINDOPACOM theater catalog
# -----------------------------
INDOPACOM_BASES = ["JBLM", "JBER", "Hawaii", "Guam", "Japan"]

# Rough great-circle style distances (miles) for cost; tune as needed
INDOPACOM_DIST = {
    ("JBLM", "JBER"): 2300,
    ("JBLM", "Hawaii"): 2670,
    ("JBLM", "Guam"): 5600,
    ("JBLM", "Japan"): 4760,
    ("JBER", "Hawaii"): 2780,
    ("JBER", "Guam"): 4700,
    ("JBER", "Japan"): 3300,
    ("Hawaii", "Guam"): 3900,
    ("Hawaii", "Japan"): 3850,
    ("Guam", "Japan"): 1600,
}

# Exercise templates targeted at 1st MDTF missions
EXERCISE_TEMPLATES: Dict[str, Dict] = {
    # Arctic Edge: preference for JBER, airborne slight global bias, medic preference
    "ArcticEdge": {
        "bases": ["JBER", "JBLM", "Hawaii"],   # can still include Guam/Japan if desired
        "dist": {**INDOPACOM_DIST},
        "mission_bias": {
            "base_bias": {"JBER": -200},
            "mos_priority_bonus": {"68W": -200},
            "airborne_bias": -50,
            "language_bonus": {},  # none specific
        },
        "policy_tweaks": {
            "TDY_cost_weight": 1.0,
            "deployable_false_penalty": 1e6,  # practically forbid
        },
    },

    # Valiant Shield: Guam-centric, high-skill/TS-friendly
    "ValiantShield": {
        "bases": ["Guam", "Hawaii", "Japan", "JBLM"],
        "dist": {**INDOPACOM_DIST},
        "mission_bias": {
            "base_bias": {"Guam": -180, "Hawaii": -60},
            "mos_priority_bonus": {"35F": -150, "25U": -100},
            "airborne_bias": 0,
            "language_bonus": {},  # could add Japanese later
        },
        "policy_tweaks": {
            "TDY_cost_weight": 1.2,  # TDY more expensive in the Pacific
        },
    },

    # Orient Shield (JP): Japan-centric, add mild language/TS emphasis
    "OrientShield": {
        "bases": ["Japan", "Guam", "Hawaii", "JBLM", "JBER"],
        "dist": {**INDOPACOM_DIST},
        "mission_bias": {
            "base_bias": {"Japan": -180},
            "mos_priority_bonus": {"11B": -80, "25U": -100},
            "airborne_bias": 0,
            "language_bonus": {"Arabic": 0, "French": 0, "Spanish": 0},  # neutralize non-JP
        },
        "policy_tweaks": {
            "clearance_mismatch_penalty": 2400,  # slightly stricter on clearance
        },
    },

    # Talisman Sabre: joint, wide dispersal; moderate TDY emphasis
    "TalismanSabre": {
        "bases": ["Hawaii", "Guam", "JBLM", "Japan"],
        "dist": {**INDOPACOM_DIST},
        "mission_bias": {
            "base_bias": {"Hawaii": -120, "Guam": -80},
            "mos_priority_bonus": {"68W": -100, "25U": -100, "12B": -80},
            "airborne_bias": -25,
            "language_bonus": {},
        },
        "policy_tweaks": {"TDY_cost_weight": 1.1},
    },
}

@dataclass
class ExerciseBuilderConfig:
    mission_name: str = "ArcticEdge"
    n_soldiers: int = 800
    n_billets: int = 75
    seed: int = 42
    use_agent_loop: bool = False         # if True, uses ManningAgent.analyze_and_tune
    target_fill: float = 0.95
    max_cost: float = 1e6

@dataclass
class ExerciseOutputs:
    emd: EMD
    assignments: pd.DataFrame
    summary: Dict

class ExerciseBuilder:
    """
    High-level scenario builder for 1st MDTF in USINDOPACOM.
    Generates a mission profile, configures EMD theater (bases + TDY distances),
    applies mission biases/policies, runs assignment, and returns results.
    """
    def __init__(self, cfg: ExerciseBuilderConfig):
        self.cfg = cfg
        if cfg.mission_name not in EXERCISE_TEMPLATES:
            raise ValueError(f"Unknown mission '{cfg.mission_name}'. "
                             f"Choose one of: {list(EXERCISE_TEMPLATES.keys())}")
        self.template = EXERCISE_TEMPLATES[cfg.mission_name]

    # -------------------------
    # Build + assign
    # -------------------------
    def build(self) -> ExerciseOutputs:
        """
        Build and execute a mission scenario using the configured parameters.
        Returns ExerciseOutputs(emd, assignments, summary).
        """
        print(f"\n🏗️  Building exercise: {self.cfg.mission_name}")
        print(f"   Soldiers={self.cfg.n_soldiers:,}, Billets={self.cfg.n_billets:,}, Seed={self.cfg.seed}")

        # 1️⃣ Instantiate EMD
        emd = EMD(self.cfg.n_soldiers, self.cfg.n_billets, self.cfg.seed)

        # 2️⃣ Configure theater
        bases = self.template["bases"]
        dist = self.template["dist"]
        print(f"🌐  Configuring theater: {bases}")
        emd.set_bases(bases, dist_overrides=dist, reseed=self.cfg.seed)

        # 3️⃣ Apply mission biases
        mb = self.template["mission_bias"]
        print(f"🎯  Applying mission biases for {self.cfg.mission_name}...")
        emd.add_mission_bias(
            mission_name=self.cfg.mission_name,
            base_bias=mb.get("base_bias"),
            mos_bonus=mb.get("mos_priority_bonus"),
            airborne_bias=mb.get("airborne_bias"),
            language_bonus=mb.get("language_bonus"),
        )

        # 4️⃣ Policy tuning for this mission
        tweaks = self.template.get("policy_tweaks", {})
        if tweaks:
            print(f"⚙️  Applying policy tweaks: {tweaks}")
            for k, v in tweaks.items():
                emd.tune_policy(**{k: v})
        else:
            print("⚙️  No custom policy tweaks defined.")

        # 5️⃣ Solve (agentic or static)
        if self.cfg.use_agent_loop:
            print("🤖  Running ManningAgent loop...")
            agent = ManningAgent(
                mission_name=self.cfg.mission_name,
                n_soldiers=self.cfg.n_soldiers,
                n_billets=self.cfg.n_billets,
                seed=self.cfg.seed,
            )
            agent.emd = emd
            assignments, summary = agent.analyze_and_tune(
                target_fill=self.cfg.target_fill,
                max_cost=self.cfg.max_cost,
            )
        else:
            print("📊  Running direct assignment (no agentic tuning)...")
            assignments, summary = emd.assign(self.cfg.mission_name)

        # 6️⃣ Final summary log
        fill = summary.get("fill_rate", 0.0)
        cost = summary.get("total_cost", 0.0)
        print(f"✅ Exercise complete: fill={fill:.2%}, cost=${cost:,.0f}\n")

        return ExerciseOutputs(emd=emd, assignments=assignments, summary=summary)

    # -------------------------
    # Quick QA helpers
    # -------------------------
    @staticmethod
    def readiness_snapshot(assignments: pd.DataFrame) -> pd.DataFrame:
        """
        Useful rollups: fill by base, rank, MOS, and clearance.
        """
        tabs = []
        tabs.append(assignments.groupby("billet_base")["billet_id"].nunique().rename("filled_by_base"))
        tabs.append(assignments.groupby("soldier_rank")["soldier_id"].count().rename("soldiers_by_rank"))
        tabs.append(assignments.groupby("soldier_mos")["soldier_id"].count().rename("soldiers_by_mos"))
        tabs.append(assignments.groupby("soldier_clearance")["soldier_id"].count().rename("soldiers_by_clearance"))
        return pd.concat(tabs, axis=1)

    @staticmethod
    def export(assignments: pd.DataFrame, summary: Dict, prefix: str) -> None:
        assignments.to_csv(f"{prefix}_assignments.csv", index=False)
        pd.DataFrame([summary]).to_json(f"{prefix}_summary.json", orient="records", indent=2)