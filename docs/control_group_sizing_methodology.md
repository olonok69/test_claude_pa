# Control Group Sizing Methodology for Recommendation A/B Testing

**Author:** Data Science Team
**Date:** 18 February 2026
**Scope:** All CloserStill Media recommendation pipelines (TSL, LVS, BVA, CPCN, ECOMM)
**Tool:** `control_group_calculator.py`

---

## 1. Why Control Groups Matter

When we send personalised session or exhibitor recommendations to event visitors, we need to answer a fundamental question: **did the recommendations actually change behaviour, or would visitors have attended those sessions anyway?**

A control group is a randomly selected subset of visitors who receive recommendations from the algorithm (so we can measure what *would* have been recommended) but are **not sent** the personal agenda email. By comparing session attendance between the two groups post-event, we can isolate the **causal impact** of sending recommendations.

| Group | Algorithm runs? | Email sent? | Purpose |
|:------|:--------------:|:-----------:|:--------|
| Treatment | ✅ Yes | ✅ Yes | Measure attendance with recommendations |
| Control | ✅ Yes | ❌ No | Measure attendance without recommendations |

The difference between the two groups is the **recommendation lift** — the true value our system delivers.

---

## 2. The Core Formula

We use a **two-proportion z-test power analysis** to determine the minimum control group size. This is the standard statistical method for comparing two rates (treatment hit rate vs organic hit rate).

### 2.1 Equal Group Allocation

For equal-sized groups, the minimum sample size per group is:

```
              (Z_α/2 + Z_β)² × [p₁(1-p₁) + p₂(1-p₂)]
    n  =  ─────────────────────────────────────────────────
                          (p₁ - p₂)²
```

### 2.2 Unequal Group Allocation (Our Case)

Since we want most visitors to receive recommendations (e.g., 85% treatment / 15% control), we use the **unequal allocation adjustment**:

```
                    (Z_α/2 + Z_β)² × [p₁(1-p₁)/k + p₂(1-p₂)]
    n_control  =  ──────────────────────────────────────────────────
                                  (p₁ - p₂)²
```

Where **k = n_treatment / n_control** (the allocation ratio).

### 2.3 Parameter Definitions

| Parameter | Symbol | Typical Value | Description |
|:----------|:------:|:-------------:|:------------|
| Treatment rate | p₁ | 0.30–0.40 | Expected % of attended sessions that were recommended, for visitors who received the email |
| Organic rate | p₂ | 0.20–0.25 | Expected % of attended sessions that were recommended, for visitors who did NOT receive the email |
| Minimum Detectable Effect | p₁ − p₂ | 0.08–0.15 | The smallest lift in percentage points we want to reliably detect |
| Significance level | α | 0.05 | Probability of a false positive (concluding there's lift when there isn't) |
| Statistical power | 1 − β | 0.80 | Probability of detecting a real effect when it exists |
| Z_α/2 | — | 1.96 | Z-score for α = 0.05, two-tailed |
| Z_β | — | 0.84 | Z-score for 80% power |
| Allocation ratio | k | 5–19 | Ratio of treatment to control group sizes |

---

## 3. How to Estimate the Input Parameters

The formula requires us to estimate the treatment and organic rates **before** the event. These come from prior post-show analyses.

### 3.1 Treatment Hit Rate (p₁)

This is the visitor-level hit rate from previous events:

| Event | Treatment Hit Rate | Source |
|:------|:------------------:|:-------|
| LVS 2025 | 34.4% | Post-show report |
| CPCN 2025 | ~30% | Post-show estimate |
| TSL 2026 (expected) | 30–35% | Based on LVS benchmark |

### 3.2 Organic Hit Rate (p₂)

This is harder to estimate because we've only recently started implementing control groups. Rules of thumb based on industry benchmarks and our LVS data:

- The organic rate is typically **60–75% of the treatment rate**
- For a 35% treatment rate → organic rate of ~21–26%
- **Conservative estimate: 20–25%** for planning purposes

As we accumulate post-show data with control groups, we'll refine these estimates per event type.

### 3.3 Minimum Detectable Effect (MDE)

The MDE = p₁ − p₂ is the **smallest lift we care about detecting**. This is a business decision:

- If we expect a 10pp lift but can only detect 15pp effects → we'll likely miss the real effect (underpowered)
- If we expect a 10pp lift and can detect 2pp effects → we're overpowered (wasting control group slots)

**Target:** Size the control group to detect an effect **50–75% of the expected lift**. If we expect 10pp, design for 5–7pp detection.

---

## 4. Sensitivity Analysis for TSL 2026

With 16,656 registered visitors and an expected organic rate of 25%:

