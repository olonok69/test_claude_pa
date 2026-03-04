# FastRP Feasibility Analysis for Visitor Similarity

**Date:** 11 February 2026
**Context:** TSL 2026 Recommendation Pipeline — Step 10 (Session Recommendations)
**Database:** Neo4j 5.27-aura Enterprise, GDS 2.26.0

---

## 1. Current Approach: Weighted Exact-Match

### How It Works

The `_find_similar_visitors()` method in `session_recommendation_processor.py` builds a Cypher query that does **weighted exact-match** on categorical attributes:

```python
# Pseudocode of the current approach
MATCH (v1:Visitor_this_year {BadgeId: $target})
MATCH (v2:Visitor_last_year_bva)  # or combined past labels
WITH v2,
  CASE WHEN v2.professional_function = $val THEN 0.9 ELSE 0 END +  # exact match or 0
  CASE WHEN v2.sector = $val THEN 0.8 ELSE 0 END +
  CASE WHEN v2.seniority = $val THEN 0.6 ELSE 0 END +
  CASE WHEN v2.decision_making = $val THEN 0.5 ELSE 0 END +
  CASE WHEN v2.representing = $val THEN 0.4 ELSE 0 END +
  CASE WHEN v2.country = $val THEN 0.3 ELSE 0 END
  AS base_similarity
WHERE base_similarity > 0
MATCH (v2)-[:attended_session]->(s:Sessions_past_year)
RETURN v2, base_similarity
ORDER BY base_similarity DESC LIMIT 3
```

### Current Limitations

| Limitation | Impact |
|-----------|--------|
| **Binary matching only** | "Cybersecurity" vs "IT Architecture" scores exactly 0 — same as "Cybersecurity" vs "Student". No notion of "close but different." |
| **Per-visitor query** | Each of 7,046 visitors runs a separate Cypher scan over all past visitors (~0.5s each). Total: ~3,500s of query time. |
| **Weight tuning is manual** | The 0.9/0.8/0.6/0.5/0.4/0.3 weights were hand-tuned. No data-driven validation. |
| **No structural signal** | Ignores that two visitors might be connected through similar attendance patterns, streams, or multi-hop graph paths. |
| **NA kills differentiation** | If an attribute is "NA" for both visitors, the CASE clause returns 0 — but two visitors who both lack sector data might still be similar through other graph signals. |

### Current Performance (TSL 2026)

| Metric | Value |
|--------|-------|
| Pipeline duration | ~33 minutes |
| Similarity lookup per visitor | ~0.5 seconds |
| Total similarity query time (est.) | ~3,500 seconds (with caching/batching) |
| Visitors needing similarity lookup | ~5,949 (those without direct past attendance) |

---

## 2. FastRP: What It Is and How It Works

**Fast Random Projection (FastRP)** is a graph embedding algorithm in Neo4j GDS. It generates dense vector representations (embeddings) for every node based on **graph topology** — nodes that share neighbors get similar vectors.

### Algorithm Steps

1. Assign random initial vectors to all nodes
2. Iteratively propagate and average vectors through relationships
3. Each iteration captures progressively longer-range neighborhoods
4. Output: a fixed-dimensional embedding per node (e.g., 128-dim)

### Why It's Relevant

FastRP can discover **implicit similarity** that attribute matching cannot. Two visitors who never share an exact attribute value could still be embedded nearby because they connect to the same streams through different-but-related sessions.

---

## 3. Live Test Results on Production Data

### Test 1: FastRP on Current Graph Structure

I projected the existing TSL graph and ran FastRP:

```
Graph: 12,477 nodes | 18,228 relationships (undirected)
Nodes: Visitor_this_year (7,046) + Visitor_last_year_bva/lva (4,626) + Sessions_past_year (458) + Stream (47)
Relationships: Same_Visitor + attended_session + HAS_STREAM
```

**Result:**

