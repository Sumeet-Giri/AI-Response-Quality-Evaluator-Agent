import plotly.graph_objects as go
import streamlit as st

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#eef1f7", family="Inter, sans-serif"),
)


def render_radar_chart(scores: dict, key: str):
    """scores: {'Relevance': 8.2, 'Accuracy': 7.5, ...} on a 0-10 scale."""
    categories = list(scores.keys())
    values = list(scores.values())
    # close the loop
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(124,92,255,0.25)",
            line=dict(color="#7c5cff", width=2),
            name="Score",
        )
    )
    fig.update_layout(
        **DARK_LAYOUT,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#262b38", tickfont=dict(color="#6b7280")),
            angularaxis=dict(gridcolor="#262b38", tickfont=dict(color="#eef1f7")),
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=40, r=40),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_score_bar(scores: dict, key: str):
    """Horizontal bar comparison of agent scores."""
    labels = list(scores.keys())
    values = list(scores.values())
    colors = ["#22c55e" if v >= 7.5 else "#f59e0b" if v >= 5 else "#ef4444" for v in values]

    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:.1f}" for v in values], textposition="outside",
        )
    )
    fig.update_layout(
        **DARK_LAYOUT,
        xaxis=dict(range=[0, 10], gridcolor="#1c2029", zeroline=False),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        margin=dict(t=10, b=10, l=10, r=30),
        height=280,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


def render_distribution_chart(all_scores: list, key: str):
    """Histogram of overall scores — used on Benchmark Validation page."""
    fig = go.Figure(
        go.Histogram(x=all_scores, marker=dict(color="#4fd1c5"), nbinsx=10)
    )
    fig.update_layout(
        **DARK_LAYOUT,
        xaxis=dict(title="Overall Score", range=[0, 10], gridcolor="#1c2029"),
        yaxis=dict(title="Count", gridcolor="#1c2029"),
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        bargap=0.1,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
