# Tech Show London 2026 — Pre-Show Recommendation Report

**Event:** Tech Show London (TSL) 2026
**Event Dates:** 4–5 March 2026
**Report Date:** 11 February 2026
**Pipeline Run:** 11 February 2026, 01:01 UTC
**Database:** Neo4j Production (neo4j-prod)
**Mode:** personal_agendas
**Configuration:** config/config_tsl.yaml

---

## 1. Executive Summary

The recommendation pipeline processed **7,046 registered visitors** for TSL 2026, generating personalised session recommendations for every single registrant. The system is operating at full coverage with strong data quality and well-calibrated similarity scoring.

| Metric | Value | Assessment |
|--------|:-----:|:----------:|
| Total visitors | 7,046 | — |
| Visitors with recommendations | 7,046 | ✅ 100% coverage |
| Total recommendations | 70,444 | — |
| Average recommendations per visitor | 10.0 | ✅ Target met |
| Returning visitors | 3,350 (47.5%) | Strong retention base |
| Control group | 352 (5.0%) | ✅ Correctly allocated |
| Max session concentration | 33.0% | ✅ Healthy |
| Weighted data quality | 95.9% | ✅ Excellent |
| Sessions with streams | 162/189 (85.7%) | ⚠️ 27 sessions unstreamed |
| Overall Grade | **B+** (82/100) | Good — minor cleanup needed |

**Key Strengths:** Full visitor coverage, excellent data quality across all six similarity attributes, well-distributed recommendations with no excessive concentration, properly implemented control group for A/B testing.

**Key Issues:** 27 sessions lack stream assignments (14 sponsored placeholders, 3 administrative fillers, 10 real content sessions), and 13 sessions receive zero recommendations. A "Closing Remarks — Theatre Chair" session is receiving 603 recommendations despite being a non-content session that should be excluded.

---

## 2. Visitor Demographics & Retention

### 2.1 New vs Returning Visitors

| Visitor Type | Count | Percentage |
|:------------|:-----:|:----------:|
| New Visitor | 3,696 | 52.5% |
| Returning from TSL 2025 only | 1,580 | 22.4% |
| Returning from TSL 2024 only | 494 | 7.0% |
| Returning from both TSL 2025 + 2024 | 1,276 | 18.1% |
| **Total Returning** | **3,350** | **47.5%** |

The event has a strong retention profile: nearly half of all registrants attended a prior TSL edition. The 1,276 visitors who attended both TSL 2025 and TSL 2024 represent a highly engaged core audience. Same_Visitor relationships confirm 2,856 links to TSL 2025 visitors and 1,770 links to TSL 2024 visitors.

### 2.2 Historical Attendance Data

Past-year session attendance provides the foundation for collaborative filtering recommendations:

| Past Event | Visitors with Attendance | Total Attendances | Avg Sessions per Visitor |
|:----------|:-----:|:-----:|:-----:|
| TSL 2025 (Visitor_last_year_bva) | 733 | 2,586 | 3.5 |
| TSL 2024 (Visitor_last_year_lva) | 402 | 1,110 | 2.8 |

These 1,135 unique past visitors with session attendance records feed the collaborative filtering engine. Their attendance patterns across 522 past sessions (464 with stream assignments) drive the similarity-based recommendations for current-year visitors.

### 2.3 Geographic Distribution

| Country | Visitors | Share |
|:--------|:-------:|:----:|
| United Kingdom | 6,143 | 87.2% |
| Ireland | 79 | 1.1% |
| Pakistan | 54 | 0.8% |
| Germany | 54 | 0.8% |
| Netherlands | 52 | 0.7% |
| Other (93 countries) | 664 | 9.4% |

The audience is predominantly UK-based (87.2%), which validates the low similarity weight (0.3) assigned to Country in the configuration — geography alone provides minimal differentiation for this event.

---

## 3. Demographic Attribute Analysis

The pipeline uses six weighted attributes for visitor similarity matching. Data quality across all active attributes is excellent.

### 3.1 Attribute Fill Rates