| Embedding Status | Visitors | Percentage |
|:---:|:---:|:---:|
| **Zero vectors** (all 0s) | 3,696 | **52.5%** |
| Non-zero vectors | 3,350 | 47.5% |

**Verdict: ❌ USELESS on current graph.** 52.5% of visitors (all new visitors) have NO relationships in the graph, so FastRP produces zero vectors for them. They're isolated nodes — FastRP has nothing to propagate.

### Why This Happens

Current TSL graph connectivity:

```
Visitor_this_year (NEW)          → NO CONNECTIONS → Zero embedding
                                                    
Visitor_this_year (RETURNING)    → Same_Visitor → Visitor_last_year → attended_session → Session_past → HAS_STREAM → Stream
                                   ✅ Has multi-hop paths → Gets meaningful embedding
```

New visitors have no structural edges. The visitor properties (professional_function, sector, seniority, etc.) are stored as **node properties**, not as relationships to concept nodes. FastRP doesn't read properties — it reads topology.

---

## 4. The Solution: Enriched Bipartite Graph

### Concept

Transform flat properties into graph structure by creating **attribute nodes**:

```
BEFORE (current):
  Visitor {professional_function: "Cybersecurity", sector: "Finance", ...}  ← flat properties

AFTER (enriched):
  Visitor --HAS_FUNCTION--> (Function: "Cybersecurity")
  Visitor --HAS_SECTOR-->   (Sector: "Finance")
  Visitor --HAS_SENIORITY--> (Seniority: "Director")
  ... etc
```

### Graph Size Estimate (TSL)

| Component | Node Count | Relationship Count |
|-----------|:---:|:---:|
| Visitor_this_year | 7,046 | — |
| Visitor_last_year_bva | 2,856 | — |
| Visitor_last_year_lva | 1,770 | — |
| Sessions_past_year | 458 | — |
| Stream | 47 | — |
| **New: FunctionNode** | **22** | **~6,984** (99.1% of visitors) |
| **New: SectorNode** | **24** | **~6,391** (90.7% of visitors) |
| **New: SeniorityNode** | **11** | **~7,037** (99.9% of visitors) |
| **New: DecisionNode** | **5** | **~6,964** (98.8% of visitors) |
| **New: RepresentingNode** | **3** | **~6,118** (86.8% of visitors) |
| **New: CountryNode** | **98** | **~7,046** (100%) |
| | | |
| **Total Nodes** | **~12,340** | |
| **Total New Relationships** | | **~40,540** |
| **Existing Relationships** | | ~8,933 |
| **Grand Total** | **~12,340 nodes** | **~49,473 rels** |

This is a small graph — FastRP would process it in seconds.

### What FastRP Would Discover

With the enriched graph, FastRP captures multi-hop signals:

```
Visitor A (Cybersecurity, Finance) → HAS_FUNCTION → "Cybersecurity" ← HAS_FUNCTION ← Visitor B
                                   → HAS_SECTOR  → "Finance"       ← HAS_SECTOR  ← Visitor C
                                   
Even if B and C never share exact attributes with A, they might both connect through
"Cybersecurity" → past visitors → attended_session → Session → HAS_STREAM → "AI Security"
```

This discovers **"Cybersecurity + Finance visitors tend to attend AI Security sessions"** — something the current exact-match approach cannot learn.

---

## 5. Implementation Architecture

### Option A: FastRP + kNN (Pre-compute All Similarities)

```
Pipeline Step 9.5 (NEW):
  1. Create attribute nodes + relationships        (~5 seconds)
  2. Project enriched graph into GDS                (~2 seconds)
  3. Run FastRP → embeddings for all visitors       (~5 seconds)
  4. Run kNN → find top-K similar visitors          (~10 seconds)
  5. Write SIMILAR_TO relationships to graph         (~10 seconds)
  6. Drop projection, cleanup attribute nodes        (~2 seconds)
                                            TOTAL: ~35 seconds

Pipeline Step 10 (MODIFIED):
  _find_similar_visitors() → Simply reads pre-computed SIMILAR_TO relationships
  No more per-visitor Cypher scans!
```

