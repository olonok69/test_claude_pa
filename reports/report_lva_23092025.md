# LVA Show Analysis Report - Production Database (After Re-run)

## Executive Summary

This report provides a comprehensive analysis of the London Vet Show (LVA) 2025 data in the Neo4j production database after the latest pipeline re-run on September 23, 2025. The analysis focuses on visitor demographics, session structures, stream mappings, and recommendation generation performance.

## 1. Event Overview

- **Event Name**: London Vet Show (LVA) 2025
- **Show Code**: `lva`
- **Configuration File**: `config/config_vet_lva.yaml`
- **Database**: Neo4j Production (`neo4j+s://928872b4.databases.neo4j.io`)
- **Last Process Run**: September 23, 2025, 22:27 UTC

## 2. Visitor Statistics

### 2.1 Overall Visitor Metrics

- **Total LVA Visitors**: 3,976
- **Visitors with Recommendations Generated**: 3,976 (100%)
- **Unique Job Roles**: 14
- **Unique Specializations**: 41
- **Unique Organization Types**: 9

### 2.2 Returning Visitors Analysis

| Visitor Type | Count | Percentage |
|-------------|-------|------------|
| Returning from BVA 2024 | 987 | 24.8% |
| Returning from LVA 2024 | 156 | 3.9% |
| **Total Returning Visitors** | **1,143** | **28.7%** |
| **New Visitors** | **2,833** | **71.3%** |

### 2.3 Job Role Distribution

| Job Role | Count | Percentage |
|----------|-------|------------|
| Vet/Vet Surgeon | 1,941 | 48.8% |
| Vet Nurse | 402 | 10.1% |
| Clinical or other Director | 388 | 9.8% |
| Practice Partner/Owner | 258 | 6.5% |
| Practice Manager | 221 | 5.6% |
| Vet/Owner | 191 | 4.8% |
| Head Nurse/Senior Nurse | 157 | 3.9% |
| Locum Vet | 138 | 3.5% |
| **Other** | **108** | **2.7%** |
| Assistant Vet | 85 | 2.1% |
| Student | 55 | 1.4% |
| Academic | 15 | 0.4% |
| Locum RVN | 10 | 0.3% |
| **Receptionist** | **7** | **0.2%** |

**Note**: Job roles in bold ("Other" and "Receptionist") have no stream mappings.

### 2.4 Practice Specialization Distribution (Top 20)

| Specialization | Count | Percentage |
|----------------|-------|------------|
| Small Animal | 2,338 | 58.8% |
| **NA** | **875** | **22.0%** |
| Mixed | 427 | 10.7% |
| Small Animal;Wildlife | 67 | 1.7% |
| Small Animal;Mixed | 49 | 1.2% |
| Equine | 35 | 0.9% |
| **Other** | **25** | **0.6%** |
| Small Animal;Wildlife;Wildlife | 22 | 0.6% |
| Small Animal;Equine | 19 | 0.5% |
| Farm | 12 | 0.3% |
| Wildlife | 9 | 0.2% |
| Small Animal;Mixed;Wildlife | 8 | 0.2% |
| Mixed;Farm | 8 | 0.2% |
| Small Animal;Farm | 8 | 0.2% |
| Equine;Farm | 7 | 0.2% |
| Small Animal;Other | 7 | 0.2% |
| Small Animal;Mixed;Wildlife;Equine;Farm;Wildlife | 6 | 0.2% |
| Small Animal;Mixed;Equine | 6 | 0.2% |
| Small Animal;Mixed;Equine;Farm | 5 | 0.1% |
| Small Animal;Equine;Farm | 5 | 0.1% |

**Note**: Specializations in bold ("NA" and "Other") have no stream mappings, affecting 900 visitors total.

### 2.5 Organization Type Distribution

| Organization Type | Count | Percentage |
|------------------|-------|------------|
| Independent Practice | 1,764 | 44.4% |
| Corporate Group | 1,677 | 42.2% |
| Locum | 177 | 4.5% |
| Charity | 147 | 3.7% |
| Industry Supplier | 100 | 2.5% |
| University | 55 | 1.4% |
| Other | 36 | 0.9% |
| Distributor | 18 | 0.5% |
| Wholesaler | 2 | 0.1% |

## 3. Session Analysis

### 3.1 Session Metrics

- **Total LVA Sessions**: 332
- **Sessions with Stream Relationships**: 129 (38.9%)
- **Sessions without Stream Relationships**: 203 (61.1%)
- **Sessions without Stream Property Value**: 203 (61.1%)
- **Unique Session Stream Values**: 85
- **Unique Theatres**: 30
- **Sponsored Sessions**: 0

### 3.2 Session-Stream Connectivity Issues

