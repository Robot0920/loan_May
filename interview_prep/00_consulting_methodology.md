# 00 — Tech Consulting Methodology (the toolkit)

> **What this is**: A transferable methodology for tech consulting DS work — applies to credit risk, supply chain, churn, fraud, recommender systems, whatever. Not a worked answer to any specific case. Read this **first**; the other notes in `interview_prep/` are case practice that exercises this methodology.
>
> **How to use it**: When stuck on any case (real or interview), come back here. Pick the relevant module (Part 1–5), follow the procedure, and check yourself against the anti-patterns. Over time the procedure becomes automatic and the anti-patterns become reflexive avoidances.
>
> **The 5 modules**:
>
> 1. **Goal decomposition** — turn a vague client ask into a structured problem
> 2. **Data understanding** — read a new data ecosystem fast, without writing code first
> 3. **Target selection** — pick the right thing to predict (the most-flunked step)
> 4. **EDA design** — explore on purpose, not for fun
> 5. **Insight generation** — make findings the client can act on, not trivia

---

## The single mental model that ties all 5 modules together

```
        ┌────────────────────────────────────────────────────────┐
        │  EVERY consulting DS task can be written as a chain:   │
        │                                                        │
        │   Goal → Decision → Prediction → Target → Data → EDA → │
        │                          ↑                             │
        │                          this is the joint where most  │
        │                          junior candidates break       │
        └────────────────────────────────────────────────────────┘
```

The chain must be **bidirectional**:
- **Forward** (decomposition): goal forces decision, decision forces prediction, prediction forces target
- **Backward** (validation): is the data actually sufficient for the target? does the prediction actually inform the decision? does the decision actually serve the goal?

A senior consultant walks both directions. A junior only walks forward.

---

## Part 1 — Goal Decomposition

### The principle

> **A client never tells you their real goal in the first sentence.** They tell you a *stated goal* (often growth/cost/risk language) that hides a *latent decision* they don't yet know how to make. Your job is to surface the latent decision.

### The procedure (do these in order — don't skip)

**Step 1.1 — Restate the goal back to the client in your own words.**

Format: "If I understand correctly, you want to ___, because ___, and the constraint is ___."

This catches misalignment in the first 60 seconds. The interviewer (or client) will correct you if you're off, which is free intelligence.

**Step 1.2 — Apply MECE to decompose into sub-problems.**

MECE = **M**utually **E**xclusive (no overlap), **C**ollectively **E**xhaustive (covers everything).

Two MECE patterns that work for ~80% of business goals:

| Pattern | When to use | Example |
|---|---|---|
| **Top-line × Bottom-line** | Profit / loss goals | "Grow revenue" → (price × volume) AND (cost reduction) |
| **Funnel decomposition** | Conversion / loss / churn goals | "Reduce defaults" → (entry rate × roll rate × loss given default × exposure) |
| **Audience × Action × Outcome** | Behavior change goals | "Increase adoption" → (who) × (does what) × (resulting in) |
| **Before × During × After** | Lifecycle / journey goals | "Improve customer experience" → onboarding × usage × support |

**Step 1.3 — For each sub-problem, name the *decision* it enables.**

A sub-problem without a decision is decoration. Force the question: *"If we solved this perfectly, what would the client actually do differently tomorrow?"*

**Step 1.4 — Walk backwards: does the union of decisions actually deliver the stated goal?**

If yes, your decomposition is complete. If no, you missed a sub-problem (decomposition not exhaustive) OR you have a sub-problem that doesn't matter (decomposition not mutually exclusive).

### The senior tools (deploy at least one in any case)

| Tool | What it is | When to use |
|---|---|---|
| **Issue tree** | A tree where the root is the goal and leaves are testable sub-questions | Default tool — start every case with this |
| **5 Whys** | Ask "why" repeatedly to reach root cause | When the stated goal is vague ("improve X") |
| **Pyramid principle** | Conclusion first, then 3 supporting arguments, then evidence per argument | Structuring your *answer*, not your analysis |
| **Hypothesis-first** | Form 2–3 candidate hypotheses BEFORE looking at data, then design tests to discriminate them | Always — pure exploration is slow |
| **Decision rights mapping** | List who has authority to make each sub-decision | When the engagement involves multiple stakeholders |

### The checks (you did this right if...)