| Control % | Control N | Treatment N | Ratio | MDE (pp) | Can Detect |
|:---------:|:---------:|:-----------:|:-----:|:--------:|:----------:|
| 3% | 499 | 16,157 | 32:1 | 5.5pp | 25% → 30.5% |
| 5% | 832 | 15,824 | 19:1 | 4.3pp | 25% → 29.3% |
| 7.5% | 1,249 | 15,407 | 12:1 | 3.6pp | 25% → 28.6% |
| 10% | 1,665 | 14,991 | 9:1 | 3.1pp | 25% → 28.1% |
| 12.5% | 2,082 | 14,574 | 7:1 | 2.9pp | 25% → 27.9% |
| **15%** | **2,498** | **14,158** | **5.7:1** | **2.6pp** | **25% → 27.6%** |
| 20% | 3,331 | 13,325 | 4:1 | 2.4pp | 25% → 27.4% |
| 25% | 4,164 | 12,492 | 3:1 | 2.2pp | 25% → 27.2% |

### How to Read This Table

- **MDE (pp)** = the smallest lift the test can detect at 80% power and 95% confidence
- At 5% control, we can detect a 4.3pp lift — well within our expected 8–10pp range
- At 15% control, we can detect a 2.6pp lift — this enables **segmented analysis** (new vs returning, by sector, etc.)
- Beyond 15%, diminishing returns set in — going from 15% to 25% only improves MDE by 0.4pp

### Diminishing Returns Visualisation

```
MDE
(pp)
 6 ┤ •
 5 ┤   •
 4 ┤      •
 3 ┤          •     •
 2 ┤                    •     •     •     •
 1 ┤
 0 ┼──────────────────────────────────────────
   0%   5%   10%   15%   20%   25%   30%   35%
                Control Group %

   ← Sweet spot: 5-15% for most events →
```

The curve flattens rapidly after ~10–15%. Increasing the control group beyond this point yields marginal statistical benefit while withholding recommendations from more visitors.

---

## 5. Scenario Comparison Across Event Types

Different events have different audience sizes and expected engagement levels:

| Scenario | Organic Rate | Treatment Rate | Lift | Min Control % | Min Control N |
|:---------|:-----------:|:-------------:|:----:|:------------:|:-------------:|
| Conservative | 20% | 28% | 8pp | 1.3% | 216 |
| Moderate (TSL expected) | 25% | 35% | 10pp | 0.9% | 149 |
| Optimistic (LVS-like) | 25% | 40% | 15pp | 0.5% | 83 |
| High-engagement event | 35% | 45% | 10pp | 1.1% | 183 |

These minimums assume you only need to detect the **overall** lift with no segmentation. For segmented analysis (which is usually what we want), multiply by 3–5×.

---

## 6. Practical Guidelines by Event Size

### 6.1 Rule of Thumb

| Event Size | Visitors | Recommended Control % | Rationale |
|:-----------|:--------:|:---------------------:|:----------|
| Small | < 2,000 | 15–20% | Absolute numbers are small; need larger proportion for adequate power |
| Medium | 2,000–10,000 | 10–15% | Good balance between power and coverage |
| Large | > 10,000 | 5–10% | Even 5% gives 500+ visitors; sufficient for overall lift detection |
| Large + segmented analysis | > 10,000 | 10–15% | Extra power needed for subgroup comparisons |

### 6.2 Event-Specific Recommendations

| Event | Expected Visitors | Recommended Control % | Control N | MDE (pp) |
|:------|:-----------------:|:--------------------:|:---------:|:--------:|
| **TSL 2026** | 16,656 | 10–15% | 1,665–2,498 | 2.6–3.1pp |
| **LVS 2026** | ~7,000 | 10–15% | 700–1,050 | 3.8–4.7pp |
| **BVA 2026** | ~7,000 | 10–15% | 700–1,050 | 3.8–4.7pp |
| **CPCN 2026** | ~1,500 | 15–20% | 225–300 | 7.0–8.2pp |
| **ECOMM 2026** | ~5,000 | 10–15% | 500–750 | 4.5–5.5pp |

For CPCN, the small visitor base means even 20% control only gives ~300 visitors — the MDE of ~7pp is close to the expected lift, so results may be inconclusive. Consider pooling CPCN data across multiple editions for more robust analysis.

---

## 7. Why 15% for TSL 2026

The current TSL 2026 configuration uses a **15% control group (2,496 visitors)**. This is justified by three factors:

### 7.1 Overall Lift Detection — Comfortable

With 2,496 control visitors, we can detect lifts as small as 2.6pp. Since we expect 8–10pp, we have a ~4× safety margin. Even if the actual lift is much smaller than expected, we'll still detect it.

### 7.2 Segmented Analysis — The Real Value

The main reason for 15% over 5% is **subgroup analysis**. We want to measure lift separately for:

- New visitors (58.1% of control = ~1,450 visitors)
- Returning visitors (41.9% of control = ~1,046 visitors)
- By professional function (top 5 functions each have 200+ control visitors)
- By sector (top 4 sectors each have 200+ control visitors)

At 5% (832 total), each subgroup would have too few visitors for reliable conclusions. At 15%, the largest subgroups have sufficient power for standalone analysis.