| Attribute | Config Key | Weight | Filled | Fill Rate | Assessment |
|:----------|:----------|:-----:|:------:|:---------:|:----------:|
| Professional Function | `...primary_professional_function...` | 0.9 | 6,983 | 99.1% | ✅ Excellent |
| Sector | `...sector_does_your_company...` | 0.8 | 6,391 | 90.7% | ✅ Good |
| Seniority Level | `...current_seniority_level` | 0.6 | 7,037 | 99.9% | ✅ Excellent |
| Decision-Making | `...involvment_in_the_decision_making...` | 0.5 | 6,964 | 98.8% | ✅ Excellent |
| Representing | `you_are_representing` | 0.4 | 6,118 | 86.8% | ✅ Good |
| Country | `Country` | 0.3 | 7,046 | 100.0% | ✅ Complete |

**Weighted average fill rate: 95.9%** (sum of weight × fill rate / sum of weights). All six attributes exceed 86%, meaning the vast majority of visitors have rich profiles for similarity matching.

### 3.2 Professional Function Distribution (Weight 0.9)

This is the highest-weighted attribute and shows excellent diversity across 22 distinct values:

| Professional Function | Count | Share |
|:---------------------|:-----:|:----:|
| IT Architecture & Infrastructure | 918 | 13.0% |
| Data Centre Management | 711 | 10.1% |
| Cybersecurity / Security & Risk Management | 676 | 9.6% |
| Digital Strategy, Transformation & Innovation | 661 | 9.4% |
| Software / IT Engineering & Development | 557 | 7.9% |
| Corporate Management | 555 | 7.9% |
| Product or Project Management | 538 | 7.6% |
| Data, BI, Analytics | 503 | 7.1% |
| Cloud, Infrastructure, or DevOps | 383 | 5.4% |
| IT Business Management | 293 | 4.2% |

No single function exceeds 13%, indicating good audience diversity. The top 4 functions collectively represent 42.1% of visitors, covering the event's core pillars: infrastructure, data centres, cybersecurity, and digital transformation.

### 3.3 Sector Distribution (Weight 0.8)

| Sector | Count | Share |
|:-------|:-----:|:----:|
| Technology | 1,560 | 22.1% |
| Finance, Banking, Insurance | 976 | 13.9% |
| Consulting / Professional Services | 841 | 11.9% |
| NA (unfilled) | 655 | 9.3% |
| Construction / Real Estate | 616 | 8.7% |
| Telecommunications | 395 | 5.6% |
| Manufacturing | 288 | 4.1% |
| Energy | 271 | 3.8% |
| Ecommerce / Retail | 216 | 3.1% |
| Media / Culture / Entertainment | 209 | 3.0% |

Sector has 655 NA values (9.3%), the highest gap among the six attributes. Since this is the second-highest-weighted attribute (0.8), these visitors lose a significant similarity signal. Consider targeted email campaigns to capture sector data from the 655 visitors before the event.

### 3.4 Seniority Distribution (Weight 0.6)

| Seniority Level | Count | Share |
|:---------------|:-----:|:----:|
| Lead/Manager (with direct reports) | 1,458 | 20.7% |
| Director | 1,141 | 16.2% |
| Technical / Operations Specialist | 1,116 | 15.8% |
| Lead/Manager (without direct reports) | 879 | 12.5% |
| Head of Department | 860 | 12.2% |
| Founder / Co-founder | 702 | 10.0% |
| C-suite (CEO, CTO, CISO, CIO, COO) | 444 | 6.3% |
| Entry-level | 340 | 4.8% |
| Board Member (non-executive) | 63 | 0.9% |
| Apprentice | 34 | 0.5% |
| NA | 9 | 0.1% |

The audience skews senior: 77.9% are at Manager level or above, and 22.5% hold Director or C-suite positions. Only 9 visitors lack seniority data.

### 3.5 Decision-Making Involvement (Weight 0.5)

