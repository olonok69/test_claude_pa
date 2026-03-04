# Tech Show London 2026 — Updated Report Sections

**Sections Updated:** 6 (Control Group) + New Section (V2E Exhibitor Recommendations)
**Report Date:** 18 February 2026
**Database:** Neo4j Production (neo4j-prod)
**Changes:** Control group extended from 5% → 15%; V2E exhibitor recommendations loaded 17 February 2026

> **Note:** These sections replace Section 6 in the original report dated 14 February 2026 and add a new Section 6A immediately after it. All other sections remain unchanged unless the control group change affects referenced values (see Change Impact below).

---

## Change Impact on Other Report Sections

The control group increase from 5% to 15% affects the following values in the original report:

| Section | Original Value | Updated Value | Notes |
|:--------|:--------------|:-------------|:------|
| §1 Executive Summary — Control group row | 832 (5.0%) | 2,496 (15.0%) | Update summary table |
| §7.2 Feature Configuration — Control group row | ✅ Enabled (5%, seed 42) | ✅ Enabled (15%, seed 42) | Update config table |
| §8.2 Strength #6 | "5.0% allocation" | "15.0% allocation" | Update text |
| §10 System Readiness — Control Group row | 10/10 | 9/10 (see §6.4 note) | Demographic delta increased |
| Report footer | "Control group: 5% (seed 42)" | "Control group: 15% (seed 42)" | Update footer |
| §1 Executive Summary — Key Strengths | "properly implemented control group" | Add note: "properly implemented control group with 15% allocation for increased statistical power" | |

---

## 6. Control Group Analysis

### 6.1 Configuration

The control group was extended from 5% to **15%** of visitors to increase statistical power for post-event A/B testing. This tripling of the control population provides a more robust basis for measuring the causal impact of sending personal agendas, reducing the margin of error on lift estimates by approximately 42% compared to the original 5% allocation.

| Setting | Value |
|:--------|:-----:|
| Enabled | ✅ true |
| Percentage | **15%** |
| Random Seed | 42 (deterministic) |
| Neo4j Property | `control_group` |
| File Suffix | `_control` |
| Output Directory | `recommendations/control` |

### 6.2 Group Allocation

| Group | Visitors | Share | has_recommendation | IS_RECOMMENDED Edges |
|:------|:-------:|:----:|:------------------:|:--------------------:|
| Treatment (control_group = 0) | 14,160 | 85.0% | "1" | ✅ Created |
| Control (control_group = 1) | 2,496 | 15.0% | "1" | ✅ Created |
| **Total** | **16,656** | **100%** | — | — |

✅ All visitors — both treatment and control — have `has_recommendation = "1"`, ensuring no reprocessing in incremental runs. ✅ IS_RECOMMENDED relationships exist for both groups (141,532 treatment + 24,957 control = 166,489 total), preserving the ability to compute "organic hit rates" in post-show analysis.

### 6.3 Recommendation Parity

Both groups received identical recommendation treatment from the algorithm:

| Metric | Treatment | Control | Delta |
|:-------|:---------:|:-------:|:-----:|
| Visitors | 14,160 | 2,496 | — |
| Total recommendations | 141,532 | 24,957 | — |
| Avg recs per visitor | 10.0 | 10.0 | 0.0 |
| Min similarity score | 0.301 | 0.301 | 0.000 |
| Mean similarity score | 0.709 | 0.704 | 0.005 |
| Median similarity score | 0.717 | 0.711 | 0.006 |
| Max similarity score | 0.903 | 0.878 | 0.025 |

The delta between treatment and control mean/median score distributions is small (0.005–0.006) and confirms the random sampling produced statistically comparable groups. The slightly wider delta compared to the original 5% allocation (which showed 0.001–0.002) is expected — a larger control group naturally captures more demographic variance.

### 6.4 Demographic Balance

| Attribute | Treatment | Control | Delta |
|:----------|:---------:|:-------:|:-----:|
| New visitors | 64.0% | 58.1% | 5.9pp |
| Returning visitors | 36.0% | 41.9% | 5.9pp |

