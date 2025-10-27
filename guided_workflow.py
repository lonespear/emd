"""
guided_workflow.py
------------------

Streamlined, prompt-based workflow for EMD Manning Dashboard.
Guides users through the entire process step-by-step.
"""

import streamlit as st
import json
import pandas as pd
from enum import Enum
from typing import Optional, Callable, Dict
from datetime import datetime


class WorkflowStep(Enum):
    """Steps in the guided workflow."""
    WELCOME = 0
    FORCE_GENERATION = 1
    QUALIFICATION_FILTER = 2
    MANNING_REQUIREMENTS = 3
    OPTIMIZATION_SETUP = 4
    RUN_OPTIMIZATION = 5
    REVIEW_RESULTS = 6
    COMPLETE = 7


class GuidedWorkflow:
    """Manages the guided workflow experience."""

    STEP_NAMES = {
        WorkflowStep.WELCOME: "Welcome",
        WorkflowStep.FORCE_GENERATION: "Generate Available Force",
        WorkflowStep.QUALIFICATION_FILTER: "Filter by Qualifications (Optional)",
        WorkflowStep.MANNING_REQUIREMENTS: "Define Requirements",
        WorkflowStep.OPTIMIZATION_SETUP: "Configure Optimization",
        WorkflowStep.RUN_OPTIMIZATION: "Run Optimization",
        WorkflowStep.REVIEW_RESULTS: "Review Results",
        WorkflowStep.COMPLETE: "Complete"
    }

    STEP_DESCRIPTIONS = {
        WorkflowStep.WELCOME: "Let's get started with your manning optimization",
        WorkflowStep.FORCE_GENERATION: "First, we need to create or upload your available soldiers",
        WorkflowStep.QUALIFICATION_FILTER: "Optionally filter soldiers by qualifications and experience",
        WorkflowStep.MANNING_REQUIREMENTS: "Tell us what capabilities you need for your mission",
        WorkflowStep.OPTIMIZATION_SETUP: "Configure how the optimization should prioritize objectives",
        WorkflowStep.RUN_OPTIMIZATION: "Run the optimization engine to find the best assignments",
        WorkflowStep.REVIEW_RESULTS: "Review your results and explore trade-offs",
        WorkflowStep.COMPLETE: "All done! You can export or start a new optimization"
    }

    @staticmethod
    def initialize():
        """Initialize workflow state."""
        if 'workflow_step' not in st.session_state:
            st.session_state.workflow_step = WorkflowStep.WELCOME
        if 'workflow_data' not in st.session_state:
            st.session_state.workflow_data = {}

    @staticmethod
    def get_current_step() -> WorkflowStep:
        """Get the current workflow step."""
        return st.session_state.workflow_step

    @staticmethod
    def set_step(step: WorkflowStep):
        """Set the current workflow step."""
        st.session_state.workflow_step = step

    @staticmethod
    def next_step():
        """Move to the next step in the workflow."""
        current = st.session_state.workflow_step
        all_steps = list(WorkflowStep)
        current_idx = all_steps.index(current)

        if current_idx < len(all_steps) - 1:
            st.session_state.workflow_step = all_steps[current_idx + 1]
            st.rerun()

    @staticmethod
    def previous_step():
        """Move to the previous step in the workflow."""
        current = st.session_state.workflow_step
        all_steps = list(WorkflowStep)
        current_idx = all_steps.index(current)

        if current_idx > 0:
            st.session_state.workflow_step = all_steps[current_idx - 1]
            st.rerun()

    @staticmethod
    def can_proceed() -> bool:
        """Check if user can proceed to next step based on current step requirements."""
        step = st.session_state.workflow_step

        if step == WorkflowStep.WELCOME:
            return True
        elif step == WorkflowStep.FORCE_GENERATION:
            # Need soldiers to proceed
            return st.session_state.get('soldiers_df') is not None
        elif step == WorkflowStep.QUALIFICATION_FILTER:
            # Optional step, can always proceed
            return True
        elif step == WorkflowStep.MANNING_REQUIREMENTS:
            # Need capabilities defined
            return st.session_state.get('capabilities') and len(st.session_state.capabilities) > 0
        elif step == WorkflowStep.OPTIMIZATION_SETUP:
            # Configuration is optional, can proceed
            return True
        elif step == WorkflowStep.RUN_OPTIMIZATION:
            # Need optimization results
            return st.session_state.get('assignments') is not None
        elif step == WorkflowStep.REVIEW_RESULTS:
            return True

        return True

    @staticmethod
    def render_progress_bar():
        """Render a progress bar showing workflow progress."""
        current = st.session_state.workflow_step
        all_steps = [s for s in WorkflowStep if s != WorkflowStep.COMPLETE]
        current_idx = all_steps.index(current) if current in all_steps else len(all_steps)

        # Clamp progress to [0.0, 1.0] range (COMPLETE step can cause > 1.0)
        progress = min(1.0, max(0.0, current_idx / (len(all_steps) - 1)))

        st.progress(progress)

        # Show step counter
        step_num = current_idx + 1
        total_steps = len(all_steps)
        st.caption(f"Step {step_num} of {total_steps}: {GuidedWorkflow.STEP_NAMES[current]}")

    @staticmethod
    def render_navigation():
        """Render navigation buttons at the bottom of the page."""
        st.markdown("---")

        col1, col2, col3 = st.columns([1, 2, 1])

        current = st.session_state.workflow_step
        all_steps = list(WorkflowStep)
        current_idx = all_steps.index(current)

        with col1:
            # Back button
            if current_idx > 0 and current != WorkflowStep.COMPLETE:
                if st.button("⬅️ Back", use_container_width=True):
                    GuidedWorkflow.previous_step()

        with col2:
            # Status message
            if not GuidedWorkflow.can_proceed() and current != WorkflowStep.COMPLETE:
                st.warning("⚠️ Complete the requirements above to continue")

        with col3:
            # Next/Continue button
            if current != WorkflowStep.COMPLETE:
                can_proceed = GuidedWorkflow.can_proceed()

                if current_idx < len(all_steps) - 1:
                    if st.button(
                        "Continue ➡️",
                        type="primary",
                        disabled=not can_proceed,
                        use_container_width=True
                    ):
                        GuidedWorkflow.next_step()

    @staticmethod
    def render_step_header():
        """Render the header for the current step."""
        current = st.session_state.workflow_step

        # Progress indicator
        GuidedWorkflow.render_progress_bar()

        # Step title and description
        st.markdown(f"## {GuidedWorkflow.STEP_NAMES[current]}")
        st.info(f"ℹ️ {GuidedWorkflow.STEP_DESCRIPTIONS[current]}")
        st.markdown("")

    @staticmethod
    def show_summary_card():
        """Show a summary card of what's been configured so far."""
        with st.sidebar:
            st.markdown("### 📋 Configuration Summary")

            # Force
            if st.session_state.get('soldiers_df') is not None:
                soldier_count = len(st.session_state.soldiers_df)
                st.success(f"✅ Force: {soldier_count:,} soldiers")
            else:
                st.warning("⚠️ No force generated")

            # Qualifications filtered
            if st.session_state.get('soldiers_ext') is not None:
                st.success("✅ Qualifications filtered")

            # Requirements
            if st.session_state.get('capabilities'):
                cap_count = len(st.session_state.capabilities)
                total_billets = sum(
                    cap.get('quantity', 1) * cap.get('team_size', 1)
                    for cap in st.session_state.capabilities
                )
                st.success(f"✅ Requirements: {cap_count} capabilities ({total_billets} billets)")
            else:
                st.warning("⚠️ No requirements defined")

            # Optimization results
            if st.session_state.get('assignments') is not None:
                st.success("✅ Optimization complete")
            else:
                st.warning("⚠️ Not yet optimized")

            st.markdown("---")

            # Theme toggle
            theme_label = "☀️ Classic View" if st.session_state.get('dark_mode', True) else "🌙 Dark Mode"
            if st.button(theme_label, use_container_width=True):
                st.session_state.dark_mode = not st.session_state.get('dark_mode', True)
                st.rerun()

            # Quick navigation
            if st.button("🏠 Start Over", use_container_width=True):
                # Clear workflow state
                st.session_state.workflow_step = WorkflowStep.WELCOME
                st.session_state.workflow_data = {}
                st.rerun()

            if st.button("⚙️ Advanced Mode", use_container_width=True):
                # Switch to classic mode
                st.session_state.guided_mode = False
                st.rerun()

            # Show save/load buttons
            GuidedWorkflow.show_save_load_buttons()

    @staticmethod
    def export_configuration() -> str:
        """
        Export current configuration to JSON string.

        Returns:
            JSON string containing all configuration data
        """
        config = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "force_config": {
                "force_size": len(st.session_state.soldiers_df) if st.session_state.get('soldiers_df') is not None else None,
                "has_force": st.session_state.get('soldiers_df') is not None
            },
            "capabilities": st.session_state.get('capabilities', []),
            "optimization_weights": st.session_state.workflow_data.get('weights', {}),
            "workflow_step": st.session_state.workflow_step.name if hasattr(st.session_state, 'workflow_step') else None,
            "template_used": st.session_state.workflow_data.get('template_used', None)
        }

        return json.dumps(config, indent=2)

    @staticmethod
    def import_configuration(config_json: str) -> bool:
        """
        Import configuration from JSON string.

        Args:
            config_json: JSON string containing configuration

        Returns:
            True if successful, False otherwise
        """
        try:
            config = json.loads(config_json)

            # Validate version
            if config.get("version") != "1.0":
                st.warning("⚠️ Configuration file version mismatch. Attempting to load anyway...")

            # Restore capabilities
            if "capabilities" in config and config["capabilities"]:
                st.session_state.capabilities = config["capabilities"]

            # Restore optimization weights
            if "optimization_weights" in config and config["optimization_weights"]:
                if 'workflow_data' not in st.session_state:
                    st.session_state.workflow_data = {}
                st.session_state.workflow_data['weights'] = config["optimization_weights"]

            # Restore template info
            if "template_used" in config:
                st.session_state.workflow_data['template_used'] = config["template_used"]

            # Restore workflow step
            if "workflow_step" in config and config["workflow_step"]:
                try:
                    st.session_state.workflow_step = WorkflowStep[config["workflow_step"]]
                except KeyError:
                    st.session_state.workflow_step = WorkflowStep.WELCOME

            return True

        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid configuration file: {e}")
            return False
        except Exception as e:
            st.error(f"❌ Error loading configuration: {e}")
            return False

    @staticmethod
    def load_template_configuration(template_dict: Dict):
        """
        Load a preset template into the workflow.

        Args:
            template_dict: Dictionary containing template data
        """
        # Clear existing state
        st.session_state.capabilities = []
        st.session_state.workflow_data = {}

        # Load capabilities from template
        if "capabilities" in template_dict:
            st.session_state.capabilities = template_dict["capabilities"]

        # Load optimization weights
        if "optimization_weights" in template_dict:
            st.session_state.workflow_data['weights'] = template_dict["optimization_weights"]

        # Store force generation params
        if "force_size" in template_dict:
            st.session_state.workflow_data['force_size'] = template_dict["force_size"]
        if "division_type" in template_dict:
            st.session_state.workflow_data['division_type'] = template_dict["division_type"]

        # Store location and duration
        if "location" in template_dict:
            st.session_state.workflow_data['location'] = template_dict["location"]
        if "duration_days" in template_dict:
            st.session_state.workflow_data['duration_days'] = template_dict["duration_days"]

        # Mark that a template was used
        st.session_state.workflow_data['template_used'] = template_dict.get("name", "Unknown")

    @staticmethod
    def show_save_load_buttons():
        """Show save and load configuration buttons in sidebar."""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 💾 Save/Load")

            # Export button
            if st.session_state.get('capabilities') or st.session_state.get('soldiers_df') is not None:
                config_json = GuidedWorkflow.export_configuration()
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                filename = f"emd_config_{timestamp}.json"

                st.download_button(
                    label="💾 Save Configuration",
                    data=config_json,
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True,
                    help="Download current configuration as a JSON file"
                )

            # Import button
            uploaded_config = st.file_uploader(
                "📁 Load Configuration",
                type=["json"],
                help="Upload a previously saved configuration file",
                label_visibility="collapsed"
            )

            if uploaded_config is not None:
                config_json = uploaded_config.read().decode("utf-8")
                if GuidedWorkflow.import_configuration(config_json):
                    st.success("✅ Configuration loaded!")
                    st.rerun()
