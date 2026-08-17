"""
Batch Charts
------------
New chart types needed specifically for batch/benchmark analytics that
components/charts.py doesn't already cover. Reuses the same dark Plotly
layout conventions (transparent background, Inter font) as charts.py so it
looks identical to the rest of the dashboard.
"""

import plotly.graph_objects as go
import streamlit as st

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#eef1f7", family="Inter, sans-serif"),
)

GOOD = "#22c55e"
BAD = "#ef4444"
NEUTRAL = "#6b7280"
WARN = "#f59e0b"


def render_pass_fail_pie(pass_count: int, fail_count: int, error_count: int, key: str):
    """Donut chart of PASS / FAIL / ERROR counts across the batch."""
    labels, values, colors = [], [], []
    if pass_count:
        labels.append("PASS"); values.append(pass_count); colors.append(GOOD)
    if fail_count:
        labels.append("FAIL"); values.append(fail_count); colors.append(BAD)
    if error_count:
        labels.append("ERROR"); values.append(error_count); colors.append(NEUTRAL)

    if not values:
        st.caption("No results to chart yet.")
        return

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#0b0d12", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#eef1f7", size=13),
                sort=False,
            )
        ]
    )
    fig.update_layout(
        **DARK_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1, font=dict(color="#a7adbd")),
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_verdict_breakdown_pie(pass_count: int, needs_improvement_count: int, fail_count: int, key: str):
    """Donut chart of the three-way Pass / Needs Improvement / Fail
    breakdown, derived from final_verdict (EXCELLENT/GOOD -> Pass,
    NEEDS IMPROVEMENT/POOR -> Needs Improvement, FAIL -> Fail) -- distinct
    from render_pass_fail_pie's binary quality-gate view above."""
    labels, values, colors = [], [], []
    if pass_count:
        labels.append("Pass"); values.append(pass_count); colors.append(GOOD)
    if needs_improvement_count:
        labels.append("Needs Improvement"); values.append(needs_improvement_count); colors.append(WARN)
    if fail_count:
        labels.append("Fail"); values.append(fail_count); colors.append(BAD)

    if not values:
        st.caption("No results to chart yet.")
        return

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#0b0d12", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#eef1f7", size=13),
                sort=False,
            )
        ]
    )
    fig.update_layout(
        **DARK_LAYOUT,
        showlegend=True,
        legend=dict(orientation="h", y=-0.1, font=dict(color="#a7adbd")),
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_score_trend(scores: list, key: str, x_axis_label: str = "Row #"):
    """Line chart of overall_score in order -- helps spot drift across a
    batch (rows) or across history (batches), depending on x_axis_label."""
    fig = go.Figure(
        go.Scatter(
            x=list(range(1, len(scores) + 1)),
            y=scores,
            mode="lines+markers",
            line=dict(color="#7c5cff", width=2),
            marker=dict(size=5, color="#4fd1c5"),
        )
    )
    fig.update_layout(
        **DARK_LAYOUT,
        xaxis=dict(title=x_axis_label, gridcolor="#1c2029", dtick=1),
        yaxis=dict(title="Overall Score", range=[0, 10], gridcolor="#1c2029"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
