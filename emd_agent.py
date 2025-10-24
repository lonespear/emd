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
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field

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
        Apply geographic distance penalties to cost matrix.

        Factors considered:
        1. Travel cost (transportation + per diem)
        2. Lead time penalty for OCONUS
        3. Same-theater bonus (if soldier already in theater)
        4. Additional distance penalty (coordination complexity)

        Returns:
            Enhanced cost matrix with geographic penalties
        """
        if self.exercise_location is None:
            return cost_matrix

        try:
            from geolocation import LocationDatabase, DistanceCalculator, TravelCostEstimator
            from advanced_profiles import AdvancedReadinessProfile

            P = self.policies
            db = LocationDatabase()

            # Get exercise location
            exercise_loc = db.get(self.exercise_location)
            if exercise_loc is None:
                # Location not found, skip geographic penalties
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

            # Reset index to ensure sequential 0, 1, 2, ... matching matrix rows
            S = self.soldiers.reset_index(drop=True)

            for i, soldier_row in S.iterrows():
                # Get soldier's home station
                home_station = soldier_row.get("base", "JBLM")
                home_loc = db.get(home_station)

                if home_loc is None:
                    # Home station not found, skip this soldier
                    continue

                # Calculate distance
                distance_miles = DistanceCalculator.calculate(home_loc, exercise_loc, db)

                # 1. Travel cost (transportation + per diem)
                travel_cost = TravelCostEstimator.estimate_travel_cost(
                    distance_miles,
                    duration_days,
                    is_oconus
                )
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

        except ImportError as e:
            # Geolocation module not available, skip
            print(f"Warning: Geographic penalties not applied ({e})")
            pass

        return cost_matrix

    def assign(self, mission_name: str = "default") -> Tuple[pd.DataFrame, Dict]:
        """
        Returns:
            assignments: DataFrame with soldier-billet pairs and costs
            summary:     dict with fill stats and totals
        """
        C = self.build_cost_matrix(mission_name)

        # Apply enhancements if configured
        C = self.apply_readiness_penalties(C)
        C = self.apply_cohesion_adjustments(C)
        C = self.apply_geographic_penalties(C)

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
        return assignments.sort_values("pair_cost"), summary

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