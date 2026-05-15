# Case 04 — Curveballs (the Twists That Separate Senior)

> Real interviewers love to wait until you're cruising and then drop a question that tests whether you can hold the line under pressure. These are the questions you should prepare for *after* you can handle 01–03 fluently.
>
> Most of these don't have a single right answer. They test how you reason when the rules of the game shift.

---

## Curveball 1 — "Your CEO wants you to use a neural network. Defend or comply."

**Why this is hard**: You've correctly chosen GBM. But the CEO read a McKinsey article about generative AI and wants the project to "use AI." Saying "your CEO is wrong" is a junior move. Saying "yes, deep learning!" is also a junior move.

**The senior response (skeleton)**:

> "I'd want to understand what the CEO's actually trying to achieve. If it's a real concern about whether we're leaving performance on the table — I can show that side-by-side on this dataset. Tabular GBM beats off-the-shelf NN by 3–5 Gini points and is faster to train. If it's a positioning concern — wanting to be able to say 'NovaLend uses AI' — there are two paths: we could call our GBM an AI system (which it is), or we could add a deep learning *complement* on the unstructured data we're not currently using, like call transcripts or document scans. The second path would be a 6-week incremental engagement, and I can put together a one-pager on the business case if it's useful."

This answer:
- Doesn't argue with the CEO directly
- Diagnoses *why* the CEO is asking
- Offers a path that respects the constraint without compromising the core model
- Implicitly upsells the next engagement

---

## Curveball 2 — "Regulators are coming Monday. Where are you exposed?"

**Why this is hard**: This tests whether you've internalized the gap between "done" and "audit-defensible." It also tests whether you can answer a stress question with calibrated honesty.

**The senior response (skeleton)**:

> "Three exposures, in order. First, our independent validation is single-developer — that's the standard SR 11-7 finding and we'd flag it before they do, and have a written plan for staffing it. Second, we don't have ZIP-level data, so our fair-lending audit can't test for geographic disparate impact — that's a known gap in `docs/09_risk_register.md` and we'd own it explicitly. Third, our adverse action reason codes are SHAP-derived rather than coefficient-derived; OCC examiners are still forming a view on that pattern, so we'd want to walk them through the methodology and offer the logistic benchmark's coefficient-based reasons as a backup."

The pattern: name the exposure → acknowledge it before they find it → explain your mitigation. Confident, calibrated, no defensiveness.

---

## Curveball 3 — "Your model just denied your CEO's cousin a loan. Walk me through what happens next."

**Why this is hard**: This is a story problem, not a technical problem. It tests whether you can map your technical work onto a real operational situation that someone senior at the bank will actually face.

**The senior response (skeleton)**:

> "The decision flow is the same as for any applicant — that's by design. The system returns a probability and top-5 SHAP reason codes. Underwriting's adverse action letter generator turns those into a Reg B-compliant notice within 30 days. If the cousin disputes the decision, the customer service workflow includes a human review path — an underwriter pulls the file and the SHAP explanations, decides whether to override, and if the override is granted, it goes into our override log. That log is one of our monitoring inputs: high override rates on a segment trigger a review of whether the model's mis-scoring that segment systematically.
>
> "The CEO doesn't get a private override path. That's the right answer operationally — overrides have to be logged and auditable, full stop. If the CEO leans on the CRO to bend that, the CRO has cover because the audit trail exists."

The killer move at the end: connecting the cousin's case to the *operational design* of the override system. That's what makes this answer senior.

---

## Curveball 4 — "Your model has the highest AUC the bank has ever seen. Why are you suspicious?"

**Why this is hard**: This is a *trap* question. The interviewer wants to know if you're conditioned to celebrate good numbers, or if your first instinct is to look for what's wrong with them.

**The senior response (skeleton)**:

> "I'd suspect leakage before I celebrate. Specifically: did any feature accidentally encode the target? On this dataset the obvious one is anything derived from `months_balance` that includes months *after* the application date. The temporal aggregations have to be strictly pre-application. I'd also check: is any feature suspiciously high in univariate predictive power? On Home Credit, individual features rarely hit AUC > 0.65 on their own — if one's hitting 0.80, that's a leakage signal. And I'd check the time-split AUC: if the in-time AUC matches the out-of-time AUC, the model's stable; if in-time is way higher, there's overfitting to a temporal artifact."

The general principle: extraordinary results require extraordinary scrutiny. State three specific checks, not a vague "I'd validate."

---

## Curveball 5 — "Your model says approve, the rule says deny. Who wins?"

**Why this is hard**: This is about *governance*, not about modeling. It tests whether you've thought about the operating model, not just the model.

**The senior response (skeleton)**:

