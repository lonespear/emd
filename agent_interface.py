# agent_interface.py
import json
from emd_agent import ManningAgent
from exercise_builder import ExerciseBuilderConfig, ExerciseBuilder

class ExerciseAgentInterface:
    """
    Natural-language interface and orchestration layer for ManningAgent.
    """
    def __init__(self):
        self.last_summary = None
        self.last_config = None

    def run_mission(self, mission: str, n_soldiers: int, n_billets: int,
                    use_agentic: bool = True, target_fill: float = 0.95,
                    max_cost: float = 1e6, max_iters: int = 8, seed: int = 42):
        """
        Executes the mission under specified parameters.
        """
        if use_agentic:
            agent = ManningAgent(
                mission_name=mission,
                n_soldiers=n_soldiers,
                n_billets=n_billets,
                seed=seed
            )
            assignments, summary = agent.analyze_and_tune(
                target_fill=target_fill,
                max_cost=max_cost,
                max_iters=max_iters
            )
        else:
            cfg = ExerciseBuilderConfig(
                mission_name=mission,
                n_soldiers=n_soldiers,
                n_billets=n_billets,
                seed=seed,
                use_agent_loop=False
            )
            builder = ExerciseBuilder(cfg)
            out = builder.build()
            assignments, summary = out.assignments, out.summary

        self.last_summary = summary
        self.last_config = {
            "mission": mission, "soldiers": n_soldiers, "billets": n_billets,
            "use_agentic": use_agentic, "target_fill": target_fill,
            "max_cost": max_cost, "max_iters": max_iters, "seed": seed
        }
        return assignments, summary

    def reflect(self):
        """
        Summarize the last run in natural language for an LLM to interpret.
        """
        if not self.last_summary:
            return "No previous mission run."
        s = self.last_summary
        text = (
            f"Mission {s['mission']} achieved {s['fill_rate']:.1%} fill rate "
            f"across {s['total_billets']} billets with a total cost of "
            f"${s['total_cost']:,.0f}. Base distribution: {json.dumps(s['by_base_filled'])}."
        )
        if s["fill_rate"] < 0.9:
            text += " Fill rate below target; MOS penalties may be too strict."
        elif s["total_cost"] > 1e6:
            text += " Costs remain high; TDY weighting could be increased."
        else:
            text += " Mission parameters appear balanced."
        return text