### 7.3 Trade-Off — Acceptable

Withholding recommendations from 2,496 visitors (15%) means ~14,160 visitors still receive their personal agendas. The business impact is modest — and the statistical value of understanding *how well* recommendations work (and for *whom*) far outweighs the cost of not sending 15% of emails.

### 7.4 Known Limitation

The 15% allocation introduced a **5.9pp skew in the new/returning ratio** (control has 41.9% returning vs 36.0% in treatment). This should be addressed by:

1. Segmenting post-event analysis by new/returning status
2. Reporting weighted average lift using treatment-group proportions as weights
3. Considering **stratified random sampling** in future runs to guarantee balanced demographics

---

## 8. Post-Event Measurement Framework

### 8.1 Core Metrics

| Metric | Formula | Interpretation |
|:-------|:--------|:---------------|
| **Treatment Hit Rate** | (Recommended sessions attended by treatment visitors) / (Total sessions attended by treatment visitors) | How often recommendations match actual attendance when sent |
| **Organic Hit Rate** | (Recommended sessions attended by control visitors) / (Total sessions attended by control visitors) | How often recommendations would have matched attendance anyway |
| **Absolute Lift** | Treatment Hit Rate − Organic Hit Rate | Percentage point improvement from sending recommendations |
| **Relative Lift** | (Treatment − Organic) / Organic × 100% | Percentage improvement over baseline |

### 8.2 Statistical Significance Test

After the event, apply a two-proportion z-test to determine if the observed lift is statistically significant:

```
              p̂₁ - p̂₂
    z = ─────────────────────────
         √[ p̂(1-p̂) × (1/n₁ + 1/n₂) ]

    where p̂ = (x₁ + x₂) / (n₁ + n₂)  (pooled proportion)
```

If |z| > 1.96, the lift is significant at the 5% level.

### 8.3 Confidence Interval

Report the lift with a 95% confidence interval:

```
    CI = (p̂₁ - p̂₂) ± 1.96 × √[ p̂₁(1-p̂₁)/n₁ + p̂₂(1-p̂₂)/n₂ ]
```

This gives stakeholders a range: "We observed a 9.2pp lift (95% CI: 6.1pp to 12.3pp)."

---

## 9. Using the Calculator

### 9.1 Running the Full Analysis

```bash
python control_group_calculator.py
```

This produces the complete analysis for TSL 2026, including sensitivity tables and scenario comparisons.

### 9.2 Using Programmatically

```python
from control_group_calculator import (
    find_optimal_control_percentage,
    print_sensitivity_table,
    detectable_effect,
)

# Find optimal control % for a specific event
result = find_optimal_control_percentage(
    total_visitors=7000,       # LVS 2026
    p_control=0.25,            # Expected organic rate
    p_treatment=0.35,          # Expected treatment rate
    alpha=0.05,
    power=0.80,
    max_control_pct=20.0,
)
print(result)

# Generate sensitivity table for any event
print_sensitivity_table(
    total_visitors=7000,
    p_control=0.25,
    percentages=[5, 10, 15, 20],
)

# Calculate MDE for a fixed control group size
mde = detectable_effect(
    n_control=700,             # Fixed at 10%
    p_control=0.25,
    p_treatment_estimate=0.35,
    allocation_ratio=9.0,      # 90/10 split → k=9
)
print(f"MDE: {mde * 100:.1f}pp")
```

### 9.3 Integrating into the Pipeline Config

The calculator can inform the `control_group.percentage` setting in each event's YAML config:

```yaml
# config/config_tsl.yaml
recommendation:
  control_group:
    enabled: true
    percentage: 15        # Validated via power analysis (MDE = 2.6pp)
    random_seed: 42
```

---

## 10. Key Takeaways

1. **The formula is standard** — two-proportion z-test power analysis, available in any statistics textbook or tool. Our `control_group_calculator.py` implements it with the unequal allocation adjustment needed for our use case.

2. **Bigger is not always better** — diminishing returns kick in around 10–15% for large events. Going from 15% to 25% barely improves detection capability while withholding recommendations from 1,600+ additional visitors.

3. **Segment analysis drives the real sizing need** — detecting overall lift requires surprisingly few control visitors (~150 for TSL). The reason to go larger (10–15%) is to enable subgroup comparisons (new vs returning, by function, by sector).

4. **Baseline rates matter more than you think** — the organic rate is the hardest parameter to estimate and has the biggest impact on required sample size. As we accumulate post-show control group data across events, these estimates will become more precise.

5. **Stratified allocation is the next improvement** — the 5.9pp new/returning skew observed in TSL's 15% control group demonstrates that simple random sampling at larger percentages can introduce demographic imbalances. Implementing stratified random sampling (balancing key attributes within the control group) would eliminate this issue.

---

*Document prepared for internal use. Calculator tool: `control_group_calculator.py`*
*Methodology validated against standard statistical references (Cohen 1988, Fleiss et al. 2003).*
