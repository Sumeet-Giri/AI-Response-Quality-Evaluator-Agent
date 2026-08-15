"""
PDF Report Export (Milestone 4)
----------------------------------
Structured PDF summaries for both Single Evaluation and Batch Evaluation,
built with reportlab's Platypus layer (tables + flowable text, not raw
canvas drawing -- the right tool for a multi-section tabular report).

Two entry points:
    build_single_evaluation_pdf(...)  -> bytes
    build_batch_evaluation_pdf(...)   -> bytes

Both return raw PDF bytes, ready for st.download_button.
"""

import io
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

_styles = getSampleStyleSheet()
_title_style = ParagraphStyle("ReportTitle", parent=_styles["Title"], fontSize=20, spaceAfter=6)
_h2 = ParagraphStyle("H2", parent=_styles["Heading2"], spaceBefore=14, spaceAfter=6)
_body = ParagraphStyle("Body", parent=_styles["BodyText"], spaceAfter=6)
_small = ParagraphStyle("Small", parent=_styles["BodyText"], fontSize=8, textColor=colors.grey)

_HEADER_BG = colors.HexColor("#1f2430")
_PASS_BG = colors.HexColor("#e8f7ee")
_FAIL_BG = colors.HexColor("#fdecec")


def _table_style(header_bg=_HEADER_BG):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f9")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])


def _wrap(text, style=_body, max_len=500):
    text = str(text or "")
    if len(text) > max_len:
        text = text[:max_len].rstrip() + "…"
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(text, style)


# --------------------------------------------------------------------------
# Single Evaluation report
# --------------------------------------------------------------------------

def build_single_evaluation_pdf(
    data: dict,
    question: str,
    response: str,
    reference: str,
    system_name: str = "Unspecified",
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                             leftMargin=0.6 * inch, rightMargin=0.6 * inch)
    story = []

    verdict = data.get("verdict", {}) or {}
    rag = data.get("rag", {}) or {}

    story.append(Paragraph("AI Response Quality Evaluation Report", _title_style))
    story.append(Paragraph(
        f"System: <b>{system_name}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        _small,
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Input", _h2))
    story.append(_wrap(f"<b>Question:</b> {question}"))
    story.append(_wrap(f"<b>Response:</b> {response}"))
    if reference:
        story.append(_wrap(f"<b>Reference Answer:</b> {reference}"))
    if rag.get("source") == "retrieved":
        story.append(_wrap(
            "<i>Note: no reference answer was supplied -- this evaluation used a reference "
            "passage automatically retrieved from the knowledge base.</i>", _small))
    elif rag.get("source") == "none":
        story.append(_wrap(
            "<i>Note: no reference answer was supplied and none was found in the knowledge base -- "
            "Accuracy and Hallucination were scored with no reference to compare against.</i>", _small))

    story.append(Paragraph("Overall Verdict", _h2))
    verdict_bg = _PASS_BG if verdict.get("quality_gate_passed") else _FAIL_BG
    verdict_table = Table(
        [["Overall Score", "Final Verdict", "Quality Gate"],
         [f"{verdict.get('overall_score', '—')}/10",
          verdict.get("final_verdict", "—"),
          "PASSED" if verdict.get("quality_gate_passed") else "FAILED"]],
        colWidths=[2.3 * inch, 2.3 * inch, 2.3 * inch],
    )
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), verdict_bg),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 8))
    story.append(_wrap(verdict.get("consolidated_reasoning", "")))

    story.append(Paragraph("Per-Dimension Breakdown", _h2))
    rows = [["Dimension", "Score /10", "Summary"]]
    dims = [
        ("Relevance", data.get("relevance", {})),
        ("Accuracy", data.get("accuracy", {})),
        ("Hallucination", data.get("hallucination", {})),
        ("Completeness", data.get("completeness", {})),
    ]
    for name, d in dims:
        rows.append([name, str(d.get("score", "—")), _wrap(d.get("reasoning", ""), max_len=220)])
    dim_table = Table(rows, colWidths=[1.1 * inch, 0.9 * inch, 4.9 * inch], repeatRows=1)
    dim_table.setStyle(_table_style())
    story.append(dim_table)

    story.append(Paragraph("Strengths & Weaknesses", _h2))
    for s in verdict.get("strengths", []) or []:
        story.append(_wrap(f"✓ {s}"))
    for w in verdict.get("weaknesses", []) or []:
        story.append(_wrap(f"✗ {w}"))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# --------------------------------------------------------------------------
# Batch Evaluation report
# --------------------------------------------------------------------------