| Role in Decision-Making | Count | Share |
|:-----------------------|:-----:|:----:|
| I am involved in decision-making | 3,686 | 52.3% |
| I make the final decisions | 1,509 | 21.4% |
| I recommend products | 1,088 | 15.4% |
| I have no influence in purchasing decisions | 681 | 9.7% |
| NA | 82 | 1.2% |

89.1% of visitors hold decision-making influence (involved, final, or recommender), reflecting a high-value audience for exhibitors.

### 3.6 Representation Type (Weight 0.4)

| Representing | Count | Share |
|:------------|:-----:|:----:|
| Private Company | 5,517 | 78.3% |
| NA | 928 | 13.2% |
| Public Sector or Government | 601 | 8.5% |

This attribute has only 3 distinct values and 13.2% NA rate. With such low cardinality, the differentiation value is limited — visitors matching on "Private Company" alone (78.3% of audience) doesn't create meaningful distinction. The 0.4 weight appropriately reflects this.

---

## 4. Session Analysis & Stream Coverage

### 4.1 Session Inventory

| Metric | Count |
|:-------|:-----:|
| Total sessions (this year) | 189 |
| Sessions with stream assignments | 162 (85.7%) |
| Sessions without streams | 27 (14.3%) |
| Active streams | 38 |
| Theatres | 13 |
| Sessions recommended ≥1 time | 176 (93.1%) |
| Sessions never recommended | 13 (6.9%) |

### 4.2 Stream Distribution

| Stream | Sessions | Share of Streamed Sessions |
|:-------|:-------:|:----:|
| Sustainable Data Centres | 37 | 22.8% |
| AI-Driven Design | 25 | 15.4% |
| AI Culture & Leadership | 18 | 11.1% |
| AI Security & Resilience | 15 | 9.3% |
| Future of Cyber Strategy | 13 | 8.0% |
| Data Strategy & Intelligence | 12 | 7.4% |
| AI-Driven DevOps | 9 | 5.6% |
| AI Agents & Automation | 8 | 4.9% |
| AI Ethics & Governance | 8 | 4.9% |
| DevOps Culture | 7 | 4.3% |
| Scaling GenAI | 6 | 3.7% |
| DevSecOps in Practice | 6 | 3.7% |
| Cloud Leadership & Culture | 5 | 3.1% |
| Scaling Smart AI Cloud | 5 | 3.1% |
| Other streams (24) | 33 | — |

"Sustainable Data Centres" dominates with 37 sessions (22.8%), followed by "AI-Driven Design" (25) and "AI Culture & Leadership" (18). The distribution reflects the event's dual focus on data centre infrastructure and AI/technology innovation.

### 4.3 Theatre Distribution

| Theatre | Sessions |
|:--------|:-------:|
| Keynote: Global Strategies, People, Environment & Innovation | 21 |
| Cloud & AI Infrastructure Keynote | 19 |
| Energy Efficiency, Cost Management & DCIM | 18 |
| Design and Build & Physical Security | 18 |
| Big Data & AI World Keynote Theatre | 17 |
| Data & AI Innovations Theatre | 17 |
| Operational Transformation & Resilience Theatre | 17 |
| Cloud, DevOps & Applications | 13 |
| Data & AI for Business Theatre | 12 |
| DevOps Live Keynote | 11 |
| Cloud & Cyber Security Expo Theatre 1 | 10 |
| Cloud & Cyber Security Expo Theatre 2 | 8 |
| Cloud & Cyber Security Expo Keynote Theatre | 8 |

Sessions are well-distributed across 13 theatres, with no single theatre hosting more than 11% of content.

### 4.4 Sessions Without Streams (27 Sessions) 🔴

Investigation reveals three distinct categories:

**Category 1 — Sponsored Placeholders (14 sessions):** Titles like "Panel sponsored by Schneider Electric", "Session presented by Red Hat", "TBC Sponsored Session". Content not yet finalised by sponsors; stream column empty in source CSV.

**Category 2 — Administrative/Filler (3 sessions):**
- "Closing Remarks — Theatre Chair" — currently receiving **603 recommendations** (8.6% of visitors). 🔴 This should be added to `titles_to_remove`.
- "Fireside chat to be confirmed" — 29 recommendations.
- "Streamed from DevOps Keynote Theatre" — 76 recommendations.

