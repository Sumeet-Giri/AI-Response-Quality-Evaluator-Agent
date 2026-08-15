# Demo Guide: Evaluating Two Distinct AI Systems

Milestone 4 asks for a final demonstration "showcasing evaluation of
minimum two distinct AI systems using the platform." This is a concrete,
repeatable walkthrough for that — both the *right* way (meaningful, with
real different outputs) and a note on the mistake that's easy to make.

## The mistake to avoid

Tagging the same CSV / same responses under two different System Name
labels does **not** demonstrate comparing two systems — it demonstrates
that the platform is deterministic (which is good to know, but is a
different claim). Two batches built from **identical** question/response
pairs will score identically, because nothing about the actual evaluated
content differs. This happened once during testing this project: two
batches tagged "GPT-4" and "Claude-3" produced byte-for-byte identical
PDF reports, because both runs reused the unmodified built-in sample
dataset. That's expected system behavior, not a demo of system
comparison — it just means the demo data was wrong.

**The fix: get genuinely different responses from each system.**

## Step-by-step

### 1. Pick a fixed set of questions

5–10 questions is enough for a clear demo. Mix easy factual ones with a
couple of harder or more nuanced ones — the comparison is more
interesting if the two systems don't perform identically on everything.

Example set:
```
What is the capital of India?
Who wrote Romeo and Juliet?
What is the boiling point of water at sea level?
Explain what machine learning is.
What year did World War II end?
```

### 2. Get real answers from two actual AI systems

Paste each question into two different chat systems (e.g. ChatGPT and
Claude, or two different model versions/settings of the same provider)
and record the **actual** responses verbatim. Don't paraphrase or
shorten them — use exactly what each system said.

### 3. Build two CSVs (or one CSV with a system column, run twice)

`gpt4_responses.csv`:
```csv
question,response,reference_answer
What is the capital of India?,<GPT-4's actual answer>,New Delhi
Who wrote Romeo and Juliet?,<GPT-4's actual answer>,William Shakespeare
...
```

`claude_responses.csv`: same questions, same `reference_answer` column,
but with Claude's actual responses in the `response` column.

Using the same `reference_answer` for both files is important — it's
what makes the comparison fair. Without a reference, both systems will
show "Unverified" for Accuracy/Hallucination regardless of which one is
actually better (see the note in the backend README about the
`verifiable` flag), which defeats the point of a comparison.

### 4. Run each CSV through Benchmark Validation

For each file:
1. Go to **Benchmark Validation**.
2. Upload the CSV.
3. Set **AI System / Model Name** to `GPT-4` (or `Claude-3` for the second run).
4. Set **Run Label** to something identifying, e.g. `Demo comparison set v1`.
5. Click **Run Batch Evaluation**.
6. Optionally download that system's PDF report right away.

### 5. Open the Dashboard

Go to **Dashboard**. With two systems now tagged, the **Compare AI
Systems** section will show:
- Two side-by-side mini-profiles, each with its own per-dimension bar chart
- A combined table with both systems' evaluation counts, average scores
  per dimension, and pass/fail counts
- The **Quality Trends Across Batch Evaluations** table will list both
  batch runs by label and system, with matching row counts

This is the actual demonstration: real, different responses to the same
questions, scored by the same pipeline, compared head-to-head with real
numbers — not two runs of the same data under different labels.

### 6. What to point out in the demo/report

- The two systems' **average scores per dimension** — which one is more
  relevant on average, more accurate, more prone to unsupported claims,
  more complete.
- Any row where one system passed the quality gate and the other didn't
  for the *same* question — the clearest, most concrete evidence the
  evaluator is discriminating between systems, not just producing noise.
- If you want a specific narrative for the report/demo, deliberately
  include one question where the systems visibly disagree (e.g. a recent
  event, or a commonly-confused fact) — this tends to produce a good example.
