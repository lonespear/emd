"""
dashboard.py
------------

Interactive web dashboard for EMD manning system using Streamlit.

Run with: streamlit run dashboard.py

Features:
- Upload MTOE-based soldier data
- Configure exercise requirements
- Run optimization with parameter tuning
- Visualize results and trade-offs
- Export assignments and orders
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Map visualization
try:
    import folium
    from streamlit_folium import st_folium
    MAPS_AVAILABLE = True
except ImportError:
    MAPS_AVAILABLE = False
    print("Warning: folium/streamlit-folium not available. Install with: pip install folium streamlit-folium")

# EMD imports
from mtoe_generator import quick_generate_force, UnitGenerator
from manning_document import (
    ManningDocument, CapabilityRequirement,
    ManningDocumentBuilder, create_custom_manning_document
)
from readiness_tracker import StandardProfiles, ReadinessAnalyzer, filter_ready_soldiers
from task_organizer import TaskOrganizer
from emd_agent import EMD
from pareto_optimizer import ParetoOptimizer, TradeOffAnalyzer
from deployment_tracker import OPTEMPOTracker, AvailabilityAnalyzer

# Qualification system imports
try:
    from qualifications import QualificationFilter, FilterCriterion, FilterGroup
    from qualifications import BilletRequirementTemplates, create_basic_requirements
    QUALIFICATION_FEATURES_AVAILABLE = True
except ImportError:
    QUALIFICATION_FEATURES_AVAILABLE = False
    print("Warning: Qualification features not available")

# Geographic optimization imports
try:
    from geolocation import LocationDatabase, DistanceCalculator, TravelCostEstimator
    from advanced_profiles import ProfileRegistry, StandardCONUSProfiles, AORProfiles
    GEOGRAPHIC_AVAILABLE = True
except ImportError:
    GEOGRAPHIC_AVAILABLE = False
    print("Warning: Geographic optimization modules not available")


# Page configuration
st.set_page_config(
    page_title="EMD Manning Dashboard",
    page_icon="🎖️",
    layout="wide"
)


def generate_pareto_executive_summary(pareto_front):
    """
    Generate an AI-powered executive summary explaining Pareto trade-offs.

    Uses intelligent analysis to:
    - Identify key decision points
    - Explain trade-offs in plain language
    - Provide recommendations based on different priorities
    - Highlight extreme solutions (best/worst for each objective)
    """
    if not pareto_front:
        return "No Pareto solutions available."

    # Analyze the Pareto frontier
    fill_rates = [s.fill_rate for s in pareto_front]
    costs = [s.total_cost for s in pareto_front]
    cohesions = [s.cohesion_score for s in pareto_front]
    cross_levs = [s.cross_leveling_score for s in pareto_front]

    # Check if there's actual variation (edge case: all solutions identical)
    fill_variation = max(fill_rates) - min(fill_rates)
    cost_variation = max(costs) - min(costs)
    cohesion_variation = max(cohesions) - min(cohesions)
    cross_lev_variation = max(cross_levs) - min(cross_levs)

    total_variation = fill_variation + cost_variation + cohesion_variation + cross_lev_variation

    # If all solutions are essentially identical, return simplified summary
    if len(pareto_front) < 3 or total_variation < 0.01:
        solution = pareto_front[0]
        return f"""
# Pareto Optimization Analysis

## Key Finding: Dominant Solution Identified

Analysis of {len(pareto_front)} solution(s) reveals **no meaningful trade-offs** - all tested policy configurations converged to the same optimal solution.

### Solution Metrics:
- **Fill Rate:** {solution.fill_rate:.1%}
- **Total Cost:** ${solution.total_cost:,.0f}
- **Unit Cohesion:** {solution.cohesion_score:.1f}
- **Cross-Leveling:** {solution.cross_leveling_score:.1f}

---

## What This Means

### ✅ Good News
This is actually a **good outcome** - it means there's a clear "best" solution that dominates across all objectives. No difficult trade-offs required.

### 📊 Interpretation

**Fill Rate ({solution.fill_rate:.1%}):**
- {'✅ Excellent - All positions filled' if solution.fill_rate >= 0.95 else '⚠️ Review - Some gaps exist'}

**Unit Cohesion ({solution.cohesion_score:.0f}):**
- {'⚠️ Low cohesion - Personnel are cross-leveled from many units' if solution.cohesion_score < 30 else '✅ Good cohesion - Teams kept together' if solution.cohesion_score > 60 else '📊 Moderate cohesion'}
- {'This is normal for exercises requiring diverse capabilities from multiple units' if solution.cohesion_score < 30 else ''}

**Cross-Leveling Score ({solution.cross_leveling_score:.0f}):**
- {'⚠️ High complexity - Sourcing from many units (coordination required)' if solution.cross_leveling_score > 50 else '✅ Low complexity - Sourcing from few units'}

---

## Recommended Actions

1. **Accept this solution** - No better alternatives exist in tested policy space
2. **Review cohesion score** - {
'Consider if cross-unit sourcing aligns with exercise objectives' if solution.cohesion_score < 30
else 'Good team integrity maintained'}
3. **Validate assignments** - Review detailed assignment list for any concerns
4. **Proceed with orders** - {'Begin FRAGO/WARNO process' if solution.fill_rate >= 0.95 else 'Address gaps before proceeding'}

---

## Why No Trade-offs?

Possible reasons:
- **Abundant qualified personnel** - Enough soldiers available to fill all requirements optimally
- **Well-aligned requirements** - Capabilities match available force structure
- **Narrow policy range** - Tested parameters didn't create meaningful variation

### Want to explore trade-offs?

Try adjusting these in the Pareto Analysis page:
- **Increase MOS mismatch penalties** (force harder matching choices)
- **Increase cohesion bonus** (test cost of keeping teams together)
- **Reduce available force** (create scarcity to force trade-offs)

---

*When true trade-offs exist, this report will show multiple distinct solutions with different strengths. In this case, the optimization has a clear winner.*
"""

    # Find extreme solutions
    best_fill = max(pareto_front, key=lambda s: s.fill_rate)
    best_cost = min(pareto_front, key=lambda s: s.total_cost)
    best_cohesion = max(pareto_front, key=lambda s: s.cohesion_score)
    best_cross_lev = min(pareto_front, key=lambda s: s.cross_leveling_score)

    # Find balanced solution (closest to center of objectives when normalized)
    def normalized_distance(sol):
        norm_fill = (sol.fill_rate - min(fill_rates)) / (max(fill_rates) - min(fill_rates) + 0.001)
        norm_cost = 1 - ((sol.total_cost - min(costs)) / (max(costs) - min(costs) + 0.001))
        norm_cohesion = (sol.cohesion_score - min(cohesions)) / (max(cohesions) - min(cohesions) + 0.001)
        norm_cross = 1 - ((sol.cross_leveling_score - min(cross_levs)) / (max(cross_levs) - min(cross_levs) + 0.001))

        # Distance from ideal (1,1,1,1)
        return abs(1 - norm_fill) + abs(1 - norm_cost) + abs(1 - norm_cohesion) + abs(1 - norm_cross)

    balanced = min(pareto_front, key=normalized_distance)

    # Generate markdown summary
    summary = f"""
# Pareto Optimization Decision Brief

## Executive Summary

Analysis of **{len(pareto_front)} Pareto-optimal solutions** reveals distinct trade-offs between fill rate, cost, unit cohesion, and cross-leveling complexity.

### Key Findings:

**Fill Rate Range:** {min(fill_rates):.1%} - {max(fill_rates):.1%}
**Cost Range:** ${min(costs):,.0f} - ${max(costs):,.0f}
**Cohesion Range:** {min(cohesions):.1f} - {max(cohesions):.1f}
**Cross-Leveling Range:** {min(cross_levs):.1f} - {max(cross_levs):.1f}

---

## Recommended Solutions by Priority

### 1. Maximum Fill Priority (Mission-Essential Staffing)
**Solution #{best_fill.solution_id}** - Best for critical exercises requiring maximum personnel

- **Fill Rate:** {best_fill.fill_rate:.1%} ✅ HIGHEST
- **Total Cost:** ${best_fill.total_cost:,.0f}
- **Unit Cohesion:** {best_fill.cohesion_score:.1f}
- **Cross-Leveling:** {best_fill.cross_leveling_score:.1f}

**Use Case:** Critical combat exercises, high-visibility operations, or situations where gaps cannot be tolerated.

**Trade-off:** Achieving maximum fill typically requires {"higher costs and more cross-unit sourcing" if best_fill.total_cost > balanced.total_cost else "acceptable costs"}.

---

### 2. Cost-Optimized Solution (Budget-Conscious)
**Solution #{best_cost.solution_id}** - Best for resource-constrained planning

- **Fill Rate:** {best_cost.fill_rate:.1%}
- **Total Cost:** ${best_cost.total_cost:,.0f} 💰 LOWEST
- **Unit Cohesion:** {best_cost.cohesion_score:.1f}
- **Cross-Leveling:** {best_cost.cross_leveling_score:.1f}

**Use Case:** Training exercises, non-critical taskings, or situations with strict budget limits.