**Category 3 — Real Content Needing Streams (10 sessions):** Legitimate sessions with descriptive titles but empty stream and synopsis fields in the source CSV. Examples include "Code to Production with DevOps Metrics" (185 recs), "From Pit Lane to Production: How F1 Scales Cloud-Native Infrastructure" (11 recs), and "Delivery at Scale, Risk at Speed: Balancing Security and Innovation at Evri" (43 recs).

**Root cause:** All 27 sessions have empty `synopsis_stripped` fields. The LLM-based backfill mechanism (`backfill_missing_streams()`) is correctly configured (`create_missing_streams: true`) but **skips sessions without a synopsis** — a deliberate guard that creates a blind spot for sessions where the organiser hasn't provided synopsis text. The session title alone contains sufficient information for stream classification in all 10 real content cases.

### 4.5 Sessions Never Recommended (13 Sessions)

| Session | Stream(s) | Theatre |
|:--------|:---------|:--------|
| Advanced Fiber Technologies: Hollow-Core & Multi-Core Fiber | Sustainable DC; AI-Driven Design | Operational Transformation |
| Cooling Tower Challenges and Solutions | Sustainable DC | Operational Transformation |
| Finding Order Amongst Chaos | AI-Driven Design | Design and Build |
| Fuel Polishing That Pays: Higher Genset Efficiency | Sustainable DC | Energy Efficiency |
| Global Growth vs Local Rules: Data Sovereignty | Circular Economy | Energy Efficiency |
| Grid Free Power. Always On. | Sustainable DC; Modernising DC Infra | Operational Transformation |
| Integrating AI Analytics with DCIM | AI-Driven Design | Design and Build |
| Panel presented by DCA | (none) | Design and Build |
| Panel sponsored by Hitachi Energy | (none) | Keynote |
| Panel sponsored by Schneider Electric | (none) | Design and Build |
| The Zero-Config Agent: Gemini 3 & Firebase Studio | AI Agents & Automation | Data & AI Innovations |
| Unlocking NHS Data with Fine-Tuned LLMs | Scaling GenAI | Big Data & AI Keynote |
| Where Automation Meets Maintenance | (none) | Keynote |

Of these 13, 10 have valid stream assignments but are so niche (specialised DC infrastructure topics) that no visitor's similarity score reaches the 0.3 minimum threshold. The remaining 3 are unstreamed sponsored placeholders. This is acceptable behaviour — forcing low-confidence recommendations would degrade quality.

---

## 5. Recommendation Quality Analysis

### 5.1 Similarity Score Distribution

| Score Range | Recommendations | Share |
|:-----------|:--------------:|:----:|
| 0.90–1.00 | 75 | 0.1% |
| 0.80–0.89 | 5,989 | 8.5% |
| 0.70–0.79 | 31,926 | 45.3% |
| 0.60–0.69 | 21,823 | 31.0% |
| 0.50–0.59 | 9,929 | 14.1% |
| 0.40–0.49 | 510 | 0.7% |
| 0.30–0.39 | 192 | 0.3% |

**Score Statistics:**

| Statistic | Value |
|:----------|:-----:|
| Minimum | 0.308 |
| Q1 (25th percentile) | 0.635 |
| Median | 0.709 |
| Mean | 0.696 |
| Q3 (75th percentile) | 0.753 |
| Maximum | 0.927 |
| IQR | 0.119 |

The score distribution is healthy: 84.9% of all recommendations score between 0.60 and 0.89, indicating strong match quality. The IQR of 0.119 shows meaningful differentiation — the algorithm is distinguishing between better and worse matches rather than clustering everything at similar scores. Only 1.0% of recommendations fall in the low-confidence zone (below 0.50).

### 5.2 Concentration Analysis

