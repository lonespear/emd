"""
ui_components.py
----------------

Reusable dashboard UI components for EMD Manning Dashboard.
Provides military-themed, concise visual elements.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Optional, List, Dict


# ============================================================================
# STATUS BANNERS
# ============================================================================

def status_banner(status: str, fill_rate: float, message: str):
    """
    Display prominent status banner at top of page.

    Args:
        status: "MISSION CAPABLE" | "MARGINAL" | "NOT MISSION CAPABLE"
        fill_rate: Float 0-1
        message: Additional context message
    """
    if status == "MISSION CAPABLE":
        st.success(f"✅ **{status}** ({fill_rate:.1%} Fill) - {message}", icon="✅")
    elif status == "MARGINAL":
        st.warning(f"⚠️ **{status}** ({fill_rate:.1%} Fill) - {message}", icon="⚠️")
    else:
        st.error(f"❌ **{status}** ({fill_rate:.1%} Fill) - {message}", icon="❌")


def critical_alert(capability: str, gap: int, total: int):
    """Display critical capability gap alert."""
    gap_pct = (gap / total) * 100 if total > 0 else 0
    st.error(f"🚨 **CRITICAL GAP:** {capability} - {gap} of {total} unfilled ({gap_pct:.0f}%)", icon="🚨")


def info_banner(message: str, icon: str = "ℹ️"):
    """Display informational banner."""
    st.info(f"{icon} {message}")


# ============================================================================
# METRIC CARDS
# ============================================================================

def hero_metric(label: str, value: str, delta: Optional[str] = None,
                delta_color: str = "normal", help_text: Optional[str] = None):
    """
    Large hero metric for dashboard top.

    Args:
        label: Metric name
        value: Main value to display
        delta: Change indicator (e.g., "+5%", "GOOD")
        delta_color: "normal", "inverse", or "off"
        help_text: Tooltip text
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def compact_metric_card(label: str, value: str, color: str = "blue"):
    """
    Compact metric card for grid layouts.

    Args:
        label: Metric name
        value: Value to display
        color: Background color theme
    """
    if color == "green":
        st.markdown(f"""
        <div style="background-color: #28a745; padding: 12px; border-radius: 5px; text-align: center;">
            <p style="color: white; margin: 0; font-size: 14px;">{label}</p>
            <h3 style="color: white; margin: 4px 0 0 0;">{value}</h3>
        </div>
        """, unsafe_allow_html=True)
    elif color == "red":
        st.markdown(f"""
        <div style="background-color: #dc3545; padding: 12px; border-radius: 5px; text-align: center;">
            <p style="color: white; margin: 0; font-size: 14px;">{label}</p>
            <h3 style="color: white; margin: 4px 0 0 0;">{value}</h3>
        </div>
        """, unsafe_allow_html=True)
    elif color == "yellow":
        st.markdown(f"""
        <div style="background-color: #ffc107; padding: 12px; border-radius: 5px; text-align: center;">
            <p style="color: black; margin: 0; font-size: 14px;">{label}</p>
            <h3 style="color: black; margin: 4px 0 0 0;">{value}</h3>
        </div>
        """, unsafe_allow_html=True)
    else:  # blue default
        st.markdown(f"""
        <div style="background-color: #0066cc; padding: 12px; border-radius: 5px; text-align: center;">
            <p style="color: white; margin: 0; font-size: 14px;">{label}</p>
            <h3 style="color: white; margin: 4px 0 0 0;">{value}</h3>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# GAUGE CHARTS
# ============================================================================

def gauge_chart(value: float, title: str, max_value: float = 100,
                thresholds: Optional[List[float]] = None):
    """
    Create a gauge chart for readiness/fill metrics.

    Args:
        value: Current value (0-100)
        title: Chart title
        max_value: Maximum value for gauge
        thresholds: List of [red_max, yellow_max, green_max]
    """
    if thresholds is None:
        thresholds = [70, 90, 100]  # Default: <70 red, 70-90 yellow, >90 green

    # Determine color
    if value < thresholds[0]:
        color = "#dc3545"  # red
    elif value < thresholds[1]:
        color = "#ffc107"  # yellow
    else:
        color = "#28a745"  # green

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        number={'suffix': "%", 'font': {'size': 32}},
        gauge={
            'axis': {'range': [None, max_value], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, thresholds[0]], 'color': '#ffcccc'},
                {'range': [thresholds[0], thresholds[1]], 'color': '#fff4cc'},
                {'range': [thresholds[1], max_value], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': thresholds[1]  # Target threshold
            }
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="white",
        font={'family': "Arial"}
    )

    st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# RISK MATRIX
# ============================================================================

def risk_indicator(risk_level: str) -> str:
    """Return colored risk indicator."""
    if risk_level == "HIGH":
        return "🔴 HIGH"
    elif risk_level == "MEDIUM":
        return "🟡 MEDIUM"
    else:
        return "🟢 LOW"


def risk_matrix_card(capability: str, gap_pct: float, priority: int):
    """
    Display risk assessment card for a capability.

    Args:
        capability: Capability name
        gap_pct: Gap percentage (0-1)
        priority: Priority level (1=critical, 2=high, 3=normal)
    """
    # Determine risk level
    if gap_pct > 0.15 or priority == 1:
        risk = "HIGH"
        color = "red"
    elif gap_pct > 0.05 or priority == 2:
        risk = "MEDIUM"
        color = "yellow"
    else:
        risk = "LOW"
        color = "green"

    st.markdown(f"""
    <div style="border-left: 4px solid {'#dc3545' if risk == 'HIGH' else '#ffc107' if risk == 'MEDIUM' else '#28a745'};
                padding: 10px; margin: 5px 0; background-color: #f8f9fa;">
        <strong>{capability}</strong><br>
        <span style="font-size: 12px;">Gap: {gap_pct:.1%} | Risk: {risk_indicator(risk)}</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# CONOP DISPLAY
# ============================================================================

def conop_card(title: str, situation: str, mission: str, execution: str):
    """
    Display CONOP in military 5-paragraph order format (abbreviated).

    Args:
        title: Operation name
        situation: Situation paragraph
        mission: Mission statement
        execution: Execution concept
    """
    st.markdown(f"""
    ### 📋 {title}

    **SITUATION:**
    {situation}

    **MISSION:**
    {mission}

    **EXECUTION:**
    {execution}
    """)


def conop_compact(title: str, summary: str):
    """Ultra-compact CONOP display."""
    with st.expander(f"📋 {title}", expanded=False):
        st.markdown(summary)


# ============================================================================
# ACTION BUTTONS
# ============================================================================

def action_button_row(buttons: List[Dict[str, str]]):
    """
    Display row of action buttons.

    Args:
        buttons: List of dicts with keys: label, icon, type (primary/secondary)
    """
    cols = st.columns(len(buttons))
    for idx, (col, btn) in enumerate(zip(cols, buttons)):
        with col:
            btn_type = btn.get("type", "secondary")
            st.button(
                f"{btn.get('icon', '')} {btn['label']}",
                key=f"action_btn_{idx}",
                type=btn_type,
                use_container_width=True
            )


# ============================================================================
# QUICK STATS SUMMARY
# ============================================================================

def quick_stats_bullets(stats: List[str]):
    """
    Display quick-glance bullet summary instead of paragraphs.

    Args:
        stats: List of stat strings with icons (e.g., "✅ 95% fill rate")
    """
    bullet_html = "<div style='font-size: 14px; line-height: 1.8;'>"
    for stat in stats:
        bullet_html += f"{stat} &nbsp;&nbsp;|&nbsp;&nbsp; "
    bullet_html = bullet_html.rstrip("&nbsp;&nbsp;|&nbsp;&nbsp; ") + "</div>"
    st.markdown(bullet_html, unsafe_allow_html=True)


# ============================================================================
# SECTION DIVIDERS
# ============================================================================

def section_divider(title: str, icon: str = ""):
    """Clean section divider with optional icon."""
    if icon:
        st.markdown(f"### {icon} {title}")
    else:
        st.markdown(f"### {title}")
    st.markdown("---")


def thin_divider():
    """Thin divider for subtle separation."""
    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #e0e0e0;'>",
                unsafe_allow_html=True)