**Trade-off:** Lower costs come with {"reduced fill rate" if best_cost.fill_rate < balanced.fill_rate else "acceptable fill"} ({(balanced.fill_rate - best_cost.fill_rate):.1%} gap).

**Savings:** ${(best_fill.total_cost - best_cost.total_cost):,.0f} vs maximum fill solution.

---

### 3. Unit Cohesion Priority (Team Integrity)
**Solution #{best_cohesion.solution_id}** - Best for maintaining team effectiveness

- **Fill Rate:** {best_cohesion.fill_rate:.1%}
- **Total Cost:** ${best_cohesion.total_cost:,.0f}
- **Unit Cohesion:** {best_cohesion.cohesion_score:.1f} 🤝 HIGHEST
- **Cross-Leveling:** {best_cohesion.cross_leveling_score:.1f}

**Use Case:** Combat operations requiring trained teams, first deployments for new units, high-risk exercises.

**Trade-off:** Keeping teams together {"costs more" if best_cohesion.total_cost > best_cost.total_cost else "is cost-effective"} but ensures pre-existing leader-subordinate relationships.

---

### 4. Balanced Solution (Recommended Default)
**Solution #{balanced.solution_id}** - Best overall compromise

- **Fill Rate:** {balanced.fill_rate:.1%}
- **Total Cost:** ${balanced.total_cost:,.0f}
- **Unit Cohesion:** {balanced.cohesion_score:.1f}
- **Cross-Leveling:** {balanced.cross_leveling_score:.1f}

**Use Case:** Most exercises and taskings where no single objective dominates.

**Rationale:** This solution represents a balanced trade-off across all objectives, avoiding extreme sacrifices in any area.

---

## Decision Matrix

| Scenario | Recommended Solution | Priority Rationale |
|----------|---------------------|-------------------|
| **Combat Deployment** | Solution #{best_cohesion.solution_id} (Cohesion) | Team integrity critical for combat effectiveness |
| **CONUS Training** | Solution #{best_cost.solution_id} (Cost) | Lower stakes, budget-conscious |
| **High-Visibility Exercise** | Solution #{best_fill.solution_id} (Fill) | Optics matter, can't have visible gaps |
| **Standard Pacific Exercise** | Solution #{balanced.solution_id} (Balanced) | Typical trade-offs apply |

---

## Trade-off Analysis

### Fill vs Cost
- **Correlation:** {"Negative" if max(fill_rates) - min(fill_rates) > 0.05 else "Weak"} - Higher fill generally requires higher TDY costs
- **Marginal Cost:** Approximately ${(max(costs) - min(costs)) / (max(fill_rates) - min(fill_rates) + 0.001):,.0f} per percentage point of fill rate

### Cohesion vs Cross-Leveling
- Maintaining high cohesion (keeping teams together) naturally reduces cross-leveling complexity
- Solutions #{best_cohesion.solution_id} demonstrates {best_cohesion.cohesion_score:.0f}% cohesion by sourcing from fewer units

---

## Commander's Decision Points

1. **What is the mission priority?**
   - Mission-essential → Choose Solution #{best_fill.solution_id}
   - Training value → Choose Solution #{best_cohesion.solution_id}
   - Budget-driven → Choose Solution #{best_cost.solution_id}

2. **Can we accept gaps?**
   - No gaps tolerable → Must use Solution #{best_fill.solution_id} (fill: {best_fill.fill_rate:.1%})
   - <5% gaps acceptable → Solutions #{balanced.solution_id} or #{best_cost.solution_id} viable

3. **Budget authority available?**
   - Limited funds (< ${min(costs) + (max(costs)-min(costs))/2:,.0f}) → Solutions #{best_cost.solution_id}-#{balanced.solution_id}
   - Full funding → All solutions viable

---

## Recommended Action

**Default Recommendation:** Solution #{balanced.solution_id} (Balanced)

This solution provides {balanced.fill_rate:.1%} fill at ${balanced.total_cost:,.0f} cost while maintaining {balanced.cohesion_score:.1f} cohesion score.

**Next Steps:**
1. Review detailed assignments for Solution #{balanced.solution_id}
2. Validate key leadership positions are filled
3. Confirm TDY costs are within budget authority
4. Brief commander on trade-offs if deviating from balanced solution

---