| Rank | Session Title | Recommended To | % of Visitors |
|:---:|:-------------|:--------------:|:-------------:|
| 1 | How AI Deployment Is Forging a New Data Centre Ecosystem | 2,323 | 33.0% |
| 2 | Building an AI Assistant for DevOps: From Noise to Action | 2,290 | 32.5% |
| 3 | Agentic DevOps | 2,257 | 32.0% |
| 4 | Sustainability & Energy Solutions: A New Approach to AI-Driven DCs | 2,253 | 32.0% |
| 5 | Scaling AI Responsibly: Energy, Efficiency & Innovation in DCs | 2,151 | 30.5% |
| 6 | Enterprise AI: A Sustainable Pathway to Production at Scale | 2,059 | 29.2% |
| 7 | Technology, Innovation and AI: Building the Next Gen DC | 2,049 | 29.1% |
| 8 | The Technology Trends Shaping the Future of the DC | 2,018 | 28.6% |
| 9 | Make Your DC Smarter & Stronger, Resilience in the Age of AI | 1,827 | 25.9% |
| 10 | Agents at Work: Rethinking Azure DevOps with AI | 1,787 | 25.4% |

The maximum concentration is **33.0%**, meaning no single session dominates more than a third of all recommendation lists. The top 10 sessions are thematically diverse, spanning AI deployment, DevOps, sustainability, and data centre infrastructure — indicating the algorithm is not over-indexing on a single topic. The concentration profile is healthy for a 189-session inventory.

### 5.3 Recommendation Distribution

| Recommendations per Visitor | Visitors | Share |
|:-------------------------:|:-------:|:----:|
| 10 | 7,042 | 99.9% |
| 6 | 4 | 0.1% |

99.9% of visitors received the full target of 10 recommendations. The 4 visitors receiving only 6 are all returning visitors — their shortfall is attributed to the overlap resolution feature (`resolve_overlapping_sessions_by_similarity: true`), which removes time-clashing sessions. All 4 are in the treatment group.

### 5.4 Sample Recommendations

**Visitor A — IT Architecture & Infrastructure, Technology sector (new visitor)**

| # | Session | Score |
|:-:|:--------|:-----:|
| 1 | The Cyber Resilience Blind Spot: Regulatory Scrutiny | 0.831 |
| 2 | Building Resilient Organisations: Cybersecurity Frameworks | 0.775 |
| 3 | AI, Humanity & Security: Protecting Trust | 0.767 |
| 4 | The Psychology of Cybersecurity Decisions | 0.759 |
| 5 | Resilient by Design: High-Performing Security Teams | 0.753 |

✅ Coherent cybersecurity and resilience focus, matching the visitor's IT Architecture profile. Scores range 0.69–0.83.

**Visitor B — Data Centre Management, returning visitor (sector NA)**

| # | Session | Score |
|:-:|:--------|:-----:|
| 1 | The Cyber Resilience Blind Spot: Regulatory Scrutiny | 0.757 |
| 2 | Building Resilient Organisations: Cybersecurity Frameworks | 0.682 |
| 3 | AI, Humanity & Security: Protecting Trust | 0.672 |
| 4 | Resilient by Design: High-Performing Security Teams | 0.653 |
| 5 | Agentic AI in SecOps: What's Real, What's Noise | 0.585 |

✅ Cyber-resilience and AI-security blend appropriate for DC management. Despite missing sector data, past attendance history provides sufficient signal. Scores wider range (0.55–0.76) reflects fewer matching attributes.

**Visitor C — Cloud/DevOps, Finance sector (new visitor)**

| # | Session | Score |
|:-:|:--------|:-----:|
| 1 | The Magic Ingredient for High Performing AI Teams | 0.721 |
| 2 | Redesigning the Way We Work: AI, Human Collaboration | 0.704 |
| 3 | How to Make AI Count: High-Impact Opportunities at Scale | 0.702 |
| 4 | Democratising AI: Citizen Developers and Lightweight Agents | 0.696 |
| 5 | What if DevOps was really simple? | 0.674 |

✅ Strong AI + DevOps mix appropriate for a Cloud/DevOps professional in finance. Includes both strategic AI sessions and practical DevOps content.

---

## 6. Control Group Analysis

