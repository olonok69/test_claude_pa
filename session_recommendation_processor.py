"""
Generic Session Recommendation Processor
Handles recommendations for all show types (BVA, ECOMM, etc.)
"""

import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime
import logging
import concurrent.futures
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Optional imports (for LangChain approach)
try:
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_openai import ChatOpenAI, AzureChatOpenAI, AzureOpenAI
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    from dotenv import dotenv_values
    has_langchain = True
except ImportError:
    has_langchain = False
    print("LangChain not available. Will use rule-based filtering only.")


class SessionRecommendationProcessor:
    """
    Generic processor for generating session recommendations for visitors.
    Works with any show type through configuration.
    """

    def __init__(self, config):
        """
        Initialize the session recommendation processor.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.output_dir = config.get("output_dir", "data")
        
        # Get event configuration
        self.event_config = config.get("event", {})
        self.main_event_name = self.event_config.get("main_event_name", "main")
        self.secondary_event_name = self.event_config.get("secondary_event_name", "secondary")
        self.show_name = config.get("neo4j", {}).get("show_name", self.main_event_name)
        
        # Determine output subdirectory based on show
        if self.main_event_name in ["bva", "lva"]:
            self.output_subdir = "bva"
        elif self.main_event_name in ["ecomm", "tfm"]:
            self.output_subdir = "ecomm"
        else:
            self.output_subdir = self.main_event_name
        
        self.output_path = os.path.join(self.output_dir, self.output_subdir)
        os.makedirs(self.output_path, exist_ok=True)
        os.makedirs(os.path.join(self.output_path, "recommendations"), exist_ok=True)

        # Load Neo4j connection parameters from .env file (consistent with other processors)
        from dotenv import load_dotenv
        load_dotenv(config.get("env_file", "keys/.env"))
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        # Fallback to config file if env variables not found (backward compatibility)
        if not self.uri:
            self.uri = config.get("neo4j", {}).get("uri")
        if not self.username:
            self.username = config.get("neo4j", {}).get("username")
        if not self.password:
            self.password = config.get("neo4j", {}).get("password")
        
        if not all([self.uri, self.username, self.password]):
            self.logger.error("Missing Neo4j credentials in .env file or config")
            raise ValueError("Missing Neo4j credentials in .env file or config")
        
        # Get Neo4j node labels from config
        neo4j_config = config.get("neo4j", {})
        self.labels = neo4j_config.get("node_labels", {})
        self.visitor_this_year_label = self.labels.get("visitor_this_year", "Visitor_this_year")
        self.visitor_last_year_main_label = self.labels.get(f"visitor_last_year_{self.main_event_name}", 
                                                             self.labels.get("visitor_last_year_bva", "Visitor_last_year_bva"))
        self.visitor_last_year_secondary_label = self.labels.get(f"visitor_last_year_{self.secondary_event_name}",
                                                                  self.labels.get("visitor_last_year_lva", "Visitor_last_year_lva"))
        self.session_this_year_label = self.labels.get("session_this_year", "Sessions_this_year")
        self.session_past_year_label = self.labels.get("session_past_year", "Sessions_past_year")

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Get recommendation configuration
        self.recommendation_config = config.get("recommendation", {})
        self.min_similarity_score = self.recommendation_config.get("min_similarity_score", 0.3)
        self.max_recommendations = self.recommendation_config.get("max_recommendations", 10)
        self.similar_visitors_count = self.recommendation_config.get("similar_visitors_count", 3)
        self.use_langchain = self.recommendation_config.get("use_langchain", False)
        
        # Get filtering rules configuration
        self.rules_config = self.recommendation_config.get("rules_config", {})
        self.enable_filtering = self.recommendation_config.get("enable_filtering", True)
        
        # Get similarity attributes configuration
        self.similarity_attributes = self.recommendation_config.get("similarity_attributes", {})
        
        # Initialize sentence transformer model
        embedding_config = config.get("embeddings", {})
        self.model_name = embedding_config.get("model", "all-MiniLM-L6-v2")
        self.model = None  # Lazy initialization

        # Initialize statistics
        self.statistics = {
            "total_visitors_processed": 0,
            "visitors_with_recommendations": 0,
            "total_recommendations_generated": 0,
            "unique_recommended_sessions": 0,
            "processing_time": 0,
            "errors": 0,
            "error_details": [],
        }

        # Initialize caches
        self._this_year_sessions_cache = None
        self._visitor_cache = {}
        self._similar_visitors_cache = {}
        
        # Load show-specific configurations
        self._load_show_specific_config()

    def _load_show_specific_config(self):
        """Load show-specific configurations based on the event type."""
        # For veterinary shows (BVA/LVA)
        if self.main_event_name in ["bva", "lva"]:
            # Define role groups for veterinary shows
            self.role_groups = {
                "vet": [
                    "Vet/Vet Surgeon",
                    "Assistant Vet",
                    "Vet/Owner",
                    "Clinical or other Director",
                    "Locum Vet",
                    "Academic",
                ],
                "nurse": ["Head Nurse/Senior Nurse", "Vet Nurse", "Locum RVN"],
                "business": ["Practice Manager", "Practice Partner/Owner"],
                "other": ["Student", "Receptionist", "Other (please specify)"]
            }
            
            # Default similarity attributes for vet shows
            if not self.similarity_attributes:
                self.similarity_attributes = {
                    "job_role": 1.0,
                    "what_type_does_your_practice_specialise_in": 1.0,
                    "organisation_type": 0.5,
                    "Country": 0.5
                }
        
        # For e-commerce shows (ECOMM/TFM)
        elif self.main_event_name in ["ecomm", "tfm"]:
            # Define role groups for e-commerce shows (if needed)
            self.role_groups = {}
            
            # Default similarity attributes for ecomm shows
            if not self.similarity_attributes:
                self.similarity_attributes = {
                    "what_is_your_job_role": 1.0,
                    "what_best_describes_what_you_do": 1.0,
                    "what_is_your_industry": 0.5,
                    "Country": 0.5
                }
            
            # Disable filtering for ECOMM by default (can be overridden in config)
            if "enable_filtering" not in self.recommendation_config:
                self.enable_filtering = False
        
        # For other/unknown shows
        else:
            self.role_groups = {}
            if not self.similarity_attributes:
                self.similarity_attributes = {
                    "job_role": 1.0,
                    "Country": 0.5
                }

    def process(self, create_only_new=True):
        """
        Run the session recommendation processor.

        Args:
            create_only_new: If True, only process new recommendations if the output file doesn't exist
        """
        start_time = time.time()
        self.logger.info(f"Starting session recommendation processing for {self.show_name} show")

        try:
            # Get visitors to process based on create_only_new flag
            badge_ids = self._get_visitors_to_process(create_only_new)

            if not badge_ids or len(badge_ids) == 0:
                self.logger.info("No visitors to process for recommendations.")
                return

            # Load visitor data
            visitor_data = self._load_visitor_data()
            if visitor_data is None or len(visitor_data) == 0:
                self.logger.error("No visitor data found. Cannot generate recommendations.")
                return

            # Process visitors in batches
            batch_size = 100
            all_recommendations = []
            
            for i in range(0, len(badge_ids), batch_size):
                batch = badge_ids[i:i+batch_size]
                self.logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} visitors)")
                
                for badge_id in batch:
                    try:
                        # Get visitor profile
                        visitor = visitor_data.get(badge_id)
                        if not visitor:
                            self.logger.warning(f"Visitor {badge_id} not found in data")
                            continue
                        
                        # Generate recommendations
                        rec_result = self.get_recommendations_and_filter(
                            badge_id=badge_id,
                            min_score=self.min_similarity_score,
                            max_recommendations=self.max_recommendations,
                            visitor_data=visitor,
                            use_langchain=self.use_langchain
                        )
                        
                        if rec_result and rec_result.get("filtered_recommendations"):
                            all_recommendations.append(rec_result)
                            self.statistics["visitors_with_recommendations"] += 1
                            self.statistics["total_recommendations_generated"] += len(
                                rec_result["filtered_recommendations"]
                            )
                        
                        self.statistics["total_visitors_processed"] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error processing visitor {badge_id}: {str(e)}")
                        self.statistics["errors"] += 1
                        self.statistics["error_details"].append({
                            "badge_id": badge_id,
                            "error": str(e)
                        })

            # Save recommendations
            if all_recommendations:
                self._save_recommendations(all_recommendations)
                
                # Update Neo4j with recommendations
                self._update_visitor_recommendations(all_recommendations)
                
                # Calculate unique sessions
                unique_sessions = set()
                for rec in all_recommendations:
                    for session in rec.get("filtered_recommendations", []):
                        if isinstance(session, dict):
                            unique_sessions.add(session.get("session_id"))
                        else:
                            unique_sessions.add(session)
                
                self.statistics["unique_recommended_sessions"] = len(unique_sessions)

            # Update processing time
            self.statistics["processing_time"] = time.time() - start_time
            
            # Log summary
            self.logger.info(f"Recommendation processing completed for {self.show_name}")
            self.logger.info(f"Total visitors processed: {self.statistics['total_visitors_processed']}")
            self.logger.info(f"Visitors with recommendations: {self.statistics['visitors_with_recommendations']}")
            self.logger.info(f"Total recommendations: {self.statistics['total_recommendations_generated']}")
            self.logger.info(f"Processing time: {self.statistics['processing_time']:.2f}s")

        except Exception as e:
            self.logger.error(f"Error in recommendation processing: {str(e)}", exc_info=True)
            self.statistics["errors"] += 1

    def _get_visitors_to_process(self, create_only_new):
        """Get list of visitors to process based on create_only_new flag."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    if create_only_new:
                        # Only get visitors without recommendations for this show
                        query = f"""
                        MATCH (v:{self.visitor_this_year_label})
                        WHERE v.show = $show_name 
                        AND (v.has_recommendation IS NULL OR v.has_recommendation = "0")
                        RETURN v.BadgeId as badge_id
                        """
                    else:
                        # Get all visitors for this show
                        query = f"""
                        MATCH (v:{self.visitor_this_year_label})
                        WHERE v.show = $show_name
                        RETURN v.BadgeId as badge_id
                        """

                    result = session.run(query, show_name=self.show_name)
                    badge_ids = [record["badge_id"] for record in result]

                    self.logger.info(f"Found {len(badge_ids)} visitors to process for {self.show_name}")
                    return badge_ids

        except Exception as e:
            self.logger.error(f"Error getting visitors to process: {str(e)}", exc_info=True)
            return []

    def _load_visitor_data(self):
        """Load visitor data from Neo4j."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    query = f"""
                    MATCH (v:{self.visitor_this_year_label})
                    WHERE v.show = $show_name
                    RETURN v
                    """
                    result = session.run(query, show_name=self.show_name)
                    
                    visitor_data = {}
                    for record in result:
                        visitor = dict(record["v"])
                        visitor_data[visitor["BadgeId"]] = visitor
                    
                    self.logger.info(f"Loaded {len(visitor_data)} visitors from Neo4j")
                    return visitor_data
                    
        except Exception as e:
            self.logger.error(f"Error loading visitor data: {str(e)}", exc_info=True)
            return None

    def get_recommendations_and_filter(self, badge_id, min_score=0.5, max_recommendations=30,
                                      visitor_data=None, use_langchain=False):
        """
        Get session recommendations and filter them based on business rules.
        
        Args:
            badge_id: Visitor's badge ID
            min_score: Minimum similarity score
            max_recommendations: Maximum number of recommendations to return
            visitor_data: Optional visitor data dictionary
            use_langchain: Whether to filter using LangChain
            
        Returns:
            Dictionary with visitor profile, raw recommendations, filtered recommendations,
            and metadata about the filtering process
        """
        start_time = time.time()
        processing_steps = []

        # Get visitor profile
        visitor = visitor_data
        if visitor is None:
            visitor = self._get_visitor_from_neo4j(badge_id)
            if not visitor:
                return None

        # Get raw recommendations using Neo4j
        raw_recommendations = self.get_neo4j_recommendations(
            visitor_id=badge_id,
            min_score=min_score,
            max_recommendations=max_recommendations * 2  # Get more for filtering
        )
        
        processing_steps.append(f"Generated {len(raw_recommendations)} raw recommendations")

        # Apply filtering if enabled
        filtered_recommendations = raw_recommendations
        rules_applied = []
        
        if self.enable_filtering and raw_recommendations:
            if use_langchain and has_langchain:
                # Use LangChain filtering
                filtered_recommendations, rules_applied = self.filter_with_langchain(
                    visitor, raw_recommendations
                )
            else:
                # Use rule-based filtering
                filtered_recommendations, rules_applied = self.filter_recommendations(
                    visitor, raw_recommendations
                )
            
            processing_steps.append(f"Applied filtering: {len(filtered_recommendations)} recommendations remain")
            processing_steps.extend(rules_applied)
        
        # Limit to max recommendations
        if filtered_recommendations and len(filtered_recommendations) > max_recommendations:
            filtered_recommendations = filtered_recommendations[:max_recommendations]
            processing_steps.append(f"Limited to {max_recommendations} recommendations")

        # Build result
        result = {
            "visitor": visitor,
            "raw_recommendations": raw_recommendations,
            "filtered_recommendations": filtered_recommendations,
            "metadata": {
                "badge_id": badge_id,
                "show": self.show_name,
                "timestamp": datetime.now().isoformat(),
                "processing_time": time.time() - start_time,
                "min_score": min_score,
                "max_recommendations": max_recommendations,
                "filtering_enabled": self.enable_filtering,
                "langchain_used": use_langchain and has_langchain,
                "processing_steps": processing_steps,
                "rules_applied": rules_applied
            }
        }

        return result

    def get_neo4j_recommendations(self, visitor_id, min_score=0.5, max_recommendations=30):
        """Get recommendations using Neo4j queries."""
        recommendations = []
        
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    # Use a transaction for better performance
                    with session.begin_transaction() as tx:
                        # Get visitor and check if they attended last year
                        visitor_info = self._get_visitor_info(tx, visitor_id)
                        if not visitor_info:
                            return []
                        
                        visitor = visitor_info["visitor"]
                        assisted = visitor_info["assisted"]
                        
                        # Get this year's sessions
                        this_year_sessions = self._get_this_year_sessions(tx)
                        
                        if assisted == "1":
                            # Visitor attended last year - get their past sessions
                            past_sessions = self.get_past_sessions(tx, visitor_id)
                            
                            if past_sessions:
                                recommendations = self.calculate_session_similarities_parallel(
                                    past_sessions=past_sessions,
                                    this_year_sessions=this_year_sessions,
                                    min_score=min_score
                                )
                        else:
                            # New visitor - find similar visitors
                            similar_visitors = self.find_similar_visitors_batch(
                                tx, visitor, self.similar_visitors_count
                            )
                            
                            if similar_visitors:
                                # Get sessions from similar visitors
                                past_sessions = self.get_sessions_from_similar_visitors(
                                    tx, similar_visitors
                                )
                                
                                if past_sessions:
                                    recommendations = self.calculate_session_similarities_parallel(
                                        past_sessions=past_sessions,
                                        this_year_sessions=this_year_sessions,
                                        min_score=min_score
                                    )
                        
                        # Apply maximum recommendations limit
                        if max_recommendations and len(recommendations) > max_recommendations:
                            recommendations = recommendations[:max_recommendations]
                        
                        return recommendations
                        
        except Exception as e:
            self.logger.error(f"Error getting Neo4j recommendations: {str(e)}", exc_info=True)
            return []

    def _get_visitor_from_neo4j(self, badge_id):
        """Get visitor data from Neo4j."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    query = f"""
                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                    WHERE v.show = $show_name
                    RETURN v
                    """
                    result = session.run(query, badge_id=badge_id, show_name=self.show_name).single()
                    
                    if result:
                        return dict(result["v"])
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting visitor from Neo4j: {str(e)}")
            return None

    def _get_visitor_info(self, tx, visitor_id):
        """Get visitor information and check if they attended last year."""
        if visitor_id in self._visitor_cache:
            return self._visitor_cache[visitor_id]

        visitor_query = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
        WHERE v.show = $show_name
        RETURN v
        """
        visitor_data = tx.run(visitor_query, visitor_id=visitor_id, show_name=self.show_name).single()

        if not visitor_data:
            return None

        visitor = visitor_data["v"]
        assisted = visitor.get("assist_year_before", "0")

        self._visitor_cache[visitor_id] = {"visitor": visitor, "assisted": assisted}
        return self._visitor_cache[visitor_id]

    def _get_this_year_sessions(self, tx):
        """Get all sessions for this year with embeddings."""
        if self._this_year_sessions_cache is not None:
            return self._this_year_sessions_cache

        query = f"""
        MATCH (s:{self.session_this_year_label})
        WHERE s.show = $show_name AND s.embedding IS NOT NULL
        RETURN s.session_id as session_id, s.title as title, s.stream as stream, 
               s.theatre__name as theatre__name, s.date as date, 
               s.start_time as start_time, s.end_time as end_time,
               s.sponsored_by as sponsored_by, s.sponsored_session as sponsored_session,
               s.embedding as embedding
        """
        
        results = tx.run(query, show_name=self.show_name).data()
        
        sessions = {}
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions[r["session_id"]] = {
                    "session_id": r["session_id"],
                    "title": r["title"],
                    "stream": r["stream"],
                    "theatre__name": r["theatre__name"],
                    "date": r["date"],
                    "start_time": r["start_time"],
                    "end_time": r["end_time"],
                    "sponsored_by": r.get("sponsored_by", ""),
                    "sponsored_session": r.get("sponsored_session", ""),
                    "embedding": embedding
                }

        self._this_year_sessions_cache = sessions
        return sessions

    def get_past_sessions(self, tx, visitor_id):
        """Get sessions the visitor attended last year."""
        # Build query based on available labels
        query_conditions = []
        if self.visitor_last_year_main_label:
            query_conditions.append(f"vp:{self.visitor_last_year_main_label}")
        if self.visitor_last_year_secondary_label:
            query_conditions.append(f"vp:{self.visitor_last_year_secondary_label}")
        
        if not query_conditions:
            return []
        
        condition_str = " OR ".join(query_conditions)
        
        query = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
        WHERE v.show = $show_name AND ({condition_str})
        RETURN DISTINCT sp.session_id as session_id, sp.embedding as embedding
        """

        results = tx.run(query, visitor_id=visitor_id, show_name=self.show_name).data()

        sessions = []
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions.append({"session_id": r["session_id"], "embedding": embedding})

        return sessions

    def find_similar_visitors_batch(self, tx, visitor, num_similar_visitors=3):
        """Find similar visitors based on configurable attributes."""
        visitor_id = visitor["BadgeId"]

        # Check cache first
        if visitor_id in self._similar_visitors_cache:
            return self._similar_visitors_cache[visitor_id]

        # Build similarity calculation based on configured attributes
        similarity_parts = []
        parameters = {"visitor_id": visitor_id, "show_name": self.show_name}
        
        for attr, weight in self.similarity_attributes.items():
            if attr in visitor and visitor.get(attr):
                similarity_parts.append(
                    f"CASE WHEN v.{attr} = ${attr} THEN {weight} ELSE 0 END"
                )
                parameters[attr] = visitor.get(attr, "")

        if not similarity_parts:
            # Fallback to basic similarity
            similarity_parts = ["1"]

        similarity_expr = " + ".join(similarity_parts)

        # Query to find similar visitors who attended last year
        query = f"""
        MATCH (v:{self.visitor_this_year_label})
        WHERE v.show = $show_name 
        AND v.assist_year_before = '1' 
        AND v.BadgeId <> $visitor_id
        WITH v, {similarity_expr} AS base_similarity
        WHERE base_similarity > 0
        // Check if they have attended sessions
        MATCH (v)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
        WHERE ({" OR ".join([f"vp:{label}" for label in [self.visitor_last_year_main_label, self.visitor_last_year_secondary_label] if label])})
        WITH v, base_similarity, COUNT(DISTINCT sp) AS session_count
        WHERE session_count > 0
        RETURN v, base_similarity
        ORDER BY base_similarity DESC, session_count DESC
        LIMIT 20
        """

        visitors_data = tx.run(query, **parameters).data()

        similar_visitors = []
        for v in visitors_data[:num_similar_visitors]:
            similar_visitors.append({
                "visitor": v["v"],
                "similarity": v["base_similarity"]
            })

        self._similar_visitors_cache[visitor_id] = similar_visitors
        return similar_visitors

    def get_sessions_from_similar_visitors(self, tx, similar_visitors):
        """Get sessions attended by similar visitors."""
        if not similar_visitors:
            return []

        visitor_ids = [v["visitor"]["BadgeId"] for v in similar_visitors]

        query = f"""
        UNWIND $visitor_ids AS vid
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: vid}})-[:Same_Visitor]->(vp)-[:attended_session]->(sp:{self.session_past_year_label})
        WHERE v.show = $show_name 
        AND ({" OR ".join([f"vp:{label}" for label in [self.visitor_last_year_main_label, self.visitor_last_year_secondary_label] if label])})
        RETURN DISTINCT sp.session_id as session_id, sp.embedding as embedding
        """

        results = tx.run(query, visitor_ids=visitor_ids, show_name=self.show_name).data()

        sessions = []
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions.append({"session_id": r["session_id"], "embedding": embedding})

        return sessions

    def calculate_session_similarities_parallel(self, past_sessions, this_year_sessions, min_score):
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
                        recommendations.append({
                            "session_id": sid,
                            "title": current_sess["title"],
                            "stream": current_sess["stream"],
                            "theatre__name": current_sess["theatre__name"],
                            "date": current_sess["date"],
                            "start_time": current_sess["start_time"],
                            "end_time": current_sess["end_time"],
                            "sponsored_by": current_sess.get("sponsored_by", ""),
                            "sponsored_session": current_sess.get("sponsored_session", ""),
                            "similarity": sim,
                        })
                except Exception as e:
                    self.logger.error(f"Error calculating similarity for session {sid}: {e}")

            return recommendations

        # Use parallel processing
        all_recommendations = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(past_sessions))) as executor:
            future_to_session = {
                executor.submit(process_past_session, ps): ps for ps in past_sessions
            }
            for future in concurrent.futures.as_completed(future_to_session):
                try:
                    recommendations = future.result()
                    all_recommendations.extend(recommendations)
                except Exception as e:
                    self.logger.error(f"Error in parallel processing: {e}")

        # Remove duplicates and sort by similarity
        unique_recommendations = {}
        for rec in all_recommendations:
            sid = rec["session_id"]
            if sid not in unique_recommendations or rec["similarity"] > unique_recommendations[sid]["similarity"]:
                unique_recommendations[sid] = rec

        final_recommendations = list(unique_recommendations.values())
        final_recommendations.sort(key=lambda x: x["similarity"], reverse=True)

        return final_recommendations

    def filter_recommendations(self, visitor, sessions):
        """
        Apply rule-based filtering to recommendations.
        Generic implementation that uses configuration.
        """
        if not sessions or not self.enable_filtering:
            return sessions, []

        filtered_sessions = sessions
        all_rules_applied = []

        # Get rule priority from config
        rule_priority = self.rules_config.get("rule_priority", [])

        for rule_type in rule_priority:
            if rule_type == "practice_type" and self.main_event_name in ["bva", "lva"]:
                # Apply veterinary-specific practice type rules
                filtered_sessions, rules_applied = self._apply_practice_type_rules(
                    visitor, filtered_sessions
                )
                all_rules_applied.extend(rules_applied)
                
            elif rule_type == "role" and self.main_event_name in ["bva", "lva"]:
                # Apply veterinary-specific role rules
                filtered_sessions, rules_applied = self._apply_role_rules(
                    visitor, filtered_sessions
                )
                all_rules_applied.extend(rules_applied)
                
            # Add more rule types as needed for other shows
            else:
                self.logger.debug(f"No handler for rule type: {rule_type} in show {self.main_event_name}")

        # Sort by similarity score (highest first)
        filtered_sessions.sort(key=lambda x: float(x.get("similarity", 0)), reverse=True)

        return filtered_sessions, all_rules_applied

    def _contains_any(self, text, keywords):
        """Check if text contains any of the keywords (case-insensitive)."""
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _apply_practice_type_rules(self, visitor, sessions):
        """Apply practice type filtering rules (veterinary-specific)."""
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
            filtered_sessions = [
                session for session in sessions
                if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
            ]
            rules_applied.append(f"practice_type: mixed/equine - excluded {', '.join(exclusions)}")
            self.logger.info(f"Applied equine/mixed rule: {len(sessions)} -> {len(filtered_sessions)} sessions")

        # Check if practice contains small animal
        elif self._contains_any(practice_type, ["small animal"]):
            exclusions = self.rules_config.get("small_animal_exclusions", [])
            filtered_sessions = [
                session for session in sessions
                if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
            ]
            rules_applied.append(f"practice_type: small animal - excluded {', '.join(exclusions)}")
            self.logger.info(f"Applied small animal rule: {len(sessions)} -> {len(filtered_sessions)} sessions")
        else:
            filtered_sessions = sessions

        return filtered_sessions, rules_applied

    def _apply_role_rules(self, visitor, sessions):
        """Apply job role filtering rules (veterinary-specific)."""
        if not visitor or "job_role" not in visitor:
            return sessions, []

        job_role = visitor.get("job_role", "")
        if not job_role or job_role == "NA":
            return sessions, []

        filtered_sessions = []
        rules_applied = []

        # Check if role is in vet roles
        if job_role in self.role_groups.get("vet", []):
            exclusions = self.rules_config.get("vet_exclusions", [])
            filtered_sessions = [
                session for session in sessions
                if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
            ]
            rules_applied.append(f"role: vet - excluded {', '.join(exclusions)}")
            self.logger.info(f"Applied vet role rule: {len(sessions)} -> {len(filtered_sessions)} sessions")

        # Check if role is in nurse roles
        elif job_role in self.role_groups.get("nurse", []):
            allowed_streams = self.rules_config.get("nurse_streams", [])
            filtered_sessions = [
                session for session in sessions
                if session.get("stream") and self._contains_any(session["stream"], allowed_streams)
            ]
            rules_applied.append(f"role: nurse - only {', '.join(allowed_streams)}")
            self.logger.info(f"Applied nurse role rule: {len(sessions)} -> {len(filtered_sessions)} sessions")
        else:
            filtered_sessions = sessions

        return filtered_sessions, rules_applied

    def filter_with_langchain(self, visitor, recommendations):
        """
        Filter recommendations using LangChain and LLM.
        Generic implementation that can be customized per show.
        """
        if not has_langchain:
            self.logger.warning("LangChain not available. Cannot filter using LLM.")
            return recommendations, ["LangChain filtering not available"]

        try:
            # Load .env file from config
            env_file = self.config.get("env_file", ".env")
            config_values = dotenv_values(env_file)

            # Initialize Azure OpenAI client
            llm = AzureChatOpenAI(
                azure_endpoint=config_values.get("AZURE_ENDPOINT", ""),
                azure_deployment=config_values.get("AZURE_DEPLOYMENT", ""),
                api_key=config_values.get("AZURE_API_KEY", ""),
                api_version=config_values.get("AZURE_API_VERSION", ""),
                temperature=0.5,
                top_p=0.9,
            )

            # Build show-specific prompt
            system_prompt = self._build_langchain_prompt(visitor, recommendations)

            prompt = PromptTemplate(
                input_variables=["sessions", "rules", "profile"],
                template=system_prompt + """
                For the Visitor with profile {profile}\n, 
                based on the attributes of these sessions: {sessions} 
                and implementing the following rules {rules}.\n 
                Filter them and just return from the list those that meet the requirements in the rules"""
            )

            # Create chain
            chain = prompt | llm

            # Convert recommendations to text
            text_rec = json.dumps(recommendations)
            
            # Get business rules for this show
            business_rules = self._get_business_rules_text()

            # Invoke the chain
            self.logger.info(f"Invoking LangChain for session filtering ({self.show_name})")
            ai_msg = chain.invoke({
                "sessions": text_rec, 
                "profile": visitor, 
                "rules": business_rules
            })

            # Parse the response
            response_text = ai_msg.content

            # Try to extract JSON from the response
            import re
            json_match = re.search(r"```json\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r"\[\s*{.*}\s*\]", response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text

            try:
                filtered_recommendations = json.loads(json_str)
                self.logger.info(f"LangChain filtered: {len(filtered_recommendations)} sessions")
                return filtered_recommendations, ["Filtered using LLM-based rules"]
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing LangChain response: {e}")
                return recommendations, ["Error in LLM filtering"]

        except Exception as e:
            self.logger.error(f"Error using LangChain for filtering: {e}")
            return recommendations, [f"Error in LLM filtering: {str(e)}"]

    def _build_langchain_prompt(self, visitor, recommendations):
        """Build show-specific prompt for LangChain filtering."""
        # Get visitor and session keys
        list_keys_vis = list(visitor.keys())
        if recommendations:
            list_keys = list(recommendations[0].keys())
        else:
            list_keys = ["session_id", "title", "stream", "theatre__name", 
                        "date", "start_time", "end_time", "sponsored_by", 
                        "sponsored_session", "similarity"]

        # Build base prompt
        base_prompt = f"""
        You are an assistant specialized in filtering sessions for the {self.show_name} event.
        - You will receive a profile of a visitor with the following keys: {list_keys_vis}
        - You will receive a list of sessions with the following keys: {list_keys}
        - Each session you return must have the same format.
        - Only return the sessions in JSON format.
        """

        # Add show-specific context
        if self.main_event_name in ["bva", "lva"]:
            # Veterinary show context
            base_prompt += """
            - The attribute what_type_does_your_practice_specialise_in can be a list separated by ";"
            - Stream in session can be a list of topics separated by ";"
            - Consider all stream values when evaluating rules
            """
        elif self.main_event_name in ["ecomm", "tfm"]:
            # E-commerce show context
            base_prompt += """
            - Consider the visitor's industry and job role
            - Sessions are categorized by business relevance
            """

        return base_prompt

    def _get_business_rules_text(self):
        """Get business rules text for the current show."""
        if self.main_event_name in ["bva", "lva"]:
            # Veterinary business rules
            return f"""
            1.) If visitor what_type_does_your_practice_specialise_in contains "equine" or "mixed", 
                exclude sessions on streams: {', '.join(self.rules_config.get('equine_mixed_exclusions', []))}
            2.) If visitor what_type_does_your_practice_specialise_in contains "small animal", 
                exclude sessions on streams: {', '.join(self.rules_config.get('small_animal_exclusions', []))}
            3.) If job_role in VET_ROLES, session.stream can't be in: {', '.join(self.rules_config.get('vet_exclusions', []))}
            4.) If job_role in NURSE_ROLES, only recommend sessions in streams: {', '.join(self.rules_config.get('nurse_streams', []))}
            5.) Rules 1 and 2 are mutually exclusive; apply first, then apply 3 and 4
            
            VET_ROLES = {self.role_groups.get('vet', [])}
            NURSE_ROLES = {self.role_groups.get('nurse', [])}
            """
        else:
            # Generic or show-specific rules for other events
            return "Apply general relevance filtering based on visitor profile and session attributes."

    def _save_recommendations(self, all_recommendations):
        """Save recommendations to JSON file."""
        try:
            # Create output filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                self.output_path, 
                "recommendations", 
                f"recommendations_{self.show_name}_{timestamp}.json"
            )
            
            # Prepare data for saving
            save_data = {
                "metadata": {
                    "show": self.show_name,
                    "timestamp": timestamp,
                    "total_visitors": len(all_recommendations),
                    "configuration": {
                        "min_similarity_score": self.min_similarity_score,
                        "max_recommendations": self.max_recommendations,
                        "similar_visitors_count": self.similar_visitors_count,
                        "filtering_enabled": self.enable_filtering,
                        "use_langchain": self.use_langchain
                    }
                },
                "recommendations": all_recommendations
            }
            
            # Save to file
            with open(output_file, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved recommendations to {output_file}")
            
            # Also save a CSV version for easier analysis
            csv_file = output_file.replace('.json', '.csv')
            df = self.json_to_dataframe(output_file)
            df.to_csv(csv_file, index=False)
            self.logger.info(f"Saved CSV version to {csv_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving recommendations: {str(e)}", exc_info=True)

    def _update_visitor_recommendations(self, recommendations_data):
        """Update visitors with has_recommendation flag and create IS_RECOMMENDED relationships."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    for rec_data in recommendations_data:
                        badge_id = rec_data["metadata"]["badge_id"]
                        filtered_recs = rec_data.get("filtered_recommendations", [])

                        if len(filtered_recs) > 0:
                            # Update has_recommendation flag
                            update_query = f"""
                            MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                            WHERE v.show = $show_name
                            SET v.has_recommendation = "1"
                            RETURN v
                            """
                            session.run(update_query, badge_id=badge_id, show_name=self.show_name)

                            # Create IS_RECOMMENDED relationships
                            for rec in filtered_recs:
                                session_id = rec.get("session_id") if isinstance(rec, dict) else rec
                                if session_id:
                                    rel_query = f"""
                                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                                    WHERE v.show = $show_name
                                    MATCH (s:{self.session_this_year_label} {{session_id: $session_id}})
                                    WHERE s.show = $show_name
                                    MERGE (v)-[r:IS_RECOMMENDED]->(s)
                                    RETURN r
                                    """
                                    session.run(
                                        rel_query,
                                        badge_id=badge_id,
                                        session_id=session_id,
                                        show_name=self.show_name
                                    )

                            self.logger.info(f"Updated visitor {badge_id} with {len(filtered_recs)} recommendations")

        except Exception as e:
            self.logger.error(f"Error updating visitor recommendations: {str(e)}", exc_info=True)

    def json_to_dataframe(self, json_file_path: str) -> pd.DataFrame:
        """Convert JSON data to a pandas DataFrame."""
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
        
        return pd.DataFrame(rows)