- ☐ You can finish the sentence "If I had a perfect prediction of __, the client could decide __, which would improve __ by __."
- ☐ Your sub-problems are MECE (no overlap, covers all of the goal)
- ☐ Each sub-problem has a named decision it enables
- ☐ You can defend why you didn't include any obvious sub-problem you left out
- ☐ You named the implicit constraints (regulatory, time, cost, political) the client didn't mention

### Anti-patterns (junior mistakes)

| ❌ Don't | ✅ Do instead |
|---|---|
| Jump from goal to "I'd use XGBoost" | Spend 5–10 min on decomposition before naming any technique |
| Use generic decomposition (people/process/technology) | Use a goal-specific decomposition pattern (funnel, top×bottom, etc.) |
| List 8 sub-problems | 3–4 max — anything more isn't MECE, you're just listing |
| Skip the "decision" question for sub-problems | Force a decision for each — drops weak sub-problems automatically |
| Solve before scoping | Defer technique discussion until the partner asks for it |

---

## Part 2 — Data Understanding (Quickly, Without Code)

### The principle

> **Read what the data is *about* before reading what's *in* it.** Metadata, lineage, ownership, schema docs, and naming conventions give you 60–80% of what you need to know — for free. Writing `df.describe()` is the **second** step, not the first.

### The procedure

**Step 2.1 — Inventory by source.**

For each table / dataset, capture:
- **Source**: internal system vs external provider vs derived
- **Owner**: who maintains it, who you'd call if it broke
- **Freshness**: how often it updates, SLA
- **Lineage**: where its columns come from (upstream pipelines)
- **Grain**: what one row represents

This is your "data catalog" entry even if no formal catalog exists. **Do this BEFORE loading anything.**

**Step 2.2 — Read schema documentation.**

In order of preference:
1. dbt docs / data catalog (DataHub, Atlan, Collibra)
2. Schema file or DDL in version control
3. The `INFORMATION_SCHEMA.COLUMNS` table in the warehouse
4. Whatever README the data team wrote (always read; usually incomplete)
5. The column names themselves (last resort)

For Kaggle / public data: read the dataset description and `feature_definitions.csv` first. **Naming conventions** are the largest free signal — Home Credit's `_P/_A/_D/_M/_T/_L` suffixes tell you dtype + transformation; production data often has similar conventions (e.g., `_dt` = date, `_amt` = amount, `_cd` = code).

**Step 2.3 — Apply the 5 W's + H to the dataset as a whole.**

| Question | What it tells you |
|---|---|
| **Who** owns it / produces it | Who to ask when something breaks; the team's incentives shape the data |
| **What** is one row | Grain. Foundational. Wrong here = everything downstream is wrong |
| **When** is it produced / what time range | Drift candidates; whether you have enough history for time-aware validation |
| **Where** does it live | Access mechanism; constraints (PII walled gardens, region locks) |
| **Why** does it exist | What business process generates it; rare cases imply rare events |
| **How** was it transformed before arriving | Stage of cleaning; which fields are raw vs. derived |

**Step 2.4 — Classify columns by role.**

Every column in any dataset is one of:
- **Identifier** (`*_id`, `case_id`) — for joins, not features
- **Timestamp** (`*_dt`, `*_date`, `*_ts`) — for ordering / windowing
- **Categorical** (`*_cd`, `*_type`, `*_status`) — needs encoding
- **Numeric metric** (`*_amt`, `*_count`, `*_pct`) — direct feature material
- **Free text / blob** — usually drop or NLP-process separately
- **Flag / boolean** (`is_*`, `has_*`) — direct feature, watch class balance
- **Target candidate** (`*_default`, `*_churn`, `*_outcome`) — handled separately (see Part 3)

A column you can't classify is a question for the data owner.

**Step 2.5 — Profile in the warehouse, not in Python (for big data).**

If the data is in Snowflake / Databricks / BigQuery, do your first-pass profile via SQL:

```sql
SELECT
    column_name,
    COUNT(*) AS rows,
    COUNT(column_name) AS non_nulls,
    COUNT(DISTINCT column_name) AS distinct_values,
    APPROX_PERCENTILE(column_name, 0.5) AS median   -- numeric only
FROM schema.table
GROUP BY column_name;
```