> "The rule wins, always, in any case where the rule is a *policy* (e.g., minimum age, no lending to active bankruptcies). Those aren't predictive features — they're business decisions encoded as code, and the model isn't competent to override them.
>
> "In cases where the 'rule' is the *old scorecard*, it's the opposite — the new model wins, because we have evidence it outperforms the rule across the dimensions that matter. But we wouldn't switch overnight. The right pattern is a 90-day shadow period where both run in parallel and we log every disagreement. The disagreements are the most informative signal — they're the cases where the systems see the borrower differently. We'd review the top 100 disagreements with the underwriting team before any production cutover."

The senior signal: distinguishing "rule as policy" from "rule as legacy model" — and proposing the shadow-mode pattern without being prompted.

---

## Curveball 6 — "What's the *one* thing in this whole project you're least confident in?"

**Why this is hard**: This tests intellectual honesty under pressure. The candidate who says "nothing, I'm confident in all of it" loses. The candidate who lists 8 things loses. The candidate who picks one substantive thing and explains it crisply wins.

**The senior response (skeleton)**:

> "The stability metric. The competition's definition is mathematically well-defined, but I'm not fully convinced it captures the *kind* of stability NovaLend's CRO actually cares about. The competition metric punishes Gini variance across time windows. But operationally, what the CRO cares about is whether the model's *approval rate per segment* stays stable — because that's what shows up in compliance reports and in board metrics. Those two are correlated but not identical. If I had another two weeks, I'd build a parallel evaluation that tracks approval-rate stability per segment and reports both, and I'd want the CRO to tell me which one she'd anchor her decision on."

This answer:
- Picks a substantive concern (not a fake-modest one like "my Python style")
- Connects the technical concern to a business concern
- Names a concrete next step
- Implicitly tees up another conversation with the client

---

## Curveball 7 — "If you had to deploy this tomorrow with no further work, would you?"

**Why this is hard**: There's no right answer. There's only the *quality of your reasoning*.

**The senior response (skeleton)**:

Either answer can be correct if defended well.

> "**No.** Three blockers. (1) Independent validation isn't done — that's the SR 11-7 deal-breaker. (2) The fair-lending audit on geography is incomplete because we don't have the data. (3) We haven't shadow-tested against the existing scorecard, so the rollout would be cold-cut, which is unacceptable in production credit."

OR:

> "**Yes, but only in shadow mode.** The model would score every application but the existing scorecard would make the actual decisions. That's safe because the model never affects an outcome; it's pure observation. We'd run shadow for 90 days, evaluate every disagreement, and only then make a cutover proposal. That actually accelerates time-to-value because we're learning from real production traffic from day one."

The interviewer is testing whether you have a stance, not whether you have *their* stance.

---

## Curveball 8 — "Your model improves portfolio profit by 6%. The CRO loves it. Six months later defaults are *up*. What happened?"

**Why this is hard**: This is asking you to reason about *post-deployment failure modes* without the benefit of hindsight. It also tests whether you understand the gap between in-sample / simulated economic improvement and live performance.

**The senior response (skeleton)**:

Five likely culprits, in order of probability:

1. **Population drift** — the borrowers applying after launch aren't the borrowers the model was trained on. PSI on the input features should show this. Most common cause.
2. **Approval rate creep** — the model approved a different *mix* of borrowers than the old scorecard, and the marginal approved borrower (those at the new approval cutoff) is performing worse than expected. Check the cohort of "new approvals" — applicants who would have been declined under the old scorecard but approved under the new one.
3. **Macro shift** — unemployment ticked up, the model didn't react because it has no macro features. Mitigation: macro overlay model (see [03 follow-up 7](03_follow_up_prompts.md)).
4. **Adverse selection** — competitors changed pricing or tightened, sending their declines to NovaLend. The applicant pool shifted, but in a way that's not visible feature-by-feature. Hard to detect; show up as PSI on the *full feature vector*, not on any single feature.
5. **Operational error** — feature pipeline drift, missing data being filled with a different default, a bureau format change. Should have been caught by monitoring; if it wasn't, the monitoring gap is the real problem.

The senior close: "The most informative thing to do is decompose the default rise into 'new-approval cohort' vs. 'returning-segment cohort.' If the new approvals are bad, it's a model problem. If the returning segments are bad, it's an environment problem. Different fixes."

---

## When to deploy these in a real interview

Most interviewers will throw 1–2 curveballs in a 60-minute case. Don't try to use all of these. The skill is *recognizing* what kind of curveball you've been handed and responding in the right register:

- **Stress test of confidence** (1, 2, 6, 7): be calibrated, name specifics, don't bluff
- **Operational reality check** (3, 5, 8): show you've thought about how this works in a real bank
- **Trap question** (4): show your first instinct is skepticism, not celebration

If you can hold composure across two of these in a session, you're operating at a senior level.
