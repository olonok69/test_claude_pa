import logging
import os
import pandas as pd
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import inspect


class Neo4jSpecializationStreamProcessor:
    """
    A generic class to process specialization to stream mappings and create relationships in Neo4j.
    This class is responsible for creating relationships between visitor nodes and
    stream nodes based on practice specializations.
    
    GENERIC: Supports configurable node labels, relationship names, field names, and show filtering.
    Compatible with both BVA and ECOMM show configurations.
    """

    def __init__(self, config):
        """
        Initialize the Neo4j Specialization Stream Processor.

        Args:
            config (dict): Configuration dictionary containing paths and settings
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initializing Neo4j Specialization Stream Processor"
        )

        self.config = config
        self.input_dir = config["output_dir"]

        # Load the environment variables to get Neo4j credentials
        load_dotenv(config["env_file"])
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not self.uri or not self.username or not self.password:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Missing Neo4j credentials in .env file"
            )
            raise ValueError("Missing Neo4j credentials in .env file")

        # GENERIC ADDITIONS - Get configuration values with fallbacks for backward compatibility
        self.neo4j_config = config.get("neo4j", {})
        self.show_name = self.neo4j_config.get("show_name", None)  # None = backward compatibility mode
        self.node_labels = self.neo4j_config.get("node_labels", {})
        self.relationships = self.neo4j_config.get("relationships", {})
        self.specialization_stream_mapping_config = self.neo4j_config.get("specialization_stream_mapping", {})
        
        # Get configuration values for specialization mapping
        self.specialization_field_this_year = self.specialization_stream_mapping_config.get(
            "specialization_field_this_year", "what_type_does_your_practice_specialise_in"
        )
        self.specialization_field_bva = self.specialization_stream_mapping_config.get(
            "specialization_field_bva", "what_areas_do_you_specialise_in"
        )
        self.specialization_field_lva = self.specialization_stream_mapping_config.get(
            "specialization_field_lva", "what_areas_do_you_specialise_in"
        )
        
        # Get node labels with fallback to original hardcoded values
        self.visitor_this_year_label = self.node_labels.get("visitor_this_year", "Visitor_this_year")
        self.visitor_last_year_bva_label = self.node_labels.get("visitor_last_year_bva", "Visitor_last_year_bva")
        self.visitor_last_year_lva_label = self.node_labels.get("visitor_last_year_lva", "Visitor_last_year_lva")
        self.stream_label = self.node_labels.get("stream", "Stream")
        self.relationship_name = self.relationships.get("specialization_stream", "specialization_to_stream")

        # Get mapping files from config
        self.specialization_mapping_file = self.specialization_stream_mapping_config.get(
            "file", "spezialization_to_stream.csv"
        )
        self.specialization_map = self.specialization_stream_mapping_config.get(
            "specialization_map", {}
        )
        
        # Fallback to default mapping if not configured
        if not self.specialization_map:
            self.specialization_map = {
                "Wildlife": "Other",
                "Small Animal": "Companion Animal",
                "Mixed": "Other",
                "Dairy": "Farm",
                "Poultry": "Farm",
                "Cattle": "Farm",
                "Pigs": "Farm",
                "Sheep": "Farm",
            }

        # Initialize statistics
        self.statistics = {
            "initial_count": 0,
            "final_count": 0,
            "visitor_nodes_processed": {
                "visitor_this_year": 0,
                "visitor_last_year_bva": 0,
                "visitor_last_year_lva": 0,
                "total": 0,
            },
            "specializations_processed": 0,
            "specializations_mapped": 0,
            "stream_matches_found": 0,
            "relationships_created": {"total": 0},
            "relationships_skipped": {"total": 0},
            "relationships_failed": {"total": 0},
        }

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Neo4j Specialization Stream Processor initialized for show: {self.show_name or 'generic'} (generic mode)"
        )

    def _test_connection(self):
        """Test the connection to Neo4j database"""
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Testing connection to Neo4j"
        )

        try:
            driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) AS count")
                count = result.single()["count"]
                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Successfully connected to Neo4j. Database contains {count} nodes"
                )
            driver.close()
            return True
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Failed to connect to Neo4j: {str(e)}"
            )
            return False

    def load_mappings(self):
        """
        Load the specialization mappings from CSV files.
        GENERIC: Uses configurable file paths and mapping configuration.

        Returns:
            tuple: (map_specialization, specialization_stream_mapping)
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loading specialization mappings"
        )

        try:
            # Use the configured specialization mapping
            map_specialization = self.specialization_map

            # Load specialization to stream mapping from configured file
            specialization_stream_file = os.path.join(
                self.input_dir, self.specialization_mapping_file
            )
            
            if not os.path.exists(specialization_stream_file):
                # Try root directory as fallback
                specialization_stream_file = self.specialization_mapping_file
                
            if not os.path.exists(specialization_stream_file):
                raise FileNotFoundError(f"Specialization mapping file not found: {self.specialization_mapping_file}")
                
            map_specialization_stream = pd.read_csv(specialization_stream_file)

            # Convert to dictionary
            specialization_stream_mapping = json.loads(
                map_specialization_stream.set_index("spezialization").to_json(
                    orient="index"
                )
            )

            # Log some stats about the mapping
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Loaded mapping for {len(specialization_stream_mapping)} specializations"
            )

            return map_specialization, specialization_stream_mapping
        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error loading specialization mappings: {str(e)}"
            )
            raise

    def _count_relationships(self, session):
        """
        Count the total number of specialization_to_stream relationships.
        GENERIC: Uses configurable relationship and node labels with show filtering.
        """
        query = f"""
        MATCH (:{self.visitor_this_year_label})-[r:{self.relationship_name}]->(:{self.stream_label})
        RETURN COUNT(r) AS count
        """
        
        # Add show filtering if configured
        if self.show_name:
            query = f"""
            MATCH (v:{self.visitor_this_year_label})-[r:{self.relationship_name}]->(s:{self.stream_label})
            WHERE v.show = $show_name AND s.show = $show_name
            RETURN COUNT(r) AS count
            """
            result = session.run(query, show_name=self.show_name)
        else:
            result = session.run(query)
            
        return result.single()["count"]

    def create_specialization_stream_relationships(
        self, map_specialization, specialization_stream_mapping, create_only_new=True
    ):
        """
        Create relationships between visitor nodes and stream nodes based on specializations.
        GENERIC: Supports configurable node labels, relationship names, and show filtering.

        Args:
            map_specialization (dict): Dictionary mapping old specialization names to new ones.
            specialization_stream_mapping (dict): Dictionary mapping specializations to streams.
            create_only_new (bool): If True, only create relationships that don't exist.

        Returns:
            dict: Statistics about the relationship creation process.
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Creating specialization to stream relationships (generic mode)"
        )

        driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

        # First count the initial relationships
        with driver.session() as session:
            initial_count = self._count_relationships(session)
            self.statistics["initial_count"] = initial_count
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Initial relationship count: {initial_count}"
            )

        # Process different visitor types
        visitor_types = [
            {
                "node_label": self.visitor_this_year_label,
                "specialization_field": self.specialization_field_this_year,
            },
            {
                "node_label": self.visitor_last_year_bva_label,
                "specialization_field": self.specialization_field_bva,
            },
            {
                "node_label": self.visitor_last_year_lva_label,
                "specialization_field": self.specialization_field_lva,
            },
        ]

        # Process each visitor type
        with driver.session() as session:
            for visitor_type in visitor_types:
                self.logger.info(
                    f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Processing {visitor_type['node_label']} nodes"
                )

                # Use write transaction for consistency
                session.execute_write(
                    self._process_visitor_type,
                    visitor_type["node_label"],
                    visitor_type["specialization_field"],
                    map_specialization,
                    specialization_stream_mapping,
                    self.statistics,
                    create_only_new,
                )

        # Count final relationships
        with driver.session() as session:
            final_count = self._count_relationships(session)
            self.statistics["final_count"] = final_count
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Final relationship count: {final_count}"
            )

        driver.close()

        # Calculate totals
        self.statistics["visitor_nodes_processed"]["total"] = sum(
            self.statistics["visitor_nodes_processed"][key]
            for key in ["visitor_this_year", "visitor_last_year_bva", "visitor_last_year_lva"]
        )

        return self.statistics

    def _process_visitor_type(
        self,
        tx,
        node_label,
        specialization_field,
        map_specialization,
        specialization_stream_mapping,
        stats,
        create_only_new=True,
    ):
        """
        Process a specific type of visitor nodes to create specialization to stream relationships.
        GENERIC: Supports configurable node labels, field names, and show filtering.

        Args:
            tx: Neo4j transaction
            node_label (str): The label of the visitor nodes to process.
            specialization_field (str): The field containing specialization information.
            map_specialization (dict): Dictionary mapping old specialization names to new ones.
            specialization_stream_mapping (dict): Dictionary mapping specializations to streams.
            stats (dict): Statistics dictionary to update.
            create_only_new (bool): If True, only create relationships that don't exist.
        """
        # Additional filter for create_only_new
        additional_filter = ""
        if create_only_new:
            additional_filter = ' AND (v.has_recommendation IS NULL OR v.has_recommendation = "0")'

        # Add show filtering if configured
        show_filter = ""
        if self.show_name:
            show_filter = ' AND v.show = $show_name'

        # Query to get visitor nodes with specializations
        query = f"""
        MATCH (v:{node_label})
        WHERE v.{specialization_field} IS NOT NULL 
        AND LOWER(v.{specialization_field}) <> 'na'
        {show_filter}
        {additional_filter}
        RETURN v, v.{specialization_field} as specializations, 
            v.BadgeId as badge_id, v.Email as email
        """

        # Execute query with parameters if needed
        if self.show_name:
            results = tx.run(query, show_name=self.show_name)
        else:
            results = tx.run(query)
            
        visitor_type_key = node_label.lower().replace(self.visitor_this_year_label.lower(), "visitor_this_year").replace(
            self.visitor_last_year_bva_label.lower(), "visitor_last_year_bva").replace(
            self.visitor_last_year_lva_label.lower(), "visitor_last_year_lva")

        for record in results:
            visitor = record["v"]
            specializations_text = record["specializations"]
            badge_id = record.get("badge_id")
            email = record.get("email")

            stats["visitor_nodes_processed"][visitor_type_key] += 1

            # Skip if BadgeId or Email is not available (needed for identification)
            if not badge_id or not email:
                continue

            # Skip processing if the specialization text is explicitly 'NA'
            if specializations_text.upper() == "NA":
                continue

            # Split specializations by semicolon
            specializations = specializations_text.split(";")

            # Process each specialization
            for spec in specializations:
                spec = spec.strip()

                # Map specialization if needed
                if spec in map_specialization:
                    mapped_spec = map_specialization[spec]
                    stats["specializations_mapped"] += 1
                else:
                    mapped_spec = spec

                # Check if this specialization exists in our mapping
                if mapped_spec in specialization_stream_mapping:
                    stream_dict = specialization_stream_mapping[mapped_spec]
                    stats["specializations_processed"] += 1

                    # For each stream that applies to this specialization
                    for stream_name, applies in stream_dict.items():
                        if applies == "YES":
                            stats["stream_matches_found"] += 1

                            # First find the stream node (case-insensitive search)
                            stream_search_filter = ""
                            if self.show_name:
                                stream_search_filter = ' AND s.show = $show_name'

                            find_stream_query = f"""
                            MATCH (s:{self.stream_label})
                            WHERE LOWER(s.stream) = LOWER($stream_name)
                            {stream_search_filter}
                            RETURN s LIMIT 1
                            """

                            stream_params = {"stream_name": stream_name}
                            if self.show_name:
                                stream_params["show_name"] = self.show_name

                            stream_result = tx.run(find_stream_query, **stream_params)
                            stream_node = stream_result.single()

                            if stream_node:
                                # Create relationship if it doesn't exist
                                visitor_filter = ""
                                if self.show_name:
                                    visitor_filter = ' AND v.show = $show_name'

                                relationship_query = f"""
                                MATCH (v:{node_label})
                                WHERE v.BadgeId = $badge_id AND v.Email = $email{visitor_filter}
                                
                                MATCH (s:{self.stream_label})
                                WHERE LOWER(s.stream) = LOWER($stream_name)
                                {stream_search_filter}
                                
                                MERGE (v)-[r:{self.relationship_name}]->(s)
                                ON CREATE SET r.created_by = 'specialization_processor'
                                RETURN r
                                """

                                rel_params = {
                                    "badge_id": badge_id,
                                    "email": email,
                                    "stream_name": stream_name
                                }
                                if self.show_name:
                                    rel_params["show_name"] = self.show_name

                                try:
                                    rel_result = tx.run(relationship_query, **rel_params)
                                    if rel_result.single():
                                        stats["relationships_created"]["total"] += 1
                                    else:
                                        stats["relationships_skipped"]["total"] += 1
                                except Exception as e:
                                    self.logger.error(
                                        f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error creating relationship: {str(e)}"
                                    )
                                    stats["relationships_failed"]["total"] += 1

    def process(self, create_only_new=True):
        """
        Main processing method that coordinates the entire specialization to stream relationship creation process.
        GENERIC: Maintains backward compatibility while supporting new configuration.

        Args:
            create_only_new (bool): If True, only create relationships that don't already exist.

        Returns:
            dict: Processing statistics
        """
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Starting specialization to stream processing (generic mode)"
        )

        try:
            # Test connection first
            if not self._test_connection():
                raise ConnectionError("Cannot connect to Neo4j database")

            # Load mappings
            map_specialization, specialization_stream_mapping = self.load_mappings()

            # Create relationships
            stats = self.create_specialization_stream_relationships(
                map_specialization, specialization_stream_mapping, create_only_new
            )

            # Log final statistics
            self._log_statistics()

            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Specialization to stream processing completed successfully"
            )

            return stats

        except Exception as e:
            self.logger.error(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Error in specialization to stream processing: {str(e)}"
            )
            raise

    def _log_statistics(self):
        """Log detailed processing statistics"""
        # Log per-visitor-type statistics
        for visitor_type in ["visitor_this_year", "visitor_last_year_bva", "visitor_last_year_lva"]:
            self.logger.info(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - {visitor_type.replace('_', ' ').title()} nodes processed: {self.statistics['visitor_nodes_processed'][visitor_type]}"
            )

        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total visitor nodes processed: {self.statistics['visitor_nodes_processed']['total']}"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total specializations processed: {self.statistics['specializations_processed']}"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total specializations mapped: {self.statistics['specializations_mapped']}"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total stream matches found: {self.statistics['stream_matches_found']}"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total relationships created: {self.statistics['relationships_created']['total']}"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total relationships skipped: {self.statistics['relationships_skipped']['total']}"
        )
        self.logger.info(
            f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - Total relationships failed: {self.statistics['relationships_failed']['total']}"
        )

        # Check for discrepancies
        actual_created = (
            self.statistics["final_count"] - self.statistics["initial_count"]
        )
        if actual_created != self.statistics["relationships_created"]["total"]:
            self.logger.warning(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - WARNING: Discrepancy detected! Database shows {actual_created} new relationships, but code tracked {self.statistics['relationships_created']['total']}."
            )
            self.logger.warning(
                f"{inspect.currentframe().f_code.co_name}:{inspect.currentframe().f_lineno} - This may indicate concurrent database access or transaction issues."
            )