import streamlit as st
import pandas as pd
from exercise_builder import ExerciseBuilder, ExerciseBuilderConfig
from emd_agent import ManningAgent  # <— add this import

st.set_page_config(page_title="USINDOPACOM Exercise Builder", layout="wide")

st.title("🪖 1st MDTF Exercise Builder")
st.markdown("Simulate manpower allocation across INDOPACOM mission templates.")

# Sidebar – Configuration
st.sidebar.header("Configuration")
mission = st.sidebar.selectbox(
    "Mission Template",
    ["ArcticEdge", "ValiantShield", "OrientShield", "TalismanSabre"]
)
n_soldiers = st.sidebar.slider("Number of Soldiers", 100, 4000, 800, step=50)
n_billets = st.sidebar.slider("Number of Billets", 10, 1000, 75, step=5)
use_agent_loop = st.sidebar.checkbox("Use Agentic Loop (ManningAgent)", value=False)
seed = st.sidebar.number_input("Random Seed", min_value=0, value=42, step=1)

# Progress bar placeholders
progress = st.progress(0)
status_text = st.empty()

def progress_callback(ratio, fill, cost):
    """Callback for live agentic progress updates."""
    progress.progress(int(ratio * 100))
    status_text.text(f"Iteration {int(ratio * 10)} | Fill={fill:.2%} | Cost=${cost:,.0f}")

# Run Simulation
if st.sidebar.button("🚀 Run Simulation"):
    if use_agent_loop:
        # --- Use ManningAgent directly ---
        agent = ManningAgent(
            mission_name=mission,
            n_soldiers=n_soldiers,
            n_billets=n_billets,
            seed=seed
        )
        assignments, summary = agent.analyze_and_tune(
            target_fill=0.95,
            max_cost=1e6,
            max_iters=8,
            callback=progress_callback
        )
        out = type("Result", (), {"assignments": assignments, "summary": summary})
    else:
        # --- Use standard builder path ---
        cfg = ExerciseBuilderConfig(
            mission_name=mission,
            n_soldiers=n_soldiers,
            n_billets=n_billets,
            seed=seed,
            use_agent_loop=use_agent_loop
        )
        builder = ExerciseBuilder(cfg)
        out = builder.build()

    st.success(f"✅ Simulation complete for {mission}")
    st.metric("Fill Rate", f"{out.summary.get('fill_rate', 0):.2%}")
    st.metric("Total Cost ($)", f"{out.summary.get('total_cost', 0):,.0f}")

    # Snapshot
    st.subheader("📊 Readiness Snapshot")
    snapshot = (
        out.assignments.groupby(["billet_base", "billet_priority"])
        .agg({"pair_cost": "mean"})
        .reset_index()
        .rename(columns={"pair_cost": "avg_cost"})
    )
    st.dataframe(snapshot)

    # Visualizations
    st.subheader("🪶 MOS Composition by Base")
    chart_data = (
        out.assignments.groupby(["billet_base", "soldier_mos"])["soldier_id"]
        .count()
        .reset_index()
        .pivot(index="billet_base", columns="soldier_mos", values="soldier_id")
        .fillna(0)
    )
    st.bar_chart(chart_data)

    # Downloads
    st.subheader("📦 Export Results")
    st.download_button(
        "Download Assignments CSV",
        out.assignments.to_csv(index=False).encode(),
        "assignments.csv"
    )
    st.download_button(
        "Download Summary JSON",
        pd.DataFrame([out.summary]).to_json(indent=2).encode(),
        "summary.json"
    )
else:
    st.info("👈 Configure options in the sidebar, then click **Run Simulation**.")