*This decision brief was generated automatically by analyzing the Pareto frontier. All {len(pareto_front)} solutions shown are Pareto-optimal (no solution is strictly better on all objectives).*
"""

    return summary


# ====================
# GEOGRAPHIC ANALYSIS HELPERS
# ====================

def create_geographic_map(assignments, exercise_location):
    """
    Create interactive folium map showing exercise location and source bases.

    Args:
        assignments: DataFrame with assignment results (must have soldier_base column)
        exercise_location: str - name of exercise location

    Returns:
        folium.Map object
    """
    if not MAPS_AVAILABLE or not GEOGRAPHIC_AVAILABLE:
        return None

    db = LocationDatabase()
    exercise_loc = db.get(exercise_location)

    if exercise_loc is None:
        return None

    # Create map centered on exercise location
    m = folium.Map(
        location=[exercise_loc.lat, exercise_loc.lon],
        zoom_start=4,
        tiles='OpenStreetMap'
    )

    # AOR color mapping
    aor_colors = {
        "NORTHCOM": "#0066CC",      # Blue
        "INDOPACOM": "#CC0000",     # Red
        "EUCOM": "#009900",         # Green
        "AFRICOM": "#FFCC00",       # Yellow
        "CENTCOM": "#9900CC",       # Purple
        "SOUTHCOM": "#FF6600"       # Orange
    }

    # Add exercise location marker (large red star)
    folium.Marker(
        location=[exercise_loc.lat, exercise_loc.lon],
        popup=f"<b>EXERCISE LOCATION</b><br>{exercise_location}<br>AOR: {exercise_loc.aor}",
        tooltip=f"⭐ {exercise_location}",
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(m)

    # Get source bases and soldier counts
    if "soldier_base" in assignments.columns:
        base_counts = assignments["soldier_base"].value_counts().to_dict()
    else:
        base_counts = {}

    # Add source base markers with flight paths
    for base_name, count in base_counts.items():
        base_loc = db.get(base_name)
        if base_loc is None:
            continue

        # Calculate distance and cost
        distance = DistanceCalculator.calculate(base_loc, exercise_loc, db)
        is_oconus = (base_loc.country != exercise_loc.country) or (exercise_loc.country != "US")
        travel_cost = TravelCostEstimator.estimate_travel_cost(distance, 14, is_oconus)
        total_cost = travel_cost * count

        # Determine marker size and color based on count and cost
        marker_size = min(max(count, 5), 20)

        # Color by cost tier
        if travel_cost < 2500:
            marker_color = 'green'
        elif travel_cost < 4000:
            marker_color = 'orange'
        else:
            marker_color = 'darkred'

        # Add base marker
        folium.CircleMarker(
            location=[base_loc.lat, base_loc.lon],
            radius=marker_size,
            popup=f"""<b>{base_name}</b><br>
                     Soldiers: {count}<br>
                     Distance: {distance:.0f} mi<br>
                     Cost/soldier: ${travel_cost:,.0f}<br>
                     Total cost: ${total_cost:,.0f}<br>
                     AOR: {base_loc.aor}""",
            tooltip=f"🏢 {base_name} ({count} soldiers)",
            color=aor_colors.get(base_loc.aor, 'gray'),
            fill=True,
            fillColor=marker_color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)

        # Add flight path line
        folium.PolyLine(
            locations=[
                [base_loc.lat, base_loc.lon],
                [exercise_loc.lat, exercise_loc.lon]
            ],
            color=marker_color,
            weight=2,
            opacity=0.6,
            popup=f"{base_name} → {exercise_location}<br>{distance:.0f} mi"
        ).add_to(m)

    # Add legend
    legend_html = f'''
    <div style="position: fixed;
                bottom: 50px; right: 50px; width: 180px; height: auto;
                background-color: white; z-index:9999; font-size:12px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
    <p style="margin:0; font-weight:bold;">AOR Colors</p>
    <p style="margin:2px; color:#0066CC;">● NORTHCOM</p>
    <p style="margin:2px; color:#CC0000;">● INDOPACOM</p>
    <p style="margin:2px; color:#009900;">● EUCOM</p>
    <p style="margin:2px; color:#FFCC00;">● AFRICOM</p>
    <p style="margin:2px; color:#9900CC;">● CENTCOM</p>
    <p style="margin:2px; color:#FF6600;">● SOUTHCOM</p>
    <hr style="margin:5px 0;">
    <p style="margin:0; font-weight:bold;">Cost Tier</p>
    <p style="margin:2px; color:green;">● Low (&lt;$2.5k)</p>
    <p style="margin:2px; color:orange;">● Medium ($2.5-4k)</p>
    <p style="margin:2px; color:darkred;">● High (&gt;$4k)</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


def calculate_geographic_metrics(assignments, exercise_location):
    """
    Calculate comprehensive geographic metrics for the assignment.

    Returns:
        dict with travel costs, distances, and sourcing statistics
    """
    if not GEOGRAPHIC_AVAILABLE:
        return None

    db = LocationDatabase()
    exercise_loc = db.get(exercise_location)

    if exercise_loc is None or "soldier_base" not in assignments.columns:
        return None

    # Calculate per-soldier metrics
    metrics = []
    for _, row in assignments.iterrows():
        base_name = row["soldier_base"]
        base_loc = db.get(base_name)

        if base_loc is None:
            continue

        distance = DistanceCalculator.calculate(base_loc, exercise_loc, db)
        is_oconus = (base_loc.country != exercise_loc.country) or (exercise_loc.country != "US")
        travel_cost = TravelCostEstimator.estimate_travel_cost(distance, 14, is_oconus)

        # Determine cost tier
        if distance < 500:
            tier = "Ground (<500 mi)"
        elif distance < 3000:
            tier = "Domestic Flight (500-3000 mi)"
        else:
            tier = "International (>3000 mi)"

        metrics.append({
            "base": base_name,
            "distance": distance,
            "cost": travel_cost,
            "tier": tier,
            "is_oconus": is_oconus,
            "aor": base_loc.aor
        })

    metrics_df = pd.DataFrame(metrics)

    # Aggregate statistics
    result = {
        "total_cost": metrics_df["cost"].sum(),
        "avg_cost": metrics_df["cost"].mean(),
        "min_cost": metrics_df["cost"].min(),
        "max_cost": metrics_df["cost"].max(),
        "avg_distance": metrics_df["distance"].mean(),
        "min_distance": metrics_df["distance"].min(),
        "max_distance": metrics_df["distance"].max(),
        "total_soldiers": len(metrics_df),
        "cost_by_tier": metrics_df.groupby("tier")["cost"].sum().to_dict(),
        "soldiers_by_tier": metrics_df.groupby("tier").size().to_dict(),
        "by_base": metrics_df.groupby("base").agg({
            "distance": "first",
            "cost": ["count", "sum", "mean"]
        }).round(0),
        "metrics_df": metrics_df
    }

    return result


def show_geographic_analysis(assignments, exercise_location):
    """
    Display comprehensive geographic analysis section with error handling.
    """
    try:
        # Check if geographic features are available
        if not GEOGRAPHIC_AVAILABLE:
            st.warning("⚠️ Geographic analysis not available. Install geographic modules:")
            st.code("pip install folium streamlit-folium", language="bash")
            st.info("The system will continue with standard analysis.")
            return

        # Validate inputs
        if assignments is None or len(assignments) == 0:
            st.info("📊 No assignments to analyze. Please run optimization first.")
            return

        if not exercise_location:
            st.warning("⚠️ Exercise location not specified. Please select a location in the Manning Document page.")
            return

        st.markdown("---")
        st.subheader("🌍 Geographic & Travel Analysis")

        # Calculate metrics with error handling
        try:
            geo_metrics = calculate_geographic_metrics(assignments, exercise_location)
        except Exception as metrics_error:
            st.error(f"❌ Error calculating geographic metrics: {metrics_error}")
            st.info("Showing partial analysis...")
            geo_metrics = None

        if geo_metrics is None:
            st.info("📍 Geographic data not available for this assignment. This may be due to:")
            st.markdown("""
            - Missing location data for some soldiers
            - Exercise location not in database
            - No geographic penalties applied during optimization
            """)
            return

        # Top-level metrics with error handling
        try:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Travel Cost",
                    f"${geo_metrics['total_cost']:,.0f}",
                    help="Total estimated travel cost for all assigned soldiers"
                )

            with col2:
                st.metric(
                    "Avg Cost/Soldier",
                    f"${geo_metrics['avg_cost']:,.0f}",
                    delta=f"Range: ${geo_metrics['min_cost']:.0f}-${geo_metrics['max_cost']:.0f}"
                )

            with col3:
                st.metric(
                    "Avg Distance",
                    f"{geo_metrics['avg_distance']:,.0f} mi",
                    delta=f"Range: {geo_metrics['min_distance']:.0f}-{geo_metrics['max_distance']:.0f} mi"
                )

            with col4:
                # Calculate potential savings vs worst case
                worst_case_cost = geo_metrics['max_cost'] * geo_metrics['total_soldiers']
                savings = worst_case_cost - geo_metrics['total_cost']
                savings_pct = (savings / worst_case_cost) * 100 if worst_case_cost > 0 else 0
                st.metric(
                    "Cost Optimization",
                    f"{savings_pct:.0f}% saved",
                    delta=f"${savings:,.0f} vs worst case",
                    help="Savings compared to sourcing all soldiers from farthest base"
                )
        except Exception as metric_error:
            st.error(f"Error displaying metrics: {metric_error}")

        # Interactive map with error handling
        if MAPS_AVAILABLE:
            try:
                st.markdown("#### Interactive Sourcing Map")
                geo_map = create_geographic_map(assignments, exercise_location)
                if geo_map:
                    st_folium(geo_map, width=1200, height=500)
                else:
                    st.info("🗺️ Map not available for selected location.")
            except Exception as map_error:
                st.warning(f"⚠️ Could not generate map: {map_error}")
                st.info("Geographic analysis will continue without the map.")

        # Travel cost breakdown with error handling
        try:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Cost by Distance Tier")
                tier_data = pd.DataFrame({
                    "Tier": list(geo_metrics["cost_by_tier"].keys()),
                    "Total Cost": list(geo_metrics["cost_by_tier"].values()),
                    "Soldiers": [geo_metrics["soldiers_by_tier"].get(tier, 0) for tier in geo_metrics["cost_by_tier"].keys()]
                })

                fig = px.pie(
                    tier_data,
                    values="Total Cost",
                    names="Tier",
                    title="Travel Cost Distribution",
                    color_discrete_sequence=px.colors.sequential.RdYlGn_r
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("#### Distance Distribution")
                fig2 = px.histogram(
                    geo_metrics["metrics_df"],
                    x="distance",
                    nbins=20,
                    title="Soldier Distribution by Distance",
                    labels={"distance": "Distance (miles)", "count": "# Soldiers"},
                    color_discrete_sequence=["#0066CC"]
                )
                st.plotly_chart(fig2, use_container_width=True)
        except Exception as viz_error:
            st.warning(f"⚠️ Error creating visualizations: {viz_error}")

        # Sourcing by base table with error handling
        try:
            st.markdown("#### Sourcing Analysis by Base")

            base_stats = geo_metrics["by_base"].copy()
            base_stats.columns = ["Distance (mi)", "# Soldiers", "Total Cost", "Avg Cost/Soldier"]
            base_stats = base_stats.sort_values("Total Cost", ascending=False)

            # Add cost efficiency score (lower is better)
            base_stats["Cost Efficiency"] = (base_stats["Avg Cost/Soldier"] / geo_metrics["avg_cost"] * 100).round(0).astype(int)
            base_stats["Rating"] = base_stats["Cost Efficiency"].apply(
                lambda x: "🟢 Excellent" if x < 90 else "🟡 Good" if x < 110 else "🔴 Expensive"
            )

            st.dataframe(base_stats, use_container_width=True)
        except Exception as table_error:
            st.warning(f"⚠️ Error creating sourcing table: {table_error}")

        # Recommendations with error handling
        try:
            st.markdown("#### 💡 Sourcing Recommendations")

            # Find most cost-effective base
            best_base = base_stats["Avg Cost/Soldier"].idxmin()
            best_cost = base_stats.loc[best_base, "Avg Cost/Soldier"]
            best_count = int(base_stats.loc[best_base, "# Soldiers"])

            # Find most expensive base
            worst_base = base_stats["Avg Cost/Soldier"].idxmax()
            worst_cost = base_stats.loc[worst_base, "Avg Cost/Soldier"]
            worst_count = int(base_stats.loc[worst_base, "# Soldiers"])

            col1, col2 = st.columns(2)

            with col1:
                st.success(f"""
                **Most Cost-Effective: {best_base}**
                - {best_count} soldiers at ${best_cost:,.0f}/soldier
                - {base_stats.loc[best_base, 'Distance (mi)']:.0f} miles from {exercise_location}
                - Consider prioritizing this base for future sourcing
                """)

            with col2:
                if worst_cost > best_cost * 1.2:  # Only show if significantly more expensive
                    st.warning(f"""
                    **Most Expensive: {worst_base}**
                    - {worst_count} soldiers at ${worst_cost:,.0f}/soldier
                    - {base_stats.loc[worst_base, 'Distance (mi)']:.0f} miles from {exercise_location}
                    - {((worst_cost - best_cost) / best_cost * 100):.0f}% more expensive than {best_base}
                    """)
                else:
                    st.info("All bases are within reasonable cost range of each other.")
        except Exception as rec_error:
            st.info(f"💡 Could not generate recommendations: {rec_error}")

    except Exception as e:
        st.error(f"❌ Error in geographic analysis: {e}")
        st.info("Geographic analysis unavailable. Please check error logs or try again.")
        import logging
        logging.getLogger("dashboard").error(f"Geographic analysis error: {e}", exc_info=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'generator' not in st.session_state:
        st.session_state.generator = None
    if 'soldiers_df' not in st.session_state:
        st.session_state.soldiers_df = None
    if 'soldiers_ext' not in st.session_state:
        st.session_state.soldiers_ext = None
    if 'assignments' not in st.session_state:
        st.session_state.assignments = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'pareto_solutions' not in st.session_state:
        st.session_state.pareto_solutions = None


def main():
    initialize_session_state()

    st.title("🎖️ EMD Manning Dashboard")
    st.markdown("**Enlisted Manpower Distribution - Interactive Planning Tool**")

    # Sidebar navigation
    pages = ["🏠 Home", "👥 Force Generation", "📋 Manning Document", "⚙️ Optimization", "📊 Analysis", "📈 Pareto Trade-offs"]

    # Add qualification filtering if available
    if QUALIFICATION_FEATURES_AVAILABLE:
        pages.insert(3, "🎯 Qualification Filtering")

    page = st.sidebar.radio("Navigation", pages)

    if page == "🏠 Home":
        show_home()
    elif page == "👥 Force Generation":
        show_force_generation()
    elif page == "🎯 Qualification Filtering":
        show_qualification_filtering()
    elif page == "📋 Manning Document":
        show_manning_document()
    elif page == "⚙️ Optimization":
        show_optimization()
    elif page == "📊 Analysis":
        show_analysis()
    elif page == "📈 Pareto Trade-offs":
        show_pareto_tradeoffs()


def show_home():
    """Home page with overview and quick start."""
    st.header("Welcome to EMD Manning Dashboard")

    feature_list = """
    This dashboard helps you plan and optimize military manning assignments.

    ### Features:
    - ✅ **MTOE-Based Force Generation** - Create realistic units
    - ✅ **Capability-Based Tasking** - Define requirements by capability
    - ✅ **Readiness Validation** - Check training gates and deployment history
    - ✅ **Unit Cohesion** - Prefer keeping teams together
    - ✅ **Multi-Objective Optimization** - Explore fill vs cost trade-offs
    - ✅ **OPTEMPO Tracking** - Account for deployment windows"""

    if QUALIFICATION_FEATURES_AVAILABLE:
        feature_list += """
    - ✅ **Qualification Filtering** - Filter soldiers by badges, skills, and experience
    - ✅ **Advanced Matching** - Match soldiers to billets based on 30+ qualification criteria"""

    feature_list += """

    ### Quick Start:
    1. **Force Generation** → Create your force from MTOE templates"""

    if QUALIFICATION_FEATURES_AVAILABLE:
        feature_list += """
    2. **Qualification Filtering** → Search and filter soldiers by qualifications"""

    feature_list += """
    2. **Manning Document** → Define exercise requirements
    3. **Optimization** → Run assignment algorithm
    4. **Analysis** → Review results and sourcing
    5. **Pareto Trade-offs** → Explore alternative solutions

    Use the sidebar to navigate between sections.
    """

    st.markdown(feature_list)

    # Quick stats if data loaded
    if st.session_state.soldiers_df is not None:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Soldiers", f"{len(st.session_state.soldiers_df):,}")
        with col2:
            st.metric("Units", f"{len(st.session_state.generator.units)}")
        with col3:
            if st.session_state.assignments is not None:
                st.metric("Assignments Made", f"{len(st.session_state.assignments)}")


def show_force_generation():
    """Force generation page."""
    st.header("👥 Force Generation")

    st.markdown("""
    Generate a realistic force structure from MTOE templates.
    Choose the number of battalions, companies, and manning level.
    """)

    # Configuration
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        n_battalions = st.number_input("Number of Battalions", min_value=1, max_value=5, value=2)

    with col2:
        companies_per_bn = st.number_input("Companies per Battalion", min_value=2, max_value=6, value=4)

    with col3:
        fill_rate = st.slider("Manning Level (%)", min_value=70, max_value=100, value=93) / 100

    with col4:
        seed = st.number_input("Random Seed", min_value=1, max_value=999, value=42)

    if st.button("🏗️ Generate Force", type="primary"):
        with st.spinner("Generating force structure..."):
            generator, soldiers_df, soldiers_ext = quick_generate_force(
                n_battalions=n_battalions,
                companies_per_bn=companies_per_bn,
                seed=seed,
                fill_rate=fill_rate
            )

            st.session_state.generator = generator
            st.session_state.soldiers_df = soldiers_df
            st.session_state.soldiers_ext = soldiers_ext

            st.success(f"✅ Generated {len(generator.units)} units with {len(soldiers_df):,} soldiers!")

    # Display results
    if st.session_state.generator is not None:
        st.subheader("Force Structure")

        # Unit breakdown
        unit_data = []
        for uic, unit in st.session_state.generator.units.items():
            unit_data.append({
                "Unit": unit.short_name,
                "Type": unit.unit_type,
                "Authorized": unit.authorized_strength,
                "Assigned": unit.assigned_strength,
                "Fill Rate": f"{unit.get_fill_rate():.1%}",
                "Location": unit.home_station
            })

        df = pd.DataFrame(unit_data)
        st.dataframe(df, use_container_width=True)

        # Visualization
        fig = px.bar(
            df,
            x="Unit",
            y=["Authorized", "Assigned"],
            title="Unit Manning Levels",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)


def show_qualification_filtering():
    """Qualification filtering and soldier search page."""
    st.header("🎯 Qualification Filtering & Search")

    if not QUALIFICATION_FEATURES_AVAILABLE:
        st.error("❌ Qualification features not available. Please ensure qualification_filter.py is present.")
        return

    if st.session_state.soldiers_df is None:
        st.warning("⚠️ Please generate a force first (Force Generation page)")
        return

    st.markdown("""
    Filter and search for soldiers based on qualifications, experience, and readiness criteria.
    Use preset filters for common use cases or build custom filters.
    """)

    # Initialize filter
    qf = QualificationFilter(st.session_state.soldiers_df)

    # Tabs for different filter modes
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Preset Filters", "🛠️ Custom Filters", "📊 Statistics", "🔎 Advanced Search"])

    with tab1:
        st.subheader("Preset Filters")
        st.markdown("Quick access to common soldier qualification filters")

        col1, col2 = st.columns(2)

        with col1:
            selected_preset = st.selectbox(
                "Select Preset Filter",
                qf.list_available_presets(),
                format_func=lambda x: x.replace("_", " ").title()
            )

            if st.button("🔍 Apply Preset Filter", type="primary"):
                with st.spinner(f"Applying {selected_preset} filter..."):
                    filtered = qf.apply_preset(selected_preset)
                    st.session_state.filtered_soldiers = filtered
                    st.success(f"✅ Found {len(filtered)} soldiers matching '{selected_preset}'")

            # Show preset description
            desc = qf.get_preset_description(selected_preset)
            st.info(f"**Description:** {desc}")

        with col2:
            # Quick stats for all presets
            st.markdown("**Filter Results Preview:**")
            preset_stats = {}
            for preset_name in qf.list_available_presets():
                result = qf.apply_preset(preset_name)
                preset_stats[preset_name.replace("_", " ").title()] = len(result)

            stats_df = pd.DataFrame(list(preset_stats.items()), columns=["Filter", "Matches"])
            stats_df = stats_df.sort_values("Matches", ascending=False)

            fig = px.bar(
                stats_df,
                x="Filter",
                y="Matches",
                title="Soldiers by Preset Filter",
                color="Matches",
                color_continuous_scale="Blues"
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Build Custom Filter")
        st.markdown("Create your own filter criteria")

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Rank & MOS**")
            filter_ranks = st.multiselect(
                "Ranks",
                ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9"],
                default=[]
            )
            filter_mos = st.multiselect(
                "MOS",
                sorted(st.session_state.soldiers_df["mos"].unique().tolist()),
                default=[]
            )

        with col2:
            st.markdown("**Fitness & Readiness**")
            min_acft = st.slider("Min ACFT Score", 0, 600, 450)
            deployable_only = st.checkbox("Deployable Only", value=False)
            min_dwell = st.slider("Min Dwell (months)", 0, 36, 0)

        with col3:
            st.markdown("**Qualifications**")
            require_airborne = st.checkbox("Airborne Qualified")
            require_ranger = st.checkbox("Ranger Qualified")
            require_combat = st.checkbox("Combat Experience")
            min_deployments = st.slider("Min Deployments", 0, 5, 0)

        if st.button("🔍 Apply Custom Filter", type="primary"):
            with st.spinner("Filtering soldiers..."):
                # Start with all soldiers
                result = st.session_state.soldiers_df.copy()
                temp_qf = QualificationFilter(result)

                # Apply filters progressively
                if filter_ranks:
                    result = temp_qf.filter_by_rank(filter_ranks)
                    temp_qf = QualificationFilter(result)

                if filter_mos:
                    result = temp_qf.filter_by_mos(filter_mos)
                    temp_qf = QualificationFilter(result)

                if min_acft > 0:
                    result = temp_qf.filter_by_acft_score(min_acft)
                    temp_qf = QualificationFilter(result)

                if deployable_only:
                    result = temp_qf.filter_deployable()
                    temp_qf = QualificationFilter(result)

                if min_dwell > 0:
                    result = temp_qf.filter_by_dwell(min_dwell)
                    temp_qf = QualificationFilter(result)

                if require_airborne:
                    result = temp_qf.filter_by_badge("AIRBORNE")
                    temp_qf = QualificationFilter(result)

                if require_ranger:
                    result = temp_qf.filter_by_badge("RANGER")
                    temp_qf = QualificationFilter(result)

                if require_combat:
                    result = temp_qf.filter_combat_veterans()
                    temp_qf = QualificationFilter(result)

                if min_deployments > 0:
                    result = temp_qf.filter_by_deployment_count(min_deployments)
                    temp_qf = QualificationFilter(result)

                st.session_state.filtered_soldiers = result
                st.success(f"✅ Found {len(result)} soldiers matching your criteria")

    with tab3:
        st.subheader("Filter Statistics & Analysis")

        if 'filtered_soldiers' in st.session_state and len(st.session_state.filtered_soldiers) > 0:
            filtered = st.session_state.filtered_soldiers
            stats = qf.get_filter_statistics(filtered)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Soldiers", stats['total_soldiers'])
            with col2:
                st.metric("Filtered Count", stats['filtered_count'])
            with col3:
                st.metric("Filter Rate", f"{stats['filter_rate']*100:.1f}%")
            with col4:
                if stats.get('avg_acft'):
                    st.metric("Avg ACFT", f"{stats['avg_acft']:.0f}")

            # Detailed statistics
            if stats['filtered_count'] > 0:
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Readiness Metrics:**")
                    st.write(f"- Deployable: {stats.get('deployable_pct', 0)*100:.1f}%")
                    st.write(f"- Avg Dwell: {stats.get('avg_dwell', 0):.1f} months")
                    st.write(f"- Avg TIS: {stats.get('avg_tis', 0):.1f} months")

                with col2:
                    st.markdown("**Top Ranks:**")
                    if stats.get('ranks'):
                        for rank, count in list(stats['ranks'].items())[:5]:
                            st.write(f"- {rank}: {count} soldiers")

                # Rank distribution chart
                if stats.get('ranks'):
                    fig = px.pie(
                        names=list(stats['ranks'].keys()),
                        values=list(stats['ranks'].values()),
                        title="Rank Distribution in Filtered Set"
                    )
                    st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("📊 Apply a filter to see statistics")

    with tab4:
        st.subheader("Advanced Search")

        search_type = st.radio(
            "Search Type",
            ["Soldier ID", "Qualification Text"]
        )

        if search_type == "Soldier ID":
            soldier_id = st.text_input("Enter Soldier ID")
            if st.button("🔎 Search"):
                if soldier_id:
                    result = qf.search_by_soldier_id(int(soldier_id))
                    st.session_state.filtered_soldiers = result
                    if len(result) > 0:
                        st.success(f"✅ Found soldier {soldier_id}")
                    else:
                        st.warning(f"⚠️ No soldier found with ID {soldier_id}")
        else:
            search_text = st.text_input("Search for qualification text (e.g., 'CIB', 'Ranger', 'Airborne')")
            if st.button("🔎 Search"):
                if search_text:
                    result = qf.search_qualification_text(search_text)
                    st.session_state.filtered_soldiers = result
                    st.success(f"✅ Found {len(result)} soldiers with '{search_text}'")

    # Display filtered results
    if 'filtered_soldiers' in st.session_state and len(st.session_state.filtered_soldiers) > 0:
        st.markdown("---")
        st.subheader("📋 Filtered Results")

        filtered = st.session_state.filtered_soldiers

        # Display controls
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**Showing {len(filtered)} soldiers**")

        with col2:
            csv = filtered.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                data=csv,
                file_name="filtered_soldiers.csv",
                mime="text/csv"
            )

        # Display table
        display_cols = ["soldier_id", "rank", "MOS", "acft_score", "deployable",
                       "months_since_deployment", "airborne", "ranger"]
        available_cols = [col for col in display_cols if col in filtered.columns]

        st.dataframe(
            filtered[available_cols].head(100),
            use_container_width=True,
            height=400
        )

        if len(filtered) > 100:
            st.info(f"Showing first 100 of {len(filtered)} results. Download CSV for full list.")


def show_manning_document():
    """Manning document creation page."""
    st.header("📋 Manning Document")

    if st.session_state.soldiers_df is None:
        st.warning("⚠️ Please generate a force first (Force Generation page)")
        return

    st.markdown("Define exercise requirements by capability.")

    # Exercise info
    col1, col2 = st.columns(2)
    with col1:
        exercise_name = st.text_input("Exercise Name", "Valiant Shield 2025")
    with col2:
        # Get all available locations from database
        if GEOGRAPHIC_AVAILABLE:
            db = LocationDatabase()
            all_locations = sorted(db.locations.keys())
            # Prioritize common locations
            common_locs = ["NTC", "JRTC", "JBLM", "Fort Bragg", "Camp Humphreys", "Guam", "Grafenwoehr", "Djibouti"]
            location_options = common_locs + [loc for loc in all_locations if loc not in common_locs]
        else:
            location_options = ["Guam", "Japan", "Hawaii", "Korea", "JBLM", "Philippines", "Australia"]

        location = st.selectbox("Exercise Location", location_options, help="Select from 56 military installations worldwide")

    # Store location in session state for auto-profile selection
    if 'exercise_location' not in st.session_state or st.session_state.exercise_location != location:
        st.session_state.exercise_location = location

    # Show location info and preview map
    if GEOGRAPHIC_AVAILABLE:
        db = LocationDatabase()
        loc_info = db.get(location)
        if loc_info:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**AOR:** {loc_info.aor}")
            with col2:
                st.info(f"**Country:** {loc_info.country}")
            with col3:
                is_oconus = loc_info.country != "US"
                st.info(f"**Type:** {'OCONUS' if is_oconus else 'CONUS'}")

            # Show recommended profile
            if GEOGRAPHIC_AVAILABLE:
                if location == "NTC":
                    recommended_profile = "NTC Rotation (30 days)"
                elif location == "JRTC":
                    recommended_profile = "JRTC Rotation (21 days)"
                elif loc_info.aor == "INDOPACOM" and is_oconus:
                    recommended_profile = "INDOPACOM Exercise (14 days)"
                elif loc_info.aor == "EUCOM" and is_oconus:
                    recommended_profile = "EUCOM Exercise (21 days)"
                elif loc_info.aor == "AFRICOM":
                    recommended_profile = "AFRICOM Exercise (14 days)"
                elif loc_info.aor == "CENTCOM":
                    recommended_profile = "CENTCOM Deployment (270 days)"
                elif is_oconus:
                    recommended_profile = "OCONUS Training"
                else:
                    recommended_profile = "CONUS Training"

                st.success(f"📋 **Recommended Profile:** {recommended_profile}")

    st.subheader("Add Capabilities")

    # Add capability form
    with st.form("add_capability"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cap_name = st.text_input("Capability Name", "Infantry Squad")
        with col2:
            mos = st.selectbox("MOS", ["11B", "13F", "68W", "35F", "12B", "88M"])
        with col3:
            rank = st.selectbox("Leader Rank", ["E-5", "E-6", "E-7", "E-8", "O-1", "O-2", "O-3"])
        with col4:
            quantity = st.number_input("Quantity", min_value=1, max_value=20, value=3)

        col5, col6, col7 = st.columns(3)
        with col5:
            team_size = st.number_input("Team Size", min_value=1, max_value=50, value=9)
        with col6:
            priority = st.selectbox("Priority", [1, 2, 3], index=2)
        with col7:
            keep_together = st.checkbox("Keep Team Together", value=True)

        submitted = st.form_submit_button("Add Capability")

        if submitted:
            if 'capabilities' not in st.session_state:
                st.session_state.capabilities = []

            st.session_state.capabilities.append({
                "name": cap_name,
                "mos": mos,
                "rank": rank,
                "quantity": quantity,
                "team_size": team_size,
                "priority": priority
            })

            st.success(f"✅ Added {quantity}x {cap_name}")

    # Show current capabilities
    if 'capabilities' in st.session_state and st.session_state.capabilities:
        st.subheader("Current Requirements")
        caps_df = pd.DataFrame(st.session_state.capabilities)
        caps_df["total_billets"] = caps_df["quantity"] * caps_df["team_size"]
        st.dataframe(caps_df, use_container_width=True)

        st.metric("Total Billets Required", f"{caps_df['total_billets'].sum()}")


def show_optimization():
    """Optimization execution page."""
    st.header("⚙️ Run Optimization")

    if st.session_state.soldiers_df is None:
        st.warning("⚠️ Please generate a force first")
        return

    if 'capabilities' not in st.session_state or not st.session_state.capabilities:
        st.warning("⚠️ Please create manning document first")
        return

    # Readiness profile - auto-selected based on exercise location
    st.subheader("Readiness Profile")

    location = st.session_state.get('exercise_location', 'JBLM')

    # Use advanced profiles if available
    if GEOGRAPHIC_AVAILABLE:
        all_profiles = ProfileRegistry.get_all_profiles()
        profile_options = list(all_profiles.keys())

        # Auto-select profile based on location
        if location == "NTC":
            default_profile = "NTC Rotation"
        elif location == "JRTC":
            default_profile = "JRTC Rotation"
        elif GEOGRAPHIC_AVAILABLE:
            db = LocationDatabase()
            loc_info = db.get(location)
            if loc_info:
                if loc_info.aor == "INDOPACOM" and loc_info.country != "US":
                    default_profile = "INDOPACOM Exercise"
                elif loc_info.aor == "EUCOM" and loc_info.country != "US":
                    default_profile = "EUCOM Exercise"
                elif loc_info.aor == "AFRICOM":
                    default_profile = "AFRICOM Exercise"
                elif loc_info.aor == "CENTCOM":
                    default_profile = "CENTCOM Deployment"
                elif loc_info.country != "US":
                    default_profile = "TDY Exercise"
                else:
                    default_profile = "Home Station Exercise"
            else:
                default_profile = profile_options[0]
        else:
            default_profile = profile_options[0]

        default_index = profile_options.index(default_profile) if default_profile in profile_options else 0

        profile_choice = st.selectbox(
            "Select Readiness Profile (auto-selected based on location)",
            profile_options,
            index=default_index,
            help="Advanced profiles include location-specific training requirements and exercise durations"
        )

        profile = all_profiles[profile_choice]

        # Show profile details
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Duration:** {profile.typical_duration_days} days")
        with col2:
            st.info(f"**AOR:** {profile.aor}")
        with col3:
            st.info(f"**Training Gates:** {len(profile.required_training)}")

        st.caption(f"📍 Location: {location} → Primary Location: {profile.primary_location}")

    else:
        # Fallback to standard profiles
        conus_locations = ["JBLM", "Fort Bragg", "Fort Campbell", "Fort Hood"]
        pacific_locations = ["Guam", "Japan", "Hawaii", "Korea", "Philippines", "Australia"]

        if location in conus_locations:
            default_profile = "CONUS Training"
        elif location in pacific_locations:
            default_profile = "Pacific Exercise"
        else:
            default_profile = "OCONUS Training"

        profile_options = ["CONUS Training", "OCONUS Training", "Combat Deployment", "Pacific Exercise"]
        default_index = profile_options.index(default_profile)

        profile_choice = st.selectbox(
            "Select Profile (auto-selected based on location)",
            profile_options,
            index=default_index
        )

        profile_map = {
            "CONUS Training": StandardProfiles.conus_training(),
            "OCONUS Training": StandardProfiles.oconus_training(),
            "Combat Deployment": StandardProfiles.combat_deployment(),
            "Pacific Exercise": StandardProfiles.pacific_exercise()
        }
        profile = profile_map[profile_choice]

        st.info(f"📍 Location: {location} → 📋 Profile: {profile_choice} → Required training: {', '.join(profile.required_training)}")

    # Policy tuning
    st.subheader("Policy Tuning (Advanced)")
    with st.expander("Adjust Policy Parameters"):
        st.markdown("**Core Policies**")
        col1, col2 = st.columns(2)

        with col1:
            mos_penalty = st.slider("MOS Mismatch Penalty", 500, 5000, 3000, step=500)
            cohesion_bonus = st.slider("Unit Cohesion Bonus", -1000, 0, -500, step=100)

        with col2:
            tdy_weight = st.slider("TDY Cost Weight", 0.5, 2.0, 1.0, step=0.1)
            readiness_penalty = st.slider("Readiness Failure Penalty", 1000, 5000, 2000, step=500)

        # Geographic policies (if available)
        if GEOGRAPHIC_AVAILABLE:
            st.markdown("---")
            st.markdown("**🌍 Geographic Optimization Policies**")
            col3, col4 = st.columns(2)

            with col3:
                geo_cost_weight = st.slider(
                    "Geographic Cost Weight",
                    0.0, 2.0, 1.0, step=0.1,
                    help="Multiplier for travel costs in optimization (0=ignore, 1=normal, 2=heavily weight)"
                )
                same_theater_bonus = st.slider(
                    "Same Theater Bonus",
                    -500, 0, -300, step=50,
                    help="Bonus for soldiers already in destination AOR (negative = bonus)"
                )

            with col4:
                lead_time_penalty = st.slider(
                    "OCONUS Lead Time Penalty",
                    0, 1000, 500, step=100,
                    help="Additional penalty for OCONUS coordination complexity"
                )
                distance_penalty = st.slider(
                    "Distance Penalty (per 1000 mi)",
                    0, 200, 100, step=20,
                    help="Additional penalty per 1000 miles beyond base travel cost"
                )
        else:
            geo_cost_weight = 1.0
            same_theater_bonus = -300
            lead_time_penalty = 500
            distance_penalty = 100

    # Run optimization
    if st.button("🚀 Run Optimization", type="primary"):
        with st.spinner("Running optimization..."):
            # Create manning document
            manning_doc = create_custom_manning_document(
                exercise_name="Dashboard Exercise",
                capabilities=st.session_state.capabilities,
                location="Guam"
            )

            # Convert to billets
            billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)

            # Convert advanced profile to base ReadinessProfile if needed
            if GEOGRAPHIC_AVAILABLE and hasattr(profile, 'to_readiness_profile'):
                filter_profile = profile.to_readiness_profile()
                emd_profile = profile  # Keep advanced profile for EMD
            else:
                filter_profile = profile
                emd_profile = profile

            # Filter ready soldiers
            ready_soldiers = filter_ready_soldiers(
                st.session_state.soldiers_df,
                st.session_state.soldiers_ext,
                filter_profile
            )

            # Create task organizer
            task_organizer = TaskOrganizer(
                st.session_state.generator.units,
                ready_soldiers,
                st.session_state.soldiers_ext
            )

            # Initialize EMD
            emd = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
            emd.soldiers_ext = st.session_state.soldiers_ext
            emd.task_organizer = task_organizer
            emd.readiness_profile = emd_profile

            # Set exercise location for geographic optimization
            if GEOGRAPHIC_AVAILABLE:
                emd.exercise_location = location

            # Apply policy tuning
            emd.tune_policy(
                mos_mismatch_penalty=mos_penalty,
                unit_cohesion_bonus=cohesion_bonus,
                TDY_cost_weight=tdy_weight,
                readiness_failure_penalty=readiness_penalty
            )

            # Apply geographic policies
            if GEOGRAPHIC_AVAILABLE:
                emd.policies["geographic_cost_weight"] = geo_cost_weight
                emd.policies["same_theater_bonus"] = same_theater_bonus
                emd.policies["lead_time_penalty_oconus"] = lead_time_penalty
                emd.policies["distance_penalty_per_1000mi"] = distance_penalty

            # Run
            assignments, summary = emd.assign()

            st.session_state.assignments = assignments
            st.session_state.summary = summary

            st.success("✅ Optimization complete!")

    # Show results
    if st.session_state.summary is not None:
        st.subheader("Results")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Fill Rate", f"{st.session_state.summary['fill_rate']:.1%}")
        with col2:
            st.metric("Total Cost", f"${st.session_state.summary['total_cost']:,.0f}")
        with col3:
            st.metric("Billets Filled", f"{st.session_state.summary['filled_billets']}/{st.session_state.summary['total_billets']}")
        with col4:
            avg_cost = st.session_state.summary['total_cost'] / st.session_state.summary['filled_billets']
            st.metric("Avg Cost/Soldier", f"${avg_cost:,.0f}")


def show_analysis():
    """Results analysis page - Leader-focused decision support."""
    st.header("📊 Assignment Analysis & Decision Brief")

    if st.session_state.assignments is None:
        st.warning("⚠️ Please run optimization first")
        return

    assignments = st.session_state.assignments
    summary = st.session_state.summary

    # ====================
    # EXECUTIVE SUMMARY
    # ====================
    st.subheader("📋 Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        fill_pct = summary.get("fill_rate", 0)
        st.metric(
            "Fill Rate",
            f"{fill_pct:.1%}",
            delta="GOOD" if fill_pct >= 0.95 else "REVIEW" if fill_pct >= 0.85 else "CRITICAL",
            delta_color="normal" if fill_pct >= 0.95 else "off"
        )

    with col2:
        total_cost = summary.get("total_cost", 0)
        st.metric(
            "Total Cost",
            f"${total_cost:,.0f}",
            help="Includes TDY, mismatch penalties, and cross-leveling costs"
        )

    with col3:
        filled = summary.get("filled", 0)
        required = summary.get("total_billets", filled)
        st.metric(
            "Positions Filled",
            f"{filled} / {required}",
            delta=f"{required - filled} gaps" if filled < required else "COMPLETE"
        )

    with col4:
        if "uic" in assignments.columns:
            units_sourced = assignments["uic"].nunique()
            st.metric(
                "Units Sourced",
                units_sourced,
                help="Number of units providing personnel"
            )

    # Status assessment
    st.markdown("---")

    if fill_pct >= 0.95:
        st.success("✅ **STATUS: MISSION CAPABLE** - All critical positions filled. Recommend approval.")
    elif fill_pct >= 0.85:
        st.warning("⚠️ **STATUS: MARGINAL** - Some gaps exist. Review critical positions below.")
    else:
        st.error("❌ **STATUS: NOT MISSION CAPABLE** - Significant gaps. Recommend re-planning or additional sourcing.")

    # ====================
    # CRITICAL GAPS
    # ====================
    if fill_pct < 1.0:
        st.subheader("🚨 Critical Gaps & Risks")

        if "capability_name" in assignments.columns:
            # Identify unfilled capabilities
            required_caps = st.session_state.get('capabilities', [])
            filled_caps = assignments.groupby("capability_name")["billet_id"].count().to_dict()

            gaps = []
            for cap in required_caps:
                cap_name = cap["name"]
                required = cap["quantity"] * cap["team_size"]
                filled = filled_caps.get(cap_name, 0)

                if filled < required:
                    gap_pct = (required - filled) / required
                    gaps.append({
                        "Capability": cap_name,
                        "Required": required,
                        "Filled": filled,
                        "Gap": required - filled,
                        "Gap %": f"{gap_pct:.1%}",
                        "Risk": "🔴 HIGH" if gap_pct > 0.15 else "🟡 MEDIUM" if gap_pct > 0.05 else "🟢 LOW"
                    })

            if gaps:
                gaps_df = pd.DataFrame(gaps).sort_values("Gap", ascending=False)
                st.dataframe(gaps_df, use_container_width=True)

                st.markdown("**Recommended Actions:**")
                for idx, gap in enumerate(gaps[:3]):  # Top 3 gaps
                    st.markdown(f"{idx+1}. **{gap['Capability']}**: Source {gap['Gap']} additional personnel or reduce requirement")
            else:
                st.info("No capability-level gaps identified.")

    # ====================
    # SOURCING BREAKDOWN
    # ====================
    st.markdown("---")
    st.subheader("🏢 Sourcing by Unit")

    if "uic" in assignments.columns:
        sourcing = assignments.groupby("uic").agg({
            "soldier_id": "count",
            "pair_cost": ["mean", "sum"]
        }).round(0)
        sourcing.columns = ["Soldiers Sourced", "Avg Cost per Soldier", "Total Unit Cost"]
        sourcing = sourcing.sort_values("Soldiers Sourced", ascending=False)

        # Add unit names if available
        if st.session_state.generator:
            unit_names = []
            for uic in sourcing.index:
                unit = st.session_state.generator.units.get(uic)
                unit_names.append(unit.short_name if unit else uic)
            sourcing.insert(0, "Unit Name", unit_names)

        st.dataframe(sourcing, use_container_width=True)

        # Plain language summary
        top_unit_uic = sourcing.index[0]
        top_unit_count = int(sourcing.iloc[0]["Soldiers Sourced"])
        total_sourced = int(sourcing["Soldiers Sourced"].sum())
        top_unit_pct = (top_unit_count / total_sourced) * 100

        if st.session_state.generator:
            top_unit_name = st.session_state.generator.units.get(top_unit_uic).short_name
        else:
            top_unit_name = top_unit_uic

        st.info(f"📊 **Primary Source:** {top_unit_name} provides {top_unit_count} soldiers ({top_unit_pct:.0f}% of total). "
                f"{'This indicates good unit cohesion.' if top_unit_pct > 50 else 'Personnel are cross-leveled from multiple units.'}")

        # Visualization
        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                assignments,
                names="uic",
                title="Soldiers by Source Unit",
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.bar(
                sourcing.reset_index(),
                x="uic",
                y="Total Unit Cost",
                title="Cost by Source Unit",
                color="Total Unit Cost",
                color_continuous_scale="Reds"
            )
            fig2.update_layout(showlegend=False, xaxis_title="Unit", yaxis_title="Cost ($)")
            st.plotly_chart(fig2, use_container_width=True)

    # ====================
    # CAPABILITY ANALYSIS
    # ====================
    st.markdown("---")
    st.subheader("🎯 Capability Fill Status")

    if "capability_name" in assignments.columns:
        by_cap = assignments.groupby("capability_name").agg({
            "billet_id": "count",
            "pair_cost": ["mean", "sum"]
        }).round(0)
        by_cap.columns = ["Positions Filled", "Avg Cost", "Total Cost"]

        # Add required count and fill %
        if 'capabilities' in st.session_state:
            required_dict = {}
            for cap in st.session_state.capabilities:
                required_dict[cap["name"]] = cap["quantity"] * cap["team_size"]

            by_cap.insert(0, "Required", by_cap.index.map(required_dict))
            by_cap["Fill %"] = (by_cap["Positions Filled"] / by_cap["Required"] * 100).round(1).astype(str) + "%"
            by_cap["Status"] = by_cap["Positions Filled"].div(by_cap["Required"]).apply(
                lambda x: "✅ Complete" if x >= 0.95 else "⚠️ Partial" if x >= 0.80 else "❌ Critical"
            )

        st.dataframe(by_cap, use_container_width=True)

        # Visualization
        fig = px.bar(
            by_cap.reset_index(),
            x="capability_name",
            y=["Required", "Positions Filled"],
            title="Required vs Filled by Capability",
            barmode="group",
            color_discrete_map={"Required": "lightblue", "Positions Filled": "darkblue"}
        )
        fig.update_layout(xaxis_title="Capability", yaxis_title="Positions")
        st.plotly_chart(fig, use_container_width=True)

    # ====================
    # COST ANALYSIS
    # ====================
    st.markdown("---")
    st.subheader("💰 Cost Analysis")

    # Cost breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Cost Statistics:**")
        avg_cost = assignments["pair_cost"].mean()
        median_cost = assignments["pair_cost"].median()
        max_cost = assignments["pair_cost"].max()

        st.metric("Average Cost per Assignment", f"${avg_cost:,.0f}")
        st.metric("Median Cost", f"${median_cost:,.0f}")
        st.metric("Highest Single Assignment", f"${max_cost:,.0f}")

        # Interpretation
        if avg_cost < 2000:
            st.success("✅ Low average cost indicates good soldier-to-billet matching")
        elif avg_cost < 4000:
            st.info("📊 Moderate costs - typical for cross-unit sourcing")
        else:
            st.warning("⚠️ High average costs suggest significant mismatches or penalties")

    with col2:
        # Cost histogram with annotations
        fig = px.histogram(
            assignments,
            x="pair_cost",
            nbins=30,
            title="Assignment Cost Distribution",
            labels={"pair_cost": "Cost per Assignment ($)", "count": "Number of Assignments"},
            color_discrete_sequence=["steelblue"]
        )
        fig.add_vline(x=avg_cost, line_dash="dash", line_color="red",
                      annotation_text=f"Avg: ${avg_cost:,.0f}")
        st.plotly_chart(fig, use_container_width=True)

    # ====================
    # QUALIFICATION MATCH ANALYSIS
    # ====================
    if QUALIFICATION_FEATURES_AVAILABLE:
        st.markdown("---")
        st.subheader("🎯 Qualification Match Analysis")

        try:
            # Check if we have extended profile data
            has_extended = any(col in assignments.columns for col in ['education_level', 'badges_required_json'])

            if has_extended:
                st.markdown("**Qualification matching was applied during optimization**")

                col1, col2 = st.columns(2)

                with col1:
                    # Calculate match quality metrics
                    if 'match_quality' in st.session_state.summary:
                        match_quality = st.session_state.summary['match_quality']
                        st.metric("Perfect Matches", f"{match_quality.get('perfect', 0)}")
                        st.metric("Good Matches", f"{match_quality.get('good', 0)}")
                        st.metric("Acceptable Matches", f"{match_quality.get('acceptable', 0)}")
                        st.metric("Poor Matches", f"{match_quality.get('poor', 0)}")

                    # Show qualification penalty impact
                    if 'qual_penalty_avg' in st.session_state.summary:
                        qual_penalty = st.session_state.summary['qual_penalty_avg']
                        st.metric("Avg Qualification Penalty", f"${qual_penalty:,.0f}")

                with col2:
                    # Top qualification mismatches
                    st.markdown("**Top Qualification Requirements:**")

                    if 'top_requirements' in st.session_state.summary:
                        for req in st.session_state.summary['top_requirements'][:5]:
                            st.write(f"- {req}")
                    else:
                        st.info("Detailed qualification matching was used to optimize assignments")

                # Qualification insights
                st.markdown("**Qualification Insights:**")
                qual_insights = []

                if 'qual_penalty_avg' in st.session_state.summary:
                    qual_penalty = st.session_state.summary['qual_penalty_avg']
                    if qual_penalty < 500:
                        qual_insights.append("✅ Excellent qualification matching - soldiers well-suited to billets")
                    elif qual_penalty < 1500:
                        qual_insights.append("📊 Good qualification matching - minor gaps present")
                    else:
                        qual_insights.append("⚠️ Some qualification mismatches - review assignments for critical requirements")

                if qual_insights:
                    for insight in qual_insights:
                        st.markdown(f"- {insight}")
                else:
                    st.info("✓ Qualification penalties were considered in cost optimization")

            else:
                st.info("💡 Enable extended profiles to see detailed qualification matching analysis")

        except Exception as e:
            st.warning(f"⚠️ Could not generate qualification analysis: {e}")

    # ====================
    # KEY INSIGHTS
    # ====================
    st.markdown("---")
    st.subheader("🔍 Key Insights & Recommendations")

    insights = []

    # Fill rate insights
    if fill_pct >= 0.95:
        insights.append("✅ **High fill rate achieved** - Exercise can proceed with minimal gaps")
    elif fill_pct < 0.85:
        insights.append("❌ **Low fill rate** - Recommend expanding sourcing pool or reducing requirements")

    # Cost insights
    cost_per_soldier = total_cost / filled if filled > 0 else 0
    if cost_per_soldier > 5000:
        insights.append(f"⚠️ **High cost per soldier** (${cost_per_soldier:,.0f}) - Consider adjusting MOS mismatch penalties")

    # Cross-leveling insights
    if "uic" in assignments.columns:
        if units_sourced > 5:
            insights.append(f"⚠️ **High cross-leveling** - Sourcing from {units_sourced} units may complicate coordination")
        elif units_sourced <= 2:
            insights.append(f"✅ **Good unit cohesion** - Most personnel from {units_sourced} unit(s)")

    # Capability-specific insights
    if "capability_name" in assignments.columns and 'capabilities' in st.session_state:
        critical_caps = [cap for cap in st.session_state.capabilities if cap.get("priority", 3) == 1]
        if critical_caps:
            for cap in critical_caps[:2]:  # Top 2 critical capabilities
                cap_name = cap["name"]
                required = cap["quantity"] * cap["team_size"]
                filled = filled_caps.get(cap_name, 0)
                if filled >= required:
                    insights.append(f"✅ **{cap_name}** (Priority 1) - Fully staffed")
                else:
                    insights.append(f"🚨 **{cap_name}** (Priority 1) - Gap of {required - filled} soldiers")

    for insight in insights:
        st.markdown(f"- {insight}")

    # ====================
    # RECOMMENDED ACTIONS
    # ====================
    st.markdown("---")
    st.subheader("📝 Recommended Actions")

    actions = []

    if fill_pct < 1.0:
        actions.append("1. **Review unfilled positions** and determine if they can be left vacant or require backfill")

    if units_sourced > 5:
        actions.append(f"2. **Coordinate with {units_sourced} source units** for personnel release and administrative actions")

    if cost_per_soldier > 4000:
        actions.append("3. **Budget approval required** - Obtain funding authority for estimated TDY costs")

    if fill_pct >= 0.95:
        actions.append("1. **Initiate orders process** - Begin drafting FRAGOs/WARNORDs for sourced units")
        actions.append("2. **Validate training currency** - Ensure assigned soldiers meet all readiness gates")

    actions.append(f"{len(actions) + 1}. **Download assignment list** (below) and distribute to source units for confirmation")

    for action in actions:
        st.markdown(action)

    # ====================
    # DOWNLOAD RESULTS
    # ====================
    st.markdown("---")
    st.subheader("📥 Export Results")

    col1, col2 = st.columns(2)

    with col1:
        csv = assignments.to_csv(index=False)
        st.download_button(
            label="📥 Download Assignments (CSV)",
            data=csv,
            file_name="emd_assignments.csv",
            mime="text/csv",
            help="Detailed assignment list for unit coordination"
        )

    with col2:
        # Generate summary report
        report = f"""# Manning Assignment Summary Report