# ============================================================================
# SCENARIO SELECTOR CARD
# ============================================================================

def scenario_card(name: str, category: str, description: str,
                  force_size: int, duration: int, selected: bool = False):
    """
    Display scenario selection card.

    Args:
        name: Scenario name
        category: Category label
        description: Brief description
        force_size: Number of soldiers
        duration: Duration in days
        selected: If currently selected
    """
    border_color = "#0066cc" if selected else "#cccccc"
    bg_color = "#f0f7ff" if selected else "#ffffff"

    st.markdown(f"""
    <div style="border: 2px solid {border_color}; border-radius: 8px; padding: 15px;
                margin: 10px 0; background-color: {bg_color}; cursor: pointer;">
        <h4 style="margin: 0 0 8px 0; color: #333;">{name}</h4>
        <p style="margin: 0; font-size: 12px; color: #666;">{category}</p>
        <p style="margin: 8px 0; font-size: 14px;">{description}</p>
        <div style="display: flex; gap: 20px; font-size: 12px; color: #666;">
            <span>👥 {force_size:,} soldiers</span>
            <span>📅 {duration} days</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# COMMANDER'S RECOMMENDATION BOX
# ============================================================================

def commanders_recommendation(recommendation: str, rationale: str,
                              status: str = "approve"):
    """
    Display commander's decision recommendation prominently.

    Args:
        recommendation: "APPROVE" | "APPROVE WITH RISK" | "DISAPPROVE"
        rationale: Brief explanation
        status: approve/caution/reject
    """
    if status == "approve":
        icon = "✅"
        color = "#28a745"
    elif status == "caution":
        icon = "⚠️"
        color = "#ffc107"
    else:
        icon = "❌"
        color = "#dc3545"

    st.markdown(f"""
    <div style="background-color: {color}; color: white; padding: 20px;
                border-radius: 8px; margin: 20px 0; text-align: center;">
        <h2 style="margin: 0; color: white;">{icon} RECOMMENDATION: {recommendation}</h2>
        <p style="margin: 10px 0 0 0; font-size: 16px;">{rationale}</p>
    </div>
    """, unsafe_allow_html=True)