def build_batch_evaluation_pdf(
    table: pd.DataFrame,
    system_name: str = "Unspecified",
    batch_label: str = "",
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                             leftMargin=0.6 * inch, rightMargin=0.6 * inch)
    story = []

    scored = table[table["final_verdict"] != "ERROR"]
    n_total = len(table)
    n_errors = int((table["final_verdict"] == "ERROR").sum())
    overall = scored["overall_score"].dropna()
    avg_scores = {
        "Relevance": scored["relevance"].mean(),
        "Accuracy": scored["accuracy"].mean(),
        "Hallucination": scored["hallucination"].mean(),
        "Completeness": scored["completeness"].mean(),
    }
    n_pass = int((scored["pass_fail"] == "PASS").sum())
    n_fail = int((scored["pass_fail"] == "FAIL").sum())
    denom = max(1, n_pass + n_fail)

    story.append(Paragraph("Batch Evaluation Report", _title_style))
    label_bits = [f"System: <b>{system_name}</b>"]
    if batch_label:
        label_bits.append(f"Run: <b>{batch_label}</b>")
    label_bits.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    story.append(Paragraph(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(label_bits), _small))
    story.append(Spacer(1, 10))

    # ---- Summary ----
    story.append(Paragraph("Summary", _h2))
    summary_rows = [
        ["Total Responses", "Avg Overall Score", "Pass %", "Fail %", "Errors"],
        [
            str(n_total),
            f"{overall.mean():.2f}/10" if not overall.empty else "—",
            f"{n_pass / denom * 100:.0f}%",
            f"{n_fail / denom * 100:.0f}%",
            str(n_errors),
        ],
    ]
    summary_table = Table(summary_rows, colWidths=[1.4 * inch] * 5)
    summary_table.setStyle(_table_style())
    story.append(summary_table)

    # ---- Dimension breakdown ----
    story.append(Paragraph("Dimension Breakdown (Batch Average)", _h2))
    dim_rows = [["Dimension", "Average Score /10"]]
    for k, v in avg_scores.items():
        dim_rows.append([k, f"{v:.2f}" if pd.notna(v) else "—"])
    dim_table = Table(dim_rows, colWidths=[3 * inch, 3 * inch])
    dim_table.setStyle(_table_style())
    story.append(dim_table)

    # ---- Flagged responses ----
    story.append(Paragraph("Flagged Responses (Failed or Errored)", _h2))
    flagged = table[table["pass_fail"].isin(["FAIL", "ERROR"])].head(25)
    if flagged.empty:
        story.append(_wrap("No failed or errored responses in this batch."))
    else:
        flagged_rows = [["#", "Question", "Overall", "Verdict"]]
        for _, row in flagged.iterrows():
            overall_val = row.get("overall_score")
            overall_display = f"{overall_val:.1f}" if pd.notna(overall_val) else "—"
            flagged_rows.append([
                str(row["#"]),
                _wrap(row["question"], max_len=180),
                overall_display,
                row["final_verdict"],
            ])
        flagged_table = Table(flagged_rows, colWidths=[0.4 * inch, 4.2 * inch, 0.8 * inch, 1 * inch], repeatRows=1)
        flagged_table.setStyle(_table_style(header_bg=colors.HexColor("#7a1f2b")))
        story.append(flagged_table)
        if len(table[table["pass_fail"].isin(["FAIL", "ERROR"])]) > 25:
            story.append(_wrap(f"... and more (showing first 25 of "
                                f"{len(table[table['pass_fail'].isin(['FAIL', 'ERROR'])])}).", _small))

    # ---- Improvement recommendations ----
    story.append(PageBreak())
    story.append(Paragraph("Improvement Recommendations", _h2))
    recs = _generate_recommendations(avg_scores, n_fail, n_pass, n_errors, n_total)
    for r in recs:
        story.append(_wrap(f"• {r}"))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _generate_recommendations(avg_scores: dict, n_fail: int, n_pass: int, n_errors: int, n_total: int) -> list[str]:
    """
    Heuristic, data-driven recommendations based on which dimension(s)
    dragged the batch average down the most -- not a fixed template,
    genuinely derived from this batch's own numbers.
    """
    recs = []
    valid_scores = {k: v for k, v in avg_scores.items() if pd.notna(v)}

    if valid_scores:
        worst_dim, worst_val = min(valid_scores.items(), key=lambda kv: kv[1])
        if worst_val < 6:
            explanations = {
                "Relevance": "responses are drifting off-topic from the questions asked -- "
                             "review prompt framing or system instructions for topical focus.",
                "Accuracy": "responses frequently diverge from reference/ground-truth answers -- "
                            "consider supplying reference answers for more of the dataset, or "
                            "reviewing the model/prompt for factual grounding.",
                "Hallucination": "a meaningful share of claims aren't supported by the available "
                                  "reference material -- consider stronger grounding (e.g. RAG "
                                  "with a more complete knowledge base) or stricter claim verification.",
                "Completeness": "responses are missing expected aspects of the question -- "
                                 "consider prompting for more thorough, structured answers.",
            }
            recs.append(
                f"{worst_dim} scored lowest on average ({worst_val:.1f}/10) across this batch — "
                + explanations.get(worst_dim, "")
            )

    if n_total:
        fail_rate = n_fail / max(1, n_pass + n_fail) * 100
        if fail_rate > 40:
            recs.append(
                f"{fail_rate:.0f}% of responses failed the quality gate — this is a high failure "
                "rate; consider reviewing the underlying model/prompt configuration before further "
                "large-scale evaluation."
            )
        elif fail_rate > 15:
            recs.append(
                f"{fail_rate:.0f}% of responses failed the quality gate — worth spot-checking the "
                "flagged responses above for a common root cause."
            )

    if n_errors:
        recs.append(
            f"{n_errors} row(s) errored out during evaluation rather than being scored — check the "
            "'Failed Rows' section on the Benchmark Validation page for the specific error messages."
        )

    if not recs:
        recs.append("No significant issues detected — all dimensions scored reasonably well on average.")

    return recs
