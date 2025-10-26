"""
guided_workflow.py
------------------

Streamlined, prompt-based workflow for EMD Manning Dashboard.
Guides users through the entire process step-by-step.
"""

import streamlit as st
from enum import Enum
from typing import Optional, Callable


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
        progress = current_idx / (len(all_steps) - 1)

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
