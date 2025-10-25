"""
emd_agent.py
------------

Agentic optimization framework for enlisted manpower distribution (EMD).

Classes:
- EMD: Generates soldier/billet data and computes cost matrices for assignments.
- SimpleHeuristicTuning: Lightweight strategy to iteratively improve fill and cost.
- ManningAgent: Adaptive controller for tuning EMD policies over multiple iterations.

Designed for extensibility with future agentic strategies (e.g., BayesianPolicyTuning).
"""

from __future__ import annotations
import numpy as np
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field

# Setup logging
logger = logging.getLogger(__name__)

try:
    from scipy.optimize import linear_sum_assignment
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False

class EMD:
    # ------------------------
    # Init
    # ------------------------
    def __init__(self, n_soldiers: int = 100, n_billets: int = 40, seed: Optional[int] = None,
                 soldiers_df: Optional[pd.DataFrame] = None,
                 billets_df: Optional[pd.DataFrame] = None):
        """
        Initialize EMD optimizer.

        Args:
            n_soldiers: Number of soldiers (if generating)
            n_billets: Number of billets (if generating)
            seed: Random seed
            soldiers_df: Pre-generated soldiers DataFrame (from MTOE generator)
            billets_df: Pre-generated billets DataFrame (from manning document)
        """
        if seed is not None:
            np.random.seed(seed)

        # reference categories
        self.bases       = ['FBNC', 'JBLM', 'JBER', 'FHTX', 'FBGA']
        self.paygrades   = ['E-3', 'E-4', 'E-5', 'E-6']
        self.mos_list    = ['11B','68W','25U','35F','12B','92Y','88M','42A','15T','31B']
        self.clearances  = ['None','Secret','TS']  # ascending sensitivity
        self.pme         = ['None','BLC','ALC','SLC']
        self.languages   = ['None','Spanish','Arabic','French']

        self.rank_num    = {'E-3':3, 'E-4':4, 'E-5':5, 'E-6':6}
        self.clear_num   = {'None':0, 'Secret':1, 'TS':2}

        # public knobs (can be swapped per mission)
        self.policies    = self._default_policies()
        self.mission     = self._default_mission()  # can be overwritten

        # NEW: Extended data structures (optional)
        self.soldiers_ext = {}  # Dict[int, SoldierExtended] - populated externally
        self.task_organizer = None  # TaskOrganizer - populated externally
        self.readiness_profile = None  # ReadinessProfile - populated externally
        self.exercise_location = None  # str - exercise/deployment location for geographic analysis

        # generate or use provided datasets
        self.n_soldiers  = n_soldiers
        self.n_billets   = n_billets

        if soldiers_df is not None:
            self.soldiers = soldiers_df
            self.n_soldiers = len(soldiers_df)
        else:
            self.soldiers = self._generate_soldiers()

        if billets_df is not None:
            self.billets = billets_df
            self.n_billets = len(billets_df)
        else:
            self.billets = self._generate_billets()

        self.TDY_costs   = self._generate_TDY_costs()

    # ------------------------
    # Policy & mission knobs
    # ------------------------
    def _default_policies(self) -> Dict[str, float]:
        # Positive = penalty (bad), Negative = bonus (good)
        return {
            "min_dwell_months_for_TDY": 6,
            "mos_mismatch_penalty": 3000,          # allow cross-leveling but expensive
            "rank_out_of_band_penalty": 5000,      # if below min or above max
            "skill_short_penalty": 1500,           # soldier skill < req
            "clearance_mismatch_penalty": 2000,    # soldier clearance < req
            "airborne_required_penalty": 1200,     # billet requires airborne, soldier not airborne
            "language_required_penalty": 1000,     # billet language mismatch
            "availability_miss_penalty": 800,      # soldier available after billet start
            "deployable_false_penalty": 8000,      # non-deployable soldier (hard block in many cases)
            "preference_bonus_same_base": -200,    # staying at same base
            "TDY_cost_weight": 1.0,                # weight on USD TDY cost in objective
            "dwell_short_penalty": 1500,           # penalty for moving soldier with short dwell
            # Priority weights multiply total billet cost (1=low, 2=med, 3=high)
            "priority_weight_low": 1.0,
            "priority_weight_med": 1.5,
            "priority_weight_high": 2.0,
            # NEW: Unit cohesion and readiness
            "unit_cohesion_bonus": -500,           # bonus for keeping teams together
            "unit_split_penalty": 300,             # penalty for breaking up teams
            "cross_unit_penalty": 200,             # penalty per additional unit sourced
            "readiness_failure_penalty": 2000,     # penalty per readiness gate failed
            "training_currency_bonus": -100,       # bonus for all training current
            # NEW: Geographic distance penalties
            "geographic_cost_weight": 1.0,         # weight for travel costs (1.0 = full cost)
            "lead_time_penalty_oconus": 500,       # additional penalty for OCONUS (coordination)
            "same_theater_bonus": -300,            # bonus if soldier already in destination theater
            "distance_penalty_per_1000mi": 100,    # additional penalty per 1000 miles (beyond cost)
            # NEW: Qualification penalties (Phase 4)
            # Education
            "education_mismatch_penalty": 1000,    # soldier below required education level
            "education_exceed_bonus": -100,        # soldier exceeds required education
            # Languages
            "language_proficiency_penalty": 2000,  # missing required language proficiency
            "language_native_bonus": -200,         # native speaker bonus
            "any_language_bonus": -150,            # has any foreign language when preferred
            # ASI/SQI
            "asi_missing_penalty": 1500,           # missing required ASI
            "asi_preferred_bonus": -200,           # has preferred ASI
            "sqi_missing_penalty": 2500,           # missing required SQI (critical quals)
            "sqi_preferred_bonus": -300,           # has preferred SQI
            # Badges
            "badge_missing_penalty": 1200,         # missing required badge
            "badge_alternative_penalty": 400,      # has alternative badge (partial credit)
            "badge_preferred_bonus": -150,         # has preferred badge
            "combat_badge_bonus": -250,            # has combat badge (CIB, CAB, CMB)
            # Licenses
            "license_missing_penalty": 800,        # missing required license
            "license_preferred_bonus": -100,       # has preferred license
            # Experience
            "combat_experience_missing_penalty": 2000,  # missing required combat experience
            "deployment_missing_penalty": 1000,    # below minimum deployment count
            "theater_experience_bonus": -400,      # has required theater experience
            "leadership_experience_penalty": 1500, # below required leadership level
            "tis_short_penalty": 500,              # below minimum TIS requirement
            "tig_short_penalty": 300,              # below minimum TIG requirement
            # Awards
            "award_missing_penalty": 600,          # missing required award
            "valor_award_bonus": -500,             # has valor award (BSM-V, ARCOM-V, etc.)
            # Medical/Fitness
            "medical_category_penalty": 1000,      # exceeds max medical category
            "dental_category_penalty": 500,        # exceeds max dental category
            "acft_short_penalty": 800,             # below minimum ACFT score
            "weapons_qual_penalty": 400,           # below minimum weapons qual
            # Availability
            "dwell_requirement_penalty": 1200,     # below minimum dwell requirement
            # Overall match quality
            "perfect_match_bonus": -1000,          # meets all required + preferred quals
            "critical_qual_missing_penalty": 5000, # missing any critical qualification
        }

    def _default_mission(self) -> Dict[str, Dict]:
        # Example mission profiles (edit/tune freely)
        return {
            "default": {
                "base_bias": {},             # e.g., {"JBER": -100}  # bonus to keep/fill at JBER
                "mos_priority_bonus": {},    # e.g., {"68W": -250}
                "airborne_bias": 0,          # subtract if airborne is globally preferred
                "language_bonus": {},        # e.g., {"Arabic": -200}
            }
        }

    def set_mission_profile(self, name: str, profile: Dict):
        """Override or add a mission profile."""
        self.mission[name] = profile

    # ------------------------
    # Soldier generator
    # ------------------------
    def _generate_soldiers(self) -> pd.DataFrame:
        n = self.n_soldiers
        base_probs = np.ones(len(self.bases)) / len(self.bases)
        df = pd.DataFrame({
            "soldier_id": range(1, n+1),
            "base": np.random.choice(self.bases, n, p=base_probs),
            "paygrade": np.random.choice(self.paygrades, n, p=[0.20,0.40,0.25,0.15]),
            "mos": np.random.choice(self.mos_list, n),
            "skill_level": np.random.choice([1,2,3,4,5], n, p=[0.30,0.40,0.20,0.08,0.02]),
            "clearance": np.random.choice(self.clearances, n, p=[0.10,0.75,0.15]),
            "pme": np.random.choice(self.pme, n, p=[0.30,0.35,0.25,0.10]),
            "airborne": np.random.choice([0,1], n, p=[0.70,0.30]),
            "pathfinder": np.random.choice([0,1], n, p=[0.95,0.05]),
            "ranger": np.random.choice([0,1], n, p=[0.95,0.05]),
            "umo": np.random.choice([0,1], n, p=[0.95,0.05]),
            "m4_score": np.round(np.clip(40*np.random.beta(10, 2, size=n), 23, 40)).astype(int),
            "acft_score": np.clip(np.random.normal(loc=450, scale=60, size=n), 360, 600),
            "body_composition_pass": np.random.choice([0,1], n, p=[0.10,0.90]),
            "asi_air_assault": np.random.choice([0,1], n, p=[0.85,0.15]),
            "asi_sniper": np.random.choice([0,1], n, p=[0.97,0.03]),
            "asi_jumpmaster": np.random.choice([0,1], n, p=[0.95,0.05]),
            "driver_license": np.random.choice(["None","HMMWV","LMTV","JLTV"], n, p=[0.40,0.30,0.20,0.10]),
            "med_cat": np.random.choice([1,2,3,4], n, p=[0.70,0.20,0.08,0.02]),
            "dental_cat": np.random.choice([1,2,3,4], n, p=[0.80,0.15,0.04,0.01]),
            "language": np.random.choice(self.languages, n, p=[0.70,0.15,0.10,0.05]),
            "dwell_months": np.random.randint(0, 37, n),
            "available_from": [
                (datetime.today() + timedelta(days=int(x))).date()
                for x in np.random.randint(0, 365, n)
            ],
        })

        # PME–rank sanity: no SLC for E-3/E-4
        df.loc[df["paygrade"].isin(["E-3","E-4"]) & (df["pme"] == "SLC"), "pme"] = "None"

        # Rank–skill alignment (soft fix)
        rank_skill_map = {"E-3":[1], "E-4":[1,2], "E-5":[2,3], "E-6":[3,4,5]}
        for rank, levels in rank_skill_map.items():
            mask = (df["paygrade"] == rank) & ~df["skill_level"].isin(levels)
            if mask.any():
                df.loc[mask, "skill_level"] = np.random.choice(levels, size=mask.sum())

        # Derived features
        df["rank_num"]   = df["paygrade"].map(self.rank_num)
        df["clear_num"]  = df["clearance"].map(self.clear_num)
        df["deployable"] = np.where(df["med_cat"] <= 2, 1, 0)
        return df

    # ------------------------
    # Billet generator
    # ------------------------
    def _generate_billets(self) -> pd.DataFrame:
        m = self.n_billets
        base_probs = np.ones(len(self.bases)) / len(self.bases)
        df = pd.DataFrame({
            "billet_id": range(101, 101+m),
            "base": np.random.choice(self.bases, m, p=base_probs),
            "priority": np.random.choice([1,2,3], m, p=[0.30,0.50,0.20]),  # 1=low,2=med,3=high
            "mos_required": np.random.choice(self.mos_list, m,
                               p=[0.20,0.15,0.10,0.10,0.15,0.10,0.10,0.05,0.03,0.02]),
            "min_rank": np.random.choice(['E-3','E-4','E-5'], m, p=[0.30,0.50,0.20]),
            "max_rank": np.random.choice(['E-4','E-5','E-6'], m, p=[0.20,0.50,0.30]),
            "skill_level_req": np.random.choice([1,2,3], m, p=[0.50,0.35,0.15]),
            "clearance_req": np.random.choice(self.clearances, m, p=[0.05,0.70,0.25]),
            "airborne_required": np.random.choice([0,1], m, p=[0.70,0.30]),
            "language_required": np.random.choice(["None","Spanish","Arabic"], m, p=[0.80,0.15,0.05]),
            "start_date": [
                (datetime.today() + timedelta(days=int(x))).date()
                for x in np.random.randint(0, 180, m)
            ]
        })

        # Ensure min_rank <= max_rank in numeric sense
        df["min_rank_num"] = df["min_rank"].map(self.rank_num).astype("int64")
        df["max_rank_num"] = df["max_rank"].map(self.rank_num).astype("int64")
        swap_mask = df["min_rank_num"] > df["max_rank_num"]

        # swap string columns separately from numeric columns
        if swap_mask.any():
            # swap rank strings
            tmp = df.loc[swap_mask, "min_rank"].copy()
            df.loc[swap_mask, "min_rank"] = df.loc[swap_mask, "max_rank"]
            df.loc[swap_mask, "max_rank"] = tmp

            # swap numeric columns
            tmpn = df.loc[swap_mask, "min_rank_num"].copy()
            df.loc[swap_mask, "min_rank_num"] = df.loc[swap_mask, "max_rank_num"]
            df.loc[swap_mask, "max_rank_num"] = tmpn

        df["clear_req_num"] = df["clearance_req"].map(self.clear_num)
        return df

    def set_bases(self, bases, dist_overrides: Optional[Dict[tuple, int]] = None, reseed: Optional[int] = None):
        """
        Swap the theater (bases) and regenerate TDY costs (+ optionally soldiers/billets).
        Keeps your public API stable; only used by ExerciseBuilder.
        """
        if reseed is not None:
            np.random.seed(reseed)
        self.bases = list(bases)
        # Rebuild TDY costs with optional theater-specific distances
        self.TDY_costs = self._generate_TDY_costs(dist_overrides)
        # Regenerate datasets so the new base set propagates everywhere
        self.soldiers = self._generate_soldiers()
        self.billets  = self._generate_billets()

    def update_distance_matrix(self, dist_overrides: Dict[tuple, int]):
        """
        Update TDY cost matrix in-place with new/overridden distances; bases unchanged.
        """
        self.TDY_costs = self._generate_TDY_costs(dist_overrides)

    def _generate_TDY_costs(self, dist_override: Optional[Dict[tuple, int]] = None) -> pd.DataFrame:
        # default CONUS-ish scaffold
        dist = {
            ('FBNC','FHTX'): 1300, ('FBNC','FBGA'): 350,  ('FBNC','JBLM'): 2800, ('FBNC','JBER'): 4300,
            ('FHTX','FBGA'): 800,  ('FHTX','JBLM'): 2100, ('FHTX','JBER'): 3900,
            ('FBGA','JBLM'): 2700, ('FBGA','JBER'): 4200,
            ('JBLM','JBER'): 2300
        }
        # Allow theater-specific overrides
        if dist_override:
            # normalize keys as sorted tuples so ('A','B') == ('B','A')
            for (a, b), miles in dist_override.items():
                dist[tuple(sorted((a, b)))] = miles

        base_rate_per_mile = 0.6
        flat_start = 600

        rows = []
        for a in self.bases:
            for b in self.bases:
                if a == b:
                    cost = 0
                else:
                    key = tuple(sorted([a,b]))
                    miles = dist.get(key, 2000)  # default if not listed
                    cost = int(flat_start + base_rate_per_mile * miles)
                rows.append((a,b,cost))
        df = pd.DataFrame(rows, columns=["from_base","to_base","TDY_cost_usd"])
        assert set(df.columns) == {"from_base", "to_base", "TDY_cost_usd"}, \
            f"TDY cost table malformed: {df.columns}"
        return df


    # ------------------------
    # Costing & assignment
    # ------------------------
    def _TDY_cost(self, from_base: str, to_base: str) -> float:
        row = self.TDY_costs[(self.TDY_costs.from_base == from_base) &
                             (self.TDY_costs.to_base   == to_base)]
        if row.empty:
            # matrix is symmetric by construction
            row = self.TDY_costs[(self.TDY_costs.from_base == to_base) &
                                 (self.TDY_costs.to_base   == from_base)]
        return float(row.TDY_cost_usd.values[0]) if not row.empty else 2000.0

    def _priority_weight(self, p: int) -> float:
        if p == 3: return self.policies["priority_weight_high"]
        if p == 2: return self.policies["priority_weight_med"]
        return self.policies["priority_weight_low"]

    def _mission_adjust(self, mission_name: str, soldier: pd.Series, billet: pd.Series) -> float:
        prof = self.mission.get(mission_name, self.mission["default"])
        adj = 0.0
        # base bias by billet base
        if "base_bias" in prof:
            adj += prof["base_bias"].get(billet["base"], 0.0)
        # MOS bonus
        if "mos_priority_bonus" in prof:
            adj += prof["mos_priority_bonus"].get(billet["mos_required"], 0.0)
        # airborne bias
        if prof.get("airborne_bias", 0) and soldier["airborne"] == 1:
            adj += prof["airborne_bias"]
        # language bonus
        if "language_bonus" in prof:
            adj += prof["language_bonus"].get(soldier["language"], 0.0)
        return adj

    def pair_cost(self, soldier: pd.Series, billet: pd.Series,
                  mission_name: str = "default") -> float:
        P = self.policies
        cost = 0.0

        # Hard-ish constraints penalized heavily (rather than INF to keep problem solvable)
        # Rank band
        if not (billet["min_rank_num"] <= soldier["rank_num"] <= billet["max_rank_num"]):
            cost += P["rank_out_of_band_penalty"]

        # Skill shortfall
        if soldier["skill_level"] < billet["skill_level_req"]:
            cost += P["skill_short_penalty"]

        # Clearance shortfall
        if soldier["clear_num"] < billet["clear_req_num"]:
            cost += P["clearance_mismatch_penalty"]

        # MOS mismatch (allow cross leveling at a price)
        mos_pen = P["mos_mismatch_penalty"]
        if billet["priority"] == 3:  # high
            mos_pen *= 1.5
        elif billet["priority"] == 1:
            mos_pen *= 0.8
        if soldier["mos"] != billet["mos_required"]:
            cost += mos_pen

        # Airborne requirement
        if billet["airborne_required"] == 1 and soldier["airborne"] == 0:
            cost += P["airborne_required_penalty"]

        # Language
        if billet["language_required"] != "None" and soldier["language"] != billet["language_required"]:
            cost += P["language_required_penalty"]

        # Availability (soldier available AFTER billet start)
        if soldier["available_from"] > billet["start_date"]:
            cost += P["availability_miss_penalty"]

        # Deployability
        if soldier["deployable"] == 0:
            cost += P["deployable_false_penalty"]

        # TDY cost (weighted)
        TDY = self._TDY_cost(soldier["base"], billet["base"])
        cost += P["TDY_cost_weight"] * TDY

        # Keep at same base bonus
        if soldier["base"] == billet["base"]:
            cost += P["preference_bonus_same_base"]

        # Dwell time (penalize moving too soon)
        if soldier["dwell_months"] < P["min_dwell_months_for_TDY"] and soldier["base"] != billet["base"]:
            # discourage TDY if dwell is short
            cost += P["dwell_short_penalty"]

        # Mission-specific adjustments
        cost += self._mission_adjust(mission_name, soldier, billet)

        # Weight by billet priority
        cost *= self._priority_weight(billet["priority"])
        return float(cost)

    def build_cost_matrix(self, mission_name: str = "default") -> np.ndarray:
        """
        Vectorized cost matrix builder — ~100x faster for large cases.
        """
        P = self.policies
        S = self.soldiers.reset_index(drop=True)  # Ensure sequential indices
        B = self.billets.reset_index(drop=True)   # Ensure sequential indices
        n_soldiers, n_billets = len(S), len(B)

        # Preload TDY cost lookup
        TDY_lookup = self.TDY_costs.set_index(["from_base", "to_base"])["TDY_cost_usd"].to_dict()

        # Convert to numpy arrays for speed
        C = np.zeros((n_soldiers, n_billets), dtype=np.float32)

        # Now j is guaranteed to be 0, 1, 2, ... matching matrix column indices
        for j, b in B.iterrows():
            # Preload billet parameters
            base_to = b["base"]
            mos_req = b["mos_required"]
            min_rank = b["min_rank_num"]
            max_rank = b["max_rank_num"]
            skill_req = b["skill_level_req"]
            clear_req = b["clear_req_num"]
            airborne_req = b["airborne_required"]
            lang_req = b["language_required"]
            start_date = b["start_date"]
            prio_weight = self._priority_weight(b["priority"])

            # Vectorized features for all soldiers
            rank_pen = np.where(
                (S["rank_num"] < min_rank) | (S["rank_num"] > max_rank),
                P["rank_out_of_band_penalty"], 0
            )
            skill_pen = np.where(S["skill_level"] < skill_req, P["skill_short_penalty"], 0)
            clear_pen = np.where(S["clear_num"] < clear_req, P["clearance_mismatch_penalty"], 0)
            mos_pen = np.where(S["mos"] != mos_req, P["mos_mismatch_penalty"], 0)
            airborne_pen = np.where(
                (airborne_req == 1) & (S["airborne"] == 0),
                P["airborne_required_penalty"], 0
            )
            lang_pen = np.where(
                (lang_req != "None") & (S["language"] != lang_req),
                P["language_required_penalty"], 0
            )
            avail_pen = np.where(S["available_from"] > start_date, P["availability_miss_penalty"], 0)
            deploy_pen = np.where(S["deployable"] == 0, P["deployable_false_penalty"], 0)

            # TDY cost via vectorized lookup
            TDY_costs = np.array([
                TDY_lookup.get((s_base, base_to), TDY_lookup.get((base_to, s_base), 2000))
                for s_base in S["base"]
            ]) * P["TDY_cost_weight"]

            same_base_bonus = np.where(S["base"] == base_to, P["preference_bonus_same_base"], 0)

            # Mission-specific adjustments (simple bias addition)
            prof = self.mission.get(mission_name, self.mission["default"])
            mission_adj = np.zeros(n_soldiers)
            if "base_bias" in prof:
                mission_adj += prof["base_bias"].get(base_to, 0)
            if "mos_priority_bonus" in prof:
                mission_adj += np.where(S["mos"] == mos_req, prof["mos_priority_bonus"].get(mos_req, 0), 0)
            if prof.get("airborne_bias", 0):
                mission_adj += np.where(S["airborne"] == 1, prof["airborne_bias"], 0)
            if "language_bonus" in prof:
                mission_adj += [prof["language_bonus"].get(lang, 0) for lang in S["language"]]

            # Combine everything
            total_cost = (
                rank_pen + skill_pen + clear_pen + mos_pen +
                airborne_pen + lang_pen + avail_pen + deploy_pen +
                TDY_costs + same_base_bonus + mission_adj
            ) * prio_weight

            C[:, j] = total_cost

        return C

    def apply_cohesion_adjustments(self, cost_matrix: np.ndarray) -> np.ndarray:
        """
        Apply unit cohesion adjustments to cost matrix.

        This is called after build_cost_matrix() if task_organizer is configured.

        Returns:
            Enhanced cost matrix with cohesion bonuses/penalties
        """
        if self.task_organizer is None:
            return cost_matrix

        # Import here to avoid circular dependency
        try:
            from task_organizer import enhance_cost_matrix_with_cohesion
            return enhance_cost_matrix_with_cohesion(
                cost_matrix,
                self.soldiers,
                self.billets,
                self.task_organizer,
                cohesion_weight=1.0
            )
        except ImportError:
            return cost_matrix

    def apply_readiness_penalties(self, cost_matrix: np.ndarray) -> np.ndarray:
        """
        Apply readiness gate penalties to cost matrix.

        This is called after build_cost_matrix() if readiness_profile is configured.

        Returns:
            Enhanced cost matrix with readiness penalties
        """
        if self.readiness_profile is None or not self.soldiers_ext:
            return cost_matrix

        # Import here to avoid circular dependency
        try:
            from readiness_tracker import ReadinessValidator
            P = self.policies

            # Reset index to ensure sequential 0, 1, 2, ... matching matrix rows
            S = self.soldiers.reset_index(drop=True)

            for i, soldier_row in S.iterrows():
                soldier_id = soldier_row["soldier_id"]
                soldier_ext = self.soldiers_ext.get(soldier_id)

                is_ready, _, failures = ReadinessValidator.validate_soldier(
                    soldier_row, soldier_ext, self.readiness_profile
                )

                if not is_ready:
                    # Add penalty to all assignments for this soldier
                    penalty = P["readiness_failure_penalty"] * len(failures)
                    cost_matrix[i, :] += penalty
                else:
                    # Bonus for soldiers with all training current
                    if soldier_ext and all(gate.is_current() for gate in soldier_ext.training_gates.values()):
                        cost_matrix[i, :] += P["training_currency_bonus"]

        except ImportError:
            pass

        return cost_matrix

    def apply_geographic_penalties(self, cost_matrix: np.ndarray) -> np.ndarray:
        """
        Apply geographic distance penalties to cost matrix with comprehensive error handling.

        Factors considered:
        1. Travel cost (transportation + per diem)
        2. Lead time penalty for OCONUS
        3. Same-theater bonus (if soldier already in theater)
        4. Additional distance penalty (coordination complexity)

        Returns:
            Enhanced cost matrix with geographic penalties (or original on errors)
        """
        if self.exercise_location is None:
            logger.info("No exercise location specified, skipping geographic penalties")
            return cost_matrix

        try:
            from geolocation import LocationDatabase, DistanceCalculator, TravelCostEstimator
            from advanced_profiles import AdvancedReadinessProfile

            P = self.policies
            db = LocationDatabase()

            # Get exercise location with error handling
            exercise_loc = db.get(self.exercise_location)
            if exercise_loc is None:
                logger.warning(f"Exercise location not found: {self.exercise_location}, skipping geographic penalties")
                return cost_matrix

            # Validate exercise location
            if not exercise_loc.is_valid():
                logger.warning(f"Exercise location has invalid coordinates: {exercise_loc}, skipping geographic penalties")
                return cost_matrix

            # Determine if OCONUS and get duration from profile
            is_oconus = self.readiness_profile.is_oconus() if (
                self.readiness_profile and
                isinstance(self.readiness_profile, AdvancedReadinessProfile)
            ) else False

            duration_days = self.readiness_profile.typical_duration_days if (
                self.readiness_profile and
                isinstance(self.readiness_profile, AdvancedReadinessProfile)
            ) else 14

            # Track success/failure for reporting
            success_count = 0
            failure_count = 0
            soldiers_missing_base = []

            # Reset index to ensure sequential 0, 1, 2, ... matching matrix rows
            S = self.soldiers.reset_index(drop=True)

            for i, soldier_row in S.iterrows():
                try:
                    # Get soldier's home station
                    home_station = soldier_row.get("base", None)

                    if not home_station:
                        failure_count += 1
                        soldier_id = soldier_row.get("soldier_id", f"index_{i}")
                        soldiers_missing_base.append(soldier_id)
                        logger.debug(f"Soldier {soldier_id} missing base information")
                        continue

                    home_loc = db.get(home_station)

                    if home_loc is None:
                        failure_count += 1
                        logger.debug(f"Home station not found: {home_station} for soldier {i}")
                        continue

                    # Validate home location
                    if not home_loc.is_valid():
                        failure_count += 1
                        logger.debug(f"Invalid home station coordinates: {home_station} for soldier {i}")
                        continue

                    # Calculate distance with error handling
                    distance_miles = DistanceCalculator.calculate(home_loc, exercise_loc, db)

                    # Calculate costs with validation (already validated in TravelCostEstimator)
                    travel_cost = TravelCostEstimator.estimate_travel_cost(
                        distance_miles,
                        duration_days,
                        is_oconus
                    )

                    # Apply penalties
                    weighted_travel_cost = travel_cost * P["geographic_cost_weight"]
                    cost_matrix[i, :] += weighted_travel_cost

                    # 2. Lead time penalty for OCONUS
                    if is_oconus:
                        cost_matrix[i, :] += P["lead_time_penalty_oconus"]

                    # 3. Same-theater bonus
                    # If soldier's home station is already in the same AOR, give bonus
                    if home_loc.aor == exercise_loc.aor and home_loc.aor != "NORTHCOM":
                        cost_matrix[i, :] += P["same_theater_bonus"]

                    # 4. Distance complexity penalty (beyond just cost)
                    # For very long distances, add coordination penalty
                    distance_penalty = (distance_miles / 1000.0) * P["distance_penalty_per_1000mi"]
                    cost_matrix[i, :] += distance_penalty

                    success_count += 1

                except Exception as soldier_error:
                    failure_count += 1
                    logger.debug(f"Error processing geographic penalty for soldier {i}: {soldier_error}")
                    continue

            # Log summary
            total_soldiers = len(S)
            logger.info(f"Geographic penalties applied: {success_count}/{total_soldiers} soldiers processed successfully")

            if failure_count > 0:
                logger.warning(f"{failure_count} soldiers failed geographic processing")

            if soldiers_missing_base:
                logger.warning(f"{len(soldiers_missing_base)} soldiers missing base information: {soldiers_missing_base[:5]}")

        except ImportError as e:
            logger.warning(f"Geographic optimization modules not available: {e}")
            return cost_matrix
        except Exception as e:
            logger.error(f"Critical error in geographic penalties: {e}", exc_info=True)
            logger.info("Returning original cost matrix")
            return cost_matrix  # Return original matrix on critical error

        return cost_matrix

    def apply_qualification_penalties(self, cost_matrix: np.ndarray) -> np.ndarray:
        """
        Apply comprehensive qualification matching penalties to cost matrix.

        Evaluates soldier qualifications against billet requirements across:
        - Education (degrees, majors)
        - Languages (proficiency levels)
        - ASIs/SQIs (additional skill identifiers)
        - Badges (Airborne, Ranger, CIB, etc.)
        - Licenses (CDL, medical, IT certs)
        - Experience (combat, deployments, theater, leadership, TIS/TIG)
        - Awards (valor, achievement)
        - Medical/Fitness (categories, ACFT, weapons qual)
        - Availability (dwell time)

        Returns:
            Enhanced cost matrix with qualification penalties (or original on errors)
        """
        try:
            from qualifications import (
                has_language, has_asi, has_sqi, has_badge, has_award,
                has_combat_experience, has_theater_experience,
                get_deployment_count, get_education_level_value,
                has_minimum_education, has_combat_badge,
                parse_json_field
            )
            from qualifications import BilletRequirements

            P = self.policies

            # Check if billets have extended requirements
            if 'min_education_level' not in self.billets.columns:
                logger.info("Billets do not have extended requirements, skipping qualification penalties")
                return cost_matrix

            # Check if soldiers have extended profiles
            if 'education_level' not in self.soldiers.columns:
                logger.info("Soldiers do not have extended profiles, skipping qualification penalties")
                return cost_matrix

            # Track statistics
            total_matches = 0
            perfect_matches = 0
            critical_mismatches = 0
            success_count = 0
            failure_count = 0

            # Reset index to ensure sequential 0, 1, 2, ... matching matrix rows/cols
            S = self.soldiers.reset_index(drop=True)
            B = self.billets.reset_index(drop=True)

            logger.info(f"Applying qualification penalties to {len(S)} soldiers x {len(B)} billets")

            for j, billet_row in B.iterrows():
                try:
                    # Track requirements for this billet
                    required_count = 0
                    preferred_count = 0
                    critical_missing = False

                    # Get billet criticality
                    criticality = billet_row.get('criticality', 2)
                    is_critical = criticality >= 3

                    for i, soldier_row in S.iterrows():
                        try:
                            total_matches += 1
                            penalty = 0.0
                            bonus = 0.0
                            requirements_met = 0
                            requirements_missed = 0
                            preferred_met = 0

                            # ========================================
                            # 1. EDUCATION REQUIREMENTS
                            # ========================================
                            min_edu = billet_row.get('min_education_level')
                            if min_edu and not pd.isna(min_edu):
                                required_count += 1
                                soldier_edu_level = get_education_level_value(soldier_row)
                                edu_map = {'NONE': 0, 'GED': 1, 'HS': 2, 'SOME_COLLEGE': 3,
                                          'AA': 4, 'BA': 5, 'MA': 6, 'PHD': 7, 'PROFESSIONAL': 7}
                                required_edu_level = edu_map.get(min_edu, 2)

                                if soldier_edu_level < required_edu_level:
                                    penalty += P["education_mismatch_penalty"]
                                    requirements_missed += 1
                                    if is_critical:
                                        critical_missing = True
                                elif soldier_edu_level > required_edu_level:
                                    bonus += P["education_exceed_bonus"]
                                    requirements_met += 1
                                else:
                                    requirements_met += 1

                            # Preferred education
                            pref_edu = billet_row.get('preferred_education_level')
                            if pref_edu and not pd.isna(pref_edu):
                                preferred_count += 1
                                if has_minimum_education(soldier_row, pref_edu):
                                    preferred_met += 1

                            # ========================================
                            # 2. LANGUAGE REQUIREMENTS
                            # ========================================
                            langs_required_json = billet_row.get('languages_required_json')
                            if langs_required_json and not pd.isna(langs_required_json):
                                langs_required = parse_json_field(langs_required_json, [])
                                for lang_req in langs_required:
                                    lang_code = lang_req.get('language_code')
                                    min_level = lang_req.get('min_listening_level', 2)
                                    is_required = lang_req.get('required', True)

                                    if is_required:
                                        required_count += 1
                                        if has_language(soldier_row, lang_code, min_level):
                                            requirements_met += 1
                                            # Bonus for native speaker
                                            if lang_req.get('native_acceptable', True):
                                                bonus += P["language_native_bonus"]
                                        else:
                                            penalty += P["language_proficiency_penalty"]
                                            requirements_missed += 1
                                            if is_critical:
                                                critical_missing = True
                                    else:
                                        preferred_count += 1
                                        if has_language(soldier_row, lang_code, min_level):
                                            preferred_met += 1

                            # Any language acceptable
                            any_lang = billet_row.get('any_language_acceptable', False)
                            if any_lang:
                                from qualifications import has_any_language
                                if has_any_language(soldier_row, min_level=2):
                                    bonus += P["any_language_bonus"]

                            # ========================================
                            # 3. ASI/SQI REQUIREMENTS
                            # ========================================
                            # Required ASIs
                            asis_required_json = billet_row.get('asi_codes_required_json')
                            if asis_required_json and not pd.isna(asis_required_json):
                                asis_required = parse_json_field(asis_required_json, [])
                                for asi_code in asis_required:
                                    required_count += 1
                                    if has_asi(soldier_row, asi_code):
                                        requirements_met += 1
                                    else:
                                        penalty += P["asi_missing_penalty"]
                                        requirements_missed += 1
                                        if is_critical:
                                            critical_missing = True

                            # Preferred ASIs
                            asis_preferred_json = billet_row.get('asi_codes_preferred_json')
                            if asis_preferred_json and not pd.isna(asis_preferred_json):
                                asis_preferred = parse_json_field(asis_preferred_json, [])
                                for asi_code in asis_preferred:
                                    preferred_count += 1
                                    if has_asi(soldier_row, asi_code):
                                        bonus += P["asi_preferred_bonus"]
                                        preferred_met += 1

                            # Required SQIs
                            sqis_required_json = billet_row.get('sqi_codes_required_json')
                            if sqis_required_json and not pd.isna(sqis_required_json):
                                sqis_required = parse_json_field(sqis_required_json, [])
                                for sqi_code in sqis_required:
                                    required_count += 1
                                    if has_sqi(soldier_row, sqi_code):
                                        requirements_met += 1
                                    else:
                                        penalty += P["sqi_missing_penalty"]
                                        requirements_missed += 1
                                        critical_missing = True  # SQIs are always critical

                            # Preferred SQIs
                            sqis_preferred_json = billet_row.get('sqi_codes_preferred_json')
                            if sqis_preferred_json and not pd.isna(sqis_preferred_json):
                                sqis_preferred = parse_json_field(sqis_preferred_json, [])
                                for sqi_code in sqis_preferred:
                                    preferred_count += 1
                                    if has_sqi(soldier_row, sqi_code):
                                        bonus += P["sqi_preferred_bonus"]
                                        preferred_met += 1

                            # ========================================
                            # 4. BADGE REQUIREMENTS
                            # ========================================
                            # Required badges
                            badges_required_json = billet_row.get('badges_required_json')
                            if badges_required_json and not pd.isna(badges_required_json):
                                badges_required = parse_json_field(badges_required_json, [])
                                for badge_req in badges_required:
                                    badge_code = badge_req.get('badge_code')
                                    is_required = badge_req.get('required', True)
                                    alternatives = badge_req.get('alternative_badges', [])

                                    if is_required:
                                        required_count += 1
                                        if has_badge(soldier_row, badge_code):
                                            requirements_met += 1
                                        elif any(has_badge(soldier_row, alt) for alt in alternatives):
                                            # Has alternative badge - partial penalty
                                            penalty += P["badge_alternative_penalty"]
                                            requirements_met += 1
                                        else:
                                            penalty += P["badge_missing_penalty"]
                                            requirements_missed += 1
                                            if is_critical:
                                                critical_missing = True
                                    else:
                                        preferred_count += 1
                                        if has_badge(soldier_row, badge_code):
                                            bonus += P["badge_preferred_bonus"]
                                            preferred_met += 1

                            # Preferred badges
                            badges_preferred_json = billet_row.get('badges_preferred_json')
                            if badges_preferred_json and not pd.isna(badges_preferred_json):
                                badges_preferred = parse_json_field(badges_preferred_json, [])
                                for badge_req in badges_preferred:
                                    badge_code = badge_req.get('badge_code')
                                    preferred_count += 1
                                    if has_badge(soldier_row, badge_code):
                                        bonus += P["badge_preferred_bonus"]
                                        preferred_met += 1

                            # Combat badge bonus (general preference)
                            if has_combat_badge(soldier_row):
                                bonus += P["combat_badge_bonus"]

                            # ========================================
                            # 5. LICENSE REQUIREMENTS
                            # ========================================
                            # Required licenses
                            licenses_required_json = billet_row.get('licenses_required_json')
                            if licenses_required_json and not pd.isna(licenses_required_json):
                                licenses_required = parse_json_field(licenses_required_json, [])
                                from qualifications import get_licenses
                                soldier_licenses = get_licenses(soldier_row)
                                soldier_license_types = {lic.get('license_type') for lic in soldier_licenses}

                                for lic_type in licenses_required:
                                    required_count += 1
                                    if lic_type in soldier_license_types:
                                        requirements_met += 1
                                    else:
                                        penalty += P["license_missing_penalty"]
                                        requirements_missed += 1

                            # Preferred licenses
                            licenses_preferred_json = billet_row.get('licenses_preferred_json')
                            if licenses_preferred_json and not pd.isna(licenses_preferred_json):
                                licenses_preferred = parse_json_field(licenses_preferred_json, [])
                                for lic_type in licenses_preferred:
                                    preferred_count += 1
                                    if lic_type in soldier_license_types:
                                        bonus += P["license_preferred_bonus"]
                                        preferred_met += 1

                            # ========================================
                            # 6. EXPERIENCE REQUIREMENTS
                            # ========================================
                            experience_required_json = billet_row.get('experience_required_json')
                            if experience_required_json and not pd.isna(experience_required_json):
                                experiences_required = parse_json_field(experience_required_json, [])
                                for exp_req in experiences_required:
                                    exp_type = exp_req.get('requirement_type')
                                    is_required = exp_req.get('required', True)

                                    if not is_required:
                                        continue  # Handle in preferred section

                                    required_count += 1

                                    if exp_type == 'combat':
                                        if exp_req.get('combat_required', False):
                                            if has_combat_experience(soldier_row):
                                                requirements_met += 1
                                            else:
                                                penalty += P["combat_experience_missing_penalty"]
                                                requirements_missed += 1
                                                if is_critical:
                                                    critical_missing = True

                                        min_deploys = exp_req.get('min_deployments', 0)
                                        if min_deploys > 0:
                                            soldier_deploys = get_deployment_count(soldier_row, combat_only=True)
                                            if soldier_deploys >= min_deploys:
                                                requirements_met += 1
                                            else:
                                                penalty += P["deployment_missing_penalty"]
                                                requirements_missed += 1

                                    elif exp_type == 'theater':
                                        theater = exp_req.get('theater')
                                        if theater and has_theater_experience(soldier_row, theater):
                                            bonus += P["theater_experience_bonus"]
                                            requirements_met += 1
                                        else:
                                            requirements_missed += 1

                                    elif exp_type == 'leadership':
                                        min_leadership = exp_req.get('min_leadership_level', 0)
                                        soldier_leadership = soldier_row.get('leadership_level', 0)
                                        if soldier_leadership >= min_leadership:
                                            requirements_met += 1
                                        else:
                                            penalty += P["leadership_experience_penalty"]
                                            requirements_missed += 1

                                    # TIS/TIG requirements
                                    min_tis = exp_req.get('min_time_in_service_months', 0)
                                    if min_tis > 0:
                                        soldier_tis = soldier_row.get('time_in_service_months', 0)
                                        if soldier_tis >= min_tis:
                                            requirements_met += 1
                                        else:
                                            penalty += P["tis_short_penalty"]
                                            requirements_missed += 1

                                    min_tig = exp_req.get('min_time_in_grade_months', 0)
                                    if min_tig > 0:
                                        soldier_tig = soldier_row.get('time_in_grade_months', 0)
                                        if soldier_tig >= min_tig:
                                            requirements_met += 1
                                        else:
                                            penalty += P["tig_short_penalty"]
                                            requirements_missed += 1

                            # ========================================
                            # 7. AWARD REQUIREMENTS
                            # ========================================
                            awards_required_json = billet_row.get('awards_required_json')
                            if awards_required_json and not pd.isna(awards_required_json):
                                awards_required = parse_json_field(awards_required_json, [])
                                for award_type in awards_required:
                                    required_count += 1
                                    if has_award(soldier_row, award_type):
                                        requirements_met += 1
                                        # Bonus for valor awards
                                        if award_type in ['BSM', 'ARCOM', 'AAM'] and '-V' in award_type:
                                            bonus += P["valor_award_bonus"]
                                    else:
                                        penalty += P["award_missing_penalty"]
                                        requirements_missed += 1

                            # ========================================
                            # 8. MEDICAL/FITNESS REQUIREMENTS
                            # ========================================
                            max_med_cat = billet_row.get('max_medical_category')
                            if max_med_cat and not pd.isna(max_med_cat):
                                soldier_med_cat = soldier_row.get('med_cat', 1)
                                if soldier_med_cat > max_med_cat:
                                    penalty += P["medical_category_penalty"]
                                    requirements_missed += 1
                                    if is_critical:
                                        critical_missing = True

                            max_dental_cat = billet_row.get('max_dental_category')
                            if max_dental_cat and not pd.isna(max_dental_cat):
                                soldier_dental_cat = soldier_row.get('dental_cat', 1)
                                if soldier_dental_cat > max_dental_cat:
                                    penalty += P["dental_category_penalty"]
                                    requirements_missed += 1

                            min_acft = billet_row.get('min_acft_score')
                            if min_acft and not pd.isna(min_acft):
                                required_count += 1
                                soldier_acft = soldier_row.get('acft_score', 0)
                                if soldier_acft >= min_acft:
                                    requirements_met += 1
                                else:
                                    penalty += P["acft_short_penalty"]
                                    requirements_missed += 1

                            min_weapons = billet_row.get('min_weapons_qual')
                            if min_weapons and not pd.isna(min_weapons):
                                required_count += 1
                                soldier_weapons = soldier_row.get('m4_score', 0)
                                if soldier_weapons >= min_weapons:
                                    requirements_met += 1
                                else:
                                    penalty += P["weapons_qual_penalty"]
                                    requirements_missed += 1

                            # ========================================
                            # 9. AVAILABILITY REQUIREMENTS
                            # ========================================
                            min_dwell = billet_row.get('min_dwell_months', 0)
                            if min_dwell > 0:
                                required_count += 1
                                soldier_dwell = soldier_row.get('dwell_months', 0)
                                if soldier_dwell >= min_dwell:
                                    requirements_met += 1
                                else:
                                    penalty += P["dwell_requirement_penalty"]
                                    requirements_missed += 1

                            # ========================================
                            # 10. OVERALL MATCH QUALITY
                            # ========================================
                            # Perfect match bonus
                            if required_count > 0 and requirements_missed == 0 and preferred_met == preferred_count:
                                bonus += P["perfect_match_bonus"]
                                perfect_matches += 1

                            # Critical qualification missing
                            if critical_missing:
                                penalty += P["critical_qual_missing_penalty"]
                                critical_mismatches += 1

                            # Apply total penalty/bonus to cost matrix
                            cost_matrix[i, j] += (penalty + bonus)

                            success_count += 1

                        except Exception as soldier_error:
                            failure_count += 1
                            logger.debug(f"Error processing qualification for soldier {i}, billet {j}: {soldier_error}")
                            continue

                except Exception as billet_error:
                    failure_count += 1
                    logger.debug(f"Error processing billet {j}: {billet_error}")
                    continue

            # Log summary
            logger.info(f"Qualification penalties applied: {success_count}/{total_matches} matches processed successfully")
            logger.info(f"  Perfect matches: {perfect_matches}")
            logger.info(f"  Critical mismatches: {critical_mismatches}")

            if failure_count > 0:
                logger.warning(f"{failure_count} soldier-billet matches failed qualification processing")

        except ImportError as e:
            logger.warning(f"Qualification matching modules not available: {e}")
            return cost_matrix
        except Exception as e:
            logger.error(f"Critical error in qualification penalties: {e}", exc_info=True)
            logger.info("Returning original cost matrix")
            return cost_matrix

        return cost_matrix

    def assign(self, mission_name: str = "default") -> Tuple[pd.DataFrame, Dict]:
        """
        Returns:
            assignments: DataFrame with soldier-billet pairs and costs
            summary:     dict with fill stats and totals
        """
        # Validate inputs
        if len(self.soldiers) == 0:
            logger.warning("No soldiers available for assignment")
            return pd.DataFrame(), {
                "total_billets": len(self.billets),
                "filled_billets": 0,
                "fill_rate": 0.0,
                "total_cost": 0.0,
                "unfilled_billets": len(self.billets)
            }

        if len(self.billets) == 0:
            logger.warning("No billets available for assignment")
            return pd.DataFrame(), {
                "total_billets": 0,
                "filled_billets": 0,
                "fill_rate": 0.0,
                "total_cost": 0.0,
                "unfilled_billets": 0
            }

        C = self.build_cost_matrix(mission_name)

        # Apply enhancements if configured
        C = self.apply_readiness_penalties(C)
        C = self.apply_cohesion_adjustments(C)
        C = self.apply_geographic_penalties(C)
        C = self.apply_qualification_penalties(C)

        # Solve: soldiers (rows) to billets (cols). If more soldiers than billets, Hungarian picks best subset.
        if SCIPY_AVAILABLE:
            row_ind, col_ind = linear_sum_assignment(C)
        else:
            # Greedy fallback: O(B * S log S). Not optimal, but works without SciPy.
            S, B = C.shape
            row_ind, col_ind = [], []
            used_rows = set()
            for j in range(B):
                i = int(np.argmin(C[:, j]))
                # find next cheapest unused soldier if needed
                if i in used_rows:
                    order = np.argsort(C[:, j])
                    for ii in order:
                        if ii not in used_rows:
                            i = int(ii)
                            break
                used_rows.add(i)
                row_ind.append(i)
                col_ind.append(j)

        # Build assignment table (filter out absurd pairings if you decide to cap max cost)
        pairs = []
        total_cost = 0.0
        for i, j in zip(row_ind, col_ind):
            s = self.soldiers.iloc[i]
            b = self.billets.iloc[j]
            cost = float(C[i, j])
            # Include additional soldier fields if available
            pair_dict = {
                "soldier_id": s.soldier_id,
                "soldier_base": s.base,
                "soldier_rank": s.paygrade,
                "soldier_rank_num": s.rank_num,
                "soldier_mos": s.mos,
                "soldier_skill": s.skill_level,
                "soldier_clearance": s.clearance,
                "soldier_airborne": s.airborne,
                "soldier_language": s.language,
                "soldier_available": s.available_from,
                "billet_id": b.billet_id,
                "billet_base": b.base,
                "billet_priority": b.priority,
                "billet_mos_req": b.mos_required,
                "billet_min_rank": b.min_rank,
                "billet_max_rank": b.max_rank,
                "billet_skill_req": b.skill_level_req,
                "billet_clear_req": b.clearance_req,
                "billet_airborne_req": b.airborne_required,
                "billet_language_req": b.language_required,
                "billet_start": b.start_date,
                "pair_cost": cost
            }

            # Add MTOE-specific fields if present
            if "uic" in s:
                pair_dict["uic"] = s.uic
            if "duty_position" in s:
                pair_dict["duty_position"] = s.duty_position
            if "para_line" in s:
                pair_dict["para_line"] = s.para_line

            # Add manning document fields if present
            if "capability_name" in b:
                pair_dict["capability_name"] = b.capability_name
            if "team_position" in b:
                pair_dict["team_position"] = b.team_position
            if "capability_instance" in b:
                pair_dict["capability_instance"] = b.capability_instance

            pairs.append(pair_dict)
            total_cost += cost

        assignments = pd.DataFrame(pairs)

        # Compute fill (some pairs may be "bad"; you can set a threshold to mark as "unfilled")
        # Here we count every billet that got some soldier as "filled".
        if len(assignments) > 0:
            filled = assignments["billet_id"].nunique()
        else:
            filled = 0
        total_billets = len(self.billets)
        fill_rate = filled / total_billets if total_billets else 0.0

        # Useful aggregates
        if len(assignments) > 0:
            by_priority = assignments.groupby("billet_priority")["billet_id"].nunique().to_dict()
            by_base = assignments.groupby("billet_base")["billet_id"].nunique().to_dict()
        else:
            by_priority = {}
            by_base = {}

        summary = {
            "mission": mission_name,
            "total_cost": total_cost,
            "fill_rate": fill_rate,
            "filled_billets": filled,
            "total_billets": total_billets,
            "by_priority_filled": by_priority,
            "by_base_filled": by_base,
        }

        # Sort by pair_cost if assignments exist
        if len(assignments) > 0:
            return assignments.sort_values("pair_cost"), summary
        else:
            return assignments, summary

    # ------------------------
    # Convenience helpers
    # ------------------------
    def tune_policy(self, **updates):
        """Set/override policy values, e.g., tune_policy(mos_mismatch_penalty=1500)."""
        for k, v in updates.items():
            if k in self.policies:
                self.policies[k] = v

    def add_mission_bias(
        self,
        mission_name: str = "default",
        base_bias: Optional[Dict[str, float]] = None,
        mos_bonus: Optional[Dict[str, float]] = None,
        airborne_bias: Optional[float] = None,
        language_bonus: Optional[Dict[str, float]] = None,
    ):
        prof = self.mission.get(mission_name, {"base_bias":{}, "mos_priority_bonus":{}, "airborne_bias":0, "language_bonus":{}})
        if base_bias is not None:
            prof["base_bias"].update(base_bias)
        if mos_bonus is not None:
            prof["mos_priority_bonus"].update(mos_bonus)
        if airborne_bias is not None:
            prof["airborne_bias"] = airborne_bias
        if language_bonus is not None:
            prof["language_bonus"].update(language_bonus)
        self.mission[mission_name] = prof

   # ------------------------
    # Analysis helpers (optional)
    # ------------------------
    def sensitivity(self, param: str, values: List[float], mission_name: str = "default",
                    metric: str = "fill_rate") -> pd.DataFrame:
        """Sweep a single policy knob and report metric trend."""
        original = self.policies[param]
        rows = []
        for v in values:
            self.tune_policy(**{param: v})
            _, summary = self.assign(mission_name)
            rows.append({param: v, metric: summary.get(metric, None), "total_cost": summary["total_cost"]})
        self.tune_policy(**{param: original})
        return pd.DataFrame(rows)