### Option B: FastRP Embeddings + Python Similarity

```
Pipeline Step 9.5 (NEW):
  1. Create attribute nodes + relationships
  2. Project → FastRP → write embeddings to visitor nodes
  3. Cleanup
  
Pipeline Step 10 (MODIFIED):
  Load all visitor embeddings once into memory
  For each visitor: cosine similarity against all others in numpy
  ~0.001s per visitor vs ~0.5s currently
```

### Recommended: Option A

Option A is better because it keeps similarity computation in Neo4j GDS (optimized C++ implementation) and doesn't require loading all embeddings into Python memory.

---

## 6. Code Changes Required

### 6.1 New Pipeline Step: `neo4j_fastrp_processor.py`

```python
"""
FastRP-based visitor similarity pre-computation.

Runs BEFORE session_recommendation_processor.py to pre-compute
SIMILAR_TO relationships between visitors using graph embeddings.
"""

class Neo4jFastRPProcessor:
    def __init__(self, config: dict):
        self.show_name = config["neo4j"]["show_name"]
        self.similarity_attributes = config["recommendation"]["similarity_attributes"]
        self.similar_visitors_count = config["recommendation"]["similar_visitors_count"]
        
        # FastRP parameters (configurable via YAML)
        fastrp_config = config["recommendation"].get("fastrp", {})
        self.embedding_dimension = fastrp_config.get("embedding_dimension", 128)
        self.iteration_weights = fastrp_config.get("iteration_weights", [0.0, 1.0, 1.0, 0.8, 0.5])
        self.top_k = fastrp_config.get("top_k", 10)  # kNN neighbors
        self.relationship_weights = fastrp_config.get("relationship_weights", {})
        
    def process(self):
        """Main execution: create attribute graph → FastRP → kNN → cleanup."""
        self._create_attribute_nodes()
        self._create_attribute_relationships()
        self._project_graph()
        self._run_fastrp()
        self._run_knn()
        self._write_similar_to_relationships()
        self._cleanup()
```

### 6.2 Cypher Templates for Each Step

**Step 1: Create attribute nodes**
```cypher
// For each unique value in each similarity attribute:
MATCH (v:Visitor_this_year) WHERE v.show = $show_name
WITH DISTINCT v.which_of_the_following_best_describes_your_primary_professional_function_... AS val
WHERE val IS NOT NULL AND val <> 'NA'
MERGE (a:AttributeNode:FunctionAttr {value: val, attribute_type: 'professional_function'})
```

**Step 2: Create visitor-to-attribute relationships**
```cypher
// Connect visitors to their function attribute
MATCH (v:Visitor_this_year) WHERE v.show = $show_name
MATCH (a:FunctionAttr {value: v.which_of_the_following_best_describes_your_primary_professional_function_...})
MERGE (v)-[:HAS_ATTRIBUTE {weight: 0.9}]->(a)
```

**Step 3: Project graph**
```cypher
CALL gds.graph.project('visitor_similarity', 
  ['Visitor_this_year', 'Visitor_last_year_bva', 'Visitor_last_year_lva',
   'Sessions_past_year', 'Stream', 'AttributeNode'],
  {
    HAS_ATTRIBUTE: {orientation: 'UNDIRECTED'},
    Same_Visitor: {orientation: 'UNDIRECTED'},
    attended_session: {orientation: 'UNDIRECTED'},
    HAS_STREAM: {orientation: 'UNDIRECTED'}
  }
)
```

**Step 4: Run FastRP**
```cypher
CALL gds.fastRP.mutate('visitor_similarity', {
  embeddingDimension: 128,
  iterationWeights: [0.0, 1.0, 1.0, 0.8, 0.5],
  mutateProperty: 'embedding'
})
```

**Step 5: Run kNN**
```cypher
CALL gds.knn.write('visitor_similarity', {
  nodeLabels: ['Visitor_this_year'],
  topK: 10,
  nodeProperties: ['embedding'],
  writeRelationshipType: 'SIMILAR_TO',
  writeProperty: 'score'
})
```

