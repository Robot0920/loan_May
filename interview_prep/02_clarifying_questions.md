# Case 02 — Clarifying Questions (and How the Interviewer Answers)

> Before reading this: did you complete [01_initial_prompt.md](01_initial_prompt.md) on your own? If not, do that first.

This file lists the clarifying questions a strong candidate would ask, the *order* they'd ask them in, and the answers the interviewer would give if you asked them. The answers reveal the actual scope of the engagement — they are the de-fogged version of the vague prompt.

---

## Tier 1 — questions you must ask in the first 5 minutes

Strong candidates ask these in roughly this priority order. The order itself is part of what's being scored — putting "what model should I use" before "what's the decision" signals junior.

### Q1. "What is NovaLend actually trying to decide?"

**Interviewer's answer**: There are really three nested decisions.
1. **Tactical (this quarter)**: Should they pause approvals on any segment right now?
2. **Strategic (this year)**: Should they replace the scorecard with an ML-based system?
3. **Governance (ongoing)**: Whatever they choose, what monitoring and re-validation posture do they need?

Your engagement is sized to inform decision 2, with a sidebar on decision 3. Decision 1 is the CRO's call regardless of what you find.

### Q2. "What does 'default rate creeping up' actually look like? Numbers?"

**Interviewer's answer**:
- Book-wide 90-day-past-due rate has gone from **3.1% → 3.4% → 3.7%** over the last three quarters.
- It's worse in two segments: (a) borrowers under 30 with thin file, and (b) borrowers in three states the lender expanded into 18 months ago.
- The current scorecard was developed on 2017–2019 data, frozen in 2019, validated annually but not re-developed.

### Q3. "What's the current scorecard? FICO-based? Custom? ML?"

**Interviewer's answer**: Custom logistic regression scorecard with about 35 variables, mostly from credit bureau data plus internal application fields. Built by a consulting firm in 2019. Has been recalibrated (intercept shifted) twice but the coefficients are unchanged. Decisions are made via a cutoff score; there is no probability output exposed to the underwriting team.

### Q4. "What's the regulatory posture? OCC examined? Last audit?"

**Interviewer's answer**: Federally chartered, OCC-supervised, subject to SR 11-7 model risk management. Last OCC exam (8 months ago) flagged two findings: (1) model documentation needs refresh, (2) recommend developing a "challenger" model for the scorecard. Both are open findings. ECOA fair lending review is internal, conducted by a 2-person compliance team. No active litigation but ECOA disparate impact has not been formally tested on the current scorecard since 2021.

### Q5. "Who else is on the engagement team and what's the deliverable?"

**Interviewer's answer**:
- **Partner** (face-to-client, owns relationship)
- **Engagement Manager** (drives the workplan)
- **You** (technical workstream — model build, data analysis)
- **Senior analyst** (business case / financial modeling — *not* technical)
- **Compliance advisor** (10% time — interprets reg findings)

**Deliverable** in 8 weeks: a board-ready recommendation memo with three appendices — (1) technical methodology, (2) financial impact projection, (3) implementation roadmap. The model you build is the *evidence base*, not the deliverable.

This is a critical distinction. The candidate who thinks the model is the deliverable will over-build and under-communicate.

---

## Tier 2 — questions a stronger candidate asks within the first 15 minutes

### Q6. "Has the underwriting team's macro hypothesis been tested?"

**Interviewer's answer**: Not rigorously. They pointed at the Fed funds rate and called it a day. No analysis of whether the default uptick is concentrated in segments that *would* be macro-sensitive (e.g., variable-rate exposure, debt-service-burdened borrowers) vs. evenly distributed (which would point to a scorecard problem, not a macro problem).

This is **your first early win** — proposing to decompose the default uptick into "what's macro" vs. "what's scorecard staleness" before doing any modeling. Senior interviewers love this move because it shows you don't conflate the diagnostic with the solution.

### Q7. "What data do we have access to?"

