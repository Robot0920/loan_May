# Case 01 — The Initial Client Prompt

> **How to use this file**: Read only the **Prompt** section below. Set a 90-minute timer. Take a blank page (or a fresh markdown file in `docs/`) and work through how you'd respond — clarifying questions first, then approach, then deep dive. Do **not** read the rest of `case_study/` until you've taken your own swing. Real interviews don't hand you the rubric in advance.

---

## Prompt (read this only)

> *"We've been engaged by NovaLend, a mid-sized US consumer lender with about $10B in outstanding unsecured personal loans. Their Chief Risk Officer flew us in last week. The story she told us:*
>
> *"Twelve months ago her team noticed that the 90-day default rate was creeping up — not catastrophically, but stubbornly. Two consecutive quarters it ticked higher. Their underwriting team blamed macro conditions. Their data science team said the scorecard, which was built six years ago, was still 'broadly performing.' Their board is now asking whether the lender should pause approvals on certain segments, raise rates across the book, or — and this is the option she leans toward — modernize the credit decisioning system altogether.*
>
> *"She's asked us for a recommendation in eight weeks. You're on the team and the partner has handed you the technical workstream. How would you approach this?"*

---

## What you're being tested on (don't read this until you've tried the prompt yourself)

This opener is deliberately under-specified. A weaker candidate dives into "I'd build a gradient boosting model and..." A stronger candidate:

1. **Restates the problem in their own words** — what does NovaLend actually need to decide?
2. **Asks 2–4 clarifying questions before proposing anything** — and asks them in priority order (most consequential first)
3. **Distinguishes the *business* question from the *technical* question** — they are related but not identical
4. **Lays out a structured approach (issue tree)** — not a list of tactics
5. **Names the biggest risks to the engagement up front** — what could make this go wrong, regardless of model quality

Once you've taken your swing, open [02_clarifying_questions.md](02_clarifying_questions.md) to compare.

---

## Self-check questions (use these to grade yourself before reading 02)

- Did you ask what "creeping up" means quantitatively? (10 bps? 100 bps? Across the whole book or one segment?)
- Did you ask about the existing scorecard — what it uses, when it was last validated, why they suspect it of failing?
- Did you ask about the time horizon and decision rights? (Who signs off on a new model? CRO? Board? Regulator?)
- Did you ask whether the underwriting team's "macro" hypothesis has been tested?
- Did you distinguish "is the scorecard broken" from "is the world different from when the scorecard was built"?
- Did you scope the engagement deliverable — a recommendation memo? A working prototype? A regulatory filing?
- Did you flag SR 11-7 / ECOA implications before being prompted?

If you hit fewer than four of these, you went too fast to "solution mode." That's the most common mid-level-candidate failure pattern. Senior candidates *delay* the solution.

---

## What the partner is actually thinking while you talk

(This is what your real interviewer's internal monologue looks like — not the rubric, just the vibe.)

- "Did they slow down or did they jump to XGBoost in the first 30 seconds?"
- "Are they treating this as a data science problem or a business problem?"
- "Do they understand that the CRO doesn't want a model — she wants a defensible decision?"
- "If they made a senior-sounding move, was it actually senior or just jargon?"
- "If I push back, do they hold the line where they should and yield where they should?"

The interviewer is not looking for you to know the answer. They're looking for you to have the *posture* of someone who's done this before.
