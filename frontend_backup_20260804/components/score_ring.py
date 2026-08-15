"""Circular score indicator (donut gauge) built with Plotly — used for every
per-dimension score and the overall verdict score."""

import plotly.graph_objects as go
import streamlit as st

COLOR_GOOD = "#22c55e"
COLOR_WARN = "#f59e0b"
COLOR_BAD = "#ef4444"
TRACK = "#232838"


def _color_for(score_0_10: float) -> str:
    if score_0_10 >= 7.5:
        return COLOR_GOOD
    if score_0_10 >= 5:
        return COLOR_WARN
    return COLOR_BAD


def render_score_ring(score_0_10: float, label: str, key: str, size: int = 190):
    """Renders a donut-style score ring (0-10 scale) with a label underneath."""
    score_0_10 = max(0, min(10, score_0_10))
    pct = score_0_10 / 10
    color = _color_for(score_0_10)

    fig = go.Figure(
        data=[
            go.Pie(
                values=[pct, 1 - pct],
                hole=0.78,
                marker=dict(colors=[color, TRACK], line=dict(width=0)),
                textinfo="none",
                sort=False,
                direction="clockwise",
                rotation=0,
            )
        ]
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        height=size,
        width=size,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=f"<b>{score_0_10:.1f}</b><span style='font-size:12px;color:#8a90a3'>/10</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=26, color="#eef1f7"),
            )
        ],
    )
    st.plotly_chart(fig, use_container_width=False, config={"displayModeBar": False}, key=key)
    st.markdown(f"<div class='score-caption'>{label}</div>", unsafe_allow_html=True)