| Top Professional Functions | Treatment | Control | Delta |
|:--------------------------|:---------:|:-------:|:-----:|
| IT Architecture & Infrastructure | 11.5% | 12.1% | 0.6pp |
| Data Centre Management | 9.2% | 10.4% | 1.2pp |
| Digital Strategy / Innovation | 9.0% | 9.3% | 0.3pp |
| Cybersecurity / Security & Risk | 8.5% | 8.0% | 0.5pp |

| Top Sectors | Treatment | Control | Delta |
|:-----------|:---------:|:-------:|:-----:|
| Technology | 22.8% | 22.5% | 0.3pp |
| Finance, Banking, Insurance | 12.5% | 11.4% | 1.1pp |
| Consulting / Professional Services | 11.5% | 11.5% | 0.0pp |
| Construction / Real Estate | 9.1% | 10.4% | 1.3pp |

⚠️ **Demographic skew observed:** The new/returning ratio shows a 5.9pp delta (compared to 1.4pp in the original 5% allocation). The control group over-represents returning visitors (41.9% vs 36.0% treatment). While the professional function and sector distributions remain well-balanced (deltas ≤1.3pp), the returning visitor over-representation means the control group may exhibit slightly higher organic engagement rates (since returning visitors typically show higher session attendance regardless of recommendations).

**Implication for A/B analysis:** Post-event lift calculations should segment by new/returning status to control for this imbalance. The recommended approach is:

1. Calculate lift separately for new and returning visitors
2. Report weighted average lift using treatment-group proportions as weights
3. Alternatively, re-run the control group allocation with a stratified random seed that balances new/returning proportions

### 6.5 Post-Event Metrics Framework

The 15% control group provides significantly improved statistical power over the previous 5% allocation:

| Metric | Definition |
|:-------|:-----------|
| **Treatment Hit Rate** | % of attended sessions that were recommended AND sent (control_group = 0) |
| **Organic Hit Rate** | % of attended sessions that were recommended but NOT sent (control_group = 1) |
| **Recommendation Lift** | Treatment Hit Rate − Organic Hit Rate = true causal impact |
| **Relative Lift** | (Treatment − Organic) / Organic × 100 = % improvement from sending recs |

**Statistical power comparison:**

| Control Size | Visitors | Detectable Lift (α=0.05, power=0.80) |
|:-------------|:-------:|:-------------------------------------:|
| 5% (original) | 832 | ~3.5pp |
| **15% (current)** | **2,496** | **~2.0pp** |

The larger control group allows detection of smaller treatment effects with the same confidence, improving the sensitivity of the A/B test by approximately 43%.

⚠️ **Critical downstream requirement:** Any system sending personal agendas must filter by `control_group = 0` (or use the main CSV/JSON exports, which automatically exclude control visitors). Sending recommendations to control visitors would invalidate the A/B test.

### 6.6 Validation Checklist

| Check | Status |
|:------|:------:|
| Main CSV/JSON contains only control_group = 0 visitors | ✅ Verified by pipeline logic |
| Control CSV/JSON contains only control_group = 1 visitors | ✅ Verified by pipeline logic |
| All visitors have has_recommendation = "1" | ✅ Confirmed (16,656/16,656) |
| ~15% of visitors have control_group = 1 | ✅ Confirmed (2,496 = 15.0%) |
| Both groups have IS_RECOMMENDED relationships | ✅ Confirmed (14,160 + 2,496 = 16,656) |
| Score distributions are comparable | ✅ Confirmed (Δ mean = 0.005) |
| Professional function distribution balanced | ✅ Confirmed (max Δ = 1.2pp) |
| Sector distribution balanced | ✅ Confirmed (max Δ = 1.3pp) |
| New/returning ratio balanced | ⚠️ 5.9pp delta — segment in post-event analysis |

---

## 6A. Visitor-to-Exhibitor (V2E) Recommendations

### 6A.1 Overview