## Exercise Details
- **Fill Rate:** {fill_pct:.1%}
- **Total Cost:** ${total_cost:,.0f}
- **Positions Filled:** {filled} / {required}
- **Units Sourced:** {units_sourced if 'uic' in assignments.columns else 'N/A'}

## Status
{insights[0] if insights else 'Analysis complete'}

## Recommended Actions
{chr(10).join(actions)}

## Key Metrics
- Average cost per assignment: ${avg_cost:,.0f}
- Primary source unit: {top_unit_name if 'uic' in assignments.columns else 'N/A'}

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
"""
        st.download_button(
            label="📄 Download Executive Summary",
            data=report,
            file_name="manning_summary.md",
            mime="text/markdown",
            help="Plain-language summary for leadership"
        )

    # ====================
    # GEOGRAPHIC ANALYSIS
    # ====================
    # Add geographic analysis if exercise location is available
    if GEOGRAPHIC_AVAILABLE and 'exercise_location' in st.session_state:
        show_geographic_analysis(assignments, st.session_state.exercise_location)


def show_pareto_tradeoffs():
    """Pareto optimization page."""
    st.header("📈 Pareto Trade-off Analysis")

    if st.session_state.soldiers_df is None:
        st.warning("⚠️ Please generate a force and manning document first")
        return

    st.markdown("""
    Explore trade-offs between competing objectives:
    - **Fill Rate** (maximize)
    - **Total Cost** (minimize)
    - **Unit Cohesion** (maximize)
    - **Cross-Leveling** (minimize)
    """)

    if st.button("🔬 Run Pareto Analysis"):
        with st.spinner("Exploring policy space... This may take a few minutes"):
            # Setup (similar to optimization page)
            manning_doc = create_custom_manning_document(
                "Pareto Analysis",
                st.session_state.capabilities,
                "Guam"
            )
            billets_df = ManningDocumentBuilder.generate_billets_from_document(manning_doc)
            profile = StandardProfiles.pacific_exercise()
            ready_soldiers = filter_ready_soldiers(
                st.session_state.soldiers_df,
                st.session_state.soldiers_ext,
                profile
            )
            task_organizer = TaskOrganizer(
                st.session_state.generator.units,
                ready_soldiers,
                st.session_state.soldiers_ext
            )

            emd = EMD(soldiers_df=ready_soldiers, billets_df=billets_df, seed=42)
            emd.soldiers_ext = st.session_state.soldiers_ext
            emd.task_organizer = task_organizer
            emd.readiness_profile = profile

            # Run Pareto optimization
            optimizer = ParetoOptimizer(emd)

            param_grid = {
                "mos_mismatch_penalty": [1500, 2500, 3500, 4500],
                "unit_cohesion_bonus": [-200, -500, -800],
                "TDY_cost_weight": [0.8, 1.0, 1.2]
            }

            solutions = optimizer.explore_policy_space(param_grid, max_solutions=30)
            pareto_front = optimizer.get_pareto_frontier()

            st.session_state.pareto_solutions = solutions
            st.session_state.pareto_front = pareto_front

            st.success(f"✅ Found {len(pareto_front)} Pareto-optimal solutions")

    # Display results
    if 'pareto_front' in st.session_state and st.session_state.pareto_front:
        pareto_front = st.session_state.pareto_front

        # AI-Generated Executive Summary
        st.subheader("🤖 AI-Generated Executive Summary")

        if st.button("📊 Generate Decision Brief"):
            with st.spinner("Analyzing Pareto solutions and generating recommendations..."):
                summary = generate_pareto_executive_summary(pareto_front)
                st.session_state.pareto_summary = summary

        if 'pareto_summary' in st.session_state:
            st.markdown(st.session_state.pareto_summary)

            # Download option
            st.download_button(
                label="📥 Download Executive Summary",
                data=st.session_state.pareto_summary,
                file_name="pareto_decision_brief.md",
                mime="text/markdown"
            )

        # Show solutions table
        solutions_data = []
        for sol in pareto_front:
            solutions_data.append({
                "ID": sol.solution_id,
                "Fill Rate": f"{sol.fill_rate:.1%}",
                "Total Cost": f"${sol.total_cost:,.0f}",
                "Cohesion": f"{sol.cohesion_score:.1f}",
                "Cross-Leveling": f"{sol.cross_leveling_score:.1f}"
            })

        st.subheader("Pareto-Optimal Solutions")
        st.dataframe(pd.DataFrame(solutions_data), use_container_width=True)

        # 2D trade-off plots
        st.subheader("Trade-off Visualizations")

        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[s.fill_rate for s in pareto_front],
                y=[s.total_cost for s in pareto_front],
                mode='markers',
                marker=dict(size=10, color='blue'),
                text=[f"Solution {s.solution_id}" for s in pareto_front],
                name='Pareto Front'
            ))

            fig.update_layout(
                title="Fill Rate vs Total Cost",
                xaxis_title="Fill Rate",
                yaxis_title="Total Cost ($)",
                hovermode='closest'
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=[s.cohesion_score for s in pareto_front],
                y=[s.cross_leveling_score for s in pareto_front],
                mode='markers',
                marker=dict(size=10, color='green'),
                text=[f"Solution {s.solution_id}" for s in pareto_front],
                name='Pareto Front'
            ))

            fig2.update_layout(
                title="Cohesion vs Cross-Leveling",
                xaxis_title="Cohesion Score",
                yaxis_title="Cross-Leveling Score (lower is better)",
                hovermode='closest'
            )

            st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    main()
