#!/usr/bin/env python3
"""
Generic Session Recommendation Processor - Final Production Version

This processor generates session recommendations for visitors based on:
- Their past attendance (if they visited last year)
- Similar visitors' attendance patterns (if they're new)

The processor is fully configurable to work with different shows (BVA, ECOMM, etc.)
through YAML configuration files without any hardcoded show-specific logic.

Key Features:
- Fully generic and configurable for different show types
- Proper incremental processing support (create_only_new)
- Consistent show attribute handling
- Complete error handling and logging
"""

import os
import json
import time
import re
import logging
import math
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any
import concurrent.futures
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from utils import vet_specific_functions


# Try to import LangChain for advanced filtering (optional)
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    has_langchain = True
except ImportError:
    has_langchain = False


class SessionRecommendationProcessor:
    """Generic session recommendation processor for different shows."""

    def __init__(self, config: Dict):
        """
        Initialize the session recommendation processor.

        Args:
            config: Configuration dictionary with all necessary settings
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Extract configuration settings
        self.show_name = config.get("neo4j", {}).get("show_name", "bva")
        self.recommendation_config = config.get("recommendation", {})
        self.neo4j_config = config.get("neo4j", {})

        # Cache for Neo4j schema discovery
        self._available_labels: Optional[Set[str]] = None
        
        # Neo4j connection parameters
        self.uri = self.neo4j_config.get("uri")
        self.username = self.neo4j_config.get("username")
        self.password = self.neo4j_config.get("password")
        
        # Recommendation parameters
        self.min_similarity_score = self.recommendation_config.get("min_similarity_score", 0.3)
        self.max_recommendations = self.recommendation_config.get("max_recommendations", 10)
        self.similar_visitors_count = self.recommendation_config.get("similar_visitors_count", 3)
        self.use_langchain = self.recommendation_config.get("use_langchain", False) and has_langchain
        self.enable_filtering = self.recommendation_config.get("enable_filtering", False)
        self.resolve_overlaps_by_similarity = self.recommendation_config.get(
            "resolve_overlapping_sessions_by_similarity", False
        )
        returning_without_history_cfg = self.recommendation_config.get(
            "returning_without_history", {}
        )
        self.handle_returning_without_history = returning_without_history_cfg.get(
            "enabled", False
        )
        exponent_value = returning_without_history_cfg.get("similarity_exponent", 1.5)
        try:
            self.returning_without_history_exponent = float(exponent_value)
        except (TypeError, ValueError):
            self.returning_without_history_exponent = 1.5
        if self.returning_without_history_exponent <= 0:
            self.returning_without_history_exponent = 1.5
        
        # Similarity attributes for finding similar visitors
        self.similarity_attributes = self.recommendation_config.get("similarity_attributes", {})
        
        # GENERIC: Load role groups from configuration instead of hardcoding
        role_groups = self.recommendation_config.get("role_groups", {})
        self.vet_roles = role_groups.get("vet_roles", [])
        self.nurse_roles = role_groups.get("nurse_roles", [])
        self.business_roles = role_groups.get("business_roles", [])
        self.other_roles = role_groups.get("other_roles", [])
        
        # GENERIC: Load field mappings from configuration
        field_mappings = self.recommendation_config.get("field_mappings", {})
        self.practice_type_field = field_mappings.get("practice_type_field", "what_type_does_your_practice_specialise_in")
        self.job_role_field = field_mappings.get("job_role_field", "job_role")
        
        # Filtering rules configuration (show-specific)
        self.rules_config = self.recommendation_config.get("rules_config", {})
        event_cfg = self.config.get("event", {})
        self.main_event_name = (
            event_cfg.get("main_event_name")
            or event_cfg.get("name")
            or ""
        ).lower()
        self.custom_rules_config = self.rules_config.get("custom_rules", {})
        self.custom_rules_enabled = (
            self.enable_filtering
            and bool(self.custom_rules_config.get("enabled", False))
            and self._event_is_allowed_for_custom_rules()
        )
        
        # Node labels from config
        self.visitor_this_year_label = self.neo4j_config.get("node_labels", {}).get(
            "visitor_this_year", "Visitor_this_year"
        )
        self.visitor_last_year_bva_label = self.neo4j_config.get("node_labels", {}).get(
            "visitor_last_year_bva", "Visitor_last_year_bva"
        )
        self.visitor_last_year_lva_label = self.neo4j_config.get("node_labels", {}).get(
            "visitor_last_year_lva", "Visitor_last_year_lva"
        )
        self.session_this_year_label = self.neo4j_config.get("node_labels", {}).get(
            "session_this_year", "Sessions_this_year"
        )
        self.session_past_year_label = self.neo4j_config.get("node_labels", {}).get(
            "session_past_year", "Sessions_past_year"
        )
        
        # Initialize caches for performance
        self._visitor_cache = {}
        self._similar_visitors_cache = {}
        self._this_year_sessions_cache = None
        
        # Initialize the sentence transformer model
        self.model = None
        self._init_model()
        
        # Initialize statistics
        self.statistics = {
            "visitors_processed": 0,
            "visitors_with_recommendations": 0,
            "visitors_without_recommendations": 0,
            "total_recommendations_generated": 0,
            "total_filtered_recommendations": 0,
            "errors": 0,
            "error_details": [],
            "processing_time": 0,
        }
        
        # Output directory
        self.output_dir = Path(config.get("output_dir", "data/output"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Intermediary CSV enrichment for step 10: override base profile and contact fields from registration+demographics output
        # Base profile fields + contact fields commonly requested in exports
        self._csv_enrichment_fields = [
            "Company",
            "JobTitle",
            "Email_domain",
            "Country",
            "Source",
            # Contact fields expected by ecomm/email.ipynb and export_additional_visitor_fields
            "Email",
            "Forename",
            "Surname",
            "Tel",
            "Mobile",
        ]
        self._visitor_profile_map = {}
        self._load_registration_demographics_this_year()

        self.logger.info(f"SessionRecommendationProcessor initialized for {self.show_name} show")
        self.logger.info(f"Filtering enabled: {self.enable_filtering}")
        if self.enable_filtering:
            self.logger.info(f"Using field mappings - Practice: {self.practice_type_field}, Job: {self.job_role_field}")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the processor."""
        logger = logging.getLogger("session_recommendation_processor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _init_model(self):
        """Initialize the sentence transformer model."""
        model_name = self.config.get("embeddings", {}).get("model", "all-MiniLM-L6-v2")
        try:
            self.model = SentenceTransformer(model_name)
            self.logger.info(f"Initialized sentence transformer model: {model_name}")
        except Exception as e:
            self.logger.error(f"Error initializing model: {str(e)}")
            self.model = None

    def _fetch_available_labels(self) -> Set[str]:
        """Fetch available Neo4j node labels for conditional query building."""
        labels: Set[str] = set()
        if not all([self.uri, self.username, self.password]):
            return labels

        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    try:
                        result = session.run("CALL db.labels()")
                    except Exception:
                        result = session.run("SHOW NODE LABELS")

                    for record in result:
                        label_value = record.get("label")
                        if label_value:
                            labels.add(label_value)

            if labels:
                self.logger.debug(
                    "Discovered Neo4j node labels: %s",
                    ", ".join(sorted(labels))
                )
        except Exception as e:
            self.logger.warning(
                "Unable to fetch Neo4j node labels for schema-aware queries: %s",
                str(e)
            )

        return labels

    def _label_exists(self, label: str) -> bool:
        """Check if a label exists in the Neo4j database (cached)."""
        if not label:
            return False

        if self._available_labels is None:
            self._available_labels = self._fetch_available_labels()

        return label in self._available_labels

    def _get_available_past_labels(self) -> List[str]:
        """Return the list of available labels for past-year visitors."""
        labels: List[str] = []
        for candidate in (self.visitor_last_year_bva_label, self.visitor_last_year_lva_label):
            if self._label_exists(candidate):
                labels.append(candidate)
        return labels

    def _event_is_allowed_for_custom_rules(self) -> bool:
        """Check whether the current event is eligible for custom filtering rules."""

        if not self.recommendation_config.get("enable_filtering", False):
            return False

        apply_to_events = self.custom_rules_config.get("apply_to_events")
        if not apply_to_events:
            return True

        apply_to = {str(val).lower() for val in apply_to_events if val}
        if not apply_to:
            return True

        event_cfg = self.config.get("event", {})
        identifiers = [
            self.main_event_name,
            str(event_cfg.get("name", "")).lower(),
            str(event_cfg.get("secondary_event_name", "")).lower(),
            str(self.show_name).lower(),
        ]

        return any(identifier in apply_to for identifier in identifiers if identifier)

    def _load_registration_demographics_this_year(self) -> None:
        """Load intermediary CSV to enrich visitor attributes for output exports.
        Reads the file configured under output_files.registration_with_demographic.this_year.
        """
        try:
            out_cfg = self.config.get("output_files", {}).get("registration_with_demographic", {})
            filename = out_cfg.get("this_year", "Registration_data_with_demographicdata_bva_this.csv")
            # File is written under <output_dir>/output/<filename>
            csv_path = Path(self.config.get("output_dir", "data/output")) / "output" / filename
            if not csv_path.exists():
                self.logger.info(f"Intermediary CSV for enrichment not found: {csv_path}")
                return
            df = pd.read_csv(csv_path, dtype=str)
            if "BadgeId" not in df.columns:
                self.logger.warning(f"Intermediary CSV missing 'BadgeId' column: {csv_path}")
                return
            # Keep only the fields we need
            present_fields = [c for c in self._csv_enrichment_fields if c in df.columns]
            if not present_fields:
                self.logger.info("No enrichment fields present in intermediary CSV; skipping enrichment load")
                return
            subset = df[["BadgeId", *present_fields]].copy()
            # Build map BadgeId -> field dict
            for _, row in subset.iterrows():
                bid = str(row.get("BadgeId", ""))
                if not bid:
                    continue
                self._visitor_profile_map[bid] = {f: (row.get(f) if pd.notna(row.get(f)) else "NA") for f in present_fields}
            self.logger.info(f"Loaded enrichment profiles for {len(self._visitor_profile_map)} visitors from {csv_path}")
        except Exception as e:
            self.logger.error(f"Failed to load intermediary CSV enrichment: {str(e)}", exc_info=True)

    def _apply_csv_enrichment(self, visitor: Dict) -> Dict:
        """Override base fields with values from intermediary CSV when present."""
        try:
            bid = str(visitor.get("BadgeId", ""))
            if not bid or bid not in self._visitor_profile_map:
                return visitor
            enrichment = self._visitor_profile_map[bid]
            for field in self._csv_enrichment_fields:
                if field in enrichment:
                    visitor[field] = enrichment.get(field, visitor.get(field, "NA"))
            return visitor
        except Exception:
            return visitor

    def _prepare_similarity_criteria(self, visitor: Dict) -> List[Dict[str, object]]:
        """Build similarity criteria from configuration for a specific visitor."""
        criteria: List[Dict[str, object]] = []

        if not isinstance(self.similarity_attributes, dict):
            return criteria

        for attribute, config_value in self.similarity_attributes.items():
            # Support both shorthand numeric weight and extended dictionaries
            if isinstance(config_value, dict):
                weight = float(config_value.get("weight", 0))
                visitor_field = config_value.get("visitor_field", attribute)
                property_names = config_value.get("properties") or config_value.get("neo4j_properties")
            else:
                weight = float(config_value)
                visitor_field = attribute
                property_names = None

            if weight <= 0:
                continue

            value = visitor.get(visitor_field)
            if isinstance(value, str):
                value = value.strip()
                if not value or value.upper() == "NA":
                    continue
            elif value is None or pd.isna(value):
                continue

            if property_names is None:
                property_names = [attribute]
            elif isinstance(property_names, str):
                property_names = [property_names]

            property_names = [name for name in property_names if name]
            if not property_names:
                continue

            criteria.append(
                {
                    "attribute": attribute,
                    "visitor_field": visitor_field,
                    "value": value,
                    "weight": weight,
                    "property_names": property_names,
                }
            )

        return criteria

    def _get_visitors_to_process(self, create_only_new: bool = False) -> List[str]:
        """
        Get list of visitors to process based on create_only_new flag.
        
        Args:
            create_only_new: If True, only get visitors without recommendations
            
        Returns:
            List of badge IDs to process
        """
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    if create_only_new:
                        # Only get visitors without recommendations
                        # Newer Neo4j versions deprecate NOT EXISTS(variable.property) for property existence.
                        # If a property does not exist, referencing it returns NULL, so the IS NULL predicate
                        # covers both missing and explicit null cases. We also include = "0" for unprocessed.
                        query = f"""
                        MATCH (v:{self.visitor_this_year_label})
                        WHERE (v.show = $show_name OR v.show IS NULL)
                        AND (v.has_recommendation IS NULL OR v.has_recommendation = "0")
                        RETURN v.BadgeId as badge_id
                        """
                    else:
                        # Get all visitors for this show (reprocess all)
                        query = f"""
                        MATCH (v:{self.visitor_this_year_label})
                        WHERE v.show = $show_name OR v.show IS NULL
                        RETURN v.BadgeId as badge_id
                        """
                    
                    result = session.run(query, show_name=self.show_name)
                    badge_ids = [record["badge_id"] for record in result]
                    
                    if create_only_new:
                        self.logger.info(f"Found {len(badge_ids)} NEW visitors to process for {self.show_name} show (without recommendations)")
                    else:
                        self.logger.info(f"Found {len(badge_ids)} TOTAL visitors to process for {self.show_name} show (all visitors)")
                    
                    return badge_ids
                    
        except Exception as e:
            self.logger.error(f"Error getting visitors to process: {str(e)}", exc_info=True)
            return []

    def _get_visitor_info(self, badge_id: str) -> Optional[Dict]:
        """Get visitor information from Neo4j."""
        if badge_id in self._visitor_cache:
            return self._visitor_cache[badge_id]
        
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    query = f"""
                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                    WHERE v.show = $show_name OR v.show IS NULL
                    RETURN v
                    """
                    result = session.run(query, badge_id=badge_id, show_name=self.show_name)
                    record = result.single()
                    
                    if record:
                        visitor_data = dict(record["v"])
                        # Apply CSV enrichment overrides for base context fields
                        visitor_data = self._apply_csv_enrichment(visitor_data)
                        self._visitor_cache[badge_id] = visitor_data
                        return visitor_data
                    
        except Exception as e:
            self.logger.error(f"Error getting visitor info for {badge_id}: {str(e)}")
        
        return None

    def _get_this_year_sessions(self) -> List[Dict]:
        """Get all sessions for this year from Neo4j."""
        if self._this_year_sessions_cache is not None:
            return self._this_year_sessions_cache
        
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    query = f"""
                    MATCH (s:{self.session_this_year_label})
                    WHERE s.show = $show_name OR s.show IS NULL
                    RETURN s
                    """
                    result = session.run(query, show_name=self.show_name)
                    sessions = [dict(record["s"]) for record in result]
                    
                    self._this_year_sessions_cache = sessions
                    self.logger.info(f"Loaded {len(sessions)} sessions for this year")
                    return sessions
                    
        except Exception as e:
            self.logger.error(f"Error getting this year sessions: {str(e)}")
            return []

    def _find_similar_visitors(self, visitor: Dict, limit: int = 3) -> List[str]:
        """Find similar visitors based on configuration-driven similarity criteria."""
        import random

        visitor_id = visitor.get("BadgeId")
        if not visitor_id:
            return []

        criteria = self._prepare_similarity_criteria(visitor)
        if not criteria:
            self.logger.warning(f"No valid similarity attributes for visitor {visitor_id}")
            return []

        cache_key = (visitor_id, tuple((c["attribute"], str(c["value"])) for c in criteria), limit)
        if cache_key in self._similar_visitors_cache:
            return self._similar_visitors_cache[cache_key]

        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    params: Dict[str, object] = {
                        "visitor_id": visitor_id,
                        "show_name": self.show_name,
                    }

                    case_clauses: List[str] = []
                    for idx, criterion in enumerate(criteria):
                        param_name = re.sub(r"[^A-Za-z0-9_]", "_", f"sim_attr_{idx}_{criterion['attribute']}")
                        params[param_name] = criterion["value"]

                        property_checks = [f"v2.{prop} = ${param_name}" for prop in criterion["property_names"]]
                        combined_condition = " OR ".join(property_checks)
                        case_clauses.append(
                            f"CASE WHEN {combined_condition} THEN {criterion['weight']} ELSE 0 END"
                        )

                    if not case_clauses:
                        self.logger.warning(f"No similarity clauses generated for visitor {visitor_id}")
                        return []

                    base_similarity_expr = " + ".join(case_clauses)

                    available_past_labels = self._get_available_past_labels()
                    if not available_past_labels:
                        self.logger.warning(
                            "No past-year visitor labels available in Neo4j; skipping similar visitor lookup."
                        )
                        return []

                    if len(available_past_labels) == 1:
                        match_v2_clause = f"MATCH (v2:{available_past_labels[0]})"
                        label_condition = ""
                    else:
                        match_v2_clause = "MATCH (v2)"
                        label_condition = " AND (" + " OR ".join(
                            f"v2:{label}" for label in available_past_labels
                        ) + ")"

                    query = f"""
                    MATCH (v1:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                    WHERE v1.show = $show_name OR v1.show IS NULL
                    {match_v2_clause}
                    WHERE v2.BadgeId <> $visitor_id AND (v2.show = $show_name OR v2.show IS NULL){label_condition}
                    WITH v2, {base_similarity_expr} AS base_similarity
                    WHERE base_similarity > 0
                    MATCH (v2)-[:attended_session]->(s:{self.session_past_year_label})
                    WITH v2.BadgeId AS similar_visitor, base_similarity, COUNT(DISTINCT s) AS sessions_attended
                    WHERE sessions_attended > 0
                    RETURN similar_visitor, sessions_attended, base_similarity
                    ORDER BY base_similarity DESC, sessions_attended DESC
                    """

                    result = session.run(query, **params)
                    all_candidates = [
                        (
                            record["similar_visitor"],
                            record["sessions_attended"],
                            record["base_similarity"],
                        )
                        for record in result
                    ]

                    if not all_candidates:
                        self.logger.warning(f"No similar visitors found for visitor {visitor_id}")
                        return []

                    total_found = len(all_candidates)

                    if total_found <= limit:
                        similar_visitors = [badge for badge, _, _ in all_candidates]
                    else:
                        pool_size = min(total_found, max(limit * 3, 10))
                        top_pool = all_candidates[:pool_size]
                        selected = random.sample(top_pool, min(limit, len(top_pool)))
                        similar_visitors = [badge for badge, _, _ in selected]

                    self._similar_visitors_cache[cache_key] = similar_visitors

                    self.logger.info(
                        "Found %d total similar visitors for %s, randomly selected %d from top performers",
                        total_found,
                        visitor_id,
                        len(similar_visitors),
                    )

                    return similar_visitors

        except Exception as e:
            self.logger.error(f"Error finding similar visitors: {str(e)}")
            return []

    def _get_past_sessions_for_visitors(self, visitor_ids: List[str], is_returning: bool = False) -> List[Dict]:
        """
        Get past sessions attended by specified visitors.
        
        Args:
            visitor_ids: List of visitor badge IDs
            is_returning: If True, these are returning visitors (need to follow Same_Visitor relationship)
        
        Returns:
            List of past session dictionaries
        """
        if not visitor_ids:
            return []
        
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    available_past_labels = self._get_available_past_labels()
                    if not available_past_labels:
                        self.logger.warning(
                            "No past-year visitor labels available in Neo4j; skipping past session lookup."
                        )
                        return []

                    if is_returning:
                        # For returning visitors, follow the Same_Visitor relationship
                        # because they have DIFFERENT BadgeIds between years!
                        if len(available_past_labels) == 1:
                            label = available_past_labels[0]
                            query = f"""
                            MATCH (v:{self.visitor_this_year_label})-[:Same_Visitor]->(v_past:{label})
                            WHERE v.BadgeId IN $visitor_ids
                            MATCH (v_past)-[:attended_session]->(s:{self.session_past_year_label})
                            RETURN DISTINCT s
                            """
                        else:
                            label_condition = " OR ".join(
                                f"v_past:{label}" for label in available_past_labels
                            )
                            query = f"""
                            MATCH (v:{self.visitor_this_year_label})-[:Same_Visitor]->(v_past)
                            WHERE v.BadgeId IN $visitor_ids AND ({label_condition})
                            MATCH (v_past)-[:attended_session]->(s:{self.session_past_year_label})
                            RETURN DISTINCT s
                            """
                    else:
                        # For similar visitors (new visitors), query directly with their past year BadgeIds
                        if len(available_past_labels) == 1:
                            label = available_past_labels[0]
                            query = f"""
                            MATCH (v:{label})-[:attended_session]->(s:{self.session_past_year_label})
                            WHERE v.BadgeId IN $visitor_ids
                            RETURN DISTINCT s
                            """
                        else:
                            label_condition = " OR ".join(
                                f"v:{label}" for label in available_past_labels
                            )
                            query = f"""
                            MATCH (v)-[:attended_session]->(s:{self.session_past_year_label})
                            WHERE v.BadgeId IN $visitor_ids AND ({label_condition})
                            RETURN DISTINCT s
                            """
                    
                    result = session.run(query, visitor_ids=visitor_ids)
                    sessions = [dict(record["s"]) for record in result]
                    
                    return sessions
                    
        except Exception as e:
            self.logger.error(f"Error getting past sessions: {str(e)}")
            return []

    def calculate_session_similarities(
        self, 
        past_sessions: List[Dict], 
        this_year_sessions: List[Dict],
        min_score: float = 0.3
    ) -> List[Dict]:
        """
        Calculate similarities between past sessions and this year's sessions.
        
        Args:
            past_sessions: Sessions attended in the past
            this_year_sessions: Available sessions this year
            min_score: Minimum similarity score threshold
            
        Returns:
            List of recommended sessions with similarity scores
        """
        if not past_sessions or not this_year_sessions or not self.model:
            return []
        
        try:
            # Extract embeddings
            past_embeddings = []
            for session in past_sessions:
                if "embedding" in session and session["embedding"]:
                    embedding = json.loads(session["embedding"])
                    past_embeddings.append(embedding)
            
            this_year_embeddings = []
            this_year_sessions_filtered = []
            for session in this_year_sessions:
                if "embedding" in session and session["embedding"]:
                    embedding = json.loads(session["embedding"])
                    this_year_embeddings.append(embedding)
                    this_year_sessions_filtered.append(session)
            
            if not past_embeddings or not this_year_embeddings:
                return []
            
            # Calculate cosine similarities
            past_embeddings = np.array(past_embeddings)
            this_year_embeddings = np.array(this_year_embeddings)
            
            similarities = cosine_similarity(this_year_embeddings, past_embeddings)
            
            # Get max similarity for each this year session
            max_similarities = similarities.max(axis=1)
            
            # Filter and prepare recommendations
            recommendations = []
            for idx, score in enumerate(max_similarities):
                if score >= min_score:
                    session = this_year_sessions_filtered[idx].copy()
                    session["similarity"] = float(score)
                    recommendations.append(session)
            
            # Sort by similarity score
            recommendations.sort(key=lambda x: x["similarity"], reverse=True)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error calculating similarities: {str(e)}")
            return []

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords (case-insensitive)."""
        if not text or not isinstance(text, str):
            return False
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _apply_practice_type_rules(self, visitor: Dict, sessions: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Apply practice type filtering rules (generic version).
        
        Args:
            visitor: Visitor information
            sessions: List of sessions to filter
            
        Returns:
            Tuple of (filtered_sessions, rules_applied)
        """
        if not self.enable_filtering or not self.rules_config:
            return sessions, []
        
        # Use configured field name
        practice_field = self.practice_type_field
        
        if not visitor or practice_field not in visitor:
            return sessions, []
        
        practice_type = visitor.get(practice_field, "")
        if not practice_type or practice_type == "NA":
            return sessions, []
        
        filtered_sessions = []
        rules_applied = []
        
        # Check for different practice types based on configuration
        filtered_sessions = sessions

        # Check if practice contains equine or mixed
        if self._contains_any(practice_type, ["equine", "mixed"]):
            exclusions = self.rules_config.get("equine_mixed_exclusions", [])
            if exclusions:
                filtered_sessions = [
                    session for session in filtered_sessions
                    if not session.get("stream") or not self._contains_any(str(session["stream"]), exclusions)
                ]
                rules_applied.append(
                    f"practice_type: mixed/equine - excluded {', '.join(exclusions)}"
                )
                self.logger.info(
                    "Applied equine/mixed rule: filtered from %d to %d sessions",
                    len(sessions),
                    len(filtered_sessions),
                )

        # Check if practice contains small animal
        elif self._contains_any(practice_type, ["small animal"]):
            exclusions = self.rules_config.get("small_animal_exclusions", [])
            if exclusions:
                filtered_sessions = [
                    session for session in filtered_sessions
                    if not session.get("stream") or not self._contains_any(str(session["stream"]), exclusions)
                ]
                rules_applied.append(
                    f"practice_type: small animal - excluded {', '.join(exclusions)}"
                )
                self.logger.info(
                    "Applied small animal rule: filtered from %d to %d sessions",
                    len(sessions),
                    len(filtered_sessions),
                )

        # Apply any custom filtering rules from configuration
        custom_rules = self.rules_config.get("custom_practice_rules", [])
        if custom_rules:
            # Placeholder for custom rules if defined
            pass

        return filtered_sessions if filtered_sessions else sessions, rules_applied

    def _apply_role_rules(self, visitor: Dict, sessions: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Apply job role filtering rules (generic version).
        
        Args:
            visitor: Visitor information
            sessions: List of sessions to filter
            
        Returns:
            Tuple of (filtered_sessions, rules_applied)
        """
        if not self.enable_filtering or not self.rules_config:
            return sessions, []
        
        # Use configured field name
        job_field = self.job_role_field
        
        if not visitor or job_field not in visitor:
            return sessions, []
        
        job_role = visitor.get(job_field, "")
        if not job_role or job_role == "NA":
            return sessions, []
        
        filtered_sessions = []
        rules_applied = []
        
        # Only apply role-based filtering if roles are configured
        if self.vet_roles and job_role in self.vet_roles:
            exclusions = self.rules_config.get("vet_exclusions", [])
            if exclusions:
                filtered_sessions = [
                    session for session in sessions
                    if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
                ]
                rules_applied.append(f"role: vet - excluded {', '.join(exclusions)}")
                self.logger.info(
                    f"Applied vet role rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions"
                )
        
        elif self.nurse_roles and job_role in self.nurse_roles:
            allowed_streams = self.rules_config.get("nurse_streams", [])
            if allowed_streams:
                filtered_sessions = [
                    session for session in sessions
                    if session.get("stream") and self._contains_any(session["stream"], allowed_streams)
                ]
                rules_applied.append(f"role: nurse - limited to {', '.join(allowed_streams)}")
                self.logger.info(
                    f"Applied nurse role rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions"
                )
        else:
            # No specific role rule applies
            filtered_sessions = sessions
        
        return filtered_sessions if filtered_sessions else sessions, rules_applied

    def filter_sessions(self, visitor: Dict, sessions: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Filter sessions based on configured rules.
        
        Args:
            visitor: Visitor information
            sessions: List of sessions to filter
            
        Returns:
            Tuple of (filtered_sessions, rules_applied)
        """
        if not sessions or not self.enable_filtering:
            return sessions, []
        
        filtered_sessions = sessions
        rule_priority = self.rules_config.get("rule_priority", ["practice_type", "role"])
        all_rules_applied = []
        
        # Apply rules in priority order
        for rule_type in rule_priority:
            if rule_type == "practice_type":
                filtered_sessions, rules_applied = self._apply_practice_type_rules(
                    visitor, filtered_sessions
                )
                all_rules_applied.extend(rules_applied)
            elif rule_type == "role":
                filtered_sessions, rules_applied = self._apply_role_rules(
                    visitor, filtered_sessions
                )
                all_rules_applied.extend(rules_applied)
            else:
                self.logger.warning(f"Unknown rule type: {rule_type}")
        
        # Sort by similarity score (highest first)
        filtered_sessions.sort(
            key=lambda x: float(x.get("similarity", 0)), reverse=True
        )
        
        return filtered_sessions, all_rules_applied

    def _get_popular_past_sessions(self, limit: int = 20) -> List[Dict]:
        """
        Get the most popular sessions from last year as a fallback.
        
        This method now:
        - Filters sessions by show name for multi-show support
        - Includes attendance from BOTH main (BVA) and secondary (LVA) events
        - Treats both events as the same audience (which they are)
        - Gets top N popular sessions then randomly selects max_recommendations from them
        
        Args:
            limit: Minimum number of popular sessions to retrieve before random selection
            
        Returns:
            List of randomly selected popular session dictionaries (up to max_recommendations)
        """
        import random
        
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    if not self._label_exists(self.session_past_year_label):
                        self.logger.warning(
                            "Past-year session label '%s' is not present in Neo4j; popular session fallback will be skipped.",
                            self.session_past_year_label,
                        )
                        return []

                    available_past_labels = self._get_available_past_labels()
                    if not available_past_labels:
                        self.logger.warning(
                            "No past-year visitor labels available in Neo4j; popular session fallback cannot be computed."
                        )
                        return []

                    main_label_exists = self.visitor_last_year_bva_label in available_past_labels
                    secondary_label_exists = self.visitor_last_year_lva_label in available_past_labels

                    # Determine how many sessions to fetch from the database
                    # We want at least 'limit' sessions, but if max_recommendations is higher,
                    # fetch more to have a good pool for random selection
                    fetch_limit = max(limit, self.max_recommendations)
                    
                    # Build attendance aggregation dynamically based on available labels
                    query_parts: List[str] = [
                        f"MATCH (s:{self.session_past_year_label})",
                        "WHERE s.show = $show_name",
                    ]

                    if main_label_exists:
                        query_parts.extend(
                            [
                                f"OPTIONAL MATCH (v_main:{self.visitor_last_year_bva_label})-[:attended_session]->(s)",
                                "WITH s, COUNT(DISTINCT v_main) as main_event_count",
                            ]
                        )
                    else:
                        query_parts.append("WITH s, 0 as main_event_count")

                    if secondary_label_exists:
                        query_parts.extend(
                            [
                                f"OPTIONAL MATCH (v_secondary:{self.visitor_last_year_lva_label})-[:attended_session]->(s)",
                                "WITH s, main_event_count, COUNT(DISTINCT v_secondary) as secondary_event_count",
                            ]
                        )
                    else:
                        query_parts.append(
                            "WITH s, main_event_count, 0 as secondary_event_count"
                        )

                    query_parts.extend(
                        [
                            "WITH s, (main_event_count + secondary_event_count) as total_attendance",
                            "WHERE total_attendance > 0",
                            "ORDER BY total_attendance DESC",
                            "LIMIT $limit",
                            "RETURN s, total_attendance",
                        ]
                    )

                    query = "\n".join(query_parts)
                    
                    result = session.run(
                        query,
                        limit=fetch_limit,
                        show_name=self.show_name
                    )
                    
                    # Get all popular sessions with their attendance counts
                    popular_sessions = []
                    for record in result:
                        session_dict = dict(record["s"])
                        session_dict["_popularity_score"] = record["total_attendance"]
                        popular_sessions.append(session_dict)
                    
                    if not popular_sessions:
                        self.logger.warning(f"No popular sessions found for show '{self.show_name}'")
                        return []
                    
                    # Now randomly select max_recommendations sessions from the popular sessions
                    num_sessions_to_return = min(self.max_recommendations, len(popular_sessions))
                    
                    if num_sessions_to_return < len(popular_sessions):
                        # Randomly select from the pool of popular sessions
                        selected_sessions = random.sample(popular_sessions, num_sessions_to_return)
                        
                        # Sort selected sessions by popularity to maintain some quality ordering
                        # This helps if the recommendations are displayed in order
                        selected_sessions.sort(key=lambda x: x.get("_popularity_score", 0), reverse=True)
                        
                        # Remove the temporary popularity score before returning
                        for sess in selected_sessions:
                            sess.pop("_popularity_score", None)
                        
                        self.logger.info(
                            f"Retrieved {len(popular_sessions)} popular sessions for show '{self.show_name}', "
                            f"randomly selected {num_sessions_to_return} as fallback "
                            f"(combined attendance from main and secondary events)"
                        )
                    else:
                        # Return all sessions if we have fewer than max_recommendations
                        selected_sessions = popular_sessions
                        
                        # Remove the temporary popularity score before returning
                        for sess in selected_sessions:
                            sess.pop("_popularity_score", None)
                        
                        self.logger.info(
                            f"Retrieved all {len(selected_sessions)} popular sessions for show '{self.show_name}' as fallback "
                            f"(fewer than max_recommendations={self.max_recommendations} available)"
                        )
                    
                    return selected_sessions
                    
        except Exception as e:
            self.logger.error(f"Error getting popular sessions for show '{self.show_name}': {str(e)}")
            return []

    def generate_recommendations_for_visitor(self, badge_id: str) -> Dict[str, Any]:
        """Generate a rich recommendation payload for a single visitor."""

        result: Dict[str, Any] = {
            "visitor": {},
            "raw_recommendations": [],
            "filtered_recommendations": [],
            "rules_applied": [],
            "metadata": {
                "raw_count": 0,
                "filtered_count": 0,
                "filtering_strategy": "disabled",
                "generation_strategy": "",
                "notes": [],
            },
        }

        try:
            visitor = self._get_visitor_info(badge_id)
            if not visitor:
                self.logger.warning(f"Visitor {badge_id} not found")
                result["metadata"]["notes"] = ["Visitor not found in graph"]
                return result

            result["visitor"] = visitor

            this_year_sessions = self._get_this_year_sessions()
            if not this_year_sessions:
                self.logger.warning("No sessions available for this year")
                result["metadata"]["notes"] = ["No sessions available for this year"]
                return result

            assist_year_before = visitor.get("assist_year_before", "0")
            past_sessions: List[Dict] = []
            generation_notes: List[str] = []
            generation_strategy = ""
            should_adjust_similarity = False
            similarity_adjustment_reason = ""

            if assist_year_before == "1":
                generation_notes.append("Returning visitor")
                past_sessions = self._get_past_sessions_for_visitors([badge_id], is_returning=True)
                has_past_attendance = bool(past_sessions)
                if self.handle_returning_without_history and not has_past_attendance:
                    should_adjust_similarity = True
                    similarity_adjustment_reason = "returning_without_history"

                if past_sessions:
                    generation_strategy = "returning_past_sessions"
                    generation_notes.append(
                        f"Source: own past sessions ({len(past_sessions)} sessions)"
                    )
                    self.logger.info(
                        f"Returning visitor {badge_id} attended {len(past_sessions)} sessions last year"
                    )
                else:
                    self.logger.warning(
                        f"Returning visitor {badge_id} has no past session records - treating as new visitor"
                    )
                    similar_visitors = self._find_similar_visitors(
                        visitor, self.similar_visitors_count
                    )
                    if similar_visitors:
                        past_sessions = self._get_past_sessions_for_visitors(
                            similar_visitors, is_returning=False
                        )
                        generation_strategy = "returning_similar_visitors"
                        generation_notes.append(
                            f"Source: similar visitors ({len(similar_visitors)} visitors, {len(past_sessions)} sessions)"
                        )
                        self.logger.info(
                            f"Found {len(past_sessions)} sessions from {len(similar_visitors)} similar visitors"
                        )
                    else:
                        generation_strategy = "returning_popular_fallback"
                        generation_notes.append("Fallback applied: popular sessions")
                        self.logger.warning(
                            f"No similar visitors found for returning visitor {badge_id} - using popular sessions"
                        )
                        past_sessions = self._get_popular_past_sessions(
                            limit=self.max_recommendations * 5
                        )
                        if not past_sessions:
                            generation_notes.append("No sessions available for recommendations")
                            result["metadata"]["notes"] = generation_notes
                            return result
            else:
                generation_notes.append("New visitor")
                similar_visitors = self._find_similar_visitors(
                    visitor, self.similar_visitors_count
                )
                if similar_visitors:
                    past_sessions = self._get_past_sessions_for_visitors(
                        similar_visitors, is_returning=False
                    )
                    generation_strategy = "new_similar_visitors"
                    generation_notes.append(
                        f"Source: similar visitors ({len(similar_visitors)} visitors, {len(past_sessions)} sessions)"
                    )
                    self.logger.info(
                        f"New visitor {badge_id}: found {len(past_sessions)} sessions from similar visitors"
                    )
                else:
                    generation_strategy = "new_popular_fallback"
                    generation_notes.append("Fallback applied: popular sessions")
                    self.logger.warning(
                        f"No similar visitors found for {badge_id} - using popular sessions as fallback"
                    )
                    past_sessions = self._get_popular_past_sessions(
                        limit=self.max_recommendations * 5
                    )
                    if not past_sessions:
                        generation_notes.append("No sessions available for recommendations")
                        result["metadata"]["notes"] = generation_notes
                        return result

            raw_recommendations: List[Dict] = []
            if past_sessions:
                raw_recommendations = self.calculate_session_similarities(
                    past_sessions, this_year_sessions, self.min_similarity_score
                )

            raw_count = len(raw_recommendations)
            generation_notes.append(f"Retrieved {raw_count} raw recommendations")

            filtered_recommendations = raw_recommendations
            removed_overlap_sessions: List[Dict] = []
            rules_applied: List[str] = []
            filtering_message = "Filtering disabled"
            filtering_strategy = "disabled"

            if self.use_langchain:
                filtering_strategy = "langchain"
                filtering_message = "Using LangChain filtering"
            elif self.enable_filtering:
                filtering_strategy = "rule_based"
                filtering_message = "Using rule-based filtering"

            if self.enable_filtering and raw_recommendations:
                filtered_recommendations, rules_applied = self.filter_sessions(
                    visitor, raw_recommendations
                )
                self.logger.info(
                    f"Filtered {len(raw_recommendations)} to {len(filtered_recommendations)} recommendations"
                )

            custom_rules_metadata = {
                "enabled": self.custom_rules_enabled,
                "applied": False,
                "rule_results": [],
                "notes": [],
            }

            if self.custom_rules_enabled and filtered_recommendations:
                filtered_recommendations, custom_rules_summary = (
                    self._apply_custom_recommendation_rules(
                        visitor, filtered_recommendations
                    )
                )
                custom_rules_metadata["applied"] = True
                custom_rules_metadata["rule_results"] = custom_rules_summary.get(
                    "rule_results", []
                )
                custom_rules_metadata["notes"] = custom_rules_summary.get("notes", [])
                if "error" in custom_rules_summary:
                    custom_rules_metadata["error"] = custom_rules_summary["error"]

                if custom_rules_metadata["notes"]:
                    generation_notes.extend(custom_rules_metadata["notes"])

                removed_total = sum(
                    int(result.get("removed_count", 0) or 0)
                    for result in custom_rules_metadata["rule_results"]
                )
                if removed_total:
                    generation_notes.append(
                        f"Custom rules removed {removed_total} session(s)"
                    )
                elif not custom_rules_summary.get("error"):
                    generation_notes.append("Custom rules applied with no removals")
            else:
                if self.custom_rules_config.get("enabled", False):
                    generation_notes.append(
                        "Custom rules inactive (event or filtering conditions not met)"
                    )

            filtered_recommendations = self._annotate_overlaps_for_recommendations(
                filtered_recommendations, badge_id
            )

            if self.resolve_overlaps_by_similarity and filtered_recommendations:
                (
                    filtered_recommendations,
                    removed_overlap_sessions,
                ) = self._resolve_overlapping_recommendations_by_similarity(
                    filtered_recommendations
                )
                filtered_recommendations = self._annotate_overlaps_for_recommendations(
                    filtered_recommendations, badge_id
                )

            generation_notes.append(filtering_message)
            if rules_applied:
                generation_notes.extend(rules_applied)
            elif self.enable_filtering:
                generation_notes.append("No filtering rules applied")

            if self.resolve_overlaps_by_similarity:
                if removed_overlap_sessions:
                    removed_ids = [
                        str(rec.get("session_id"))
                        for rec in removed_overlap_sessions
                        if rec.get("session_id")
                    ]
                    removed_ids_str = ", ".join(removed_ids) if removed_ids else ""
                    if removed_ids_str:
                        generation_notes.append(
                            f"Overlap resolution removed {len(removed_overlap_sessions)} session(s): {removed_ids_str}"
                        )
                    else:
                        generation_notes.append(
                            f"Overlap resolution removed {len(removed_overlap_sessions)} session(s)"
                        )
                    self.logger.info(
                        "Removed %d overlapping session(s) for visitor %s via similarity resolution",
                        len(removed_overlap_sessions),
                        badge_id,
                    )
                else:
                    generation_notes.append("Overlap resolution applied: no conflicts detected")
            else:
                generation_notes.append("Overlap resolution disabled")

            # Apply max recommendations cap
            filtered_recommendations = filtered_recommendations[: self.max_recommendations]

            similarity_exponent_applied = False
            if should_adjust_similarity and filtered_recommendations:
                filtered_recommendations = self._apply_similarity_exponent(
                    filtered_recommendations,
                    self.returning_without_history_exponent,
                )
                similarity_exponent_applied = True

            filtered_recommendations = self._annotate_overlaps_for_recommendations(
                filtered_recommendations, badge_id
            )
            filtered_count = len(filtered_recommendations)

            if similarity_exponent_applied:
                exponent_note = (
                    f"Similarity exponent applied (^{self.returning_without_history_exponent})"
                )
                if similarity_adjustment_reason:
                    exponent_note += (
                        f" due to {similarity_adjustment_reason.replace('_', ' ')}"
                    )
            elif should_adjust_similarity:
                exponent_note = "Similarity exponent flagged but no recommendations to adjust"
            elif self.handle_returning_without_history and assist_year_before == "1":
                exponent_note = "Similarity exponent skipped (past attendance found)"
            else:
                exponent_note = "Similarity exponent disabled"

            generation_notes.append(exponent_note)
            generation_notes.append(f"Filtered to {filtered_count} recommendations")

            overlap_metadata = {
                "enabled": self.resolve_overlaps_by_similarity,
                "removed_count": len(removed_overlap_sessions),
                "removed_sessions": [
                    rec.get("session_id")
                    for rec in removed_overlap_sessions
                    if rec.get("session_id")
                ],
            }

            similarity_adjustment_metadata = {
                "enabled": self.handle_returning_without_history,
                "flagged": should_adjust_similarity,
                "applied": similarity_exponent_applied,
                "exponent": self.returning_without_history_exponent
                if self.handle_returning_without_history
                else 1.0,
                "reason": similarity_adjustment_reason if similarity_adjustment_reason else "",
            }

            metadata = {
                "raw_count": raw_count,
                "filtered_count": filtered_count,
                "filtering_strategy": filtering_strategy,
                "generation_strategy": generation_strategy,
                "notes": generation_notes,
                "rules_applied": rules_applied,
                "overlap_resolution": overlap_metadata,
                "similarity_adjustment": similarity_adjustment_metadata,
                "custom_rules": custom_rules_metadata,
            }

            result.update(
                {
                    "visitor": visitor,
                    "raw_recommendations": raw_recommendations,
                    "filtered_recommendations": filtered_recommendations,
                    "rules_applied": rules_applied,
                    "metadata": metadata,
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error generating recommendations for {badge_id}: {str(e)}")
            result["metadata"]["notes"].append("Error while generating recommendations")
            return result

    def _update_visitor_recommendations(self, recommendations_data: List[Dict]):
        """Update visitors with has_recommendation flag and create IS_RECOMMENDED relationships."""
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    updated_with_recs = 0
                    updated_without_recs = 0
                    
                    for rec in recommendations_data:
                        visitor_id = rec["visitor"]["BadgeId"]
                        recommended_sessions = rec.get("filtered_recommendations", [])
                        
                        if recommended_sessions:
                            # Update visitor with has_recommendation flag
                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            WHERE v.show = $show_name OR v.show IS NULL
                            SET v.has_recommendation = "1",
                                v.show = $show_name,
                                v.recommendations_generated_at = $timestamp
                            """
                            session.run(update_query, 
                                       visitor_id=visitor_id, 
                                       show_name=self.show_name,
                                       timestamp=datetime.now().isoformat())
                            updated_with_recs += 1
                            
                            # Create IS_RECOMMENDED relationships
                            for rec_session in recommended_sessions:
                                session_id = rec_session.get("session_id")
                                if session_id:
                                    rel_query = f"""
                                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                                    WHERE v.show = $show_name
                                    MATCH (s:{self.session_this_year_label} {{session_id: $session_id}})
                                    WHERE s.title IS NOT NULL AND trim(s.title) <> ''
                                    MERGE (v)-[r:IS_RECOMMENDED]->(s)
                                    SET r.similarity_score = $score,
                                        r.generated_at = $timestamp,
                                        r.show = $show_name
                                    """
                                    session.run(
                                        rel_query,
                                        visitor_id=visitor_id,
                                        show_name=self.show_name,
                                        session_id=session_id,
                                        score=rec_session.get("similarity", 0),
                                        timestamp=datetime.now().isoformat()
                                    )
                        else:
                            # Mark visitor as processed but without recommendations
                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            WHERE v.show = $show_name OR v.show IS NULL
                            SET v.has_recommendation = "0",
                                v.show = $show_name,
                                v.recommendations_generated_at = $timestamp
                            """
                            session.run(update_query, 
                                       visitor_id=visitor_id, 
                                       show_name=self.show_name,
                                       timestamp=datetime.now().isoformat())
                            updated_without_recs += 1
                    
                    self.logger.info(f"Updated {updated_with_recs} visitors with recommendations, {updated_without_recs} without")
                    
        except Exception as e:
            self.logger.error(f"Error updating visitor recommendations: {str(e)}")

    def json_to_dataframe(self, json_file: str) -> pd.DataFrame:
        """
        Convert recommendations JSON to DataFrame for analysis.
        Includes ALL similarity attributes configured for the show.
        """
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            rows = []
            # Config-driven additional visitor fields for enrichment
            extra_fields = self.recommendation_config.get("export_additional_visitor_fields", [])
            extra_fields = [f for f in extra_fields if isinstance(f, str) and f]
            # Always include common contact fields if present in visitor profile
            for f in ["Email", "Forename", "Surname", "Tel", "Mobile"]:
                if f not in extra_fields:
                    extra_fields.append(f)

            for visitor_id, recs in data.get("recommendations", {}).items():
                visitor_info = recs.get("visitor", {})
                metadata = recs.get("metadata", {})
                notes = metadata.get("notes", [])
                if isinstance(notes, list):
                    metadata_list = [str(n) for n in notes if n]
                elif isinstance(notes, str):
                    metadata_list = [notes] if notes else []
                else:
                    metadata_list = []
                metadata_summary = json.dumps(metadata_list)
                
                for rec in recs.get("filtered_recommendations", []):
                    # Start with basic fields
                    row = {
                        "visitor_id": visitor_id,
                        "assist_year_before": visitor_info.get("assist_year_before", "0"),
                        "show": self.show_name,
                    }
                    
                    # Add ALL configured similarity attributes dynamically
                    for attr_name in self.similarity_attributes.keys():
                        # Clean column name for CSV (replace spaces and special chars)
                        col_name = attr_name.replace(" ", "_").replace(".", "")
                        row[col_name] = visitor_info.get(attr_name, "NA")
                    
                    # Add base context fields (if not part of similarity attributes)
                    base_context_fields = ["Company", "JobTitle", "Email_domain", "Country", "Source"]
                    for field in base_context_fields:
                        if field not in self.similarity_attributes:
                            row[field] = visitor_info.get(field, "NA")

                    # Add configured extra enrichment fields (Email, Forename, Surname, Tel, Mobile, etc.)
                    for field in extra_fields:
                        # Only add if not already present (avoid overwrite) and value exists
                        if field not in row:
                            row[field] = visitor_info.get(field, "NA")
                    
                    row["overlapping_sessions"] = rec.get("overlapping_sessions", "")

                    # Add session recommendation details
                    row.update({
                        "session_id": rec.get("session_id"),
                        "session_title": rec.get("title"),
                        "session_stream": rec.get("stream"),
                        "session_date": rec.get("date"),
                        "session_start_time": rec.get("start_time"),
                        "session_end_time": rec.get("end_time"),
                        "similarity_score": rec.get("similarity"),
                        "sponsored_by": rec.get("sponsored_by", ""),
                        "session_theatre_name": rec.get("theatre__name")
                        or rec.get("theatre_name")
                        or rec.get("theatre")
                        or "",
                    })

                    row["recommendation_metadata"] = metadata_summary
                    
                    rows.append(row)
            
            df = pd.DataFrame(rows)

            # Flag overlapping sessions so we can identify concurrent recommendations per visitor
            df = self._flag_overlapping_sessions(df)
            
            # Reorder columns for better readability
            priority_cols = ["visitor_id", "show", "assist_year_before"]
            similarity_cols = [col for col in df.columns if col in [
                attr.replace(" ", "_").replace(".", "") for attr in self.similarity_attributes.keys()
            ]]
            session_cols = [col for col in df.columns if col.startswith("session_")]
            if "overlapping_sessions" in df.columns:
                session_cols.append("overlapping_sessions")

            # Keep extra/enrichment fields grouped after priority + similarity
            enrichment_cols = [c for c in ["Company", "JobTitle", "Email_domain", "Country", "Source"] if c in df.columns]
            # Append configured extra fields preserving order
            for f in extra_fields:
                if f in df.columns and f not in enrichment_cols:
                    enrichment_cols.append(f)

            # Other cols are anything not already categorized
            categorized = set(priority_cols + similarity_cols + session_cols + enrichment_cols)
            other_cols = [c for c in df.columns if c not in categorized]
            
            ordered_cols = priority_cols + similarity_cols + enrichment_cols + other_cols + session_cols
            df = df[[col for col in ordered_cols if col in df.columns]]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error converting JSON to DataFrame: {str(e)}")
            return pd.DataFrame()

    def _flag_overlapping_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Annotate each visitor's recommendations with overlapping sessions by time."""

        if df.empty:
            return df

        # Resolve column names as they appear in the CSV export
        column_aliases = {
            "visitor_id": ["visitor_id", "BadgeId", "badgeid"],
            "session_id": ["session_id"],
            "session_date": ["session_date", "date"],
            "session_start_time": ["session_start_time", "start_time"],
            "session_end_time": ["session_end_time", "end_time"],
        }

        resolved_cols: Dict[str, str] = {}
        for logical_name, candidates in column_aliases.items():
            for candidate in candidates:
                if candidate in df.columns:
                    resolved_cols[logical_name] = candidate
                    break

        required_keys = set(column_aliases.keys())
        if not required_keys.issubset(resolved_cols.keys()):
            missing = required_keys - set(resolved_cols.keys())
            self.logger.warning(
                "Unable to flag overlapping sessions; missing columns: %s",
                ", ".join(sorted(missing)),
            )
            return df

        df = df.copy()

        session_date_col = resolved_cols["session_date"]
        start_col = resolved_cols["session_start_time"]
        end_col = resolved_cols["session_end_time"]

        df["start_datetime"] = pd.to_datetime(
            df[session_date_col].astype(str) + " " + df[start_col].astype(str),
            errors="coerce",
        )
        df["end_datetime"] = pd.to_datetime(
            df[session_date_col].astype(str) + " " + df[end_col].astype(str),
            errors="coerce",
        )

        overlap_col = "overlapping_sessions"
        df[overlap_col] = ""

        visitor_col = resolved_cols["visitor_id"]
        session_id_col = resolved_cols["session_id"]

        for visitor_id, group in df.groupby(visitor_col):
            if len(group) <= 1:
                continue

            valid_mask = group["start_datetime"].notna() & group["end_datetime"].notna()
            group = group[valid_mask]
            if group.empty:
                continue

            for idx, row in group.iterrows():
                current_start = row["start_datetime"]
                current_end = row["end_datetime"]
                current_id = row[session_id_col]

                overlaps = group[
                    (group[session_id_col] != current_id)
                    & (group["start_datetime"] < current_end)
                    & (group["end_datetime"] > current_start)
                ][session_id_col].tolist()

                if overlaps:
                    df.at[idx, overlap_col] = "|".join(map(str, overlaps))

        df.drop(columns=["start_datetime", "end_datetime"], inplace=True)
        return df

    def _annotate_overlaps_for_recommendations(
        self, recommendations: List[Dict], visitor_id: Optional[str] = None
    ) -> List[Dict]:
        """Add an overlapping_sessions field to each recommendation entry."""

        if not recommendations:
            return recommendations

        df = pd.DataFrame(recommendations)
        if visitor_id is not None and "visitor_id" not in df.columns:
            df["visitor_id"] = visitor_id
        df = self._flag_overlapping_sessions(df)

        if "overlapping_sessions" not in df.columns:
            return [
                {**rec, "overlapping_sessions": rec.get("overlapping_sessions", "")}
                for rec in recommendations
            ]

        overlaps = df["overlapping_sessions"].tolist()
        annotated: List[Dict] = []
        for rec, overlap in zip(recommendations, overlaps):
            value = ""
            if isinstance(overlap, str) and overlap:
                value = overlap
            annotated.append({**rec, "overlapping_sessions": value})

        return annotated

    def _parse_session_interval(self, session: Dict) -> Optional[Tuple[pd.Timestamp, pd.Timestamp]]:
        """Parse session start/end datetimes. Returns None when parsing fails."""

        date_value = session.get("session_date") or session.get("date")
        start_value = session.get("session_start_time") or session.get("start_time")
        end_value = session.get("session_end_time") or session.get("end_time")

        if not date_value or not start_value or not end_value:
            return None

        start_dt = pd.to_datetime(f"{date_value} {start_value}", errors="coerce")
        end_dt = pd.to_datetime(f"{date_value} {end_value}", errors="coerce")

        if pd.isna(start_dt) or pd.isna(end_dt):
            return None

        return start_dt, end_dt

    def _resolve_overlapping_recommendations_by_similarity(
        self, recommendations: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Remove overlapping sessions keeping the highest similarity entries."""

        if not recommendations:
            return recommendations, []

        kept: List[Dict] = []
        removed: List[Dict] = []

        for rec in recommendations:
            interval = self._parse_session_interval(rec)
            if interval is None:
                kept.append(rec)
                continue

            overlaps_indices: List[int] = []
            for idx, existing in enumerate(kept):
                existing_interval = existing.get("_interval")
                if existing_interval is None:
                    existing_interval = self._parse_session_interval(existing)
                    if existing_interval is None:
                        continue
                    kept[idx]["_interval"] = existing_interval

                existing_start, existing_end = existing_interval
                current_start, current_end = interval

                if existing_start < current_end and existing_end > current_start:
                    overlaps_indices.append(idx)

            if not overlaps_indices:
                rec_copy = {**rec, "_interval": interval}
                kept.append(rec_copy)
                continue

            current_similarity = float(rec.get("similarity", 0) or 0)

            removable_indices: List[int] = []
            discard_current = False

            for idx in overlaps_indices:
                existing = kept[idx]
                existing_similarity = float(existing.get("similarity", 0) or 0)

                if existing_similarity >= current_similarity:
                    discard_current = True
                    break
                removable_indices.append(idx)

            if discard_current:
                removed.append(rec)
                continue

            for idx in sorted(removable_indices, reverse=True):
                removed_entry = kept.pop(idx)
                removed_entry.pop("_interval", None)
                removed.append(removed_entry)

            rec_copy = {**rec, "_interval": interval}
            kept.append(rec_copy)

        for rec in kept:
            rec.pop("_interval", None)

        kept.sort(key=lambda x: float(x.get("similarity", 0) or 0), reverse=True)

        return kept, removed

    def _apply_similarity_exponent(
        self, recommendations: List[Dict], exponent: float
    ) -> List[Dict]:
        """Raise similarity scores to the given exponent while clamping the result."""

        if not recommendations:
            return recommendations

        if exponent == 1:
            return recommendations

        adjusted: List[Dict] = []
        for rec in recommendations:
            similarity_value = rec.get("similarity")
            try:
                similarity_float = float(similarity_value)
            except (TypeError, ValueError):
                adjusted.append(rec)
                continue

            # Clamp input to sensible bounds before exponentiation
            similarity_float = max(0.0, min(similarity_float, 1.0))
            adjusted_similarity = math.pow(similarity_float, exponent)
            adjusted_similarity = max(0.0, min(adjusted_similarity, 1.0))

            updated_rec = dict(rec)
            updated_rec["similarity"] = adjusted_similarity
            adjusted.append(updated_rec)

        return adjusted

    def _apply_custom_recommendation_rules(
        self, visitor: Dict, sessions: List[Dict]
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """Apply vet-specific custom recommendation rules when configured."""

        if not sessions:
            return sessions, {"notes": [], "rule_results": []}

        try:
            adjusted_sessions, summary = (
                vet_specific_functions.apply_vet_custom_recommendation_rules(
                    visitor=visitor,
                    sessions=sessions,
                    processor=self,
                    rules_config=self.custom_rules_config,
                )
            )

            if not isinstance(summary, dict):
                summary = {"notes": [], "rule_results": []}

            if "notes" not in summary or not isinstance(summary["notes"], list):
                summary["notes"] = []
            if "rule_results" not in summary or not isinstance(summary["rule_results"], list):
                summary["rule_results"] = []

            return adjusted_sessions, summary

        except Exception as exc:
            self.logger.error(
                "Error applying custom recommendation rules: %s", str(exc), exc_info=True
            )
            return sessions, {
                "notes": [f"Custom rule processing error: {exc}"],
                "rule_results": [],
                "error": str(exc),
            }

    def process(self, create_only_new: bool = False):
        """
        Main processing method to generate recommendations for all visitors.
        
        Args:
            create_only_new: If True, only process visitors without existing recommendations
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting session recommendation processing for {self.show_name} show")
            self.logger.info(f"Mode: {'Incremental (new only)' if create_only_new else 'Full (all visitors)'}")
            
            # Get visitors to process
            visitors_to_process = self._get_visitors_to_process(create_only_new)
            
            if not visitors_to_process:
                # Ensure summary utilities have the expected alias key even when nothing processed
                self.statistics["visitors_processed"] = 0
                self.statistics["total_visitors_processed"] = 0
                self.logger.info("No visitors to process for recommendations.")
                return
            
            self.statistics["visitors_processed"] = len(visitors_to_process)
            
            # Process visitors and generate recommendations
            all_recommendations = []
            successful = 0
            errors = 0
            total_recommendations = 0
            unique_sessions = set()
            
            # Create output file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"recommendations/visitor_recommendations_{self.show_name}_{timestamp}.json"
            output_file.parent.mkdir(exist_ok=True)
            
            # Process each visitor
            recommendations_dict = {}
            
            for i, badge_id in enumerate(visitors_to_process, 1):
                if i % 100 == 0:
                    self.logger.info(f"Processing visitor {i}/{len(visitors_to_process)}")
                
                try:
                    visitor_payload = self.generate_recommendations_for_visitor(badge_id)
                    visitor = visitor_payload.get("visitor", {})
                    raw_recommendations = visitor_payload.get("raw_recommendations", [])
                    filtered_recommendations = visitor_payload.get("filtered_recommendations", [])
                    rules_applied = visitor_payload.get("rules_applied", [])
                    metadata = visitor_payload.get("metadata", {})
                    raw_count = metadata.get("raw_count", len(raw_recommendations))
                    filtered_count = metadata.get("filtered_count", len(filtered_recommendations))

                    self.statistics["total_filtered_recommendations"] += filtered_count

                    payload_for_storage = {
                        "visitor": visitor,
                        "raw_recommendations": raw_recommendations,
                        "filtered_recommendations": filtered_recommendations,
                        "metadata": metadata,
                        "rules_applied": rules_applied,
                    }

                    can_update_neo4j = bool(visitor.get("BadgeId"))

                    if filtered_recommendations:
                        self.statistics["visitors_with_recommendations"] += 1
                        successful += 1
                        total_recommendations += filtered_count

                        for rec in filtered_recommendations:
                            session_id = rec.get("session_id")
                            if session_id:
                                unique_sessions.add(session_id)

                        if can_update_neo4j:
                            all_recommendations.append(payload_for_storage)
                        recommendations_dict[badge_id] = payload_for_storage

                        self.logger.debug(
                            f"Generated {filtered_count} recommendations for visitor {badge_id}"
                        )
                    else:
                        self.statistics["visitors_without_recommendations"] += 1
                        if can_update_neo4j:
                            all_recommendations.append(payload_for_storage)
                        recommendations_dict[badge_id] = payload_for_storage
                        
                        if not visitor:
                            errors += 1
                            self.statistics["errors"] += 1
                            self.statistics["error_details"].append(
                                f"{badge_id}: visitor context missing"
                            )
                            self.logger.error(
                                f"Visitor context missing for badge {badge_id}; unable to update Neo4j"
                            )
                        
                except Exception as e:
                    errors += 1
                    self.statistics["errors"] += 1
                    self.statistics["error_details"].append(f"{badge_id}: {str(e)}")
                    self.logger.error(f"Error processing visitor {badge_id}: {str(e)}")
            
            # Update statistics
            self.statistics["total_recommendations_generated"] = total_recommendations
            self.statistics["unique_recommended_sessions"] = len(unique_sessions)
            
            # Add alias for backward compatibility with summary_utils
            self.statistics["total_visitors_processed"] = self.statistics["visitors_processed"]
            self.statistics["unique_recommended_sessions"] = len(unique_sessions)
            
            # Save recommendations to file
            output_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "show": self.show_name,
                    "visitors_processed": len(visitors_to_process),
                    "successful": successful,
                    "errors": errors,
                    "total_recommendations": total_recommendations,
                    "unique_sessions": len(unique_sessions),
                    "filtering_enabled": self.enable_filtering,
                    "create_only_new": create_only_new,
                    "configuration": {
                        "min_similarity_score": self.min_similarity_score,
                        "max_recommendations": self.max_recommendations,
                        "similar_visitors_count": self.similar_visitors_count,
                    }
                },
                "recommendations": recommendations_dict,
                "statistics": self.statistics,
            }
            
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved recommendations to {output_file}")
            self.logger.info(
                f"Generated recommendations for {successful} visitors with {errors} errors"
            )
            
            # Save as CSV if configured
            if self.recommendation_config.get("save_csv", True):
                df = self.json_to_dataframe(output_file)
                csv_file = str(output_file).replace(".json", ".csv")
                df.to_csv(csv_file, index=False)
                self.logger.info(f"Saved recommendations DataFrame to {csv_file}")
            
            # Update Neo4j with recommendations
            if len(all_recommendations) > 0:
                self.logger.info("Updating Neo4j with recommendation data")
                self._update_visitor_recommendations(all_recommendations)
                self.logger.info("Completed Neo4j updates")
            
            # Calculate processing time
            self.statistics["processing_time"] = time.time() - start_time
            self.logger.info(
                f"Completed session recommendation processing in {self.statistics['processing_time']:.2f} seconds"
            )
            
        except Exception as e:
            self.logger.error(
                f"Error in session recommendation processing: {str(e)}", exc_info=True
            )
            self.statistics["errors"] += 1
            self.statistics["error_details"].append(f"General error: {str(e)}")
            self.statistics["processing_time"] = time.time() - start_time


if __name__ == "__main__":
    """Direct test execution."""
    import argparse
    from utils.config_utils import load_config
    
    parser = argparse.ArgumentParser(description="Process session recommendations")
    parser.add_argument(
        "--config",
        type=str,
        default="config/config_vet.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--create-only-new",
        action="store_true",
        help="Only create recommendations for visitors without them"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Create and run processor
    processor = SessionRecommendationProcessor(config)
    processor.process(create_only_new=args.create_only_new)
    
    # Print statistics
    print("\nProcessing Statistics:")
    for key, value in processor.statistics.items():
        if key != "error_details":
            print(f"  {key}: {value}")
    
    # Print error details if any
    if processor.statistics.get("error_details"):
        print("\nError Details:")
        for error in processor.statistics["error_details"][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(processor.statistics["error_details"]) > 10:
            print(f"  ... and {len(processor.statistics['error_details']) - 10} more errors")