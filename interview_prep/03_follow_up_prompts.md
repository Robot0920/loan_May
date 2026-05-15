# Case 03 — Follow-Up Prompts (Progressive Deepening)

> Once you've handled the opener and the clarifying questions, the interviewer drills. They pick one branch of your issue tree and push you into the weeds, then back out, then push you into a different branch. This file simulates that.
>
> **How to use**: Work through each follow-up in order. Don't peek at the "what good looks like" until you've taken your shot.

---

## Follow-up 1 — Data strategy

> *"OK, you've laid out an issue tree. The partner wants you to pressure-test the data foundation before any modeling. Walk me through how you'd assess whether the data we have is sufficient to answer the diagnostic question — is the default uptick a scorecard problem or a macro problem?"*

### What a strong answer looks like

A junior candidate says "I'd do EDA." A strong candidate proposes a *structured data sufficiency assessment*:

1. **Population stability check** — has the applicant population shifted between the 2017–2019 scorecard development window and 2023–2024?
   - Compare distributions of all 35 scorecard inputs across vintages (PSI per feature)
   - If PSI > 0.25 on any high-weight feature: that's evidence the *world* changed, not the model
   - If PSI is low and defaults are still rising: model has decayed, not the world
2. **Target stability check** — has the *definition* of default been stable? (Sometimes operational policy changes — e.g., a new charge-off policy — masquerade as model decay.)
3. **Vintage analysis** — bucket loans by origination quarter, plot 90-day default by months-on-book. If recent vintages diverge from older ones at the same month-on-book, that's an underwriting/model problem, not macro.
4. **Macro overlay** — pull unemployment, CPI, Fed funds rate, and segment-level macro indicators. If the default uptick correlates with macro, fine; if it doesn't, macro hypothesis fails.
5. **Segment decomposition** — is the uptick concentrated in the two segments the CRO mentioned (under-30 thin file, three expansion states)? Or spread across the book? If concentrated, the diagnosis is different.

The key move: **you're separating "is the model broken" from "is the world different" before you build anything**. Senior interviewers will let you skip ahead to modeling only after you've shown you'd do this diagnostic first.

### Where this maps in your repo

- [docs/02_data_understanding.md](../docs/02_data_understanding.md) — write up the data audit plan
- [notebooks/01_data_audit.ipynb](../notebooks/01_data_audit.ipynb) — execute it
- [docs/03_data_gaps.md](../docs/03_data_gaps.md) — note what data you'd want but don't have

---

## Follow-up 2 — Feature engineering tradeoffs

> *"Suppose your data audit comes back clean and you decide to build a model. You have access to credit bureau pulls, internal application data, and 24 months of monthly repayment history per prior account. The partner asks: 'Are you going to engineer 30 features or 800? Both choices have showed up in industry. Defend your number.'"*

### What a strong answer looks like

This is a tradeoff question, not a feature engineering question. Don't list features — defend a *philosophy*.

**The senior framing**: "I'd target ~80–150 features. Here's why both extremes are wrong for this client."

- **30 features (interpretable purist)**: defensible to compliance, easy to audit, but leaves predictive signal on the table — especially the temporal aggregations that Kaggle winners on this exact dataset show are the strongest non-bureau signal. Likely under-performs the current scorecard once macro is controlled for.
- **800 features (Kaggle-style)**: maximizes leaderboard rank but is un-auditable. SR 11-7 requires "conceptual soundness" — every feature should be explainable to a model risk reviewer. 800 features means most are not. NovaLend's previous "black box GBM" got pulled from production for exactly this reason.
- **80–150 features (the right answer)**: gives you the temporal aggregations and ratio features that drive most of the lift, while keeping each feature individually justifiable. Targeted around 8–10 feature categories ([see docs/04_features.md](../docs/04_features.md)) rather than a kitchen-sink approach.

**Bonus move**: propose that *every* feature gets a one-paragraph business reasoning in `docs/04_features.md`. This is what survives a model risk review.

### Where this maps in your repo

- [docs/04_features.md](../docs/04_features.md) — the feature catalog with reasoning
- [src/features/](../src/features/) — the implementation, organized by feature category

---

## Follow-up 3 — Model family choice

> *"You've engineered your features. You're sitting in front of a blank notebook. You can pick logistic regression, gradient boosting, a neural network, or some ensemble. For each, give me a 30-second reason why it's wrong for this client — then tell me which you'd actually pick."*