In-warehouse SQL handles 10B rows; pandas chokes at 10M. **Pull to Python only after you know what subset you need.**

For Kaggle / Python-only contexts, Polars is the right tool for this scale (5M+ rows, multi-table joins).

### The senior tools

| Tool | What it does | Where it lives |
|---|---|---|
| **Data dictionary as code** | Auto-generated docs of every column + description + owner | dbt docs, Atlan, DataHub |
| **Lineage graph** | "where did this column come from" visualized | dbt, OpenMetadata, Marquez |
| **Schema tests** | Fail the pipeline if schema changes unexpectedly | dbt tests, Great Expectations |
| **Profile cards** | Standardized one-pager per table: grain, freshness, owner, sample | Often internal templates |
| **Data contracts** | Formal SLA between producer and consumer team | Newer pattern, gaining adoption |

### The checks (you did this right if...)

- ☐ You can name the grain of every table you'll use
- ☐ You know who owns each upstream source
- ☐ You know which fields are PII / sensitive / regulated
- ☐ You can list the naming conventions and what they encode
- ☐ You've identified ≥ 1 "known unknown" — a question only the data owner can answer

### Anti-patterns

| ❌ Don't | ✅ Do instead |
|---|---|
| Open the dataset in pandas and start `df.head()` | Read docs and schema first; you'll know what to look for |
| Trust column names blindly | Spot-check 2-3 values per "important" column to confirm meaning |
| Skip the data dictionary because it's tedious | The 30 min spent here saves 3 days of confusion later |
| Treat raw data as ground truth | Every dataset has a producer with incentives; some fields are intentionally lossy |
| Ignore the freshness SLA | If your model retrains weekly but bureau data updates monthly, you have a bug |

---

## Part 3 — Target Selection (The Most-Flunked Step)

### The principle

> **The target is reverse-engineered from the decision.** It is not "what's in the data". A perfect prediction of the wrong target is useless. An imperfect prediction of the right target is gold.

### The procedure

**Step 3.1 — Write the decision sentence.**

> "The client will decide ___ based on a prediction of ___, at the time of ___, and the consequence of a wrong prediction is ___."

If any blank is unfillable, you're not ready to pick a target.

**Step 3.2 — Test target candidates against the "good target" criteria.**

A good target satisfies all 8:

| # | Criterion | Test |
|---|---|---|
| 1 | **Observable** | Is it actually measured in your data? |
| 2 | **Actionable** | Does predicting it change a decision? |
| 3 | **Time-locked** | Can it be assigned to a specific date (no time travel)? |
| 4 | **Available with horizon** | Do you have outcomes within an acceptable wait time? |
| 5 | **Stable definition** | Has the definition been consistent historically? |
| 6 | **Sampling unbiased** | Is your training set representative of inference-time population? |
| 7 | **Sufficient events** | Enough positive cases to train (rule of thumb: ≥ 1000 events) |
| 8 | **Dollar-translatable** | Can you express it in business impact ($, time, count)? |

Fail any of these → either fix the target, change the decision, or document the limitation.

**Step 3.3 — Choose the target *type* by decision type.**

| Decision shape | Target type | Output |
|---|---|---|
| Yes / no | Binary classification | P(event) |
| One of several options | Multiclass classification | P(class_k) per option |
| How much | Regression | E[continuous outcome] |
| When | Survival / time-to-event | hazard function or quantile |
| How much, conditional on event | Two-stage (binary × regression) | P(event) × E[outcome \| event] |
| Effect of intervention | Causal / uplift modeling | E[outcome \| treat] − E[outcome \| control] |
| Best action under uncertainty | Optimization / bandit | argmax over policy |

**Step 3.4 — If multiple targets are plausible, build a target hierarchy.**

Often you'll have nested options (e.g., default → loss given default → recovery time). Pick the **most upstream target that still enables the decision** — upstream targets have more data and simpler models.

Only go downstream if the decision demands it. E.g., for limit-setting, predicting just default isn't enough; you need expected loss.

**Step 3.5 — Document what you *rejected* and why.**

In the deliverable: "We considered targets A, B, C. We chose B because [reason]. A was rejected because [reason]. C was rejected because [reason]." This is the **conceptual soundness** documentation a model risk reviewer (or interviewer) wants.

### Heuristics for common target traps