### 6.3 Modify `_find_similar_visitors()` in `session_recommendation_processor.py`

```python
def _find_similar_visitors(self, visitor, limit=3, find_from_this_year_returning=False):
    """Find similar visitors using pre-computed SIMILAR_TO relationships."""
    badge_id = visitor.get("BadgeId")
    
    if self.use_fastrp_similarity:
        # NEW PATH: Read pre-computed kNN results
        query = f"""
        MATCH (v1:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
              -[r:SIMILAR_TO]->(v2)
        WHERE v2.show = $show_name
        // v2 could be this-year returning or past-year visitor
        MATCH (v2)-[:attended_session]->(s:{self.session_past_year_label})
        RETURN v2.BadgeId AS similar_visitor, r.score AS similarity, count(s) AS sessions
        ORDER BY r.score DESC
        LIMIT $limit
        """
        # ... execute and return
    else:
        # EXISTING PATH: weighted exact-match (fallback)
        # ... current implementation unchanged
```

### 6.4 Config Addition (`config_tsl.yaml`)

```yaml
recommendation:
  # ... existing config ...
  
  # FastRP-based similarity (NEW)
  fastrp:
    enabled: true                                  # Toggle on/off
    embedding_dimension: 128                       # Vector size
    iteration_weights: [0.0, 1.0, 1.0, 0.8, 0.5]  # Propagation depth/decay
    top_k: 10                                      # kNN neighbors per visitor
    relationship_weights:                          # Optional: weight different edge types
      HAS_ATTRIBUTE: 1.0
      Same_Visitor: 0.8
      attended_session: 1.0
      HAS_STREAM: 0.5
```

### 6.5 Pipeline Step Registration

```yaml
pipeline_steps:
  # ... existing steps ...
  neo4j_fastrp_processing: true    # NEW: runs between step 9 and step 10
  session_recommendation_processing: true
```

---

## 7. Advantages vs Current Approach

| Dimension | Current (Exact-Match) | FastRP + kNN |
|-----------|:---:|:---:|
| **Similarity type** | Binary (match/no-match) | Continuous (dense vectors) |
| **Multi-hop reasoning** | ❌ No | ✅ Yes — discovers indirect connections |
| **Missing values** | "NA matches NA" inflation | No edge = no influence (natural handling) |
| **Weight tuning** | Manual (6 weights) | Learned from graph structure (+ optional relationship weights) |
| **Computation model** | Per-visitor query (O(n) per visitor) | Batch pre-compute (O(1) lookup per visitor) |
| **Estimated total time** | ~3,500s similarity queries | **~35s** total (100× faster) |
| **New visitor handling** | Works (matches on properties) | ✅ Works via attribute nodes |
| **Returning visitor bonus** | Separate exponent hack | ✅ Natural — more edges = richer embedding |
| **Session diversity** | Limited by top-3 similar visitors | Naturally more diverse (structural neighbors) |
| **Explainability** | ✅ Clear ("matched on sector + function") | ⚠️ Harder ("similar embedding vectors") |
| **Complexity** | Simple | Moderate (new pipeline step + config) |

### Key Expected Improvements

1. **Performance**: ~100× faster similarity computation (35 seconds vs ~58 minutes)
2. **Better new visitor matching**: Currently new visitors without close exact-match neighbors fall to popular sessions fallback. With attribute nodes, every visitor with at least one non-NA attribute gets a meaningful embedding.
3. **Implicit category relationships**: "Data Centre Management" and "IT Architecture" visitors likely attend overlapping sessions — FastRP discovers this through the `Function → Visitor → attended → Session → Stream` path. Current approach sees them as completely different.
4. **Reduced fallback rate**: Fewer visitors should fall to "popular sessions" because similarity computation operates on continuous vectors rather than discrete matches.

---

## 8. Risks and Mitigations