**⚠️ CRITICAL FINDING**: 203 sessions (61.1%) lack both:
- Stream relationships (no HAS_STREAM edge)
- Stream property values (empty or null stream field)

This significantly impacts the recommendation algorithm's ability to match sessions to visitors based on their professional interests and specializations.

### 3.3 Sessions with Most Recommendations

| Session Title | Stream | Times Recommended | Avg Score |
|--------------|--------|------------------|-----------|
| Top tips: Managing diabetics with SGLT2-inhibitors | Internal Medicine | 2,386 | 0.772 |
| A practical guide to effective therapy in canine allergic dermatitis | **(No Stream)** | 1,734 | 0.746 |
| Behind the build: Secrets to successful veterinary projects | **(No Stream)** | 1,486 | 0.771 |
| RVC Opening Welcome | **(No Stream)** | 1,408 | 0.874 |
| Not a copycat: Why cats are not small dogs... | **(No Stream)** | 1,213 | 0.752 |
| From veterinarian to entrepreneur | **(No Stream)** | 1,067 | 0.728 |
| Saving all nine lives: Top tips for feline emergency | **(No Stream)** | 1,019 | 0.723 |
| What lies beneath: Mastering dental radiography | Dentistry | 999 | 0.750 |
| Beyond the big six and traditional practice | **(No Stream)** | 961 | 0.703 |
| BVA President's Address | **(No Stream)** | 932 | 0.955 |

**Note**: 8 out of 10 most recommended sessions lack stream assignments.

## 4. Stream Analysis

### 4.1 Stream Node Statistics

- **Total Stream Nodes for LVA**: 61
- **Streams with Connected Sessions**: 37 (60.7%)
- **Streams without Any Sessions**: 24 (39.3%)

### 4.2 Streams Without Connected Sessions

The following 24 streams have no sessions assigned to them:

Animal Welfare, Behaviour, Business, Cardiology, Career Development, Clinical Pathology, Community, Debate, Diagnostics, Endocrinology, Exotic Animal, Farm, Farm Animal, Feline, Gastroenterology, Geriatric Medicine, Leadership, Obesity, Orthopeadics, Parasitology, Small Animal, Sustainability, Toxicology, Urology

### 4.3 Top Streams by Session Count

| Stream | Connected Sessions |
|--------|-------------------|
| Equine | 33 |
| Internal Medicine | 23 |
| Nursing | 17 |
| Emergency Medicine | 16 |
| Dentistry | 13 |
| Orthopaedics | 12 |
| Large Animal | 9 |
| Sports Medicine | 9 |
| Anaesthesia | 9 |
| Practice Management | 7 |

## 5. Visitor-Stream Mapping Analysis

### 5.1 Job Role to Stream Mapping

- **Configuration Status**: `job_stream_mapping.enabled = true` ✓
- **Mapping File**: `job_to_stream.csv`
- **Visitors with Job-to-Stream Relationships**: 3,861 (97.1%)
- **Visitors without Job-to-Stream Relationships**: 115 (2.9%)
- **Average Streams per Visitor**: 43.0
- **Range**: 0 - 48 streams per visitor

**Unmapped Job Roles**:
| Job Role | Affected Visitors |
|----------|------------------|
| Other | 108 |
| Receptionist | 7 |
| **Total** | **115** |

### 5.2 Specialization to Stream Mapping

- **Configuration Status**: `specialization_stream_mapping.enabled = true` ✓
- **Mapping File**: `spezialization_to_stream.csv`
- **Visitors with Specialization-to-Stream Relationships**: 3,076 (77.4%)
- **Visitors without Specialization-to-Stream Relationships**: 900 (22.6%)
- **Average Streams per Visitor**: 39.3
- **Range**: 0 - 266 streams per visitor

**Unmapped Specializations**:
| Specialization | Affected Visitors |
|---------------|------------------|
| NA | 875 |
| Other | 25 |
| **Total** | **900** |

### 5.3 Stream Connection Analysis

**Most Connected Streams via Job Role Mapping**:
- All top streams connect to 3,861 visitors (all mapped visitors)
- Includes: Career Development, Debate, Business, Behaviour, Sustainability, Leadership, Community

**Most Connected Streams via Specialization Mapping**:
- All top streams connect to 3,076 visitors (all mapped visitors)
- Includes: Gastroenterology, Anaesthesia, Animal Welfare, Cardiology, Career Development

**Observation**: The broad connection pattern suggests most job roles and specializations map to many common streams, potentially reducing recommendation differentiation.

## 6. Recommendation Generation Analysis

### 6.1 Overall Recommendation Statistics

- **Total Recommendations Generated**: 39,720
- **Visitors with Recommendations**: 3,976 (100%)
- **Unique Sessions Recommended**: 271 out of 332 (81.6%)
- **Average Similarity Score**: 0.710
- **Minimum Similarity Score**: 0.304
- **Maximum Similarity Score**: 1.000
- **Generation Timestamp**: September 23, 2025, 22:27 UTC