**Interviewer's answer**: NovaLend has given us:
- 3 years of loan applications (~2.8M)
- Bureau pulls at time of application
- Repayment history (monthly cash-flow records)
- Their current scorecard's scores for each historical applicant
- Loan terms, default outcomes, and recovery data on charged-off loans

What we **don't** have:
- Real-time bureau pull capability (we'll work off snapshots)
- Customer service / call center logs
- External macro data (we can pull public sources)
- Geocoded applicant data beyond state (fair-lending implication)

For purposes of this practice repo, the Home Credit Credit Risk Model Stability Kaggle dataset is the stand-in for NovaLend's data. The Kaggle dataset has the same shape (multi-table, applications + bureau + behavior + outcomes) and the same stability evaluation philosophy.

### Q8. "What's the data science team currently doing? Will we step on toes?"

**Interviewer's answer**: NovaLend has a small data science team (4 people, mostly former actuaries). They're skeptical of consulting — last firm built them a "black box GBM" that the CRO had to pull from production because it failed model risk review. Your political reality: any model you propose has to be *more* defensible than what their internal team would have built, not less.

This shapes everything downstream. **Interpretability is not optional**.

### Q9. "What's the partner's view going in?"

**Interviewer's answer**: She thinks the answer is "yes, modernize the scorecard, but the priority is governance, not the model itself." She's not going to tell you that directly — she wants you to find your way there. But she'd be uncomfortable with a recommendation that says "replace the scorecard with a black-box ML system." She'd be comfortable with "replace the scorecard with a documented, monitored ML system whose performance gains are validated against an interpretable benchmark and whose limitations are quantified."

### Q10. "What's the success criterion for our recommendation?"

**Interviewer's answer**: Three layers, in order of importance to the client:
1. **Defensibility** — can the recommendation survive a board risk committee, an OCC follow-up exam, and a fair-lending challenge?
2. **Economic value** — is the projected benefit large enough to justify the implementation cost? (Working assumption: any new system needs to pay back implementation in 18 months.)
3. **Time-to-value** — when does NovaLend start seeing the benefit? If it's >24 months, the board may prefer to wait for next year's strategic review.

---

## Tier 3 — questions that mark you as senior (ask one or two of these)

You don't ask all of these. You pick the one or two that the *answers already on the table* would not have addressed.

- "What's our hypothesis on whether the 2019 scorecard's coefficient stability has decayed, vs. it's structurally a different population now?" *(separates concept drift from data drift)*
- "Is the CRO comfortable with us building a champion-challenger setup where her team would operate the challenger for 12 months before any production cutover?" *(addresses politics + governance simultaneously)*
- "Are there any segments where we *should not* try to improve the model — e.g., where the marginal applicant is so risky that the right answer is policy, not modeling?" *(shows you understand the limits of ML)*
- "How does NovaLend's loan pricing work? Is the model output used only for approve/decline, or also for rate-setting?" *(if rate-setting, ECOA implications are much heavier)*
- "What's the appetite for synthetic adverse action codes vs. the SHAP-derived versions that have started showing up in fintech? Has compliance signed off on that pattern?" *(shows you know what's current in the industry)*

---

## What you do *after* clarifying

Once you've asked your clarifying questions and gotten answers, you owe the interviewer:

1. **A 30-second restated problem** — "OK, so to make sure I have this right: NovaLend's board needs a recommendation on whether to modernize their credit decisioning system. The core diagnostic question is whether the rising default rate is driven by scorecard staleness or by macro conditions. The deliverable is a board memo, not a model, and any recommendation has to clear SR 11-7 and ECOA defensibility bars. Anything I'm missing?"
2. **A structured approach** — your issue tree / workplan. See [03_follow_up_prompts.md](03_follow_up_prompts.md) for what comes next.

If the interviewer says "good, now walk me through your approach," that's your cue to move to [03_follow_up_prompts.md](03_follow_up_prompts.md).
