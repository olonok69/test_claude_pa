
import numpy as np
import json
import time
from datetime import datetime
import logging
import concurrent.futures
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import streamlit as st

# Optional imports (for LangChain approach)
has_langchain = False
try:
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_openai import ChatOpenAI, AzureChatOpenAI, AzureOpenAI
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    from dotenv import dotenv_values
    has_langchain = True
except ImportError as e:
    has_langchain = False
    # Only log once, not multiple times
    import logging
    logger = logging.getLogger(__name__)
    logger.info("LangChain not available. Will use rule-based filtering only.")

# Sentence transformers import with error handling
has_sentence_transformers = False
try:
    from sentence_transformers import SentenceTransformer
    has_sentence_transformers = True
except ImportError as e:
    has_sentence_transformers = False
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("sentence-transformers not available. Similarity calculations will be disabled.")


class StreamlitSessionRecommendationService:
    """
    Session recommendation service adapted for Streamlit application.
    """

    def __init__(self, config: dict):
        """
        Initialize the recommendation service.

        Args:
            config: Configuration dictionary from Streamlit session state
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Neo4j connection parameters from environment or config
        neo4j_config = config.get("neo4j", {})
        self.uri = neo4j_config.get("uri", "neo4j+s://c6cfaac8.databases.neo4j.io")
        self.username = neo4j_config.get("username", "neo4j")
        self.password = neo4j_config.get("password", "")

        # Initialize sentence transformer model
        self.model_name = "all-MiniLM-L6-v2"
        self.model = None  # Lazy initialization

        # Define role groups (for rule processing)
        self.vet_roles = [
            "Vet/Vet Surgeon",
            "Assistant Vet",
            "Vet/Owner",
            "Clinical or other Director",
            "Locum Vet",
            "Academic",
        ]

        self.nurse_roles = ["Head Nurse/Senior Nurse", "Vet Nurse", "Locum RVN"]
        self.business_roles = ["Practice Manager", "Practice Partner/Owner"]
        self.other_roles = ["Student", "Receptionist", "Other (please specify)"]

        # Initialize caches
        self._this_year_sessions_cache = None
        self._visitor_cache = {}
        self._similar_visitors_cache = {}

        # Load business rules
        self.business_rules = """
        1.) if visitor what_type_does_your_practice_specialise_in contains "equine" or "mixed", you can't propose session on stream "exotics", "feline", "exotic animal", "farm", "small animal"
        2.) if visitor what_type_does_your_practice_specialise_in contains "small animal", you can't propose session on stream "equine", "farm animal", "farm", "large animal"
        3.) if job_role in VET_ROLES session.stream cant be "nursing"
        4.) if job_role in NURSE_ROLES you only recommend sessions in stream "nursing", "wellbeing", "welfare"
        5.) rule 1 and 2 are mutually exclusive and apply first then apply 3 and 4
        """

        # Rules configuration
        self.rules_config = config.get("recommendation", {}).get("rules_config", {
            "equine_mixed_exclusions": [
                "exotics",
                "feline", 
                "exotic animal",
                "farm",
                "small animal",
            ],
            "small_animal_exclusions": [
                "equine",
                "farm animal",
                "farm",
                "large animal",
            ],
            "vet_exclusions": ["nursing"],
            "nurse_streams": ["nursing", "wellbeing", "welfare"],
            "rule_priority": ["practice_type", "role"],
        })

    def _init_model(self):
        """Initialize the sentence transformer model if not already initialized."""
        if self.model is None:
            if not has_sentence_transformers:
                self.logger.error("sentence-transformers library not available. Cannot initialize model.")
                return False
            
            try:
                # Set torch threads to avoid conflicts
                import os
                os.environ['TOKENIZERS_PARALLELISM'] = 'false'
                
                self.model = SentenceTransformer(self.model_name)
                self.logger.info(f"Initialized sentence transformer model {self.model_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error initializing sentence transformer model: {str(e)}")
                self.model = None
                return False
        return True

    def get_visitor_by_badge_id(self, badge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get visitor information by badge ID from Neo4j.

        Args:
            badge_id: Visitor's badge ID

        Returns:
            Visitor data dictionary or None if not found
        """
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    query = """
                    MATCH (v:Visitor_this_year {BadgeId: $badge_id})
                    RETURN v
                    """
                    result = session.run(query, badge_id=badge_id).single()
                    
                    if result:
                        visitor_data = dict(result["v"])
                        self.logger.info(f"Found visitor {badge_id} in Neo4j")
                        return visitor_data
                    else:
                        self.logger.warning(f"Visitor {badge_id} not found in Neo4j")
                        return None
        except Exception as e:
            self.logger.error(f"Error getting visitor from Neo4j: {str(e)}")
            return None

    def get_all_visitors(self) -> List[Dict[str, Any]]:
        """
        Get all visitors from Neo4j.

        Returns:
            List of visitor data dictionaries
        """
        try:
            with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
                with driver.session() as session:
                    query = """
                    MATCH (v:Visitor_this_year)
                    RETURN v.BadgeId as badge_id, 
                           v.what_type_does_your_practice_specialise_in as what_type_does_your_practice_specialise_in, 
                           v.Country as country, 
                           v.JobTitle as job_title, 
                           v.job_role as job_role
                    ORDER BY v.BadgeId
                    """
                    results = session.run(query).data()
                    return results
        except Exception as e:
            self.logger.error(f"Error getting all visitors from Neo4j: {str(e)}")
            return []

    def get_this_year_sessions(self, tx):
        """
        Get all sessions for this year with their embeddings.
        Uses caching for better performance.
        """
        if self._this_year_sessions_cache is not None:
            return self._this_year_sessions_cache

        # Query to get this year's sessions with embeddings
        query = """
        MATCH (s:Sessions_this_year)
        WHERE s.embedding IS NOT NULL
        RETURN s.session_id as session_id, 
               s.title as title, 
               s.stream as stream, 
               s.synopsis_stripped as synopsis_stripped,
               s.theatre__name as theatre__name,
               s.embedding as embedding,
               s.date as date,
               s.start_time as start_time,
               s.end_time as end_time,
               s.sponsored_by as sponsored_by,
               s.sponsored_session as sponsored_session
        """

        results = tx.run(query).data()

        # Process results and cache them
        sessions = {}
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None

            if embedding is not None:
                sessions[r["session_id"]] = {
                    "session_id": r["session_id"],
                    "title": r["title"],
                    "stream": r["stream"],
                    "synopsis_stripped": r["synopsis_stripped"],
                    "theatre__name": r["theatre__name"],
                    "embedding": embedding,
                    "date": r["date"],
                    "start_time": r["start_time"],
                    "end_time": r["end_time"],
                    "sponsored_by": r["sponsored_by"],
                    "sponsored_session": r["sponsored_session"],
                }

        self._this_year_sessions_cache = sessions
        return sessions

    def get_visitor_info(self, tx, visitor_id):
        """
        Get visitor information with caching.
        """
        if visitor_id in self._visitor_cache:
            return self._visitor_cache[visitor_id]

        visitor_query = """
        MATCH (v:Visitor_this_year {BadgeId: $visitor_id})
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
        """
        Get sessions the visitor attended last year.
        """
        query_past = """
        MATCH (v:Visitor_this_year {BadgeId: $visitor_id})-[:Same_Visitor]->(vp)-[:attended_session]->(sp:Sessions_past_year)
        WHERE (vp:Visitor_last_year_bva OR vp:Visitor_last_year_lva)
        RETURN DISTINCT sp.session_id as session_id, sp.embedding as embedding
        """

        results = tx.run(query_past, visitor_id=visitor_id).data()

        # Process embeddings
        sessions = []
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions.append({"session_id": r["session_id"], "embedding": embedding})

        return sessions

    def find_similar_visitors_batch(self, tx, visitor, num_similar_visitors=3):
        """
        Find similar visitors with batch processing.
        """
        visitor_id = visitor["BadgeId"]

        # Check cache first
        if visitor_id in self._similar_visitors_cache:
            return self._similar_visitors_cache[visitor_id]

        # Get all visitors with sessions in one query
        query = """
        MATCH (v:Visitor_this_year)
        WHERE v.assist_year_before = '1' AND v.BadgeId <> $visitor_id
        WITH v, 
             CASE WHEN v.job_role = $job_role THEN 1 ELSE 0 END + 
             CASE WHEN v.what_type_does_your_practice_specialise_in = $practice_type THEN 1 ELSE 0 END +
             CASE WHEN v.organisation_type = $org_type THEN 1 ELSE 0 END +
             CASE WHEN v.Country = $country THEN 1 ELSE 0 END AS base_similarity
        WHERE base_similarity > 0
        MATCH (v)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:Sessions_past_year)
        WHERE (vp:Visitor_last_year_bva OR vp:Visitor_last_year_lva)
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

        # If we can't find enough similar visitors, try a more general query
        if len(visitors_data) < num_similar_visitors:
            query = """
            MATCH (v:Visitor_this_year)
            WHERE v.assist_year_before = '1' AND v.BadgeId <> $visitor_id
            MATCH (v)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:Sessions_past_year)
            WHERE (vp:Visitor_last_year_bva OR vp:Visitor_last_year_lva)
            WITH v, COUNT(DISTINCT sp) AS session_count
            WHERE session_count > 0
            RETURN v, 0 AS base_similarity
            ORDER BY session_count DESC
            LIMIT 20
            """
            visitors_data = tx.run(query, visitor_id=visitor_id).data()

        # Extract visitor features for comparison
        def get_visitor_features(v):
            attributes = [
                v.get("what_type_does_your_practice_specialise_in", ""),
                v.get("job_role", ""),
                v.get("organisation_type", ""),
                v.get("JobTitle", ""),
                v.get("Country", ""),
            ]
            return " ".join([
                str(attr) for attr in attributes 
                if attr and str(attr).strip() and str(attr) != "NA"
            ])

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
                    # Combine neural and rule-based similarity
                    combined_sim = (sim * 0.7) + (base_similarity * 0.3 / 4)
                    similarities.append((v_compare["BadgeId"], combined_sim))
                except Exception as e:
                    self.logger.error(f"Error comparing with visitor {v_compare['BadgeId']}: {e}")
                    continue

            # Sort by similarity and get top N
            similarities.sort(key=lambda x: -x[1])
            similar_visitors = [sid for sid, _ in similarities[:num_similar_visitors]]

            # Cache for future use
            self._similar_visitors_cache[visitor_id] = similar_visitors
            return similar_visitors

        except Exception as e:
            self.logger.error(f"Error encoding visitor profile: {e}")
            return []

    def get_similar_visitor_sessions_batch(self, tx, similar_visitor_badge_ids):
        """
        Get sessions attended by similar visitors using a batch query.
        """
        if not similar_visitor_badge_ids:
            return []

        query = """
        MATCH (v:Visitor_this_year)-[:Same_Visitor]->(vp)-[:attended_session]->(sp:Sessions_past_year)
        WHERE v.BadgeId IN $similar_visitor_ids AND 
              (vp:Visitor_last_year_bva OR vp:Visitor_last_year_lva)
        RETURN DISTINCT sp.session_id AS session_id, sp.embedding AS embedding
        """

        results = tx.run(query, similar_visitor_ids=similar_visitor_badge_ids).data()

        # Process embeddings
        sessions = []
        for r in results:
            embedding = np.array(json.loads(r["embedding"])) if r["embedding"] else None
            if embedding is not None:
                sessions.append({"session_id": r["session_id"], "embedding": embedding})

        return sessions

    def calculate_session_similarities_parallel(self, past_sessions, this_year_sessions, min_score=0.0):
        """
        Calculate similarities between past sessions and this year's sessions in parallel.
        """
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

        # Use parallel processing for faster calculation
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
                    self.logger.error(f"Error processing session: {e}")

        # Deduplicate recommendations, keeping the highest similarity score
        session_to_best_rec = {}
        for rec in all_recommendations:
            sid = rec["session_id"]
            if sid not in session_to_best_rec or rec["similarity"] > session_to_best_rec[sid]["similarity"]:
                session_to_best_rec[sid] = rec

        # Convert back to list and sort by similarity
        recommendations = list(session_to_best_rec.values())
        recommendations.sort(key=lambda x: -x["similarity"])

        return recommendations

    def recommend_sessions_optimized(self, badge_id: str, min_score: float = 0.0, 
                                   max_recommendations: int = None, 
                                   num_similar_visitors: int = 3) -> List[Dict[str, Any]]:
        """
        Generate optimized session recommendations for a visitor.
        """
        start_time = time.time()

        with GraphDatabase.driver(self.uri, auth=(self.username, self.password)) as driver:
            with driver.session() as session:
                # Get visitor information
                visitor_info = session.execute_read(self.get_visitor_info, visitor_id=badge_id)
                if not visitor_info:
                    self.logger.warning(f"Visitor with BadgeId {badge_id} not found.")
                    return []

                visitor = visitor_info["visitor"]
                assisted = visitor_info["assisted"]

                # Get all this year's sessions in one go (uses caching)
                this_year_sessions = session.execute_read(self.get_this_year_sessions)
                self.logger.info(f"Loaded {len(this_year_sessions)} sessions for this year")

                past_sessions = []

                if assisted == "1":
                    # Case 1: Visitor attended last year
                    self.logger.info(f"Case 1: Visitor {badge_id} attended last year")
                    past_sessions = session.execute_read(self.get_past_sessions, visitor_id=badge_id)
                    self.logger.info(f"Found {len(past_sessions)} past sessions")
                else:
                    # Case 2: New visitor - find similar visitors
                    self.logger.info(f"Case 2: Finding {num_similar_visitors} similar visitors for {badge_id}")
                    
                    # Check if sentence transformers are available
                    if not has_sentence_transformers:
                        self.logger.warning("Cannot find similar visitors without sentence-transformers. Using rule-based approach only.")
                        return []
                    
                    similar_visitors = session.execute_read(
                        self.find_similar_visitors_batch,
                        visitor=visitor,
                        num_similar_visitors=num_similar_visitors
                    )
                    self.logger.info(f"Found {len(similar_visitors)} similar visitors")

                    if similar_visitors:
                        past_sessions = session.execute_read(
                            self.get_similar_visitor_sessions_batch,
                            similar_visitor_badge_ids=similar_visitors
                        )
                        self.logger.info(f"Found {len(past_sessions)} sessions from similar visitors")

                # Calculate similarities in parallel
                recommendations = self.calculate_session_similarities_parallel(
                    past_sessions=past_sessions,
                    this_year_sessions=this_year_sessions,
                    min_score=min_score
                )

                # Apply maximum recommendations limit
                if max_recommendations and len(recommendations) > max_recommendations:
                    recommendations = recommendations[:max_recommendations]

                self.logger.info(f"Total recommendation time: {time.time() - start_time:.2f}s")
                return recommendations

    def _contains_any(self, text, keywords):
        """Check if text contains any of the keywords (case-insensitive)."""
        if not text or not isinstance(text, str):
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _apply_practice_type_rules(self, visitor, sessions):
        """Apply practice type filtering rules."""
        if not visitor or "what_type_does_your_practice_specialise_in" not in visitor:
            return sessions, []

        practice_type = visitor.get("what_type_does_your_practice_specialise_in", "")
        if not practice_type or practice_type == "NA":
            return sessions, []

        filtered_sessions = []
        rules_applied = []

        # Check if practice contains equine or mixed
        if self._contains_any(practice_type, ["equine", "mixed"]):
            exclusions = self.rules_config["equine_mixed_exclusions"]
            filtered_sessions = [
                session for session in sessions
                if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
            ]
            rules_applied.append(f"practice_type: mixed/equine - excluded {', '.join(exclusions)}")
            self.logger.info(f"Applied equine/mixed rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions")

        # Check if practice contains small animal
        elif self._contains_any(practice_type, ["small animal"]):
            exclusions = self.rules_config["small_animal_exclusions"]
            filtered_sessions = [
                session for session in sessions
                if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
            ]
            rules_applied.append(f"practice_type: small animal - excluded {', '.join(exclusions)}")
            self.logger.info(f"Applied small animal rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions")
        else:
            filtered_sessions = sessions

        return filtered_sessions, rules_applied

    def _apply_role_rules(self, visitor, sessions):
        """Apply job role filtering rules."""
        if not visitor or "job_role" not in visitor:
            return sessions, []

        job_role = visitor.get("job_role", "")
        if not job_role or job_role == "NA":
            return sessions, []

        filtered_sessions = []
        rules_applied = []

        # Rule for VET_ROLES
        if job_role in self.vet_roles:
            exclusions = self.rules_config["vet_exclusions"]
            filtered_sessions = [
                session for session in sessions
                if not session.get("stream") or not self._contains_any(session["stream"], exclusions)
            ]
            rules_applied.append(f"role: vet - excluded {', '.join(exclusions)}")
            self.logger.info(f"Applied vet role rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions")

        # Rule for NURSE_ROLES
        elif job_role in self.nurse_roles:
            allowed_streams = self.rules_config["nurse_streams"]
            filtered_sessions = [
                session for session in sessions
                if session.get("stream") and self._contains_any(session["stream"], allowed_streams)
            ]
            rules_applied.append(f"role: nurse - limited to {', '.join(allowed_streams)}")
            self.logger.info(f"Applied nurse role rule: filtered from {len(sessions)} to {len(filtered_sessions)} sessions")
        else:
            filtered_sessions = sessions

        return filtered_sessions, rules_applied

    def filter_sessions(self, visitor, sessions):
        """
        Filter sessions based on visitor profile and business rules.

        Args:
            visitor: Dictionary containing visitor profile
            sessions: List of session dictionaries to filter

        Returns:
            Tuple of (filtered_sessions, rules_applied)
        """
        if not sessions:
            return [], []

        filtered_sessions = sessions
        rule_priority = self.rules_config["rule_priority"]
        all_rules_applied = []

        # Apply rules in priority order
        for rule_type in rule_priority:
            if rule_type == "practice_type":
                filtered_sessions, rules_applied = self._apply_practice_type_rules(visitor, filtered_sessions)
                all_rules_applied.extend(rules_applied)
            elif rule_type == "role":
                filtered_sessions, rules_applied = self._apply_role_rules(visitor, filtered_sessions)
                all_rules_applied.extend(rules_applied)

        # Sort by similarity score (highest first)
        filtered_sessions.sort(key=lambda x: float(x.get("similarity", 0)), reverse=True)

        return filtered_sessions, all_rules_applied

    def filter_with_langchain(self, visitor, recommendations):
        """
        Filter recommendations using LangChain and LLM.

        Args:
            visitor: Visitor profile dictionary
            recommendations: List of recommended sessions

        Returns:
            Filtered list of recommendations and a list of processing notes
        """
        if not has_langchain:
            self.logger.warning("LangChain not available. Cannot filter using LLM.")
            return recommendations, ["LangChain filtering not available"]

        try:
            # Load environment from Streamlit session state config
            config_values = st.session_state.get("config", {})
            
            # Initialize Azure OpenAI client
            llm = AzureChatOpenAI(
                azure_endpoint=config_values.get("AZURE_ENDPOINT", ""),
                azure_deployment=config_values.get("AZURE_DEPLOYMENT", ""),
                api_key=config_values.get("AZURE_API_KEY", ""),
                api_version=config_values.get("AZURE_API_VERSION", ""),
                temperature=0.5,
                top_p=0.9,
            )

            # Get keys from visitor and recommendations
            list_keys_vis = list(visitor.keys())
            if recommendations:
                list_keys = list(recommendations[0].keys())
            else:
                list_keys = ["session_id", "title", "stream", "theatre__name", "date", 
                           "start_time", "end_time", "sponsored_by", "sponsored_session", "similarity"]

            # Generate the prompt
            system_prompt = f"""
            you are an assistant specialized in filter sessions of an Event based in bussiness rules and profiles of users.
            - you will receive a profile of a visitor with the following keys: {list_keys_vis}
              the attribute what_type_does_your_practice_specialise_in can be a list of specializations separated by ";"
            - you will receive a list of session with the following keys: {list_keys}
              stream in session can be a list of topics separated by ";". When you evaluate the rule you need to consider all of them 
            - each session you return must have the same format.
            - different Job_Roles Groups:
            VET_ROLES = {self.vet_roles}
            NURSE_ROLES = {self.nurse_roles}
            BUSINESS = {self.business_roles}
            OTHER_ROLES = {self.other_roles}
            - only return the sessions in json format
            """

            prompt = PromptTemplate(
                input_variables=["sessions", "rules", "profile"],
                template=system_prompt + 
                """For the Visitor with profile {profile}, based on the attributes of these session: {sessions} and implementing the following rules {rules}.
                Filter them and just return from the list those that meet the requirements in the rules""",
            )

            # Create chain
            chain = prompt | llm

            # Convert recommendations to text
            text_rec = json.dumps(recommendations)

            # Invoke the chain
            self.logger.info("Invoking LangChain for session filtering")
            ai_msg = chain.invoke({
                "sessions": text_rec, 
                "profile": visitor, 
                "rules": self.business_rules
            })

            # Parse the response to extract the filtered recommendations
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
                self.logger.info(f"Successfully filtered recommendations using LangChain: {len(filtered_recommendations)} sessions")
                return filtered_recommendations, ["Filtered using LLM-based rules"]
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing LangChain response: {e}")
                return recommendations, ["Error in LLM filtering"]

        except Exception as e:
            self.logger.error(f"Error using LangChain for filtering: {e}")
            return recommendations, ["Error in LLM filtering: " + str(e)]

    def get_recommendations_and_filter(self, badge_id: str, min_score: float = 0.3, 
                                     max_recommendations: int = 30, 
                                     visitor_data: Optional[Dict] = None,
                                     use_langchain: bool = False) -> Dict[str, Any]:
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

        # Get visitor profile from Neo4j if not provided
        visitor = visitor_data
        if visitor is None:
            visitor = self.get_visitor_by_badge_id(badge_id)
            if visitor:
                processing_steps.append(f"Found visitor {badge_id} in Neo4j")
            else:
                processing_steps.append(f"Visitor {badge_id} not found in Neo4j")

        # If visitor still not found, return empty result
        if visitor is None:
            return {
                "visitor": None,
                "raw_recommendations": [],
                "filtered_recommendations": [],
                "metadata": {
                    "error": "Visitor not found",
                    "processing_time": time.time() - start_time,
                    "processing_steps": processing_steps,
                },
            }

        # Get recommendations
        try:
            # Get raw recommendations
            recommendations = self.recommend_sessions_optimized(
                badge_id=badge_id,
                min_score=min_score,
                max_recommendations=max_recommendations,
            )

            processing_steps.append(f"Retrieved {len(recommendations)} raw recommendations")

            # Choose filtering approach
            if use_langchain and has_langchain:
                # Use LangChain filtering
                processing_steps.append("Using LangChain for filtering")
                filtered_recommendations, filter_notes = self.filter_with_langchain(
                    visitor=visitor, recommendations=recommendations
                )
                processing_steps.extend(filter_notes)
            else:
                # Use rule-based filtering
                processing_steps.append("Using rule-based filtering")
                filtered_recommendations, filter_notes = self.filter_sessions(visitor, recommendations)
                processing_steps.extend(filter_notes)

            processing_steps.append(f"Filtered to {len(filtered_recommendations)} recommendations")

            # Create result dictionary
            result = {
                "visitor": visitor,
                "raw_recommendations": recommendations,
                "filtered_recommendations": filtered_recommendations,
                "metadata": {
                    "badge_id": badge_id,
                    "num_raw_recommendations": len(recommendations),
                    "num_filtered_recommendations": len(filtered_recommendations),
                    "processing_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "processing_steps": processing_steps,
                },
            }

            return result

        except Exception as e:
            self.logger.error(f"Error getting recommendations: {str(e)}")
            return {
                "visitor": visitor,
                "raw_recommendations": [],
                "filtered_recommendations": [],
                "metadata": {
                    "error": str(e),
                    "processing_time": time.time() - start_time,
                    "processing_steps": processing_steps,
                },
            }

    def clear_caches(self):
        """Clear all caches."""
        self._this_year_sessions_cache = None
        self._visitor_cache = {}
        self._similar_visitors_cache = {}