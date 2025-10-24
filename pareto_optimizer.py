"""
pareto_optimizer.py
-------------------

Multi-objective Pareto optimization for manning decisions.

Instead of single-cost optimization, explore trade-offs between:
- Fill rate (maximize)
- Total cost (minimize)
- Unit cohesion (maximize)
- Cross-leveling complexity (minimize)

Classes:
- ParetoSolution: Represents a single solution point
- ParetoOptimizer: Generates Pareto frontier
- TradeOffAnalyzer: Analyzes trade-offs between objectives
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import matplotlib.pyplot as plt

from emd_agent import EMD
from task_organizer import TaskOrganizer


@dataclass
class ParetoSolution:
    """
    Represents a single solution in the Pareto frontier.

    Each solution is characterized by multiple objectives.
    """
    solution_id: int

    # Objectives
    fill_rate: float
    total_cost: float
    cohesion_score: float
    cross_leveling_score: float  # Lower = better (fewer units sourced)

    # Policy configuration that generated this solution
    policies: Dict[str, float] = field(default_factory=dict)

    # Assignments
    assignments: Optional[pd.DataFrame] = None
    summary: Optional[Dict] = None

    def dominates(self, other: 'ParetoSolution') -> bool:
        """
        Check if this solution dominates another (better on all objectives).

        For maximization objectives (fill_rate, cohesion): higher is better
        For minimization objectives (cost, cross_leveling): lower is better
        """
        # This solution is better or equal on all objectives
        better_or_equal = (
            self.fill_rate >= other.fill_rate and
            self.total_cost <= other.total_cost and
            self.cohesion_score >= other.cohesion_score and
            self.cross_leveling_score <= other.cross_leveling_score
        )

        # This solution is strictly better on at least one objective
        strictly_better = (
            self.fill_rate > other.fill_rate or
            self.total_cost < other.total_cost or
            self.cohesion_score > other.cohesion_score or
            self.cross_leveling_score < other.cross_leveling_score
        )

        return better_or_equal and strictly_better


class ParetoOptimizer:
    """
    Generates Pareto frontier by exploring policy space.

    Strategy:
    1. Sample policy space (e.g., varying penalties/bonuses)
    2. Run optimization for each configuration
    3. Calculate multi-objective metrics
    4. Filter to Pareto-optimal solutions
    """

    def __init__(self, emd: EMD, mission_name: str = "default"):
        self.emd = emd
        self.mission_name = mission_name
        self.solutions: List[ParetoSolution] = []

    def explore_policy_space(
        self,
        param_grid: Dict[str, List[float]],
        max_solutions: int = 50
    ) -> List[ParetoSolution]:
        """
        Explore policy parameter space and generate solutions.

        Args:
            param_grid: Dict of {parameter_name: [values_to_try]}
            max_solutions: Maximum number of solutions to generate

        Example:
            param_grid = {
                "mos_mismatch_penalty": [1000, 2000, 3000, 4000],
                "unit_cohesion_bonus": [0, -300, -600, -900],
                "TDY_cost_weight": [0.5, 1.0, 1.5, 2.0]
            }
        """
        print(f"\n🔬 Exploring policy space...")
        print(f"   Parameters: {list(param_grid.keys())}")

        # Save original policies
        original_policies = self.emd.policies.copy()

        # Generate parameter combinations (sample if too many)
        from itertools import product
        param_names = list(param_grid.keys())
        param_values = [param_grid[name] for name in param_names]
        combinations = list(product(*param_values))

        if len(combinations) > max_solutions:
            # Random sample
            indices = np.random.choice(len(combinations), max_solutions, replace=False)
            combinations = [combinations[i] for i in indices]

        print(f"   Testing {len(combinations)} policy combinations...")

        # Test each combination
        for idx, param_combo in enumerate(combinations):
            # Create policy dict
            policy_config = dict(zip(param_names, param_combo))

            # Apply policies
            self.emd.tune_policy(**policy_config)

            # Run optimization
            try:
                assignments, summary = self.emd.assign(self.mission_name)

                # Calculate objectives
                fill_rate = summary["fill_rate"]
                total_cost = summary["total_cost"]
                cohesion_score = self._calculate_cohesion_score(assignments)
                cross_leveling_score = self._calculate_cross_leveling_score(assignments)

                # Create solution
                solution = ParetoSolution(
                    solution_id=idx,
                    fill_rate=fill_rate,
                    total_cost=total_cost,
                    cohesion_score=cohesion_score,
                    cross_leveling_score=cross_leveling_score,
                    policies=policy_config.copy(),
                    assignments=assignments,
                    summary=summary
                )

                self.solutions.append(solution)

                if (idx + 1) % 10 == 0:
                    print(f"   ... {idx + 1}/{len(combinations)} complete")

            except Exception as e:
                print(f"   ⚠️  Solution {idx} failed: {e}")
                continue

        # Restore original policies
        self.emd.policies = original_policies

        print(f"   ✅ Generated {len(self.solutions)} solutions")
        return self.solutions

    def _calculate_cohesion_score(self, assignments: pd.DataFrame) -> float:
        """
        Calculate cohesion score (0-100).

        Higher = better (more intact teams assigned together)
        """
        if "uic" not in assignments.columns or "capability_name" not in assignments.columns:
            return 50.0  # Neutral score

        # Count how many capabilities are filled from single units
        intact_capabilities = 0
        total_capabilities = assignments["capability_name"].nunique()

        for cap_name in assignments["capability_name"].unique():
            cap_assignments = assignments[assignments["capability_name"] == cap_name]
            units_used = cap_assignments["uic"].nunique()

            if units_used == 1:
                intact_capabilities += 1

        cohesion_pct = (intact_capabilities / total_capabilities) * 100 if total_capabilities > 0 else 0
        return cohesion_pct

    def _calculate_cross_leveling_score(self, assignments: pd.DataFrame) -> float:
        """
        Calculate cross-leveling complexity (0-100).

        Lower = better (fewer units sourced from)
        """
        if "uic" not in assignments.columns:
            return 50.0  # Neutral score

        units_sourced = assignments["uic"].nunique()
        # Normalize: assume 10+ units is maximum complexity
        score = min(100, (units_sourced / 10.0) * 100)
        return score

    def get_pareto_frontier(self) -> List[ParetoSolution]:
        """
        Filter solutions to Pareto-optimal set (non-dominated solutions).
        """
        if not self.solutions:
            return []

        pareto_front = []

        for solution in self.solutions:
            is_dominated = False

            for other in self.solutions:
                if other.dominates(solution):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_front.append(solution)

        print(f"\n📊 Pareto Frontier: {len(pareto_front)}/{len(self.solutions)} solutions are Pareto-optimal")
        return pareto_front

    def to_dataframe(self, pareto_only: bool = False) -> pd.DataFrame:
        """Convert solutions to DataFrame for analysis."""
        solutions = self.get_pareto_frontier() if pareto_only else self.solutions

        rows = []
        for sol in solutions:
            row = {
                "solution_id": sol.solution_id,
                "fill_rate": sol.fill_rate,
                "total_cost": sol.total_cost,
                "cohesion_score": sol.cohesion_score,
                "cross_leveling_score": sol.cross_leveling_score,
                **{f"policy_{k}": v for k, v in sol.policies.items()}
            }
            rows.append(row)

        return pd.DataFrame(rows)


class TradeOffAnalyzer:
    """
    Analyzes trade-offs between objectives in Pareto frontier.
    """

    @staticmethod
    def plot_tradeoff_2d(
        solutions: List[ParetoSolution],
        obj_x: str,
        obj_y: str,
        pareto_only: bool = True,
        save_path: Optional[str] = None
    ):
        """
        Plot 2D trade-off between two objectives.

        Args:
            solutions: List of solutions
            obj_x: Objective for x-axis ("fill_rate", "total_cost", etc.)
            obj_y: Objective for y-axis
            pareto_only: Only plot Pareto-optimal solutions
            save_path: If provided, save plot to file
        """
        import matplotlib.pyplot as plt

        # Filter to Pareto frontier if requested
        if pareto_only:
            optimizer = ParetoOptimizer(None)
            optimizer.solutions = solutions
            solutions = optimizer.get_pareto_frontier()

        # Extract objective values
        x_vals = [getattr(sol, obj_x) for sol in solutions]
        y_vals = [getattr(sol, obj_y) for sol in solutions]

        # Create plot
        plt.figure(figsize=(10, 6))
        plt.scatter(x_vals, y_vals, alpha=0.6, s=100)

        # Labels
        plt.xlabel(obj_x.replace('_', ' ').title(), fontsize=12)
        plt.ylabel(obj_y.replace('_', ' ').title(), fontsize=12)
        plt.title(f"Pareto Frontier: {obj_x} vs {obj_y}", fontsize=14)
        plt.grid(True, alpha=0.3)

        # Annotate some points
        for i, sol in enumerate(solutions[:5]):  # Annotate first 5
            plt.annotate(
                f"#{sol.solution_id}",
                (x_vals[i], y_vals[i]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8
            )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300)
            print(f"   💾 Plot saved to {save_path}")

        plt.show()

    @staticmethod
    def compare_solutions(
        sol_a: ParetoSolution,
        sol_b: ParetoSolution
    ) -> pd.DataFrame:
        """
        Compare two solutions across all objectives.

        Returns DataFrame showing differences.
        """
        comparison = {
            "Objective": [
                "Fill Rate",
                "Total Cost",
                "Cohesion Score",
                "Cross-Leveling Score"
            ],
            "Solution A": [
                f"{sol_a.fill_rate:.1%}",
                f"${sol_a.total_cost:,.0f}",
                f"{sol_a.cohesion_score:.1f}",
                f"{sol_a.cross_leveling_score:.1f}"
            ],
            "Solution B": [
                f"{sol_b.fill_rate:.1%}",
                f"${sol_b.total_cost:,.0f}",
                f"{sol_b.cohesion_score:.1f}",
                f"{sol_b.cross_leveling_score:.1f}"
            ],
            "Difference": [
                f"{(sol_b.fill_rate - sol_a.fill_rate):.1%}",
                f"${(sol_b.total_cost - sol_a.total_cost):+,.0f}",
                f"{(sol_b.cohesion_score - sol_a.cohesion_score):+.1f}",
                f"{(sol_b.cross_leveling_score - sol_a.cross_leveling_score):+.1f}"
            ],
            "Better": [
                "B" if sol_b.fill_rate > sol_a.fill_rate else "A" if sol_a.fill_rate > sol_b.fill_rate else "Tie",
                "B" if sol_b.total_cost < sol_a.total_cost else "A" if sol_a.total_cost < sol_b.total_cost else "Tie",
                "B" if sol_b.cohesion_score > sol_a.cohesion_score else "A" if sol_a.cohesion_score > sol_b.cohesion_score else "Tie",
                "B" if sol_b.cross_leveling_score < sol_a.cross_leveling_score else "A" if sol_a.cross_leveling_score < sol_b.cross_leveling_score else "Tie"
            ]
        }

        return pd.DataFrame(comparison)

    @staticmethod
    def recommend_solution(
        solutions: List[ParetoSolution],
        priorities: Dict[str, float]
    ) -> ParetoSolution:
        """
        Recommend best solution based on user-specified priorities.

        Args:
            solutions: Pareto frontier solutions
            priorities: Dict of {objective: weight}, e.g.,
                {"fill_rate": 0.4, "total_cost": 0.3, "cohesion_score": 0.3}

        Returns:
            Recommended solution
        """
        # Normalize priorities
        total_weight = sum(priorities.values())
        normalized_priorities = {k: v / total_weight for k, v in priorities.items()}

        # Normalize objectives to 0-1 scale
        fills = [s.fill_rate for s in solutions]
        costs = [s.total_cost for s in solutions]
        cohesions = [s.cohesion_score for s in solutions]
        cross_levels = [s.cross_leveling_score for s in solutions]

        min_cost, max_cost = min(costs), max(costs)
        min_cross, max_cross = min(cross_levels), max(cross_levels)

        # Score each solution
        best_solution = None
        best_score = -float('inf')

        for sol in solutions:
            # Normalize (higher is better for all after normalization)
            norm_fill = sol.fill_rate  # Already 0-1
            norm_cost = 1.0 - ((sol.total_cost - min_cost) / (max_cost - min_cost)) if max_cost > min_cost else 0.5
            norm_cohesion = sol.cohesion_score / 100.0  # 0-100 to 0-1
            norm_cross = 1.0 - ((sol.cross_leveling_score - min_cross) / (max_cross - min_cross)) if max_cross > min_cross else 0.5

            # Weighted score
            score = (
                norm_fill * normalized_priorities.get("fill_rate", 0) +
                norm_cost * normalized_priorities.get("total_cost", 0) +
                norm_cohesion * normalized_priorities.get("cohesion_score", 0) +
                norm_cross * normalized_priorities.get("cross_leveling_score", 0)
            )

            if score > best_score:
                best_score = score
                best_solution = sol

        return best_solution