### What a strong answer looks like

This is the rare interview question where the format of the answer is *part of the answer*. Don't just defend your choice — show you understand the alternatives' specific failure modes for *this* client.

| Choice | Why it's wrong here | When it would be right |
|---|---|---|
| **Logistic regression alone** | Will plateau at ~5 points of Gini below GBM on this dataset because the strongest signal is in nonlinear interactions between bureau aggregates and temporal trends. You'd leave meaningful economic value on the table. | If the client were a small lender with no MLOps maturity. |
| **Neural network** | Tabular data, ~3M rows — NNs do not reliably beat GBMs in this regime. And the SR 11-7 / ECOA explainability burden is harder. CRO will not approve. | If you had unstructured data (call transcripts, document scans) to fuse. |
| **Heavy ensemble (stacking)** | Compounds the interpretability problem. Adverse action explanations become "the average of five model interpretations" — not defensible to a fair lending audit. | In a research / Kaggle context where leaderboard rank is the only goal. |
| **Gradient boosting (the pick)** | Industry standard for credit risk for the right reasons: handles missingness natively, monotonic constraints available for stability, SHAP-derivable for adverse action codes, fast to train, well-understood by examiners. | Always — but pair with a logistic baseline for the SR 11-7 "interpretable benchmark" requirement. |

**The senior close**: "I'd build LightGBM as the champion, logistic regression with the same feature set as the interpretable benchmark, and report both. The benchmark anchors the conversation with model risk; the champion is what we'd recommend deploying."

### Where this maps in your repo

- [credit_risk_system_roadmap.md Phase 5](../credit_risk_system_roadmap.md) — full reasoning
- [notebooks/03_baseline_logistic.ipynb](../notebooks/03_baseline_logistic.ipynb) — the benchmark
- [notebooks/05_gbm_modeling.ipynb](../notebooks/05_gbm_modeling.ipynb) — the champion

---

## Follow-up 4 — Evaluation

> *"You've trained two models. They both look 'good.' How do you decide which to recommend?"*

### What a strong answer looks like

If you say "whichever has higher AUC," you've failed. The competition metric is *Gini stability*, and the client is a real lender, so the evaluation framework has four layers, in this order of priority:

1. **Stability over time** — walk-forward validation. A model whose Gini drops 8 points from Q1 to Q4 is worse than a model that's 3 points lower on average but stays flat. Production credit models that drift quarterly are operationally useless.
2. **Business simulation** — convert prediction → approval decision → expected profit at portfolio level. Compare against the rule-based baseline. This is what the CRO actually looks at. ("My model is 6.3% more profitable in simulation" lands very differently from "my AUC is 0.78.")
3. **Fairness** — 4/5 disparate impact rule, demographic parity, equal opportunity across protected attributes. If you fail any of these, the higher-AUC model is *not* deployable, full stop.
4. **Standard offline metrics** — AUC, PR-AUC, Brier, KS, calibration. These are the floor, not the ceiling.

**Killer move**: propose the recommendation framework *before* you have results. "If stability differs by < 2 Gini points, I recommend the more stable model. If business simulation differs by < 3% portfolio profit, I recommend the more stable model. Stability ties break in favor of the simpler model." This pre-commits you to a defensible rule and prevents post-hoc rationalization.

### Where this maps in your repo

- [docs/05_evaluation.md](../docs/05_evaluation.md) — the framework
- [notebooks/06_stability_analysis.ipynb](../notebooks/06_stability_analysis.ipynb)
- [notebooks/07_business_simulation.ipynb](../notebooks/07_business_simulation.ipynb)
- [notebooks/08_fairness_audit.ipynb](../notebooks/08_fairness_audit.ipynb)

---

## Follow-up 5 — Deployment & monitoring

> *"Pretend we've gotten the green light to deploy. Walk me through what 'deployment' actually means, and what could go wrong in the first 90 days."*

### What a strong answer looks like

Don't talk about Docker. Talk about *failure modes* and *mitigations*.

**Architecture (one paragraph, not a diagram)**: FastAPI service, model loaded in-memory at startup, single-record sync API at < 200ms p99, batch endpoint for backfill. Every prediction logged with timestamp, model version, input hash, predicted probability, top-5 SHAP reasons, request ID. Audit log is immutable and replayable.

**The four failure modes that matter**:

1. **Input drift** — bureau format changes, a new state goes live, an upstream data source has an outage that gets silently filled with defaults. Mitigation: PSI per feature per day, alert on > 0.10, page on > 0.25.
2. **Output drift** — approval rate quietly shifts because some segment is being scored differently than in training. Mitigation: daily histogram of predicted probabilities, alert on KS test > threshold vs. training distribution.
3. **Fairness regression** — disparate impact ratio creeps from 0.82 toward 0.78 over six months due to population shift. Mitigation: weekly Fairlearn job, alert at 0.80.
4. **Concept drift in target** — operational definitions of default change, charge-off policy changes, or there's a regulatory change in what counts as delinquency. Mitigation: outcome reconciliation report monthly, comparing predicted vs. actual default rate by segment.

**The retraining policy** — propose one. "Retrain quarterly on a rolling 24-month window, gate behind shadow-mode evaluation against current production model for 30 days, automatic rollback if stability metric degrades by > 5% vs. baseline."

### Where this maps in your repo

- [src/serving/](../src/serving/) — FastAPI implementation
- [src/monitoring/](../src/monitoring/) — drift detection
- [deployment/](../deployment/) — Dockerfile, compose
- [docs/10_governance.md](../docs/10_governance.md) — retraining & rollback policy

---

## Follow-up 6 — Compliance close

> *"Walk me through how you'd brief NovaLend's compliance officer in 5 minutes."*

### What a strong answer looks like

The compliance officer cares about three things, in this order:

1. **Can I document this to a regulator?** Yes — point at `docs/06_compliance.md` mapping every SR 11-7 principle to a project artifact, `docs/07_fairness_audit.md` for ECOA evidence, and `docs/99_decisions_log.md` for the conceptual soundness narrative.
2. **What's the worst-case adverse action defense?** Every prediction returns top-5 SHAP-derived reasons; reason codes are human-readable; the model is shadowed by an interpretable logistic benchmark; we can explain any individual decision to a customer or a regulator within 30 days.
3. **What's the disparate impact risk?** Quantified in `docs/07_fairness_audit.md` — 4/5 rule passes at 0.X on age and gender, no proxy testing on geography because we don't have ZIP-level data, and that gap is flagged in `docs/09_risk_register.md` as a known limitation requiring stakeholder input before production.

The compliance officer's response should be "OK, that's the standard package, plus you've done the disparate impact work in advance, plus you've flagged your own gaps. Send me the risk register." That's a successful 5-minute brief.

### Where this maps in your repo

- [docs/06_compliance.md](../docs/06_compliance.md) — SR 11-7 / ECOA / NIST mapping
- [docs/07_fairness_audit.md](../docs/07_fairness_audit.md)
- [docs/09_risk_register.md](../docs/09_risk_register.md)

---

## Follow-up 7 — The "what would you do differently" close

> *"You've presented to the board. They approved the recommendation. The CRO pulls you aside afterward and asks: 'If you had another four weeks of engagement, what would you do?' Three answers."*

### What a strong answer looks like

This is *not* a chance to list everything you wish you'd done. It's a chance to show you understand what matters next.

Pick three that span technical depth, governance, and political reality:

1. **Independent validation** — your project's single-developer validation does not meet SR 11-7's bar. Standing up a 2-person model validation team — internal or external — is the single largest credibility gap to close. (Technical / governance)
2. **Champion-challenger setup with the internal DS team** — give them ownership of the challenger model for 12 months. This is *political* work that pays dividends: their team becomes co-owners of the new model rather than skeptics. (Political)
3. **Macro overlay model** — the current model controls for macro implicitly through feature distributions but doesn't *react* to macro shifts in real time. A simple overlay (e.g., logistic model on unemployment-rate change x segment) would let the CRO tighten or loosen approval at the segment level when macro shifts. This is the one thing that would get the board to fund the next engagement. (Technical with business framing)

### Why this matters

The "what would you do differently" close is when interviewers test whether you understand the *limits* of your own work. Junior candidates either over-claim or rattle off a wishlist. Senior candidates name 2–3 specific, high-leverage things and explain *why* those specifically.

---

## Where to go next

If the basic case feels in-hand, go to [04_curveballs.md](04_curveballs.md) — the twists that separate strong from senior. If the math feels shaky, go to [06_estimation_drills.md](06_estimation_drills.md) first.