### 6.1 Configuration

The control group is configured to withhold recommendations from a random 5% of visitors, enabling post-event A/B testing to measure the causal impact of sending personal agendas.

| Setting | Value |
|:--------|:-----:|
| Enabled | ✅ true |
| Percentage | 5% |
| Random Seed | 42 (deterministic) |
| Neo4j Property | `control_group` |
| File Suffix | `_control` |

### 6.2 Group Allocation

| Group | Visitors | Share | has_recommendation | IS_RECOMMENDED Edges |
|:------|:-------:|:----:|:------------------:|:--------------------:|
| Treatment (control_group = 0) | 6,694 | 95.0% | "1" | ✅ Created |
| Control (control_group = 1) | 352 | 5.0% | "1" | ✅ Created |
| **Total** | **7,046** | **100%** | — | — |

✅ All visitors — both treatment and control — have `has_recommendation = "1"`, ensuring no reprocessing in incremental runs. ✅ IS_RECOMMENDED relationships exist for both groups, preserving the ability to compute "organic hit rates" in post-show analysis.

### 6.3 Recommendation Parity

Both groups received identical recommendation treatment from the algorithm:

| Metric | Treatment | Control | Delta |
|:-------|:---------:|:-------:|:-----:|
| Visitors | 6,694 | 352 | — |
| Total recommendations | 66,924 | 3,520 | — |
| Avg recs per visitor | 10.0 | 10.0 | 0.0 |
| Min similarity score | 0.308 | 0.308 | 0.000 |
| Mean similarity score | 0.696 | 0.693 | 0.003 |
| Median similarity score | 0.709 | 0.705 | 0.004 |
| Max similarity score | 0.927 | 0.927 | 0.000 |

The negligible delta (0.003–0.004) between treatment and control score distributions confirms the random sampling produced statistically equivalent groups.

### 6.4 Demographic Balance

| Attribute | Treatment | Control |
|:----------|:---------:|:-------:|
| **New visitors** | 3,514 (52.5%) | 182 (51.7%) |
| **Returning visitors** | 3,180 (47.5%) | 170 (48.3%) |
| **Top sector: Technology** | 24.5% | 21.8% |
| **Top sector: Finance** | 15.2% | 16.5% |
| **Top sector: Consulting** | 13.0% | 16.8% |

✅ The new/returning split is well-balanced (within 1 percentage point). Sector distributions show minor sampling variance — expected with a 352-person control group — but no systematic bias. The deterministic seed (42) ensures reproducibility across runs.

### 6.5 File Export Separation

| Output File | Contains |
|:-----------|:---------|
| `visitor_recommendations_tsl_*.json` | Treatment group only (6,694 visitors) — sent to team |
| `visitor_recommendations_tsl_*.csv` | Treatment group only — CRM/marketing integration |
| `visitor_recommendations_tsl_*_control.json` | Control group only (352 visitors) — withheld |
| `visitor_recommendations_tsl_*_control.csv` | Control group only — audit/analysis |

### 6.6 Post-Event A/B Testing Readiness

The control group implementation is fully ready for post-show analysis. After the event, when `assisted_session_this_year` relationships are loaded, the following comparisons will be available:

| Analysis | Method |
|:---------|:-------|
| **Treatment Hit Rate** | % of attended sessions that were recommended AND sent (control_group = 0) |
| **Organic Hit Rate** | % of attended sessions that were recommended but NOT sent (control_group = 1) |
| **Recommendation Lift** | Treatment Hit Rate − Organic Hit Rate = true causal impact |
| **Relative Lift** | (Treatment − Organic) / Organic × 100 = % improvement from sending recs |

⚠️ **Critical downstream requirement:** Any system sending personal agendas must filter by `control_group = 0` (or use the main CSV/JSON exports, which automatically exclude control visitors). Sending recommendations to control visitors would invalidate the A/B test.

### 6.7 Validation Checklist

