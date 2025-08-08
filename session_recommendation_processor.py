"""
Generic Session Recommendation Processor - Fixed Version
This processor handles session recommendations for any show type through configuration.
Fixed to match old processor behavior exactly.
"""

import os
import sys
import time
import json
import logging
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_utils import load_config
from utils.logging_utils import setup_logging

# Try to import LangChain components (optional)
try:
    from langchain_openai import AzureChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    has_langchain = True
except ImportError:
    has_langchain = False


class SessionRecommendationProcessor:
    """
    Generic processor for generating session recommendations.
    Works with any show type through configuration.
    """

    def __init__(self, config: dict):
        """Initialize the session recommendation processor."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Get event configuration
        self.event_config = config.get("event", {})
        self.main_event_name = self.event_config.get("main_event_name", "bva")
        self.show_name = self.event_config.get("show_name", self.main_event_name)
        self.year = self.event_config.get("year", datetime.now().year)
        
        # Setup data paths
        self.data_dir = Path(config.get("data_dir", "data"))
        self.output_dir = Path(config.get("output_dir", "output"))
        self.show_data_dir = self.data_dir / self.main_event_name
        
        # Get recommendations output configuration
        rec_config = config.get("output_files", {}).get("recommendations", {})
        self.rec_output_dir = rec_config.get("output_directory", "recommendations")
        self.rec_filename_pattern = rec_config.get("filename_pattern", "visitor_recommendations_{timestamp}")
        
        # Create recommendations directory
        self.recommendations_dir = self.show_data_dir / self.rec_output_dir
        self.recommendations_dir.mkdir(parents=True, exist_ok=True)
        
        # Load Neo4j configuration
        self._load_neo4j_config()
        
        # Load recommendation configuration
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

    def _load_neo4j_config(self):
        """Load Neo4j configuration from environment or config file."""
        # Try to load from environment file first
        env_file = self.config.get("env_file", "keys/.env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
            self.logger.info(f"Loaded environment from {env_file}")
        
        # Get Neo4j credentials
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        # Fallback to config file if not in environment
        if not all([self.uri, self.username, self.password]):
            neo4j_config = self.config.get("neo4j", {})
            self.uri = self.uri or neo4j_config.get("uri")
            self.username = self.username or neo4j_config.get("username")
            self.password = self.password or neo4j_config.get("password")
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Neo4j credentials not found in environment or config")
        
        # Get node labels configuration
        self.node_labels = self.config.get("neo4j", {}).get("node_labels", {})
        self.visitor_this_year_label = self.node_labels.get("visitor_this_year", "Visitor_this_year")
        self.visitor_last_year_label = self.node_labels.get("visitor_last_year", "Visitor_last_year")
        self.sessions_this_year_label = self.node_labels.get("sessions_this_year", "Sessions_this_year")
        self.sessions_past_year_label = self.node_labels.get("sessions_past_year", "Sessions_past_year")

    def _load_show_specific_config(self):
        """Load show-specific configurations based on the event type."""
        # Define role groups based on show type
        if self.main_event_name in ["bva", "lva"]:
            # Veterinary-specific roles
            self.role_groups = {
                "vet": [
                    "Veterinary Surgeon",
                    "Vet",
                    "Veterinary surgeon",
                    "veterinary surgeon",
                    "Locum",
                    "Other Vet Professional"
                ],
                "nurse": [
                    "Veterinary Nurse",
                    "Veterinary nurse",
                    "Student Veterinary Nurse",
                    "Nurse",
                    "veterinary nurse"
                ]
            }
        else:
            # Generic or other show types
            self.role_groups = self.config.get("role_groups", {})

    def _init_model(self):
        """Initialize the sentence transformer model lazily."""
        if self.model is None:
            self.logger.info(f"Initializing sentence transformer model {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"Initialized sentence transformer model {self.model_name}")

    def process(self, create_only_new=False):
        """
        Main processing function for session recommendations.
        
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
                        
                        # FIXED: Check length > 0 explicitly like old processor
                        if (rec_result and 
                            "filtered_recommendations" in rec_result and 
                            len(rec_result["filtered_recommendations"]) > 0):
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

            # Update Neo4j with recommendations
            if all_recommendations:
                self._update_neo4j_recommendations(all_recommendations)
            
            # Save recommendations to file
            self._save_recommendations(all_recommendations)
            
            # Log final statistics
            self.statistics["processing_time"] = time.time() - start_time
            self.logger.info(f"Completed session recommendation processing in {self.statistics['processing_time']:.2f} seconds")
            self._log_statistics()
            
        except Exception as e:
            self.logger.error(f"Error in session recommendation processing: {str(e)}", exc_info=True)
            raise

    def get_recommendations_and_filter(self, badge_id, min_score, max_recommendations, visitor_data=None, use_langchain=False):
        """
        Get recommendations for a visitor and apply filtering.
        FIXED: Matches old processor behavior - limit before filtering.
        
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
        # FIXED: Use exact limit (don't multiply by 2) to match old processor
        raw_recommendations = self.get_neo4j_recommendations(
            visitor_id=badge_id,
            min_score=min_score,
            max_recommendations=max_recommendations  # Use exact limit like old processor
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
        
        # FIXED: Don't apply limit again - already limited before filtering
        # This matches old processor behavior
        
        return {
            "visitor": visitor,
            "raw_recommendations": raw_recommendations,
            "filtered_recommendations": filtered_recommendations,
            "metadata": {
                "badge_id": badge_id,
                "num_raw_recommendations": len(raw_recommendations),
                "num_filtered_recommendations": len(filtered_recommendations),
                "processing_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat(),
                "processing_steps": processing_steps,
            }
        }

    def get_neo4j_recommendations(self, visitor_id, min_score=0.3, max_recommendations=10):
        """
        Get recommendations using Neo4j graph traversal.
        
        Args:
            visitor_id: Badge ID of the visitor
            min_score: Minimum similarity score
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of recommended sessions
        """
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    # Get visitor info
                    visitor_info = session.execute_read(
                        self._get_visitor_info_tx, visitor_id
                    )
                    
                    if not visitor_info:
                        self.logger.warning(f"Visitor {visitor_id} not found in Neo4j")
                        return []
                    
                    assist_year_before = visitor_info.get("assist_year_before", "0")
                    
                    # Load sessions for this year
                    this_year_sessions = session.execute_read(
                        self._get_sessions_this_year_tx
                    )
                    
                    if assist_year_before == "1":
                        # Case 1: Visitor attended last year
                        past_sessions = session.execute_read(
                            self._get_attended_sessions_tx, visitor_id
                        )
                    else:
                        # Case 2: New visitor - find similar visitors
                        similar_visitors = session.execute_read(
                            self._find_similar_visitors_tx,
                            visitor_id,
                            self.similar_visitors_count
                        )
                        
                        if similar_visitors:
                            past_sessions = session.execute_read(
                                self._get_sessions_from_visitors_tx,
                                similar_visitors
                            )
                        else:
                            past_sessions = []
                    
                    # Calculate similarities and get recommendations
                    if past_sessions and this_year_sessions:
                        recommendations = self._calculate_session_similarities(
                            past_sessions, this_year_sessions, min_score
                        )
                        
                        # Sort by similarity and limit
                        recommendations.sort(key=lambda x: x["similarity"], reverse=True)
                        
                        if max_recommendations:
                            recommendations = recommendations[:max_recommendations]
                        
                        return recommendations
                    
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting Neo4j recommendations: {str(e)}")
            return []

    def _get_visitor_info_tx(self, tx, visitor_id):
        """Transaction function to get visitor information."""
        query = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
        RETURN v
        """
        result = tx.run(query, visitor_id=visitor_id)
        record = result.single()
        return dict(record["v"]) if record else None

    def _get_sessions_this_year_tx(self, tx):
        """Transaction function to get sessions for this year."""
        query = f"""
        MATCH (s:{self.sessions_this_year_label})
        WHERE s.embedding IS NOT NULL
        RETURN s
        """
        result = tx.run(query)
        sessions = {}
        for record in result:
            s = dict(record["s"])
            if "embedding" in s:
                s["embedding"] = self._parse_embedding(s["embedding"])
                session_id = s.get("session_id")
                if session_id:
                    sessions[session_id] = s
        return sessions

    def _get_attended_sessions_tx(self, tx, visitor_id):
        """Transaction function to get sessions attended by visitor last year."""
        query = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})-[:Same_Visitor]->(v_past)
        MATCH (v_past)-[:attended_session]->(s:{self.sessions_past_year_label})
        RETURN DISTINCT s
        """
        result = tx.run(query, visitor_id=visitor_id)
        sessions = []
        for record in result:
            session_data = dict(record["s"])
            if "embedding" in session_data:
                session_data["embedding"] = self._parse_embedding(session_data["embedding"])
            sessions.append(session_data)
        return sessions

    def _find_similar_visitors_tx(self, tx, visitor_id, num_similar):
        """Transaction function to find similar visitors."""
        query = f"""
        MATCH (v:{self.visitor_this_year_label} {{BadgeId: $visitor_id}})
        MATCH (other:{self.visitor_this_year_label})
        WHERE other.BadgeId <> $visitor_id
        AND other.assist_year_before = "1"
        WITH v, other,
            CASE WHEN v.job_role = other.job_role THEN 1.0 ELSE 0.0 END +
            CASE WHEN v.what_type_does_your_practice_specialise_in = other.what_type_does_your_practice_specialise_in THEN 1.0 ELSE 0.0 END +
            CASE WHEN v.organisation_type = other.organisation_type THEN 0.5 ELSE 0.0 END +
            CASE WHEN v.Country = other.Country THEN 0.5 ELSE 0.0 END AS similarity
        ORDER BY similarity DESC
        LIMIT $num_similar
        RETURN other.BadgeId as badge_id
        """
        result = tx.run(query, visitor_id=visitor_id, num_similar=num_similar)
        return [record["badge_id"] for record in result]

    def _get_sessions_from_visitors_tx(self, tx, visitor_ids):
        """Transaction function to get sessions from multiple visitors."""
        query = f"""
        MATCH (v:{self.visitor_this_year_label})-[:Same_Visitor]->(v_past)
        WHERE v.BadgeId IN $visitor_ids
        MATCH (v_past)-[:attended_session]->(s:{self.sessions_past_year_label})
        RETURN DISTINCT s
        """
        result = tx.run(query, visitor_ids=visitor_ids)
        sessions = []
        for record in result:
            session_data = dict(record["s"])
            if "embedding" in session_data:
                session_data["embedding"] = self._parse_embedding(session_data["embedding"])
            sessions.append(session_data)
        return sessions

    def _normalize_stream(self, stream_value):
        """
        Normalize stream values for consistency.
        Handles None, "No Data", and other edge cases.
        
        Args:
            stream_value: The stream value from database or file
            
        Returns:
            Normalized stream value (empty string for null/No Data)
        """
        if stream_value is None:
            return ""
        if isinstance(stream_value, str):
            if stream_value == "No Data" or stream_value.lower() == "no data":
                return ""
            return stream_value
        return str(stream_value)  # Convert to string if it's some other type

    def _calculate_session_similarities(self, past_sessions, this_year_sessions, min_score):
        """
        Calculate similarities between past and current sessions.
        
        Args:
            past_sessions: List of past session dictionaries
            this_year_sessions: Dictionary of current sessions
            min_score: Minimum similarity score
            
        Returns:
            List of recommendations with similarity scores
        """
        if not past_sessions or not this_year_sessions:
            return []

        def process_past_session(past_sess):
            recommendations = []
            past_emb = past_sess.get("embedding")
            if past_emb is None:
                return recommendations

            for sid, current_sess in this_year_sessions.items():
                try:
                    current_emb = current_sess.get("embedding")
                    if current_emb is None:
                        continue
                        
                    sim = cosine_similarity([past_emb], [current_emb])[0][0]

                    if sim >= min_score:
                        # Handle stream field - could be None, "No Data", or actual value
                        stream = current_sess.get("stream", "")
                        if stream is None:
                            stream = ""
                        elif stream == "No Data":
                            stream = ""  # Treat "No Data" as empty for consistency
                        
                        recommendations.append({
                            "session_id": sid,
                            "title": current_sess.get("title", ""),
                            "stream": stream,
                            "theatre__name": current_sess.get("theatre__name", ""),
                            "date": current_sess.get("date", ""),
                            "start_time": current_sess.get("start_time", ""),
                            "end_time": current_sess.get("end_time", ""),
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
            return recommendations, ["LangChain not available"]

        try:
            # Initialize LLM
            llm = self._initialize_llm()
            if not llm:
                return recommendations, ["Failed to initialize LLM"]

            # Create prompt template
            template = self._get_filter_prompt_template()
            prompt = PromptTemplate(
                input_variables=["visitor_profile", "recommendations", "business_rules"],
                template=template
            )

            # Create chain
            chain = LLMChain(llm=llm, prompt=prompt)

            # Get business rules for the show
            business_rules = self._get_business_rules()

            # Format visitor profile and recommendations
            visitor_str = json.dumps(visitor, indent=2)
            recommendations_str = json.dumps(recommendations, indent=2)

            # Run the chain
            result = chain.run(
                visitor_profile=visitor_str,
                recommendations=recommendations_str,
                business_rules=business_rules
            )

            # Parse the result
            filtered_recommendations = self._parse_llm_result(result, recommendations)
            
            return filtered_recommendations, ["Applied LangChain filtering"]

        except Exception as e:
            self.logger.error(f"Error in LangChain filtering: {str(e)}")
            return recommendations, [f"LangChain error: {str(e)}"]

    def _get_visitors_to_process(self, create_only_new):
        """Get list of visitors to process based on create_only_new flag."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
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

                    self.logger.info(f"Found {len(badge_ids)} visitors to process for {self.main_event_name}")
                    return badge_ids

        except Exception as e:
            self.logger.error(f"Error getting visitors to process: {str(e)}", exc_info=True)
            return []

    def _load_visitor_data(self):
        """Load visitor data from CSV files."""
        try:
            # Get the file name from configuration
            combined_files = self.config.get("output_files", {}).get("combined_demographic_registration", {})
            visitor_filename = combined_files.get("this_year", "df_reg_demo_this.csv")
            
            # Build the path: output_dir/output/filename
            visitor_file = self.output_dir / "output" / visitor_filename
            
            if not visitor_file.exists():
                self.logger.error(f"Visitor file not found: {visitor_file}")
                return None
            
            df = pd.read_csv(visitor_file)
            
            # Convert to dictionary for faster lookup
            visitor_dict = {}
            for _, row in df.iterrows():
                visitor_dict[row["BadgeId"]] = row.to_dict()
            
            self.logger.info(f"Loaded {len(visitor_dict)} visitors from {visitor_file}")
            return visitor_dict
            
        except Exception as e:
            self.logger.error(f"Error loading visitor data: {str(e)}")
            return None

    def _get_visitor_from_neo4j(self, badge_id):
        """Get visitor data from Neo4j."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    query = f"""
                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                    RETURN v
                    """
                    result = session.run(query, badge_id=badge_id)
                    record = result.single()
                    
                    if record:
                        return dict(record["v"])
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting visitor from Neo4j: {str(e)}")
            return None

    def _update_neo4j_recommendations(self, recommendations_data):
        """Update Neo4j with recommendations."""
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    # Clear existing recommendations
                    session.run(f"""
                        MATCH (v:{self.visitor_this_year_label})-[r:IS_RECOMMENDED]->()
                        DELETE r
                    """)
                    
                    session.run(f"""
                        MATCH (v:{self.visitor_this_year_label})
                        SET v.has_recommendation = NULL
                    """)
                    
                    # Create new recommendations
                    for rec_data in recommendations_data:
                        badge_id = rec_data["metadata"]["badge_id"]
                        recommendations = rec_data["filtered_recommendations"]
                        
                        if recommendations:
                            # Set has_recommendation flag
                            session.run(f"""
                                MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                                SET v.has_recommendation = "1"
                            """, badge_id=badge_id)
                            
                            # Create IS_RECOMMENDED relationships
                            for rec in recommendations:
                                session.run(f"""
                                    MATCH (v:{self.visitor_this_year_label} {{BadgeId: $badge_id}})
                                    MATCH (s:{self.sessions_this_year_label} {{session_id: $session_id}})
                                    CREATE (v)-[:IS_RECOMMENDED]->(s)
                                """, badge_id=badge_id, session_id=rec["session_id"])
                    
                    self.logger.info("Updated Neo4j with recommendations")
                    
        except Exception as e:
            self.logger.error(f"Error updating Neo4j recommendations: {str(e)}")

    def _save_recommendations(self, all_recommendations):
        """Save recommendations to JSON file."""
        try:
            # Get output configuration
            rec_config = self.config.get("output_files", {}).get("recommendations", {})
            filename_pattern = rec_config.get("filename_pattern", "visitor_recommendations_{timestamp}")
            
            # Create timestamp and filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filename_pattern.format(timestamp=timestamp, show=self.show_name, year=self.year)
            
            # Create full output path
            output_file = self.recommendations_dir / f"{filename}.json"
            
            # Prepare data for saving
            save_data = {
                "metadata": {
                    "show": self.show_name,
                    "year": self.year,
                    "timestamp": timestamp,
                    "generated_at": datetime.now().isoformat(),
                    "total_visitors_processed": self.statistics["total_visitors_processed"],
                    "visitors_with_recommendations": self.statistics["visitors_with_recommendations"],
                    "total_recommendations": self.statistics["total_recommendations_generated"],
                    "unique_sessions": self.statistics.get("unique_recommended_sessions", 0),
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
            
            # Save to JSON file
            with open(output_file, 'w') as f:
                json.dump(save_data, f, indent=2, default=str)
            
            self.logger.info(f"Saved recommendations to {output_file}")
            
            # Also save a CSV version for easier analysis if configured
            save_csv = rec_config.get("save_csv", True)
            if save_csv:
                csv_file = str(output_file).replace('.json', '.csv')
                df = self._json_to_dataframe(save_data)
                df.to_csv(csv_file, index=False)
                self.logger.info(f"Saved CSV version to {csv_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving recommendations: {str(e)}", exc_info=True)

    def _json_to_dataframe(self, data):
        """
        Convert recommendation JSON data to DataFrame.
        
        Args:
            data: Dictionary containing recommendations data
            
        Returns:
            pandas DataFrame with visitor and session information
        """
        rows = []
        recommendations = data.get('recommendations', [])
        
        for rec in recommendations:
            visitor = rec.get('visitor', {})
            filtered_recs = rec.get('filtered_recommendations', [])
            rec_metadata = rec.get('metadata', {})
            
            for filtered_rec in filtered_recs:
                row = {}
                
                # Add visitor data with prefix
                for key, value in visitor.items():
                    row[f"visitor_{key}"] = value
                
                # Add recommendation data
                if isinstance(filtered_rec, dict):
                    for key, value in filtered_rec.items():
                        row[f"session_{key}"] = value
                else:
                    row["session_id"] = filtered_rec
                
                # Add metadata with prefix
                for key, value in rec_metadata.items():
                    if key not in ['processing_steps']:  # Skip long text fields
                        row[f"metadata_{key}"] = value
                
                rows.append(row)
        
        return pd.DataFrame(rows)

    def _initialize_llm(self):
        """Initialize the LLM for filtering."""
        # Implementation depends on available LLM configuration
        # This is a placeholder that should be customized
        return None

    def _get_filter_prompt_template(self):
        """Get the prompt template for LLM filtering."""
        return """
        Given a visitor profile and a list of recommended sessions, filter the recommendations
        based on the following business rules:
        
        {business_rules}
        
        Visitor Profile:
        {visitor_profile}
        
        Recommendations:
        {recommendations}
        
        Return a JSON list of session IDs that should be kept after filtering.
        """

    def _get_business_rules(self):
        """Get business rules for the current show type."""
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

    def _parse_llm_result(self, result, original_recommendations):
        """Parse LLM filtering result."""
        try:
            # Try to parse as JSON
            import json
            session_ids = json.loads(result)
            
            # Filter recommendations based on LLM result
            filtered = [
                rec for rec in original_recommendations
                if rec["session_id"] in session_ids
            ]
            
            return filtered
            
        except:
            # If parsing fails, return original recommendations
            self.logger.warning("Failed to parse LLM result, returning original recommendations")
            return original_recommendations


def main():
    """Main function for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Session Recommendation Processor")
    parser.add_argument("--config", default="config/config_vet.yaml", help="Configuration file path")
    parser.add_argument("--create-only-new", action="store_true", help="Only process new recommendations")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_dir = Path(config.get("log_dir", "logs"))
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"session_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    setup_logging(log_file=str(log_file))
    
    # Initialize and run processor
    processor = SessionRecommendationProcessor(config)
    processor.process(create_only_new=args.create_only_new)


if __name__ == "__main__":
    main()