import streamlit as st
from pathlib import Path

from pages_content import home, about, single_evaluation, benchmark_validation
from utils.api_client import backend_health

st.set_page_config(
    page_title="AI Response Quality Evaluator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css():
    css_path = Path(__file__).parent / "theme" / "style.css"
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def sidebar_nav() -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-wrap">
                <div class="brand-badge">AI</div>
                <div>
                    <div class="brand-title">Response Quality<br/>Evaluator</div>
                    <div class="brand-sub">Multi-Agent Evaluation System</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<hr class='hr-soft'>", unsafe_allow_html=True)

        page = st.radio(
            "Navigate",
            ["🏠 Home", "📘 About Project", "🧪 Single Evaluation", "📊 Benchmark Validation"],
            label_visibility="collapsed",
        )

        st.markdown("<hr class='hr-soft'>", unsafe_allow_html=True)
        ok = backend_health()
        status_badge = (
            "<span class='badge badge-good'>● Backend Connected</span>"
            if ok
            else "<span class='badge badge-warn'>● Backend Offline (Demo Mode)</span>"
        )
        st.markdown(status_badge, unsafe_allow_html=True)
        st.caption("Milestone 1: Jun 30 – Jul 9")

    return page


def main():
    inject_css()
    page = sidebar_nav()

    if page == "🏠 Home":
        home.render()
    elif page == "📘 About Project":
        about.render()
    elif page == "🧪 Single Evaluation":
        single_evaluation.render()
    elif page == "📊 Benchmark Validation":
        benchmark_validation.render()


if __name__ == "__main__":
    main()