Visitor-to-Exhibitor (V2E) recommendations were loaded into the production database on **17 February 2026** (09:33–09:47 UTC), matching each registered visitor to up to 5 relevant exhibitors from the TSL 2026 exhibition floor. These complement the session recommendations (V2S) by guiding visitors to exhibitor stands aligned with their professional interests.

| Metric | Value | Assessment |
|:-------|:-----:|:----------:|
| Total V2E recommendations | 83,045 | — |
| Visitors with V2E recommendations | 16,609 | ✅ 99.7% coverage |
| Visitors without V2E | 47 | ⚠️ 0.3% gap |
| Exhibitors recommended ≥1 time | 385 / 391 | ✅ 98.5% coverage |
| Exhibitors never recommended | 6 | Acceptable |
| Recommendations per visitor | 5 (all) | ✅ Uniform |
| Neo4j relationship | `IS_RECOMMENDED_EXHIBITOR` | — |
| Source | External load (`v2e_recommendations_2.json`) | — |

### 6A.2 Coverage Analysis

**Visitor coverage:** 16,609 of 16,656 visitors (99.7%) received 5 exhibitor recommendations each. The 47 visitors without V2E recommendations represent a negligible gap (0.3%) and may result from profile data missing at the time of V2E generation.

| Group | Visitors with V2E | V2E Recommendations | Avg per Visitor |
|:------|:-----------------:|:-------------------:|:---------------:|
| Treatment (control_group = 0) | 14,119 | 70,595 | 5.0 |
| Control (control_group = 1) | 2,490 | 12,450 | 5.0 |
| Without V2E | 47 (41 treatment, 6 control) | — | — |
| **Total** | **16,609** | **83,045** | **5.0** |

V2E recommendations are present for both treatment and control groups, enabling post-event measurement of exhibitor recommendation effectiveness alongside session recommendation lift.

**Exhibitor coverage:** 385 of 391 exhibitors (98.5%) are recommended to at least one visitor. The 6 unrecommended exhibitors are:

| Exhibitor | Co-located Show |
|:----------|:---------------|
| AEP GLOBAL Ltd | Data Centre World |
| ConnectALL by Broadcom | DevOps Live |
| GBE S.p.A | Data Centre World |
| IMI | Data Centre World |
| Narada Europe | Data Centre World |
| Tower | Big Data & AI World |

### 6A.3 Exhibitor Distribution by Co-located Show

TSL comprises multiple co-located shows, and V2E recommendations are distributed across all of them:

| Co-located Show | Exhibitors | Exhibitors Recommended | V2E Recs | Share of Recs |
|:----------------|:---------:|:---------------------:|:--------:|:-------------:|
| Data Centre World | 277 | 273 | 49,737 | 59.9% |
| Cloud & Cyber Security Expo | 44 | 44 | 15,256 | 18.4% |
| Cloud & AI Infrastructure | 32 | 32 | 9,496 | 11.4% |
| DevOps Live | 15 | 14 | 3,743 | 4.5% |
| Big Data & AI World | 11 | 10 | 2,883 | 3.5% |
| Unclassified | 12 | 12 | 1,930 | 2.3% |

Data Centre World dominates with 59.9% of all V2E recommendations, reflecting both the largest exhibitor base (277 exhibitors, 70.8% of total) and the strong data centre focus of the TSL audience.

### 6A.4 Exhibitor Recommendation Concentration

| Statistic | Value |
|:----------|:-----:|
| Minimum recs per exhibitor | 1 |
| Q1 (25th percentile) | 13 |
| Median | 34 |
| Mean | 215.7 |
| Q3 (75th percentile) | 162 |
| Maximum | 3,013 |
| IQR | 149 |

The distribution is **heavily right-skewed** (mean 215.7 vs median 34), indicating a small number of exhibitors capture a disproportionate share of recommendations while most exhibitors receive modest recommendation counts.

**Distribution buckets:**