### 6.2 Recommendation Distribution

| Recommendation Count | Visitors | Percentage |
|---------------------|----------|------------|
| 1-5 recommendations | 6 | 0.15% |
| 6-9 recommendations | 2 | 0.05% |
| Exactly 10 recommendations | 3,968 | 99.80% |

**Finding**: 99.8% of visitors receive exactly the maximum 10 recommendations, indicating the algorithm consistently finds sufficient matches above the 0.3 similarity threshold.

## 7. Configuration Analysis

### 7.1 Key Configuration Parameters (config_vet_lva.yaml)

**Similarity Attributes & Weights**:
- `job_role`: 1.0
- `what_type_does_your_practice_specialise_in`: 1.0
- `organisation_type`: 1.0
- `Country`: 0.5

**Recommendation Settings**:
- `min_similarity_score`: 0.3
- `max_recommendations`: 10
- `similar_visitors_count`: 3
- `enable_filtering`: true (veterinary-specific rules active)

**Filtering Rules (Vet-Specific)**:
- Equine/Mixed exclusions from: exotics, feline, exotic animal, farm, small animal
- Small Animal exclusions from: equine, farm animal, farm, large animal
- Vet exclusions from: nursing streams
- Nurse-specific streams: nursing, wellbeing, welfare

### 7.2 Vet-Specific Processing Status

✅ **Enabled Features**:
- Specialization stream mapping
- Job role stream mapping
- Veterinary filtering rules
- Practice type matching
- Role group categorization

## 8. Critical Issues and Impact Analysis

### 8.1 High Priority Issues

| Issue | Impact | Affected Count |
|-------|--------|---------------|
| **Sessions without streams** | Reduces recommendation accuracy | 203 sessions (61.1%) |
| **Unmapped specializations** | Limits personalization | 900 visitors (22.6%) |
| **Unmapped job roles** | Reduces stream matching | 115 visitors (2.9%) |
| **Orphaned streams** | Unused content categories | 24 streams (39.3%) |

### 8.2 Impact on Recommendation Quality

1. **Session Stream Gap**: With 61% of sessions lacking stream assignments, the algorithm cannot properly filter recommendations based on visitor interests
2. **Over-broad Mappings**: Most visitors connect to 40+ streams, reducing differentiation
3. **Popular Session Bias**: Sessions without streams still get recommended heavily based on other similarity factors
4. **Maximum Recommendation Saturation**: 99.8% of visitors hit the 10-recommendation cap

## 9. Recommendations for Improvement

### 9.1 Immediate Actions Required

1. **Fix Session Stream Assignments** (Critical)
   - Review and assign streams to 203 unmapped sessions
   - Priority focus on highly recommended sessions without streams
   - Validate stream assignments match session content

2. **Update Mapping Files**
   - Add "Receptionist" role to `job_to_stream.csv`
   - Define default mappings for "Other" categories
   - Handle "NA" specializations (map or exclude)

3. **Stream Utilization**
   - Review 24 orphaned streams for relevance
   - Either assign sessions or remove unused streams
   - Ensure stream taxonomy matches event content

### 9.2 Algorithm Optimization Suggestions

1. **Increase Selectivity**
   - Consider raising `min_similarity_score` from 0.3 to 0.4-0.5
   - Implement diversity requirements in recommendations
   - Add session popularity dampening

2. **Refine Stream Mappings**
   - Reduce number of streams per job role/specialization
   - Create more specific mappings for differentiation
   - Consider weighted stream associations

3. **Data Quality Controls**
   - Implement pre-import validation for session streams
   - Add monitoring for mapping coverage
   - Create alerts for data quality issues

## 10. Comparison with Previous Run

The data appears consistent with the previous analysis, indicating:
- No changes to the underlying data issues
- Session stream mapping gap persists at 61.1%
- Same unmapped job roles and specializations
- Recommendation generation completed successfully despite gaps

## 11. Conclusion

The LVA show recommendation system successfully generates recommendations for 100% of visitors, but faces significant data quality challenges:

1. **Primary Issue**: 61% of sessions lack stream assignments, severely limiting content categorization
2. **Secondary Issue**: 22.6% of visitors have unmapped specializations
3. **System Health**: Despite gaps, the recommendation engine runs successfully using available similarity metrics

**Priority Action**: Assign streams to the 203 unmapped sessions to improve recommendation relevance and accuracy.

**System Status**: 
- ✅ Pipeline execution successful
- ✅ Veterinary-specific features enabled
- ⚠️ Data quality issues persist
- ⚠️ Recommendation differentiation limited

The system architecture is sound, but immediate attention to session stream mapping and specialization coverage will significantly improve recommendation quality.