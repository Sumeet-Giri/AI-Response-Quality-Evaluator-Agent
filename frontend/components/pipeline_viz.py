import streamlit as st

DEFAULT_STAGES = [
    "Question", "AI Response", "Relevance", "Accuracy",
    "Hallucination", "Completeness", "Verdict", "Final Report",
]


def render_pipeline(stages=None, completed_upto: int = -1, active_index: int = -1):
    """
    Renders a horizontal pipeline of pill/node steps.
    completed_upto: index (inclusive) of the last completed stage (-1 = none)
    active_index: index currently running (-1 = none)
    """
    stages = stages or DEFAULT_STAGES
    parts = ["<div class='pipe-row'>"]
    for i, stage in enumerate(stages):
        cls = "pipe-node"
        icon = "○"
        if i <= completed_upto:
            cls += " done"
            icon = "✓"
        if i == active_index:
            cls += " active"
            icon = "●"
        parts.append(f"<div class='{cls}'><span>{icon}</span>{stage}</div>")
        if i < len(stages) - 1:
            parts.append("<span class='pipe-arrow'>&#8594;</span>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)