| Check | Status |
|:------|:------:|
| Main CSV/JSON contains only control_group = 0 visitors | ✅ Verified by pipeline logic |
| Control CSV/JSON contains only control_group = 1 visitors | ✅ Verified by pipeline logic |
| All visitors have has_recommendation = "1" | ✅ Confirmed (7,046/7,046) |
| ~5% of visitors have control_group = 1 | ✅ Confirmed (352 = 5.0%) |
| Both groups have IS_RECOMMENDED relationships | ✅ Confirmed (352 + 6,694 = 7,046) |
| Score distributions are equivalent | ✅ Confirmed (Δ mean = 0.003) |
| New/returning ratio is balanced | ✅ Confirmed (Δ = 0.8pp) |

---

## 7. Pipeline Configuration Summary

### 7.1 Similarity Weights

| Attribute | Weight | Fill Rate | Effective Contribution |
|:----------|:-----:|:---------:|:---------------------:|
| Professional Function | 0.9 | 99.1% | Dominant differentiator |
| Sector | 0.8 | 90.7% | Strong signal |
| Seniority Level | 0.6 | 99.9% | Moderate signal |
| Decision-Making | 0.5 | 98.8% | Moderate signal |
| Representing | 0.4 | 86.8% | Weak signal (low cardinality) |
| Country | 0.3 | 100.0% | Minimal signal (87% UK) |

Maximum possible similarity score: 0.9 + 0.8 + 0.6 + 0.5 + 0.4 + 0.3 = **3.5** (if all 6 attributes match). Scores are normalised against this total.

### 7.2 Feature Configuration

| Feature | Setting | Notes |
|:--------|:-------:|:------|
| Overlap resolution | ✅ Enabled | Removes time-clashing sessions by similarity |
| Returning without history boost | ✅ Enabled (exponent 1.5) | Adjusts scores for returning visitors with no past attendance |
| Content-based filtering | ❌ Disabled | Not applicable for TSL (no vet/pharmacy rules) |
| Theatre capacity limits | ❌ Disabled | — |
| Job-stream mapping | ❌ Disabled | — |
| Specialisation-stream mapping | ❌ Disabled | — |
| LLM stream backfill | ✅ Enabled | But blocked by empty synopses (see §4.4) |
| Max recommendations | 10 | — |
| Min similarity score | 0.3 | — |
| Similar visitors count | 3 | For collaborative filtering |

---

## 8. Data Quality Assessment

### 8.1 Strengths ✅

1. **100% recommendation coverage** — every registered visitor receives personalised suggestions
2. **99.9% full recommendation sets** — only 4 visitors below the 10-session target (due to overlap resolution)
3. **Excellent attribute fill rates** — weighted average 95.9%, all attributes ≥86.8%
4. **Healthy concentration** — max 33.0%, no single session dominates
5. **Well-calibrated scores** — 84.9% in the 0.60–0.89 range, IQR of 0.119 shows meaningful differentiation
6. **Control group properly implemented** — 5.0% allocation, balanced demographics, score parity, IS_RECOMMENDED preserved for both groups
7. **Sample recommendations are coherent** — domain-focused, diverse, appropriate for visitor profiles

### 8.2 Issues ⚠️ 🔴

1. 🔴 **"Closing Remarks — Theatre Chair" receiving 603 recommendations** — this administrative session should be in `titles_to_remove` but is not. It differs from the already-excluded "opening remarks - theatre chair" only by the opening/closing word.

2. ⚠️ **27 sessions without stream assignments (14.3%)** — breaks down as 14 sponsored placeholders, 3 administrative fillers, and 10 real content sessions with classifiable titles but no synopsis.

3. ⚠️ **LLM backfill blocked by empty synopses** — the `backfill_missing_streams()` function skips sessions without `synopsis_stripped`, even when the title contains sufficient classification signal. All 27 unstreamed sessions lack synopses.

4. ⚠️ **655 visitors (9.3%) missing sector data** — this is the second-highest-weighted attribute (0.8). These visitors lose significant differentiation power.

5. ⚠️ **928 visitors (13.2%) missing representation type** — though this attribute has low cardinality (3 values) and low weight (0.4), the gap is notable.

---

