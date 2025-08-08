#!/usr/bin/env python3
"""
Generic Session Recommendation Processor

This processor generates session recommendations for visitors based on:
- Their past attendance (if they visited last year)
- Similar visitors' attendance patterns (if they're new)

The processor is configurable to work with different shows (BVA, ECOMM, etc.)
through YAML configuration files.
"""

import os
import json
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import concurrent.futures
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

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
        
        # Neo4j connection parameters
        self.uri = self.neo4j_config.get("uri")
        self.username = self.neo4j_config.get("username")
        self.password = self.neo4j_config.get("password")
        
        # Recommendation parameters
        self.min_similarity_score = self.recommendation_config.get("min_similarity_score", 0.3)
        self.max_recommendations = self.recommendation_config.get("max_recommendations", 10)
        self.similar_visitors_count = self.recommendation_config.get("similar_visitors_count", 3)
        self.use_langchain = self.recommendation_config.get("use_langchain", False) and has_langchain
        self.enable_filtering = self.recommendation_config.get("enable_filtering", True)
        
        # Similarity attributes for finding similar visitors
        self.similarity_attributes = self.recommendation_config.get("similarity_attributes", {})
        
        # Filtering rules configuration (show-specific)
        self.rules_config = self.recommendation_config.get("rules_config", {})
        
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
        
        # Job role groups (for veterinary shows)
        self.vet_roles = [
            "Vet/Vet Surgeon",
            "Assistant Vet",
            "Vet/Owner",
            "Clinical or other Director",
            "Locum Vet",
            "Academic",
        ]
        self.nurse_roles = ["Head Nurse/Senior Nurse", "Vet Nurse", "Locum RVN"]
        
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
        
        self.logger.info(f"SessionRecommendationProcessor initialized for {self.show_name} show")

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the processor."""
        logger = logging.getLogger("session_recommendation_processor")
        logger.setLevel(logging.INFO)
        
        # Console handler
        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            ch.setFormatter(formatter)
            logger.addHandler(ch)
        
        return logger

    def _init_model(self):
        """Initialize the sentence transformer model if not already initialized."""
        if self.model is None:
            model_name = self.config.get("embeddings", {}).get("model", "all-MiniLM-L6-v2")
            self.logger.info(f"Loading sentence transformer model: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.logger.info("Model loaded successfully")

    def _get_visitors_to_process(self, create_only_new):
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
                        query = f"""
                        MATCH (v:{self.visitor_this_year_label})
                        WHERE v.has_recommendation IS NULL OR v.has_recommendation = "0"
                        RETURN v.BadgeId as badge_id
                        """
                    else:
                        # Get all visitors
                        query = f"""
                        MATCH (v:{self.visitor_this_year_label})
                        RETURN v.BadgeId as badge_id
                        """

                    result = session.run(query)
                    badge_ids = [record["badge_id"] for record in result]

                    self.logger.info(f"Found {len(badge_ids)} visitors to process")
                    return badge_ids

        except Exception as e:
            self.logger.error(
                f"Error getting visitors to process: {str(e)}", exc_info=True
            )
            return []

    def get_visitor_info(self, tx, visitor_id):
        """Get visitor information and check if they visited last year."""
        if visitor_id in self._visitor_cache:
            return self._visitor_cache[visitor_id]

        visitor_query = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
        RETURN v
        """
        visitor_data = tx.run(visitor_query, visitor_id=visitor_id).single()

        if not visitor_data:
            return None

        visitor = visitor_data["v"]
        assisted = visitor.get("assist_year_before", "0")

        self._visitor_cache[visitor_id] = {"visitor": visitor, "assisted": assisted}
        return self._visitor_cache[visitor_id]

    def get_past_sessions(self, tx, visitor_id):
        """Get sessions the visitor attended last year."""
        query_past = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
        WHERE (vp:{self.visitor_last_year_bva_label} OR vp:{self.visitor_last_year_lva_label})
        RETURN DISTINCT sp.session_id as session_id, sp.embedding as embedding
        """

        results = tx.run(query_past, visitor_id=visitor_id).data()

        sessions = []
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions.append({"session_id": r["session_id"], "embedding": embedding})

        return sessions

    def find_similar_visitors_batch(self, tx, visitor, num_similar_visitors=3):
        """
        Find similar visitors with batch processing.
        Uses the EXACT SAME hybrid approach as the old processor:
        1. SQL-based pre-filtering with attribute matching
        2. Text embedding similarity calculation
        3. Combined scoring: (embedding_sim * 0.7) + (base_similarity * 0.3 / 4)
        """
        visitor_id = visitor["BadgeId"]

        # Check cache first
        if visitor_id in self._similar_visitors_cache:
            return self._similar_visitors_cache[visitor_id]

        # Get all visitors with sessions in one query
        # Note: We always look at ALL visitors who attended last year, not just new ones
        query = f"""
        MATCH (v:{self.visitor_this_year_label})
        WHERE v.assist_year_before = '1' AND v.BadgeId <> $visitor_id
        // Pre-filter to avoid processing all visitors
        WITH v, 
             CASE WHEN v.job_role = $job_role THEN 1 ELSE 0 END + 
             CASE WHEN v.what_type_does_your_practice_specialise_in = $practice_type THEN 1 ELSE 0 END +
             CASE WHEN v.organisation_type = $org_type THEN 1 ELSE 0 END +
             CASE WHEN v.Country = $country THEN 1 ELSE 0 END AS base_similarity
        // Only process those with some similarity
        WHERE base_similarity > 0
        // Check if they have attended sessions (to save processing visitors without sessions)
        MATCH (v)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
        WHERE (vp:{self.visitor_last_year_bva_label} OR vp:{self.visitor_last_year_lva_label})
        WITH v, base_similarity, COUNT(DISTINCT sp) AS session_count
        WHERE session_count > 0
        RETURN v, base_similarity
        ORDER BY base_similarity DESC, session_count DESC
        LIMIT 20
        """

        visitors_data = tx.run(
            query,
            visitor_id=visitor_id,
            job_role=visitor.get("job_role", ""),
            practice_type=visitor.get("what_type_does_your_practice_specialise_in", ""),
            org_type=visitor.get("organisation_type", ""),
            country=visitor.get("Country", ""),
        ).data()

        # If we can't find enough similar visitors with the pre-filtering,
        # try a more general query
        if len(visitors_data) < num_similar_visitors:
            query = f"""
            MATCH (v:{self.visitor_this_year_label})
            WHERE v.assist_year_before = '1' AND v.BadgeId <> $visitor_id
            // Check if they have attended sessions
            MATCH (v)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
            WHERE (vp:{self.visitor_last_year_bva_label} OR vp:{self.visitor_last_year_lva_label})
            WITH v, COUNT(DISTINCT sp) AS session_count
            WHERE session_count > 0
            RETURN v, 0 AS base_similarity
            ORDER BY session_count DESC
            LIMIT 20
            """
            visitors_data = tx.run(query, visitor_id=visitor_id).data()

        # Extract visitor features for comparison (EXACT SAME as old processor)
        def get_visitor_features(v):
            attributes = [
                v.get("what_type_does_your_practice_specialise_in", ""),
                v.get("job_role", ""),
                v.get("organisation_type", ""),
                v.get("JobTitle", ""),
                v.get("Country", ""),
            ]
            return " ".join(
                [
                    str(attr)
                    for attr in attributes
                    if attr and str(attr).strip() and str(attr) != "NA"
                ]
            )

        # Get embedding for our visitor
        visitor_text = get_visitor_features(visitor)
        if not visitor_text.strip():
            visitor_text = "default visitor profile"

        try:
            # Ensure model is initialized
            self._init_model()
            visitor_embedding = self.model.encode(visitor_text)

            # Calculate similarities for top 20 pre-filtered visitors
            similarities = []
            for vdata in visitors_data:
                v_compare = vdata["v"]
                base_similarity = vdata["base_similarity"]

                compare_text = get_visitor_features(v_compare)
                if not compare_text.strip():
                    continue

                try:
                    compare_embedding = self.model.encode(compare_text)
                    sim = cosine_similarity([visitor_embedding], [compare_embedding])[0][0]
                    # Combine neural and rule-based similarity (EXACT SAME formula)
                    combined_sim = (sim * 0.7) + (base_similarity * 0.3 / 4)  # Max base_similarity is 4
                    similarities.append((v_compare["BadgeId"], combined_sim))
                except Exception as e:
                    self.logger.error(
                        f"Error comparing with visitor {v_compare['BadgeId']}: {e}"
                    )
                    continue

            # Sort by similarity (highest first) and get top N
            similarities.sort(key=lambda x: -x[1])
            similar_visitors = [sid for sid, _ in similarities[:num_similar_visitors]]

            # Cache for future use
            self._similar_visitors_cache[visitor_id] = similar_visitors
            return similar_visitors

        except Exception as e:
            self.logger.error(f"Error encoding visitor profile: {e}")
            return []

    def get_similar_visitor_sessions_batch(self, tx, similar_visitor_badge_ids):
        """Get sessions attended by similar visitors in batch."""
        if not similar_visitor_badge_ids:
            return []

        query = f"""
        MATCH (v:{self.visitor_this_year_label})-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
        WHERE v.BadgeId IN $badge_ids AND (vp:{self.visitor_last_year_bva_label} OR vp:{self.visitor_last_year_lva_label})
        RETURN DISTINCT sp.session_id as session_id, sp.embedding as embedding
        """

        results = tx.run(query, badge_ids=similar_visitor_badge_ids).data()

        sessions = []
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions.append({"session_id": r["session_id"], "embedding": embedding})

        return sessions

    def get_this_year_sessions(self, tx):
        """Get all sessions for this year with their embeddings."""
        if self._this_year_sessions_cache is not None:
            return self._this_year_sessions_cache

        query = f"""
        MATCH (s:{self.session_this_year_label})
        RETURN s.session_id as session_id, 
               s.title as title,
               s.stream as stream,
               s.theatre__name as theatre__name,
               s.date as date,
               s.start_time as start_time,
               s.end_time as end_time,
               s.sponsored_by as sponsored_by,
               s.sponsored_session as sponsored_session,
               s.embedding as embedding
        """

        results = tx.run(query).data()

        sessions = {}
        for r in results:
            if r["embedding"]:
                sessions[r["session_id"]] = {
                    "title": r["title"],
                    "stream": r["stream"],
                    "theatre__name": r["theatre__name"],
                    "date": r["date"],
                    "start_time": r["start_time"],
                    "end_time": r["end_time"],
                    "sponsored_by": r.get("sponsored_by", ""),
                    "sponsored_session": r.get("sponsored_session", ""),
                    "embedding": np.array(json.loads(r["embedding"])),
                }

        self._this_year_sessions_cache = sessions
        return sessions

    def calculate_session_similarities_parallel(
        self, past_sessions, this_year_sessions, min_score
    ):
        """Calculate similarities between past and current sessions in parallel."""
        if not past_sessions or not this_year_sessions:
            return []

        def process_past_session(past_sess):
            recommendations = []
            past_emb = past_sess["embedding"]

            for sid, current_sess in this_year_sessions.items():
                try:
                    current_emb = current_sess["embedding"]
                    sim = cosine_similarity([past_emb], [current_emb])[0][0]

                    if sim >= min_score:
                        recommendations.append(
                            {
                                "session_id": sid,
                                "title": current_sess["title"],
                                "stream": current_sess["stream"],
                                "theatre__name": current_sess["theatre__name"],
                                "date": current_sess["date"],
                                "start_time": current_sess["start_time"],
                                "end_time": current_sess["end_time"],
                                "sponsored_by": current_sess.get("sponsored_by", ""),
                                "sponsored_session": current_sess.get(
                                    "sponsored_session", ""
                                ),
                                "similarity": sim,
                            }
                        )
                except Exception as e:
                    self.logger.error(
                        f"Error calculating similarity for session {sid}: {e}"
                    )

            return recommendations

        all_recommendations = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(8, len(past_sessions))
        ) as executor:
            future_to_session = {
                executor.submit(process_past_session, ps): ps for ps in past_sessions
            }
            for future in concurrent.futures.as_completed(future_to_session):
                recommendations = future.result()
                all_recommendations.extend(recommendations)

        # Remove duplicates and sort by similarity
        unique_recommendations = {}
        for rec in all_recommendations:
            sid = rec["session_id"]
            if sid not in unique_recommendations or rec["similarity"] > unique_recommendations[sid]["similarity"]:
                unique_recommendations[sid] = rec

        return sorted(unique_recommendations.values(), key=lambda x: x["similarity"], reverse=True)

    def get_recommendations_for_visitor(
        self, session, badge_id, num_similar_visitors, min_score, max_recommendations
    ):
        """Get recommendations for a single visitor."""
        start_time = time.time()

        visitor_info = session.execute_read(self.get_visitor_info, visitor_id=badge_id)

        if not visitor_info:
            self.logger.warning(f"Visitor {badge_id} not found")
            return []

        visitor = visitor_info["visitor"]
        assisted = visitor_info["assisted"]

        this_year_sessions = session.execute_read(self.get_this_year_sessions)
        self.logger.info(
            f"Loaded {len(this_year_sessions)} sessions for this year in {time.time() - start_time:.2f}s"
        )

        past_sessions = []

        if assisted == "1":
            # Case 1: Visitor attended last year
            self.logger.info(f"Case 1: Visitor {badge_id} attended last year")
            case_start = time.time()

            past_sessions = session.execute_read(
                self.get_past_sessions, visitor_id=badge_id
            )
            self.logger.info(
                f"Found {len(past_sessions)} past sessions in {time.time() - case_start:.2f}s"
            )

        else:
            # Case 2: New visitor - find similar visitors
            self.logger.info(
                f"Case 2: Finding {num_similar_visitors} similar visitors for {badge_id}"
            )
            case_start = time.time()

            similar_visitors = session.execute_read(
                self.find_similar_visitors_batch,
                visitor=visitor,
                num_similar_visitors=num_similar_visitors,
            )

            self.logger.info(
                f"Found {len(similar_visitors)} similar visitors in {time.time() - case_start:.2f}s"
            )
            sim_sessions_start = time.time()

            if similar_visitors:
                past_sessions = session.execute_read(
                    self.get_similar_visitor_sessions_batch,
                    similar_visitor_badge_ids=similar_visitors,
                )

                self.logger.info(
                    f"Found {len(past_sessions)} sessions from similar visitors in {time.time() - sim_sessions_start:.2f}s"
                )

        # Calculate similarities in parallel
        sim_calc_start = time.time()
        recommendations = self.calculate_session_similarities_parallel(
            past_sessions=past_sessions,
            this_year_sessions=this_year_sessions,
            min_score=min_score,
        )
        self.logger.info(
            f"Calculated similarities in {time.time() - sim_calc_start:.2f}s"
        )

        # Apply maximum recommendations limit
        if max_recommendations and len(recommendations) > max_recommendations:
            recommendations = recommendations[:max_recommendations]

        self.logger.info(
            f"Total recommendation time: {time.time() - start_time:.2f}s"
        )
        return recommendations

    def _contains_any(self, text, keywords):
        """Check if text contains any of the keywords (case-insensitive)."""
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _apply_practice_type_rules(self, visitor, sessions):
        """Apply practice type filtering rules (for veterinary shows)."""
        if not self.enable_filtering or not self.rules_config:
            return sessions, []

        if not visitor or "what_type_does_your_practice_specialise_in" not in visitor:
            return sessions, []

        practice_type = visitor.get("what_type_does_your_practice_specialise_in", "")
        if not practice_type or practice_type == "NA":
            return sessions, []

        filtered_sessions = []
        rules_applied = []

        # Check if practice contains equine or mixed
        if self._contains_any(practice_type, ["equine", "mixed"]):
            exclusions = self.rules_config.get("equine_mixed_exclusions", [])
            if exclusions:
                filtered_sessions = [
                    session
                    for session in sessions
                    if not session.get("stream")
                    or not self._contains_any(session["stream"], exclusions)
                ]
                rules_applied.append(
                    f"practice_type: mixed/equine - excluded {', '.join(exclusions)}"
                )
                self.logger.info(
                    f"Applied equine/mixed rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions"
                )

        # Check if practice contains small animal
        elif self._contains_any(practice_type, ["small animal"]):
            exclusions = self.rules_config.get("small_animal_exclusions", [])
            if exclusions:
                filtered_sessions = [
                    session
                    for session in sessions
                    if not session.get("stream")
                    or not self._contains_any(session["stream"], exclusions)
                ]
                rules_applied.append(
                    f"practice_type: small animal - excluded {', '.join(exclusions)}"
                )
                self.logger.info(
                    f"Applied small animal rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions"
                )

        else:
            filtered_sessions = sessions

        return filtered_sessions if filtered_sessions else sessions, rules_applied

    def _apply_role_rules(self, visitor, sessions):
        """Apply job role filtering rules (for veterinary shows)."""
        if not self.enable_filtering or not self.rules_config:
            return sessions, []

        if not visitor or "job_role" not in visitor:
            return sessions, []

        job_role = visitor.get("job_role", "")
        if not job_role or job_role == "NA":
            return sessions, []

        filtered_sessions = []
        rules_applied = []

        # Rule for VET_ROLES
        if job_role in self.vet_roles:
            exclusions = self.rules_config.get("vet_exclusions", [])
            if exclusions:
                filtered_sessions = [
                    session
                    for session in sessions
                    if not session.get("stream")
                    or not self._contains_any(session["stream"], exclusions)
                ]
                rules_applied.append(f"role: vet - excluded {', '.join(exclusions)}")
                self.logger.info(
                    f"Applied vet role rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions"
                )

        # Rule for NURSE_ROLES
        elif job_role in self.nurse_roles:
            allowed_streams = self.rules_config.get("nurse_streams", [])
            if allowed_streams:
                filtered_sessions = [
                    session
                    for session in sessions
                    if session.get("stream")
                    and self._contains_any(session["stream"], allowed_streams)
                ]
                rules_applied.append(
                    f"role: nurse - limited to {', '.join(allowed_streams)}"
                )
                self.logger.info(
                    f"Applied nurse role rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions"
                )

        else:
            filtered_sessions = sessions

        return filtered_sessions if filtered_sessions else sessions, rules_applied

    def filter_sessions(self, visitor, sessions):
        """Filter sessions based on configured rules."""
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

    def _update_visitor_recommendations(self, recommendations_data):
        """Update visitors with has_recommendation flag and create IS_RECOMMENDED relationships."""
        try:
            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                with driver.session() as session:
                    # Update visitors with recommendations
                    for rec in recommendations_data:
                        visitor_id = rec["visitor"]["BadgeId"]
                        recommended_sessions = rec.get("filtered_recommendations", [])
                        
                        if recommended_sessions:
                            # Update visitor with has_recommendation flag
                            # Add show attribute when creating/updating nodes
                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            SET v.has_recommendation = "1",
                                v.show = $show_name
                            """
                            session.run(update_query, visitor_id=visitor_id, show_name=self.show_name)
                            
                            # Create IS_RECOMMENDED relationships
                            for sess in recommended_sessions:
                                if isinstance(sess, dict) and "session_id" in sess:
                                    session_id = sess["session_id"]
                                    similarity = sess.get("similarity", 0.0)
                                    
                                    rel_query = f"""
                                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                                    MATCH (s:{self.session_this_year_label} {{session_id: $session_id}})
                                    MERGE (v)-[r:IS_RECOMMENDED]->(s)
                                    SET r.similarity_score = $similarity,
                                        r.created_at = $timestamp
                                    """
                                    session.run(
                                        rel_query,
                                        visitor_id=visitor_id,
                                        session_id=session_id,
                                        similarity=similarity,
                                        timestamp=datetime.now().isoformat()
                                    )
                        else:
                            # Update visitor with no recommendations flag
                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
                            SET v.has_recommendation = "0",
                                v.show = $show_name
                            """
                            session.run(update_query, visitor_id=visitor_id, show_name=self.show_name)
                    
                    self.logger.info("Successfully updated Neo4j with recommendation data")
                    
        except Exception as e:
            self.logger.error(f"Error updating Neo4j: {str(e)}", exc_info=True)

    def json_to_dataframe(self, json_file_path):
        """Convert recommendations JSON to DataFrame."""
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        rows = []
        recommendations = data.get('recommendations', [])
        
        for rec in recommendations:
            visitor = rec.get('visitor', {})
            filtered_recs = rec.get('filtered_recommendations', [])
            rec_metadata = rec.get('metadata', {})
            
            for filtered_rec in filtered_recs:
                row = {}
                
                # Add visitor data
                for key, value in visitor.items():
                    row[f"visitor_{key}"] = value
                
                # Add filtered recommendation data
                if isinstance(filtered_rec, dict):
                    for key, value in filtered_rec.items():
                        row[f"session_{key}"] = value
                else:
                    row["session_id"] = filtered_rec
                
                # Add recommendation metadata
                for key, value in rec_metadata.items():
                    row[f"metadata_{key}"] = value
                
                rows.append(row)
        
        df = pd.DataFrame(rows)
        return df

    def process(self, create_only_new=True):
        """
        Run the session recommendation processor.

        Args:
            create_only_new: If True, only process new visitors without recommendations
        """
        start_time = time.time()
        self.logger.info(f"Starting session recommendation processing for {self.show_name} show")

        try:
            # Get visitors to process
            badge_ids = self._get_visitors_to_process(create_only_new)

            if not badge_ids or len(badge_ids) == 0:
                self.logger.info("No visitors to process for recommendations.")
                return

            # Process recommendations
            all_recommendations = []
            successful = 0
            errors = 0
            total_recommendations = 0
            unique_sessions = set()

            with GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            ) as driver:
                for badge_id in badge_ids:
                    try:
                        self.statistics["visitors_processed"] += 1
                        
                        with driver.session() as session:
                            # Get recommendations for this visitor
                            recommendations = self.get_recommendations_for_visitor(
                                session=session,
                                badge_id=badge_id,
                                num_similar_visitors=self.similar_visitors_count,
                                min_score=self.min_similarity_score,
                                max_recommendations=self.max_recommendations,
                            )
                            
                            self.statistics["total_recommendations_generated"] += len(recommendations)
                            
                            # Get visitor info for filtering
                            visitor_info = session.execute_read(
                                self.get_visitor_info, visitor_id=badge_id
                            )
                            visitor = visitor_info["visitor"] if visitor_info else {}
                            
                            # Apply filtering if enabled
                            filtered_recommendations, rules_applied = self.filter_sessions(
                                visitor, recommendations
                            )
                            
                            self.statistics["total_filtered_recommendations"] += len(filtered_recommendations)
                            
                            if filtered_recommendations:
                                self.statistics["visitors_with_recommendations"] += 1
                                successful += 1
                                total_recommendations += len(filtered_recommendations)
                                
                                for rec in filtered_recommendations:
                                    unique_sessions.add(rec["session_id"])
                                
                                all_recommendations.append({
                                    "visitor": visitor,
                                    "raw_recommendations": recommendations,
                                    "filtered_recommendations": filtered_recommendations,
                                    "metadata": {
                                        "rules_applied": rules_applied,
                                        "raw_count": len(recommendations),
                                        "filtered_count": len(filtered_recommendations),
                                    }
                                })
                                
                                self.logger.info(
                                    f"Generated {len(filtered_recommendations)} recommendations for visitor {badge_id}"
                                )
                            else:
                                self.statistics["visitors_without_recommendations"] += 1
                                self.logger.info(f"No recommendations for visitor {badge_id}")
                                
                    except Exception as e:
                        errors += 1
                        self.statistics["errors"] += 1
                        self.statistics["error_details"].append(
                            f"Error processing visitor {badge_id}: {str(e)}"
                        )
                        self.logger.error(
                            f"Error processing visitor {badge_id}: {str(e)}", exc_info=True
                        )

            # Save recommendations
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_subdir = self.output_dir / "output" / self.recommendation_config.get(
                "output_directory", "recommendations"
            )
            output_subdir.mkdir(parents=True, exist_ok=True)
            
            filename_pattern = self.recommendation_config.get(
                "filename_pattern", "visitor_recommendations_{timestamp}"
            )
            output_file = output_subdir / f"{filename_pattern.format(timestamp=timestamp)}.json"

            output_data = {
                "timestamp": timestamp,
                "show": self.show_name,
                "recommendations": all_recommendations,
                "statistics": {
                    "visitors_processed": self.statistics["visitors_processed"],
                    "successful": successful,
                    "errors": errors,
                    "total_recommendations": total_recommendations,
                    "unique_sessions_recommended": len(unique_sessions),
                },
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
            if successful > 0:
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