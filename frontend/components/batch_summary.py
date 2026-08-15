"""
Batch Summary
-------------
Summary tiles ("Total Responses", "Average Score", ...) and standout-response
cards (Best / Worst / Highest Accuracy / Lowest Hallucination Risk). Built
entirely on top of existing components (card, badge_html, metric_tile) —
no new visual language introduced.
"""

import pandas as pd
import streamlit as st

from components.badges import card, badge_html, metric_tile, section_label


def summary_tiles(table: pd.DataFrame):
    """Total Responses, Average / Highest / Lowest Score, Pass %, Fail %."""
    scored = table[table["final_verdict"] != "ERROR"]
    total = len(table)
    n_errors = int((table["final_verdict"] == "ERROR").sum())

    if scored.empty or scored["overall_score"].dropna().empty:
        avg_score = highest = lowest = float("nan")
        pass_pct = fail_pct = 0.0
    else:
        overall = scored["overall_score"].dropna()
        avg_score = overall.mean()
        highest = overall.max()
        lowest = overall.min()
        n_pass = int((scored["pass_fail"] == "PASS").sum())
        n_fail = int((scored["pass_fail"] == "FAIL").sum())
        denom = max(1, n_pass + n_fail)
        pass_pct = n_pass / denom * 100
        fail_pct = n_fail / denom * 100

    r1 = st.columns(4)
    with r1[0]:
        metric_tile("Total Responses", str(total))
    with r1[1]:
        metric_tile("Average Score", f"{avg_score:.2f}/10" if avg_score == avg_score else "—")
    with r1[2]:
        metric_tile("Highest Score", f"{highest:.2f}/10" if highest == highest else "—")
    with r1[3]:
        metric_tile("Lowest Score", f"{lowest:.2f}/10" if lowest == lowest else "—")

    r2 = st.columns(4)
    with r2[0]:
        metric_tile("Pass %", f"{pass_pct:.0f}%")
    with r2[1]:
        metric_tile("Fail %", f"{fail_pct:.0f}%")
    with r2[2]:
        metric_tile("Failed Rows (Errors)", str(n_errors))
    with r2[3]:
        metric_tile("Rows Processed", f"{total - n_errors}/{total}")


def _standout_card(title: str, badge_kind: str, row: pd.Series | None, score_label: str, score_col: str):
    with card():
        section_label(title)
        if row is None:
            st.caption("Not enough data yet.")
            return
        st.markdown(f"**Q:** {row['question']}")
        st.caption(f"Response: {row['response_preview']}")
        val = row.get(score_col)
        st.markdown(
            badge_html(f"{score_label}: {val:.1f}/10" if val == val else f"{score_label}: —", badge_kind),
            unsafe_allow_html=True,
        )
        st.markdown(
            badge_html(row.get("final_verdict", "—"), "good" if row.get("pass_fail") == "PASS" else "bad"),
            unsafe_allow_html=True,
        )


def standout_responses(table: pd.DataFrame):
    """Best Overall / Worst Overall / Highest Accuracy / Lowest Hallucination Risk."""
    scored = table[table["final_verdict"] != "ERROR"].copy()

    best_row = worst_row = best_acc_row = best_halluc_row = None

    if not scored["overall_score"].dropna().empty:
        best_row = scored.loc[scored["overall_score"].idxmax()]
        worst_row = scored.loc[scored["overall_score"].idxmin()]
    if not scored["accuracy"].dropna().empty:
        best_acc_row = scored.loc[scored["accuracy"].idxmax()]
    if not scored["hallucination"].dropna().empty:
        # hallucination score is "hallucination-free-ness": higher = fewer hallucinations
        best_halluc_row = scored.loc[scored["hallucination"].idxmax()]

    c1, c2 = st.columns(2)
    with c1:
        _standout_card("🏆 Best Overall Response", "good", best_row, "Overall", "overall_score")
    with c2:
        _standout_card("⚠️ Worst Overall Response", "bad", worst_row, "Overall", "overall_score")

    c3, c4 = st.columns(2)
    with c3:
        _standout_card("🎯 Highest Accuracy", "good", best_acc_row, "Accuracy", "accuracy")
    with c4:
        _standout_card("🛡️ Lowest Hallucination Risk", "good", best_halluc_row, "Hallucination-Free", "hallucination")