## 9. Priority Actions

### Immediate — Before Event (Week 1)

**Action 1: Add to `titles_to_remove` in config_tsl.yaml** 🔴

```yaml
titles_to_remove:
  # ... existing entries ...
  - 'closing remarks - theatre chair'
  - 'fireside chat to be confirmed'
  - 'streamed from devops keynote theatre'
  - 'tbc sponsored session'
  - 'panel sponsored by'      # Pattern match if supported
  - 'session sponsored by'    # Pattern match if supported  
  - 'panel presented by'      # Pattern match if supported
  - 'session presented by'    # Pattern match if supported
```

**Action 2: Assign streams to 10 real content sessions** ⚠️

| Session | Suggested Stream |
|:--------|:----------------|
| Code to Production with DevOps Metrics | AI-Driven DevOps |
| From Pit Lane to Production (F1 Cloud-Native) | Scaling Smart AI Cloud |
| Sweating the Stack: Scaling DevOps for 200+ Gym Sites | DevOps Culture |
| Delivery at Scale, Risk at Speed (Evri) | DevSecOps in Practice |
| Climate-Tech Sustainable & Efficient Cooling | Sustainable Data Centres |
| Operational Excellence in Dynamic DC World | Sustainable Data Centres |
| Seeing Everything, Missing Nothing (AI Deployments) | AI-Driven Design |
| Technology, Power and Equality | AI Ethics & Governance |
| Where Automation Meets Maintenance | Sustainable Data Centres |
| Streamed from Mainstage: Technology Meets Humanity | AI Culture & Leadership |

**Action 3: Re-run pipeline** after Actions 1–2 to regenerate recommendations with cleaned session inventory and complete stream assignments.

### Short-Term — Post-Event (Month 1)

**Action 4:** Modify `backfill_missing_streams()` to fall back to **title-only classification** when synopsis is empty, rather than skipping entirely.

**Action 5:** Investigate 9 never-recommended sessions with valid streams — verify the 0.3 minimum threshold is appropriate for niche DC infrastructure topics, or consider a popularity-based floor.

**Action 6:** Consider increasing `similar_visitors_count` from 3 to 5 for broader collaborative filtering pool, especially beneficial for new visitors.

### Medium-Term — Next Pipeline Iteration (Quarter 1)

**Action 7:** Implement pattern-based title exclusions (e.g., regex matching on "sponsored by", "presented by", "to be confirmed") to catch placeholder sessions automatically rather than relying on exact title matching.

**Action 8:** Explore FastRP graph embedding algorithm (GDS 2.26.0 available) for similarity computation — tested on production data, could provide 100× performance improvement and multi-hop reasoning capability. See separate analysis document.

---

## 10. System Readiness Assessment

| Category | Score | Notes |
|:---------|:-----:|:------|
| Coverage | 10/10 | 100% of visitors, 99.9% at full 10-rec target |
| Data Quality | 9/10 | 95.9% weighted fill rate, all attributes ≥86.8% |
| Algorithm Quality | 8/10 | Good score distribution, coherent samples, healthy IQR |
| Session Inventory | 7/10 | 27 unstreamed sessions, 1 filler session in recommendations |
| Concentration | 9/10 | Max 33.0%, diverse top-10 sessions |
| Control Group | 10/10 | Perfectly implemented, balanced, A/B-ready |
| **Overall** | **82/100 (B+)** | Ready for event with minor cleanup |

### Bottom Line

The TSL 2026 recommendation system is operating well. Full coverage is achieved, data quality is excellent, and the control group is correctly implemented for post-event impact measurement. The primary risk is the "Closing Remarks" session consuming 603 recommendation slots and the 27 unstreamed sessions reducing the algorithm's session pool. Executing Actions 1–3 before the event (estimated 2–3 hours of work plus one pipeline re-run) would bring the system to A− grade.

---

*Report generated from Neo4j Production database, pipeline run 11 February 2026 01:01 UTC.*
*Configuration: config/config_tsl.yaml | Mode: personal_agendas | Control group: 5% (seed 42)*