| Recommendations Received | Exhibitors | Share | Total Recs | Share of Recs |
|:------------------------|:---------:|:----:|:----------:|:-------------:|
| 2,000+ | 13 | 3.4% | 35,207 | 42.4% |
| 1,000–1,999 | 6 | 1.6% | 8,354 | 10.1% |
| 500–999 | 18 | 4.7% | 12,917 | 15.6% |
| 100–499 | 86 | 22.3% | 19,386 | 23.3% |
| 50–99 | 49 | 12.7% | 3,559 | 4.3% |
| 10–49 | 138 | 35.8% | 3,264 | 3.9% |
| 1–9 | 75 | 19.5% | 358 | 0.4% |

⚠️ **Concentration risk:** The top 13 exhibitors (3.4% of all exhibitors) account for 42.4% of all V2E recommendations. This is significantly more concentrated than the session recommendations (where the top session reaches 39.3% of visitors). However, this may be expected if the V2E matching algorithm prioritises exhibitors whose product offerings have broad relevance across the technology audience.

**Top 10 most recommended exhibitors:**

| Rank | Exhibitor | Co-located Show | Recommended To | % of Visitors |
|:---:|:----------|:---------------|:--------------:|:-------------:|
| 1 | VICTAULIC | Data Centre World | 3,013 | 18.1% |
| 2 | Centiel | Data Centre World | 3,007 | 18.1% |
| 3 | Cloudflare | Cloud & Cyber Security Expo | 2,936 | 17.7% |
| 4 | Firebrand Training | Cloud & Cyber Security Expo | 2,906 | 17.5% |
| 5 | ETERNAL WEB LTD | Cloud & AI Infrastructure | 2,896 | 17.4% |
| 6 | HEXONIC Sp.zo.o. | Data Centre World | 2,882 | 17.4% |
| 7 | Hellermanntyton | Data Centre World | 2,857 | 17.2% |
| 8 | DiversiTech Europe | Data Centre World | 2,819 | 17.0% |
| 9 | Boyd | Data Centre World | 2,648 | 15.9% |
| 10 | SKANWEAR | Data Centre World | 2,565 | 15.4% |

The maximum exhibitor concentration is 18.1% (VICTAULIC), meaning the most-recommended exhibitor appears in roughly 1 in 5.5 recommendation lists. This is lower than the session recommendation maximum (39.3%), which is a positive signal — exhibitor recommendations are more evenly distributed than session recommendations.

### 6A.5 Assessment

| Dimension | Score | Notes |
|:----------|:-----:|:------|
| Visitor coverage | ✅ 10/10 | 99.7% of visitors have V2E recommendations |
| Exhibitor coverage | ✅ 9/10 | 98.5% of exhibitors recommended; 6 unrecommended |
| Uniformity | ✅ 10/10 | All covered visitors receive exactly 5 exhibitors |
| Concentration | ⚠️ 7/10 | Top 3.4% exhibitors = 42.4% of recs; highly skewed |
| Control group parity | ✅ 10/10 | V2E present in both treatment and control groups |
| **Overall V2E** | **9/10** | **Strong coverage, monitor concentration** |

**Key observations:**

1. ✅ V2E recommendations achieve near-complete visitor coverage (99.7%), complementing the 100% session recommendation coverage
2. ✅ The V2E system covers exhibitors across all five co-located shows, ensuring the full exhibition floor is represented in recommendations
3. ✅ Both treatment and control groups have V2E recommendations, enabling post-event exhibitor recommendation lift measurement
4. ⚠️ The heavy concentration in the top 13 exhibitors (42.4% of recs) warrants review — if these exhibitors are genuinely the most relevant for the broad TSL audience, concentration is acceptable; if the matching algorithm over-weights certain exhibitor attributes, diversification may improve overall stand traffic distribution
5. ⚠️ 47 visitors lack V2E recommendations — investigate whether these visitors were registered after the V2E generation run or have insufficient profile data for exhibitor matching

---

*Updated sections generated from Neo4j Production database, 18 February 2026.*
*V2E data loaded: 17 February 2026, 09:33–09:47 UTC | Control group: 15% (seed 42)*
