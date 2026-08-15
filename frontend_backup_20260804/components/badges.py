import streamlit as st


def badge(text: str, kind: str = "neutral"):
    st.markdown(
        f"<span class='badge badge-{kind}'>{text}</span>",
        unsafe_allow_html=True,
    )


def badge_html(text: str, kind: str = "neutral") -> str:
    return f"<span class='badge badge-{kind}'>{text}</span>"


def metric_tile(label: str, value: str):
    st.markdown(
        f"""
        <div class="metric-tile">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str):
    st.markdown(
        f"<span class='pill'><span class='pill-dot'></span>{text}</span>",
        unsafe_allow_html=True,
    )


def section_label(text: str):
    st.markdown(
        f"<div class='section-label'>{text}</div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# FIX FOR BLACK STRIPS
# --------------------------------------------------

def card():
    """
    Native Streamlit container.
    No HTML divs.
    """
    return st.container(border=True)

def card_open(extra_class=""):
    pass


def card_close():
    pass