| Trap | What goes wrong | Fix |
|---|---|---|
| **Survivorship bias** | Target only observable for population that "made it" (e.g., approved loans only have default outcomes) | Document as limitation; consider reject inference |
| **Right censoring** | Outcome not yet observed for recent observations | Drop censored OR use survival analysis |
| **Definition drift** | Target redefined mid-history (policy change, system migration) | Cut training data to post-change period only |
| **Leakage in target** | Target derived from feature, feature appears in input | Audit every feature for time-of-knowledge |
| **Composite targets** | "Engagement = clicks + scrolls + purchases / 3" | Almost always wrong — separate models per component |
| **Proxy targets** | Real target unobservable, use a proxy that correlates loosely | Quantify proxy-true correlation; warn stakeholders |

### The checks

- ☐ You can write the decision sentence with no blanks
- ☐ Your target passes all 8 "good target" criteria (or you've documented failures)
- ☐ You've named at least 2 candidate targets and justified your choice
- ☐ You've identified and documented the leakage risks
- ☐ You've translated the target to a dollar / volume / time impact

### Anti-patterns

| ❌ Don't | ✅ Do instead |
|---|---|
| Pick the target column that's already labeled in the dataset | Pick the target your decision requires; check if you can construct it from data |
| Build a composite "score" as target | Build separate models for the components, combine after |
| Optimize for AUC without thinking about calibration | If downstream uses probability values, calibration matters more than ranking |
| Skip the rejection memo ("here's why I didn't choose target X") | This is what makes you sound senior |

---

## Part 4 — EDA Design (Explore on Purpose)

### The principle

> **Hypothesis-driven EDA beats exploratory EDA.** Every chart you make should test a specific question. Charts you make "just to look" are 90% wasted time and produce 100% of the misleading conclusions.

### The procedure

**Step 4.1 — Write your hypotheses BEFORE looking at data.**

Format: "I expect X to be true because Y. If I'm wrong, the data will show Z."

This is the single biggest leap from junior to senior EDA. It forces you to engage with the business / domain before being biased by what's in front of you.

For a credit risk EDA, hypotheses might be:
- "Default rate is increasing over time → if true, vintage analysis will show recent quarters worse than older quarters at same months-on-book."
- "Default rate is concentrated in under-30 thin-file borrowers → if true, decomposition by (age × file thickness) will show this segment 2-3x the average."
- "Missing income_verified field is informative → if true, default rate for missing == True will differ from missing == False by > 1 pp."

Then design ONE chart per hypothesis.

**Step 4.2 — Use the 6-question backbone.**

For any new dataset, these 6 questions always apply. Answer them in this order:

| # | Question | Tool |
|---|---|---|
| 1 | **Distribution**: what does each feature look like alone? | Histogram, value counts |
| 2 | **Time**: how does it change across time buckets? | Line plot, faceted by quarter |
| 3 | **Segment**: how does it differ across business segments? | Bar plot, grouped |
| 4 | **Target relation**: how does it correlate with the target? | Boxplot grouped by target; mean target by bin |
| 5 | **Outliers**: which values are extreme, are they real or junk? | Top/bottom 20 rows; percentile cuts |
| 6 | **Missingness**: where are the gaps, are they informative? | Null fraction per column; target rate by missing flag |

**Step 4.3 — Compare-first. Never report absolute numbers alone.**

"Default rate is 3.4%" is useless. **"Default rate is 3.4%, up from 3.1% last quarter, while peer benchmark is 2.9%"** is an insight. Every number needs a comparison: historical baseline, peer benchmark, segment average, or counterfactual.

**Step 4.4 — Time-decompose first, then segment-decompose.**

Most insights hide in time series. Always plot the time view of any metric you care about before slicing other ways. After time, slice by segment — aggregates hide important segment differences (Simpson's paradox is real and frequent).

**Step 4.5 — Confounders are everywhere. Name them.**

For any observed relationship, write down the candidate confounders. Example: "Default rate is higher for new customers (1 yr tenure) than long-tenured customers" — confounder: **new customers were originated under a different scorecard**. Without controlling for vintage, you'd misread this as "tenure causes default".

### The senior tools

| Tool | What it gives you | When to deploy |
|---|---|---|
| **Vintage analysis** | Performance plotted by origination cohort × months-on-book | Whenever loans / accounts / subscriptions evolve over time |
| **PSI / KS test** | Quantify distribution drift between two time windows | Stability checks; concept drift detection |
| **Mosaic plot** | Visualize joint distribution of 2 categoricals + target | Segment × feature interaction |
| **Conditional default rate** | `default_rate.groupby([feat_bin, segment]).mean()` | Spot interactions without modeling |
| **Quantile-quantile (QQ) plot** | Compare two distributions (train vs test, segment A vs B) | Drift between populations |
| **Cumulative gains / lift chart** | Show concentration of the target | Use existing scorecard's outputs as a "feature" |

### The checks

- ☐ Every chart you produced answered a pre-written hypothesis
- ☐ Every number you reported has a comparison
- ☐ You've decomposed by time AND by segment
- ☐ You've named the candidate confounders for any apparent relationship
- ☐ You've identified ≥ 3 things that *surprised* you (if 0, you didn't engage)

### Anti-patterns

| ❌ Don't | ✅ Do instead |
|---|---|
| `pandas-profiling` / `ydata-profiling` and call it EDA | These are starting points; the real EDA is hypothesis-tested |
| Make 50 charts | Make 8 high-impact charts with one finding each |
| Report correlations without scatterplots | Correlations can hide non-linearity, outliers, Simpson's paradox |
| Use only aggregates | Always decompose; aggregates hide everything |
| Skip the missingness audit | Missingness patterns are often the highest-impact finding |
| Treat outliers as data errors by default | Sometimes outliers ARE the signal (fraud detection, default modeling) |

---

## Part 5 — Insight Generation (Make It Actionable)

### The principle

> **An insight is not a fact. An insight is a fact that changes a decision.** The "so what" test: would a senior stakeholder react with "interesting" (you found a fact) or with "what should we do about it?" (you found an insight)?

### The procedure

**Step 5.1 — Apply the 3-gate test to every finding.**

A finding becomes an insight only if it passes:

1. **Surprising** — would the client's VP be surprised by this? If no, it's a fact, not an insight.
2. **Decision-relevant** — does it change what the client would do? If no, it's trivia.
3. **Quantified** — can you put a dollar / volume / time number on it? If no, it's vibes.

Failing any gate → either dig further to upgrade it, or drop it from the deliverable.

**Step 5.2 — Format every insight in the F-I-A-E-C structure.**

| Element | Content |
|---|---|
| **F**inding | One sentence stating the specific quantified observation |
| **I**mplication | One sentence on what this means for the client |
| **A**ction | One sentence on what to do about it |
| **E**vidence | The chart / number / analysis that supports it |
| **C**onfidence | One line on how much you trust this finding (sample size, caveats) |

Example:

> **F**: 47% of the 30-day-late roll to 90-day late in Q4, up from 38% in Q1 — a 9 pp shift concentrated in borrowers with debt-to-income > 40%.
> **I**: The scorecard is correctly identifying default risk at origination but failing to capture the stress-period roll-to-default behavior in high-DTI segments. This is a roll-rate problem, not an origination problem.
> **A**: Recommend a roll-rate model overlay specifically for the high-DTI segment, and re-evaluate collections staffing for that cohort. Origination scorecard change is NOT the right intervention.
> **E**: See `notebooks/02_eda.py` Cell 12 — quarterly roll rate by DTI bucket.
> **C**: High — sample size N=87k in Q4 high-DTI segment; pattern consistent across 3 quarters.

**Step 5.3 — Prioritize findings by impact × confidence × actionability.**

In any deliverable, you'll have 5-20 findings. The client (or interviewer) only remembers 3. Rank them and lead with the top 3.

Rough scoring rubric (0-3 each, multiply):

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Impact | Negligible | Tactical | Strategic | Existential |
| Confidence | Anecdote | Single test | Replicated | Triangulated |
| Actionability | Cannot act | Long-term | This quarter | Today |

A finding with impact=3, confidence=2, actionability=3 (18) beats a finding with 3,3,1 (9). The first is what you lead with.

**Step 5.4 — Use the pyramid principle for the deliverable.**

Structure the deliverable top-down (Barbara Minto):

```
Conclusion / recommendation
├── Supporting argument 1
│   ├── Evidence 1a
│   ├── Evidence 1b
├── Supporting argument 2
│   ├── Evidence 2a
│   ├── Evidence 2b
└── Supporting argument 3
    ├── Evidence 3a
```

The executive reads only the top. The analyst reads the bottom. Both should get what they need without reading the other half.

**Step 5.5 — Always include "what's next, even if you don't know yet".**

Even a preliminary finding can guide the next analysis. "The default rate trend is flat across vintages → the next thing to test is segment-specific drift, specifically the under-30 thin-file segment." This shows you're thinking about the analysis as a flow, not a one-shot.

### The senior tools

| Tool | What it does | When to deploy |
|---|---|---|
| **Pyramid principle** | Conclusion-first structuring | All deliverables, all the time |
| **Action-grid (impact × effort)** | Visualize where to invest | When you have multiple recommendation candidates |
| **Counterfactual framing** | "If we don't act, what happens" | When recommending intervention |
| **Sensitivity analysis** | "What if my assumption is wrong by ±X%" | Quantitative recommendations |
| **Pre-mortem** | "Assume this fails — why?" | Before finalizing any recommendation |

### The checks

- ☐ Every "insight" passes the 3-gate test
- ☐ Every finding is in F-I-A-E-C format
- ☐ You've ranked findings and led with the top 3
- ☐ Your deliverable is structured pyramid-style
- ☐ You've named the "what's next" even for preliminary findings

### Anti-patterns

| ❌ Don't | ✅ Do instead |
|---|---|
| List 15 findings of equal weight | Rank and lead with 3 |
| State findings without dollar / impact context | Always translate to business units |
| Hide the conclusion at the end | Pyramid principle: lead with the answer |
| Use jargon ("model exhibits high AUC") | Translate ("model correctly ranks 84% of cases by risk") |
| Skip the action | A finding without an action is trivia |
| Pretend high confidence when you don't have it | Calibrated honesty signals seniority |

---

## The 10 senior moves (the synthesis checklist)

After applying all 5 modules, do these 10 things to feel senior:

1. **Restate the goal before solving** — Part 1
2. **Use MECE decomposition with a named pattern** — Part 1
3. **Read data docs / lineage / ownership before code** — Part 2
4. **Profile in warehouse SQL before pulling to Python** — Part 2
5. **Write the decision sentence to validate target** — Part 3
6. **Document rejected target candidates explicitly** — Part 3
7. **Hypothesis-write before charting** — Part 4
8. **Compare every number to a baseline / benchmark / segment** — Part 4
9. **Format every finding as F-I-A-E-C** — Part 5
10. **Pyramid-structure the final deliverable** — Part 5

If you hit 8 out of 10 in any case, you're operating at a senior level.

---

## How this maps to a 60-minute case interview

| Time | Activity | Methodology module |
|---|---|---|
| 0–5 min | Restate goal, ask clarifying questions | Part 1 |
| 5–15 min | Lay out MECE issue tree, propose hypotheses | Part 1 |
| 15–25 min | Walk through data understanding approach | Part 2 |
| 25–35 min | Define target, defend choice, name limitations | Part 3 |
| 35–45 min | Sketch EDA design with specific hypotheses | Part 4 |
| 45–55 min | Discuss what would constitute actionable insights | Part 5 |
| 55–60 min | Synthesize: pyramid recommendation | Part 5 |

This is the **bones**. The **flesh** (model architecture, evaluation framework, fairness, deployment, monitoring) lives in `interview_prep/03_follow_up_prompts.md` and `interview_prep/04_curveballs.md`. Master Parts 1–5 first; then layer the flesh.

---

## How to drill this methodology

Pick any business problem (real or hypothetical). Set a 30-minute timer. Walk through all 5 modules out loud (or in writing). Don't optimize for completeness — optimize for **noticing when you skipped a step**.

Some practice prompts that aren't credit risk (test transferability):
- An e-commerce client wants to reduce return rate by 20%
- A SaaS company wants to identify accounts at risk of churn 90 days out
- A supply chain client wants to predict warehouse out-of-stock events
- A telecom wants to optimize tower placement for 5G rollout
- A hospital network wants to predict patient no-shows

For each: write the decision sentence, choose a target, name the data you'd want, sketch the EDA, predict what an actionable insight would look like.

**The point isn't the answer. The point is whether the methodology runs smoothly through your head.**