# ------------------------
# Agent state & strategy
# ------------------------
@dataclass
class AgentState:
    iteration: int = 0
    fill_rate: float = 0.0
    total_cost: float = 0.0
    tuned_policies: Dict[str, float] = field(default_factory=dict)
    converged: bool = False
    history: List[Dict] = field(default_factory=list)

class PolicyTuningStrategy:
    """Interface for policy tuning strategies."""
    def tune(self, emd: 'EMD', summary: Dict, state: AgentState) -> Dict[str, float]:
        raise NotImplementedError

class SimpleHeuristicTuning(PolicyTuningStrategy):
    """Improved heuristic that balances fill vs. cost dynamically."""
    def __init__(self, target_fill: float = 0.95, max_cost: float = 1e6):
        self.target_fill = target_fill
        self.max_cost = max_cost

    def tune(self, emd: 'EMD', summary: Dict, state: AgentState) -> Dict[str, float]:
        updates = {}
        fill = summary.get("fill_rate", 0.0)
        cost = summary.get("total_cost", np.inf)

        # --- Phase 1: improve fill ---
        if fill < self.target_fill:
            updates["mos_mismatch_penalty"] = max(
                500, emd.policies["mos_mismatch_penalty"] * 0.8
            )

        # --- Phase 2: manage excessive cost ---
        elif cost > self.max_cost:
            updates["TDY_cost_weight"] = emd.policies["TDY_cost_weight"] * 1.2

        # --- Phase 3: optimize cost once fill target met ---
        elif fill >= self.target_fill:
            # Gradually reduce TDY weighting to favor cheaper fills
            updates["TDY_cost_weight"] = max(
                0.5, emd.policies["TDY_cost_weight"] * 0.9
            )
            # Optionally tighten MOS mismatch penalty again for realism
            updates["mos_mismatch_penalty"] = min(
                4000, emd.policies["mos_mismatch_penalty"] * 1.05
            )

        # --- Convergence check ---
        if fill >= self.target_fill and abs(cost - state.total_cost) < 0.01 * state.total_cost:
            state.converged = True

        return updates