| Risk | Severity | Mitigation |
|------|:---:|-----------|
| **GDS memory** on Aura instance | Low | 12K nodes / 50K rels is tiny (~10MB). GDS 2.26 handles this easily. |
| **Embedding quality** depends on hyperparameters | Medium | Start with defaults, validate against current approach on historical data (TSL 2025 post-show analysis as ground truth). |
| **Attribute node cleanup** if pipeline fails mid-run | Medium | Wrap in try/finally; always drop projection and delete AttributeNode nodes in cleanup. |
| **Regression risk** — new approach might perform worse | Medium | Keep current approach as `fastrp.enabled: false` fallback. Run both in parallel on first event and compare hit rates. |
| **Schema conflicts** with other shows sharing the same Neo4j | Low | Tag AttributeNode with `show` property; use show-specific projection filter. |
| **kNN doesn't respect "must have attended sessions"** constraint | Medium | Post-filter kNN results to only include neighbors with `attended_session` relationships. |

---

## 9. Implementation Effort Estimate

| Component | Effort | Complexity |
|-----------|:---:|:---:|
| `neo4j_fastrp_processor.py` (new file) | **3–4 days** | Medium |
| Config additions to all YAML files | 0.5 day | Low |
| Modify `_find_similar_visitors()` with toggle | 1 day | Low |
| Pipeline orchestration (new step) | 0.5 day | Low |
| Integration testing | 2 days | Medium |
| Validation against historical data | 1–2 days | Medium |
| **Total** | **8–10 days** | **Medium** |

---

## 10. Recommendation

### Should We Implement FastRP?

**Yes, but as a phased approach:**

**Phase 1 (Quick Win — 2 days):** Pre-compute kNN using GDS `gds.knn` with **one-hot encoded node properties** (no FastRP yet). This alone eliminates the per-visitor Cypher scan and gives ~100× speedup without the complexity of attribute nodes. The kNN in GDS supports property-based similarity directly.

```cypher
// One-hot encode attributes as float arrays on nodes
// Then run kNN directly on properties
CALL gds.knn.write('graph', {
  nodeLabels: ['Visitor_this_year'],
  nodeProperties: ['function_onehot', 'sector_onehot', 'seniority_onehot'],
  topK: 10,
  writeRelationshipType: 'SIMILAR_TO',
  writeProperty: 'score'
})
```

**Phase 2 (Full FastRP — 8 days):** Implement the enriched bipartite graph + FastRP pipeline. This adds the multi-hop reasoning and implicit category discovery on top of Phase 1.

**Phase 3 (Validation):** Run both approaches on the next event with post-show data. Compare hit rates between:
- Current exact-match
- Phase 1 (kNN on properties)  
- Phase 2 (FastRP + kNN on graph)

Pick the winner based on actual attendance data.

### Priority Assessment

| Factor | Assessment |
|--------|-----------|
| **Impact on recommendation quality** | Medium-High — fixes the "all-or-nothing" matching problem |
| **Impact on pipeline performance** | Very High — ~100× faster similarity computation |
| **Impact on fallback rate** | Medium — should reduce popular sessions fallbacks |
| **Implementation risk** | Low — existing approach stays as fallback |
| **Urgency for TSL 2026 (4 March)** | Low — current system is B+ and functional |
| **Value for future events** | High — generic approach works across all shows |

**Verdict:** Not urgent for TSL 2026 (3 weeks away), but a strong candidate for the next pipeline iteration. The performance gain alone justifies Phase 1, and the quality improvements from Phase 2 would benefit all future events.

---

## Appendix: GDS Availability Confirmation

```
Neo4j: 5.27-aura Enterprise
GDS:   2.26.0

Available procedures:
✅ gds.fastRP.stream / mutate / write
✅ gds.knn.stream / mutate / write
✅ gds.knn.filtered.stream / mutate / write
✅ gds.similarity.cosine / euclidean / jaccard
✅ gds.graph.project / gds.graph.project.cypher
```

All required components are available in the current production environment.