class ManningAgent:
    def __init__(self,
                 mission_name: str = "default",
                 n_soldiers: int = 800,
                 n_billets: int = 75,
                 seed: int = 42,
                 strategy: PolicyTuningStrategy | None = None,
                 explore_prob: float = 0.10,
                 converge_tol_fill: float = 0.01,
                 converge_tol_cost_frac: float = 0.02):
        self.emd = EMD(n_soldiers, n_billets, seed)
        self.mission_name = mission_name
        self.strategy = strategy or SimpleHeuristicTuning()
        self.state = AgentState()
        self.explore_prob = explore_prob
        self.converge_tol_fill = converge_tol_fill
        self.converge_tol_cost_frac = converge_tol_cost_frac

    # ---------- policy persistence ----------
    def save_policy(self, path: str = "policies/"):
        import os
        os.makedirs(path, exist_ok=True)
        with open(f"{path}{self.mission_name}_policy.json", "w") as f:
            json.dump(self.emd.policies, f, indent=2)

    def load_policy(self, path: str = "policies/"):
        try:
            with open(f"{path}{self.mission_name}_policy.json", "r") as f:
                self.emd.policies.update(json.load(f))
        except FileNotFoundError:
            pass

    # ---------- helper ----------
    def has_converged(self, fill, cost, last_fill, last_cost) -> bool:
        """Return True if fill/cost change are below convergence thresholds."""
        return (
            last_fill is not None and last_cost is not None and
            abs(fill - last_fill) < self.converge_tol_fill and
            abs(cost - last_cost) < self.converge_tol_cost_frac * max(last_cost, 1.0)
        )
    
    # ---------- main loop ----------
    def analyze_and_tune(self, target_fill: float = 0.95, max_cost: float = 1e6, max_iters: int = 50, callback=None):
        """
        Agentic loop with:
        - pluggable tuning strategy
        - convergence detection
        - light stochastic exploration to avoid local minima
        """
        # keep strategy aligned to caller's goals (if it's the default strategy)
        if isinstance(self.strategy, SimpleHeuristicTuning):
            self.strategy.target_fill = target_fill
            self.strategy.max_cost = max_cost

        last_fill = None
        last_cost = None
        best = {"summary": None, "assignments": None}

        for it in range(max_iters):
            self.state.iteration = it
            assignments, summary = self.emd.assign(self.mission_name)
            fill, cost = summary["fill_rate"], summary["total_cost"]

            print(f"[Iter {it}] Fill={fill:.3f}, Cost={cost:,.0f}")

            # track history
            self.state.history.append({
                "iter": it, "fill": fill, "cost": cost, "policies": self.emd.policies.copy()
            })
            self.state.fill_rate = fill
            self.state.total_cost = cost

            # keep best (maximize fill, then minimize cost)
            if (best["summary"] is None or
                fill > best["summary"]["fill_rate"] or
                (fill == best["summary"]["fill_rate"] and cost < best["summary"]["total_cost"])):
                best = {"summary": summary, "assignments": assignments}

            # convergence check (trend)
            if self.has_converged(fill, cost, last_fill, last_cost):
                print("🧠 Convergence detected (small deltas).")
                break

            # ask strategy for updates
            updates = self.strategy.tune(self.emd, summary, self.state)

            # light exploration to escape local minima
            if np.random.rand() < self.explore_prob:
                key = np.random.choice(list(self.emd.policies.keys()))
                jitter = np.random.uniform(0.9, 1.1)
                updates[key] = self.emd.policies[key] * jitter
                print(f"  🎲 Exploring: jittered {key} by {jitter:.3f}")

            # apply updates
            if updates:
                self.emd.tune_policy(**updates)
                self.state.tuned_policies.update(updates)
                print("  🔧 Policy updates:", {k: round(v, 4) if isinstance(v, float) else v for k, v in updates.items()})
            else:
                print("  ✅ Strategy reports no changes (likely converged).")
                break

            last_fill, last_cost = fill, cost
            # optional user-supplied progress callback
            if callback:
                callback(it / max_iters, fill, cost)
            # hard convergence from strategy
            if self.state.converged:
                print("🧠 Strategy flagged convergence.")
                break
        
        delta = {
            k: round(self.emd.policies[k] / v - 1, 3)
            for k, v in self.state.tuned_policies.items()
            if k in self.emd.policies
        }
        if delta:
            print("\n📊 Policy change summary (fractional deltas):")
            for k, v in delta.items():
                print(f"   {k:<30}: {v:+.1%}")

        # return best seen
        return best["assignments"], best["summary"]
    
    def run(self):
        """Run the agent loop and return (assignments, summary)."""
        print(f"🚀 Launching ManningAgent for mission: {self.mission_name}")
        out = self.analyze_and_tune()
        print("✅ Agent run complete.")
        self.reflect()
        return out
    
    def reflect(self):
        """After-action summary of last iteration."""
        last = self.state.history[-1] if self.state.history else {}
        if not last:
            print("No history recorded.")
            return
        print(f"🤔 Reflection after {last['iter']+1} iterations:")
        print(f"   Fill rate: {last['fill']:.2%}, Total cost: ${last['cost']:,.0f}")
        if last['fill'] < 0.9:
            print("   ➤ Recommendation: loosen MOS mismatch or dwell penalties.")
        elif last['cost'] > 1e6:
            print("   ➤ Recommendation: increase TDY cost weight or adjust priority scaling.")